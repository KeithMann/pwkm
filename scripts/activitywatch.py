"""ActivityWatch integration for PWKM daily planning.

Queries the ActivityWatch API and produces structured JSON describing how a
day was actually spent. Correlates window focus with AFK status so only active
(non-idle) time is reported.

Usage:
    python activitywatch.py                    # Yesterday
    python activitywatch.py --date 2026-04-10  # Specific date
    python activitywatch.py --today            # Current day, live
    python activitywatch.py --week             # Last 7 days
    python activitywatch.py --days 14          # Last N days

Configuration:
    PWKM_ACTIVITYWATCH            on | off | unset. See below.
    PWKM_ACTIVITYWATCH_URL        API base. Default http://localhost:5600/api/0
    PWKM_ACTIVITYWATCH_HOSTNAME   Bucket suffix. Discovered if unset.
    PWKM_ACTIVITYWATCH_CATEGORIES Path to a category map. Optional.

THREE STATES, NOT TWO. A service that is absent because nobody wanted it and a
service that is absent because it broke are different situations that deserve
different responses, and a plain reachability check cannot tell them apart.

    unset   Undeclared. The script probes. Unreachable is fine and silent:
            you never asked for it. Reachable prints a one-line notice that
            ActivityWatch is available but unused, because that is probably
            worth knowing and is trivially silenced.

    on      Declared. You have said this should be running. Unreachable is now
            a FAULT: it exits non-zero with the URL it tried, because
            something you expected to be working is not.

    off     Declined. No probe is attempted at all. Not a quieter version of
            unset: the probe is itself a local network call, and someone who
            does not want PWKM touching ActivityWatch should get no probe
            rather than a silent one.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone, time as dt_time
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from pwkm_env import load_env

load_env()

SCRIPT_DIR = Path(__file__).resolve().parent

AW_BASE = os.environ.get("PWKM_ACTIVITYWATCH_URL", "http://localhost:5600/api/0").rstrip("/")
HOSTNAME = os.environ.get("PWKM_ACTIVITYWATCH_HOSTNAME", "").strip()
TZ = ZoneInfo(os.environ.get("LOCAL_TIMEZONE", "America/New_York"))

_MODE_RAW = os.environ.get("PWKM_ACTIVITYWATCH", "").strip().lower()
_ON = {"on", "true", "yes", "1", "expected", "required"}
_OFF = {"off", "false", "no", "0", "disabled"}


def resolve_mode() -> str:
    """Return 'on', 'off', or 'unset'. An unrecognised value is a config typo."""
    if not _MODE_RAW:
        return "unset"
    if _MODE_RAW in _ON:
        return "on"
    if _MODE_RAW in _OFF:
        return "off"
    raise ValueError(
        f"unrecognised PWKM_ACTIVITYWATCH value {_MODE_RAW!r}. "
        f"Use one of: {', '.join(sorted(_ON))} / {', '.join(sorted(_OFF))}, or leave it unset."
    )


def fail(msg: str) -> int:
    """Report a failure and return exit code 1.

    STDERR deliberately: startup.py reads stderr when a helper exits non-zero
    and discards stdout, so a diagnostic printed only to stdout is replaced by
    "Error: Unknown error" in the report.
    """
    print(json.dumps({"error": msg}))
    print(msg, file=sys.stderr)
    return 1


def probe() -> tuple[bool, str]:
    """Is the ActivityWatch server answering? Returns (reachable, detail)."""
    try:
        r = requests.get(f"{AW_BASE}/info", timeout=3)
        r.raise_for_status()
        return True, ""
    except requests.ConnectionError:
        return False, "connection refused"
    except Exception as e:
        return False, str(e)


def discover_hostname() -> str | None:
    """Find the bucket suffix from the server rather than hardcoding a machine name."""
    if HOSTNAME:
        return HOSTNAME
    try:
        r = requests.get(f"{AW_BASE}/buckets", timeout=5)
        r.raise_for_status()
        for bucket in r.json():
            if bucket.startswith("aw-watcher-window_"):
                return bucket[len("aw-watcher-window_"):]
    except Exception:
        return None
    return None

# Category mapping. These defaults are deliberately small and generic: a
# personal taxonomy of every application someone happens to run belongs in a
# config file, not in shipped code.
#
# PWKM_ACTIVITYWATCH_CATEGORIES may point at a JSON file of the shape:
#     {
#       "app_categories":     {"Code.exe": "Programming / VS Code"},
#       "browser_apps":       ["msedge.exe", "chrome.exe"],
#       "browser_title_rules": [["github", "GitHub (web)"],
#                                [["calendar", "google"], "Google Calendar (web)"]]
#     }
# Any key you omit falls back to the defaults below. Browser title rules are
# matched in order against the lowercased window title, so put the specific
# ones first.

DEFAULT_APP_CATEGORIES = {
    "Code.exe": "Programming / VS Code",
    "WindowsTerminal.exe": "Terminal",
    "cmd.exe": "Terminal",
    "powershell.exe": "Terminal",
    "WINWORD.EXE": "Writing / Word",
    "EXCEL.EXE": "Spreadsheets / Excel",
    "POWERPNT.EXE": "Presentations / PowerPoint",
    "OUTLOOK.EXE": "Email / Outlook",
    "explorer.exe": "File Management",
    "notepad.exe": "Text Editing / Notepad",
}

DEFAULT_BROWSER_APPS = ["msedge.exe", "chrome.exe", "firefox.exe", "brave.exe", "safari"]

DEFAULT_BROWSER_TITLE_RULES = [
    ["github", "GitHub (web)"],
    ["stack overflow", "Stack Overflow"],
    ["stackoverflow", "Stack Overflow"],
    ["youtube", "YouTube"],
    ["reddit", "Reddit"],
]


def load_categories():
    """Load the category map, falling back to the generic defaults."""
    app_categories = dict(DEFAULT_APP_CATEGORIES)
    browser_apps = list(DEFAULT_BROWSER_APPS)
    title_rules = [list(r) for r in DEFAULT_BROWSER_TITLE_RULES]

    path = os.environ.get("PWKM_ACTIVITYWATCH_CATEGORIES", "").strip()
    if not path:
        return app_categories, browser_apps, title_rules

    target = Path(path)
    if not target.is_absolute():
        target = SCRIPT_DIR / target
    if not target.exists():
        raise ValueError(f"PWKM_ACTIVITYWATCH_CATEGORIES points at a missing file: {target}")

    try:
        data = json.loads(target.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f"could not read {target}: {e}") from e

    if "app_categories" in data:
        app_categories = dict(data["app_categories"])
    if "browser_apps" in data:
        browser_apps = list(data["browser_apps"])
    if "browser_title_rules" in data:
        title_rules = [list(r) for r in data["browser_title_rules"]]

    return app_categories, browser_apps, title_rules


APP_CATEGORIES, BROWSER_APPS_LIST, BROWSER_TITLE_RULES = {}, [], []
BROWSER_APPS = set()

TIME_BUCKETS = [
    ("morning", 6, 12),
    ("afternoon", 12, 17),
    ("evening", 17, 21),
    ("late_night", 21, 30),
]


def get_bucket(hour):
    for name, start, end in TIME_BUCKETS:
        if end > 24:
            if hour >= start or hour < (end - 24):
                return name
        elif start <= hour < end:
            return name
    return "late_night"


def categorize_app(app, title=""):
    """Map an application (and browser window title) to a display category."""
    if app.lower() in {b.lower() for b in BROWSER_APPS}:
        tl = title.lower()
        for needle, label in BROWSER_TITLE_RULES:
            # A needle may be a string, or a list of strings that must ALL be
            # present. The list form exists because some sites are only
            # identifiable by a combination, e.g. "calendar" plus "google".
            if isinstance(needle, (list, tuple)):
                if all(str(n).lower() in tl for n in needle):
                    return label
            elif str(needle).lower() in tl:
                return label
        return "Web Browsing"

    for app_key, category in APP_CATEGORIES.items():
        if app.lower() == app_key.lower():
            return category

    return f"Other ({app})"


def query_events(bucket, start_iso, end_iso):
    url = f"{AW_BASE}/buckets/{bucket}/events"
    params = {"start": start_iso, "end": end_iso, "limit": -1}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.ConnectionError:
        sys.exit(fail(f"ActivityWatch not reachable at {AW_BASE} (connection refused)"))
    except Exception as e:
        sys.exit(fail(f"ActivityWatch: failed to query {bucket}: {e}"))


def build_active_intervals(afk_events):
    """Build sorted list of (start_dt, end_dt) intervals where user was active."""
    intervals = []
    for event in afk_events:
        if event.get("data", {}).get("status") != "not-afk":
            continue
        start = datetime.fromisoformat(event["timestamp"])
        duration = event.get("duration", 0)
        if duration < 1:
            continue
        end = start + timedelta(seconds=duration)
        intervals.append((start, end))
    intervals.sort(key=lambda x: x[0])
    # Merge overlapping
    merged = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def active_overlap(event_start, event_end, active_intervals):
    """Calculate seconds of overlap between an event and active intervals."""
    total = 0.0
    for a_start, a_end in active_intervals:
        if a_start >= event_end:
            break
        if a_end <= event_start:
            continue
        overlap_start = max(event_start, a_start)
        overlap_end = min(event_end, a_end)
        total += (overlap_end - overlap_start).total_seconds()
    return total


def analyze_day(date_obj):
    day_start = datetime.combine(date_obj, dt_time.min, tzinfo=TZ)
    day_end = datetime.combine(date_obj + timedelta(days=1), dt_time.min, tzinfo=TZ)
    start_iso = day_start.isoformat()
    end_iso = day_end.isoformat()

    window_events = query_events(f"aw-watcher-window_{HOSTNAME}", start_iso, end_iso)
    afk_events = query_events(f"aw-watcher-afk_{HOSTNAME}", start_iso, end_iso)

    # Build active intervals from AFK data
    active_intervals = build_active_intervals(afk_events)

    # Total active time
    total_active_secs = sum((e - s).total_seconds() for s, e in active_intervals)

    # Build active sessions (merge nearby active intervals with < 5 min gaps)
    sessions = []
    for start, end in active_intervals:
        start_et = start.astimezone(TZ)
        end_et = end.astimezone(TZ)
        if sessions:
            prev_end_minutes = _hm_to_minutes(sessions[-1]["end"])
            this_start_minutes = start_et.hour * 60 + start_et.minute
            gap = this_start_minutes - prev_end_minutes
            if 0 <= gap <= 5:
                sessions[-1]["end"] = end_et.strftime("%H:%M")
                sessions[-1]["minutes"] += round((end - start).total_seconds() / 60) + gap
                continue
        minutes = round((end - start).total_seconds() / 60)
        if minutes >= 1:
            sessions.append({
                "start": start_et.strftime("%H:%M"),
                "end": end_et.strftime("%H:%M"),
                "minutes": minutes,
            })

    # Aggregate window time by category, cross-referenced with AFK
    category_active_secs = {}
    category_by_bucket = {}
    top_windows = {}

    for event in window_events:
        ev_start = datetime.fromisoformat(event["timestamp"])
        duration = event.get("duration", 0)
        if duration < 1:
            continue
        ev_end = ev_start + timedelta(seconds=duration)

        # Only count time when user was actively at keyboard
        active_secs = active_overlap(ev_start, ev_end, active_intervals)
        if active_secs < 1:
            continue

        app = event.get("data", {}).get("app", "unknown")
        title = event.get("data", {}).get("title", "")
        category = categorize_app(app, title)

        ev_start_et = ev_start.astimezone(TZ)
        bucket = get_bucket(ev_start_et.hour)

        category_active_secs[category] = category_active_secs.get(category, 0) + active_secs

        if category not in category_by_bucket:
            category_by_bucket[category] = {}
        category_by_bucket[category][bucket] = (
            category_by_bucket[category].get(bucket, 0) + active_secs
        )

        short_title = title[:80] if title else "(no title)"
        if category not in top_windows:
            top_windows[category] = {}
        top_windows[category][short_title] = (
            top_windows[category].get(short_title, 0) + active_secs
        )

    # Build category summary
    categories = []
    for cat, secs in sorted(category_active_secs.items(), key=lambda x: -x[1]):
        if secs < 60:
            continue
        titles = sorted(top_windows.get(cat, {}).items(), key=lambda x: -x[1])[:3]
        categories.append({
            "category": cat,
            "minutes": round(secs / 60),
            "time_of_day": {
                k: round(v / 60)
                for k, v in category_by_bucket.get(cat, {}).items()
                if v >= 60
            },
            "top_windows": [
                {"title": t, "minutes": round(s / 60)} for t, s in titles if s >= 60
            ],
        })

    # Time-of-day active totals
    bucket_totals = {}
    for start, end in active_intervals:
        start_et = start.astimezone(TZ)
        secs = (end - start).total_seconds()
        bucket = get_bucket(start_et.hour)
        bucket_totals[bucket] = bucket_totals.get(bucket, 0) + secs

    return {
        "date": date_obj.isoformat(),
        "day_of_week": date_obj.strftime("%A"),
        "active_minutes": round(total_active_secs / 60),
        "sessions": sessions,
        "time_of_day_minutes": {
            k: round(v / 60) for k, v in bucket_totals.items() if v >= 60
        },
        "categories": categories,
    }


def _hm_to_minutes(hm_str):
    h, m = map(int, hm_str.split(":"))
    return h * 60 + m


def main():
    global APP_CATEGORIES, BROWSER_APPS_LIST, BROWSER_TITLE_RULES, BROWSER_APPS, HOSTNAME

    parser = argparse.ArgumentParser(description="ActivityWatch PWKM integration")
    parser.add_argument("--date", help="Specific date (YYYY-MM-DD)")
    parser.add_argument("--week", action="store_true", help="Last 7 days")
    parser.add_argument("--days", type=int, help="Last N days")
    parser.add_argument("--today", action="store_true", help="Current day (live)")
    args = parser.parse_args()

    try:
        mode = resolve_mode()
    except ValueError as e:
        return fail(f"ActivityWatch: {e}")

    # Declined. No probe at all: the probe is itself the access being refused.
    if mode == "off":
        print(json.dumps({"enabled": False, "message": "ActivityWatch disabled by configuration."}))
        return 0

    reachable, detail = probe()

    # Declared but absent. This is a fault, and it is the whole point of the
    # tri-state: the user said this should be running, so say so loudly.
    if mode == "on" and not reachable:
        return fail(
            f"ActivityWatch is configured as expected (PWKM_ACTIVITYWATCH=on) but is "
            f"not reachable at {AW_BASE} ({detail}). Start the ActivityWatch server, "
            f"correct PWKM_ACTIVITYWATCH_URL, or set PWKM_ACTIVITYWATCH=off if you no "
            f"longer want it."
        )

    # Undeclared and absent. Nobody asked for it; say nothing of substance.
    if mode == "unset" and not reachable:
        print(json.dumps({
            "enabled": False,
            "message": "ActivityWatch not configured and not running.",
        }))
        return 0

    # Undeclared but present. Worth mentioning once, and trivially silenced.
    notice = None
    if mode == "unset" and reachable:
        notice = (f"ActivityWatch is running at {AW_BASE} but PWKM is not configured to "
                  f"use it. Set PWKM_ACTIVITYWATCH=on to include it, or =off to stop "
                  f"this notice.")

    try:
        APP_CATEGORIES, BROWSER_APPS_LIST, BROWSER_TITLE_RULES = load_categories()
    except ValueError as e:
        return fail(f"ActivityWatch: {e}")
    BROWSER_APPS = set(BROWSER_APPS_LIST)

    resolved_host = discover_hostname()
    if not resolved_host:
        msg = (f"ActivityWatch: no aw-watcher-window bucket found at {AW_BASE}. "
               f"Set PWKM_ACTIVITYWATCH_HOSTNAME if your buckets are named unusually.")
        if mode == "on":
            return fail(msg)
        print(json.dumps({"enabled": False, "message": msg}))
        return 0
    HOSTNAME = resolved_host

    today = datetime.now(TZ).date()

    if args.date:
        target = datetime.strptime(args.date, "%Y-%m-%d").date()
        result = analyze_day(target)
    elif args.week:
        result = {"period": "last_7_days",
                  "days": [analyze_day(today - timedelta(days=i)) for i in range(7, 0, -1)]}
    elif args.days:
        result = {"period": f"last_{args.days}_days",
                  "days": [analyze_day(today - timedelta(days=i)) for i in range(args.days, 0, -1)]}
    elif args.today:
        result = analyze_day(today)
    else:
        result = analyze_day(today - timedelta(days=1))

    if notice:
        result = dict(result)
        result["notice"] = notice

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
