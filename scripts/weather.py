#!/usr/bin/env python3
"""
Weather and alerts for the startup report.

Usage:
    python weather.py              # Human-readable output
    python weather.py --json       # JSON output for structured parsing

Configuration (see .env.example):
    PWKM_WEATHER_LAT        Latitude, e.g. 43.65
    PWKM_WEATHER_LON        Longitude, e.g. -79.38
    PWKM_WEATHER_LOCATION   Display name, e.g. "Toronto, ON". Optional.
    PWKM_WEATHER_PROVIDER   Default "environment_canada".

If latitude and longitude are not set, the script says so and exits 0. Weather
is an optional section; an unconfigured one should read as "not set up", not
as a failure.

PROVIDER SUPPORT: Environment Canada only, which covers Canada only. The
provider seam below exists so another source can be added without touching the
rest of the script; nothing else is implemented yet. If you are outside Canada,
leave the coordinates unset and the section will skip cleanly.

No external packages required. Standard library only.
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

from pwkm_env import load_env

load_env()

LAT = os.environ.get("PWKM_WEATHER_LAT", "").strip()
LON = os.environ.get("PWKM_WEATHER_LON", "").strip()
LOCATION = os.environ.get("PWKM_WEATHER_LOCATION", "").strip()
PROVIDER = os.environ.get("PWKM_WEATHER_PROVIDER", "environment_canada").strip()

TIMEOUT = 10  # seconds
NS = {"atom": "http://www.w3.org/2005/Atom"}


def ec_urls(lat: str, lon: str) -> tuple[str, str]:
    """Environment Canada Atom feed URLs for a coordinate pair."""
    return (
        f"https://weather.gc.ca/rss/weather/{lat}_{lon}_e.xml",
        f"https://weather.gc.ca/rss/alerts/{lat}_{lon}_e.xml",
    )


def fetch_xml(url: str) -> ET.Element | None:
    """Fetch and parse an XML feed. Returns the root element, or None on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PWKM/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return ET.fromstring(resp.read())
    except Exception:
        return None


def strip_html(text: str) -> str:
    """Remove HTML tags and clean up whitespace."""
    text = text.replace("<br/>", " | ").replace("<br />", " | ")
    text = text.replace("&deg;", "\u00b0").replace("&amp;", "&")
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def parse_weather_feed(root: ET.Element) -> dict:
    """Parse the Environment Canada weather Atom feed."""
    result = {"current": None, "forecasts": [], "warnings": [], "updated": None}

    for entry in root.findall("atom:entry", NS):
        title_el = entry.find("atom:title", NS)
        summary_el = entry.find("atom:summary", NS)
        category_el = entry.find("atom:category", NS)

        if title_el is None:
            continue

        title = title_el.text or ""
        summary = strip_html(summary_el.text or "") if summary_el is not None else ""
        cat = category_el.get("term", "") if category_el is not None else ""

        if cat == "Current Conditions":
            result["current"] = {"title": title, "details": summary}
            updated_el = entry.find("atom:updated", NS)
            if updated_el is not None:
                result["updated"] = updated_el.text
        elif cat == "Weather Forecasts":
            result["forecasts"].append({"period": title, "summary": summary})
        elif cat == "Warnings and Watches":
            result["warnings"].append({"title": title, "summary": summary})

    return result


def parse_alerts_feed(root: ET.Element) -> list[dict]:
    """Parse the Environment Canada alerts Atom feed."""
    alerts = []
    for entry in root.findall("atom:entry", NS):
        title_el = entry.find("atom:title", NS)
        summary_el = entry.find("atom:summary", NS)
        if title_el is None:
            continue
        title = title_el.text or ""
        if "no watches or warnings" in title.lower():
            continue
        summary = strip_html(summary_el.text or "") if summary_el is not None else ""
        alerts.append({"title": title, "summary": summary})
    return alerts

def display_location() -> str:
    """Label for the report header. Falls back to the coordinates."""
    if LOCATION:
        return LOCATION
    return f"{LAT}, {LON}"


def format_human(weather: dict, alerts: list[dict], source: str) -> str:
    """Format weather data for the startup report."""
    lines = []
    now = datetime.now()
    ts = now.strftime("%I:%M %p").lstrip("0").lower()
    lines.append(f"[Generated: {now.strftime('%Y-%m-%d')} {ts}]")
    lines.append(f"{display_location()} ({source})")

    if weather.get("current"):
        lines.append(f"  {weather['current']['title']}")
        if weather["current"]["details"]:
            lines.append(f"  {weather['current']['details']}")

    # The same warning usually appears twice: once in the weather feed's
    # "Warnings and Watches" category and again in the dedicated alerts feed.
    # Deduplicate on the normalised title so it is reported once.
    seen = set()
    combined = []
    for item in list(weather.get("warnings", [])) + list(alerts):
        title = (item.get("title") or "").strip()
        if not title or "no watches or warnings" in title.lower():
            continue
        key = " ".join(title.lower().split())
        if key in seen:
            continue
        seen.add(key)
        combined.append(title)

    if combined:
        lines.append("  ALERTS:")
        for title in combined:
            lines.append(f"    {title}")
    else:
        lines.append("  No active alerts.")

    # First four periods with detail, the rest as one-liners. The extended
    # period titles already carry the high, low, and precipitation chance.
    if weather.get("forecasts"):
        lines.append("  Forecast:")
        for i, fc in enumerate(weather["forecasts"]):
            if i < 4:
                summary = re.sub(r"\s*Forecast issued.*$", "", fc["summary"])
                if len(summary) > 200:
                    summary = summary[:200] + "..."
                lines.append(f"    {fc['period']}: {summary}")
            else:
                lines.append(f"    {fc['period']}")

    return "\n".join(lines)


def format_json(weather: dict, alerts: list[dict], source: str, feed_url: str) -> str:
    """Format weather data as JSON."""
    return json.dumps({
        "location": display_location(),
        "latitude": LAT,
        "longitude": LON,
        "source": source,
        "feed_url": feed_url,
        "current": weather.get("current"),
        "warnings": weather.get("warnings", []),
        "alerts": alerts,
        "forecasts": weather.get("forecasts", []),
        "updated": weather.get("updated"),
    }, indent=2)


def run_environment_canada(use_json: bool) -> int:
    """Fetch, parse, and print Environment Canada data. Returns an exit code."""
    feed_url, alerts_url = ec_urls(LAT, LON)
    source = "Environment Canada"

    root = fetch_xml(feed_url)
    if root is None:
        msg = "Failed to fetch weather feed"
        print(json.dumps({"error": msg}) if use_json else f"[Weather unavailable: {msg}]")
        return 1

    weather = parse_weather_feed(root)

    # Alerts live in a separate feed. A failure there is not fatal: current
    # conditions and the forecast are still worth reporting.
    alerts_root = fetch_xml(alerts_url)
    alerts = parse_alerts_feed(alerts_root) if alerts_root is not None else []

    print(format_json(weather, alerts, source, feed_url) if use_json
          else format_human(weather, alerts, source))
    return 0


PROVIDERS = {
    "environment_canada": run_environment_canada,
}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Weather for the startup report")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if not LAT or not LON:
        msg = ("Weather not configured. Set PWKM_WEATHER_LAT and "
               "PWKM_WEATHER_LON in .env to enable this section.")
        print(json.dumps({"configured": False, "message": msg}) if args.json
              else f"[{msg}]")
        # Exit 0: an unconfigured optional section is not a failure.
        return 0

    handler = PROVIDERS.get(PROVIDER)
    if handler is None:
        msg = (f"Unknown PWKM_WEATHER_PROVIDER {PROVIDER!r}. "
               f"Supported: {', '.join(sorted(PROVIDERS))}.")
        print(json.dumps({"error": msg}) if args.json else f"[Weather unavailable: {msg}]")
        return 1

    return handler(args.json)


if __name__ == "__main__":
    sys.exit(main())