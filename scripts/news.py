#!/usr/bin/env python3
"""
News scan for the startup report: general headlines plus an optional tech section.

Usage:
    python news.py                  # Human-readable output
    python news.py --json           # JSON output
    python news.py --limit 5        # Override the general per-source limit
    python news.py --tech-limit 3   # Override the tech per-source limit
    python news.py --no-tech        # Skip the tech section entirely

Configuration:
    Feeds and filters live in a JSON file, not in .env. Ten feed URLs and two
    substantial regexes do not belong on an environment-variable line.

    PWKM_NEWS_FEEDS_FILE   Path to that file.
                           Default: news_feeds.json beside this script.

    Copy news_feeds.example.json to news_feeds.json and edit. If the file is
    absent the section skips cleanly, like every other optional part of the
    startup report.

File shape (both sections optional):

    {
      "general": {
        "limit": 5,
        "feeds": {"BBC": "https://..."},
        "exclude_categories": ["sport", "celebrity"],
        "exclude_title_pattern": "\\\\b(?:horoscope|recipe)\\\\b"
      },
      "tech": { ... same shape ... }
    }

Filtering is deliberately two-layered. `exclude_categories` matches as a
substring against each entry's declared categories, which is cheap and catches
well-tagged feeds. `exclude_title_pattern` is a single case-insensitive regex
against the headline, for feeds that tag nothing useful. Leave either out to
skip that layer.

Uses requests when available, urllib otherwise. No other external packages.
"""

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from pwkm_env import load_env

try:
    import requests as _requests
except ImportError:
    _requests = None

load_env()

SCRIPT_DIR = Path(__file__).resolve().parent
FEEDS_FILE = Path(os.environ.get("PWKM_NEWS_FEEDS_FILE", str(SCRIPT_DIR / "news_feeds.json")))
TIMEOUT = 10


def fail(msg: str, use_json: bool) -> int:
    """Report a failure and return exit code 1.

    The message goes to STDERR deliberately. startup.py reads stderr when a
    helper exits non-zero and discards stdout, so a diagnostic printed only to
    stdout is replaced by "Error: Unknown error" in the report.
    """
    if use_json:
        print(json.dumps({"error": msg}))
    print(msg, file=sys.stderr)
    return 1


def build_section(raw: dict, name: str):
    """Turn one section of the config into (feeds, limit, exclude_fn).

    Raises ValueError with an actionable message on a bad regex, since a
    silently-ignored filter is worse than a refusal to start.
    """
    feeds = dict(raw.get("feeds") or {})
    limit = int(raw.get("limit", 5))
    categories = {c.strip().lower() for c in (raw.get("exclude_categories") or []) if c.strip()}

    pattern = raw.get("exclude_title_pattern") or ""
    title_re = None
    if pattern:
        try:
            title_re = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"invalid exclude_title_pattern in section {name!r}: {e}") from e

    def exclude(entry: dict) -> bool:
        if not entry["title"]:
            return True
        for cat in entry["categories"]:
            for excl in categories:
                if excl in cat:
                    return True
        return bool(title_re and title_re.search(entry["title"]))

    return feeds, limit, exclude

def fetch_rss(url: str) -> bytes | None:
    """Fetch a feed. Prefers requests, which handles gzip more reliably."""
    if _requests is None:
        import urllib.request
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PWKM/1.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read()
        except Exception:
            return None
    try:
        resp = _requests.get(url, timeout=TIMEOUT, headers={"User-Agent": "PWKM/1.0"})
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None


def _clean_description(text: str) -> str:
    """Strip HTML, decode common entities, and truncate on a sentence boundary."""
    if not text:
        return ""
    text = re.sub(r"<!\[CDATA\[|\]\]>", "", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 250:
        cut = text[:250].rfind(". ")
        text = text[:cut + 1] if cut > 100 else text[:250].rsplit(" ", 1)[0] + "..."
    return text


def parse_entries(data: bytes) -> list[dict]:
    """Parse RSS and Atom entries from feed data."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return []

    entries = []

    for item in root.iter("item"):
        cats = {c.text.strip().lower() for c in item.findall("category") if c.text}
        entries.append({
            "title": (item.findtext("title") or "").strip(),
            "link": (item.findtext("link") or "").strip(),
            "description": _clean_description((item.findtext("description") or "").strip()),
            "categories": cats,
        })

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("atom:entry", ns):
        link_el = entry.find("atom:link[@rel='alternate']", ns) or entry.find("atom:link", ns)
        desc = (entry.findtext("atom:summary", default="", namespaces=ns)).strip()
        if not desc:
            desc = (entry.findtext("atom:content", default="", namespaces=ns)).strip()
        cats = {c.get("term", "").lower() for c in entry.findall("atom:category", ns) if c.get("term")}
        entries.append({
            "title": (entry.findtext("atom:title", default="", namespaces=ns)).strip(),
            "link": link_el.get("href", "") if link_el is not None else "",
            "description": _clean_description(desc),
            "categories": cats,
        })

    return entries


def fetch_and_filter(name: str, url: str, limit: int, exclude_fn):
    """Fetch, parse, filter, and cap one feed."""
    data = fetch_rss(url)
    if data is None:
        return name, []
    entries = parse_entries(data)
    return name, [e for e in entries if not exclude_fn(e)][:limit]


def render_section(lines: list[str], feeds: dict, results: dict) -> None:
    """Append one section's headlines, preserving configured feed order."""
    for source in feeds:
        entries = results.get(source, [])
        if not entries:
            lines.append(f"  {source}: [unavailable]")
            continue
        lines.append(f"  {source}:")
        for e in entries:
            lines.append(f"    - {e['title']}")
            if e.get("description"):
                lines.append(f"      {e['description']}")
            if e.get("link"):
                lines.append(f"      {e['link']}")


def as_payload(feeds: dict, results: dict) -> dict:
    return {
        src: [
            {"title": e["title"], "link": e["link"], "description": e.get("description", "")}
            for e in results.get(src, [])
        ]
        for src in feeds
    }

def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="News scan for the startup report")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--limit", type=int, default=None,
                        help="Override the general per-source limit")
    parser.add_argument("--tech-limit", type=int, default=None,
                        help="Override the tech per-source limit")
    parser.add_argument("--no-tech", action="store_true", help="Skip the tech section")
    args = parser.parse_args()

    if not FEEDS_FILE.exists():
        msg = (f"News not configured. Copy news_feeds.example.json to "
               f"{FEEDS_FILE} to enable this section.")
        print(json.dumps({"configured": False, "message": msg}) if args.json else f"[{msg}]")
        # Exit 0: an unconfigured optional section is not a failure.
        return 0

    try:
        config = json.loads(FEEDS_FILE.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as e:
        return fail(f"News unavailable: could not read {FEEDS_FILE}: {e}", args.json)

    try:
        gen_feeds, gen_limit, gen_exclude = build_section(config.get("general") or {}, "general")
        tech_feeds, tech_limit, tech_exclude = build_section(config.get("tech") or {}, "tech")
    except ValueError as e:
        return fail(f"News unavailable: {e}", args.json)

    if args.limit is not None:
        gen_limit = args.limit
    if args.tech_limit is not None:
        tech_limit = args.tech_limit
    if args.no_tech:
        tech_feeds = {}

    if not gen_feeds and not tech_feeds:
        msg = f"News not configured: no feeds listed in {FEEDS_FILE}."
        print(json.dumps({"configured": False, "message": msg}) if args.json else f"[{msg}]")
        return 0

    now = datetime.now()
    ts = now.strftime("%I:%M %p").lstrip("0").lower()

    plan = [("general", n, u, gen_limit, gen_exclude) for n, u in gen_feeds.items()]
    plan += [("tech", n, u, tech_limit, tech_exclude) for n, u in tech_feeds.items()]

    results = {"general": {}, "tech": {}}
    with ThreadPoolExecutor(max_workers=min(8, len(plan)) or 1) as executor:
        futures = {
            executor.submit(fetch_and_filter, name, url, limit, fn): (kind, name)
            for (kind, name, url, limit, fn) in plan
        }
        for future in as_completed(futures):
            kind, name = futures[future]
            _, entries = future.result()
            results[kind][name] = entries

    if args.json:
        output = {
            "generated": now.strftime("%Y-%m-%d %H:%M"),
            "sources": as_payload(gen_feeds, results["general"]),
        }
        if tech_feeds:
            output["tech_sources"] = as_payload(tech_feeds, results["tech"])
        print(json.dumps(output, indent=2))
        return 0

    lines = [f"[Generated: {now.strftime('%Y-%m-%d')} {ts}]"]
    render_section(lines, gen_feeds, results["general"])
    if tech_feeds:
        lines.append("")
        lines.append("--- TECH NEWS ---")
        render_section(lines, tech_feeds, results["tech"])

    print("\n".join(lines))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())