"""Goodreads Currently-Reading sync with Notion Reading Queue reconciliation.

Fetches your Goodreads currently-reading shelf via authenticated RSS,
queries the Notion Reading Queue for entries with Status="Reading" via a real
property filter (not semantic search), computes the diff via normalized title
matching, and (by default) creates Notion pages for any books that are on the
Goodreads shelf but not in Notion.

The reconciliation is done here so the startup protocol does not have to rely
on Claude doing property-filter work via semantic search, which silently does
not filter by property values.

Usage:
    python goodreads_sync.py [--json] [--no-create]

Options:
    --json       Emit a structured JSON object instead of human-readable output.
    --no-create  Do not create Notion pages for to_add items; report only.

JSON output keys:
    goodreads_currently_reading  list of Goodreads RSS entries
    notion_currently_reading     list of Notion Reading Queue entries (Status=Reading)
    added_to_notion              list of pages just created (empty if --no-create)
    needs_review                 list of Notion entries that are Status=Reading but
                                 are no longer on the Goodreads currently-reading shelf
                                 (likely candidates for Completed or Paused)
    errors                       optional list of non-fatal errors

Configuration (see .env.example):
    NOTION_API_KEY            Notion integration secret
    PWKM_READING_QUEUE_DB_ID  The Reading Queue database ID
    GOODREADS_USER_ID         Numeric user ID from your Goodreads profile URL
    GOODREADS_RSS_KEY         From the RSS link on your shelf page

    Goodreads profiles can be private; the RSS key is what makes the feed
    readable, so treat it as a credential.

    Set nothing and this script skips cleanly, like every other optional part
    of the startup report.

    Property names on the Reading Queue database are assumed to be Title,
    Author, Status and Started, with Status a select containing "Reading".
"""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

import os

import requests

from pwkm_env import load_env

load_env()

# Goodreads RSS feed. Credentials (user ID + RSS key) are loaded from .env,
# not hardcoded. See build_goodreads_feed_url() and main().
SHELF = "currently-reading"


def build_goodreads_feed_url(user_id: str, rss_key: str, shelf: str = SHELF) -> str:
    """Build the authenticated Goodreads RSS feed URL from credentials."""
    return (
        f"https://www.goodreads.com/review/list_rss/{user_id}"
        f"?key={rss_key}&shelf={shelf}"
    )

# Notion Reading Queue. Single-data-source database, so the 2022-06-28 query
# endpoint at /databases/{id}/query works, and /pages with parent.database_id
# accepts the database ID for creates.
NOTION_READING_QUEUE_DB_ID = os.environ.get("PWKM_READING_QUEUE_DB_ID", "").strip()
NOTION_API_VERSION = "2022-06-28"
NOTION_PAGES_URL = "https://api.notion.com/v1/pages"


def notion_query_url() -> str:
    return f"https://api.notion.com/v1/databases/{NOTION_READING_QUEUE_DB_ID}/query"

GOODREADS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

TIMEOUT = 15


def fetch_goodreads_currently_reading(feed_url: str):
    """Fetch and parse the Goodreads currently-reading RSS feed."""
    response = requests.get(feed_url, headers=GOODREADS_HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    root = ET.fromstring(response.text)
    items = root.findall(".//item")

    books = []
    for item in items:
        def text_of(tag):
            el = item.find(tag)
            return el.text.strip() if (el is not None and el.text) else ""

        books.append({
            "title": unescape(text_of("title")) or "Unknown",
            "author": unescape(text_of("author_name")) or "Unknown",
            "book_id": text_of("book_id"),
            "goodreads_url": text_of("guid"),
            "added_date": text_of("pubDate"),
        })
    return books


def notion_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
    }


def fetch_notion_currently_reading(api_key: str) -> list:
    """Query the Notion Reading Queue for entries with Status='Reading'."""
    headers = notion_headers(api_key)
    payload = {
        "filter": {"property": "Status", "select": {"equals": "Reading"}},
        "page_size": 100,
    }

    pages = []
    has_more = True
    start_cursor = None
    while has_more:
        if start_cursor:
            payload["start_cursor"] = start_cursor
        response = requests.post(notion_query_url(), headers=headers, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        pages.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    books = []
    for page in pages:
        props = page.get("properties", {})

        title_array = (props.get("Title") or {}).get("title", []) or []
        title = title_array[0].get("plain_text", "") if title_array else ""

        author_array = (props.get("Author") or {}).get("rich_text", []) or []
        author = author_array[0].get("plain_text", "") if author_array else ""

        started_obj = (props.get("Started") or {}).get("date") or {}
        started_date = started_obj.get("start", "") if started_obj else ""

        books.append({
            "title": title,
            "author": author,
            "started": started_date,
            "notion_url": page.get("url", ""),
            "page_id": page.get("id", ""),
        })
    return books


_TITLE_NORMALIZE_CUTS = (": ", " (")


def normalize_title(title: str) -> str:
    """Strip subtitle/series suffix from a book title for cross-source matching.

    'A Drop of Corruption (Shadow of the Leviathan, #2)' -> 'a drop of corruption'
    'Coders: The Making of a New Tribe...'              -> 'coders'
    """
    if not title:
        return ""
    t = title.strip().lower()
    cut_idx = len(t)
    for sep in _TITLE_NORMALIZE_CUTS:
        idx = t.find(sep)
        if idx >= 0 and idx < cut_idx:
            cut_idx = idx
    return t[:cut_idx].strip()


def reconcile(goodreads_books: list, notion_books: list) -> dict:
    """Compute the diff between Goodreads currently-reading and Notion Status=Reading."""
    notion_by_key = {}
    for nb in notion_books:
        key = normalize_title(nb["title"])
        if key:
            notion_by_key[key] = nb

    goodreads_by_key = {}
    for gb in goodreads_books:
        key = normalize_title(gb["title"])
        if key:
            goodreads_by_key[key] = gb

    to_add = [gb for key, gb in goodreads_by_key.items() if key not in notion_by_key]
    needs_review = [nb for key, nb in notion_by_key.items() if key not in goodreads_by_key]
    return {"to_add": to_add, "needs_review": needs_review}


def goodreads_pubdate_to_iso_date(pub_date: str) -> str:
    """Convert a Goodreads RFC 822 pubDate (e.g. 'Mon, 27 Apr 2026 21:56:09 -0700') to ISO date.

    Returns empty string on parse failure.
    """
    if not pub_date:
        return ""
    try:
        dt = parsedate_to_datetime(pub_date)
        return dt.date().isoformat()
    except (TypeError, ValueError):
        return ""


def create_notion_reading_page(api_key: str, book: dict) -> dict:
    """Create a Notion Reading Queue page for a Goodreads book.

    Returns the API response (dict) on success, or {'error': ...} on failure.
    """
    headers = notion_headers(api_key)
    started_iso = goodreads_pubdate_to_iso_date(book.get("added_date", ""))

    properties = {
        "Title": {"title": [{"type": "text", "text": {"content": book.get("title", "")}}]},
        "Author": {"rich_text": [{"type": "text", "text": {"content": book.get("author", "")}}]},
        "Status": {"select": {"name": "Reading"}},
    }
    if started_iso:
        properties["Started"] = {"date": {"start": started_iso}}

    payload = {
        "parent": {"database_id": NOTION_READING_QUEUE_DB_ID},
        "properties": properties,
    }

    try:
        response = requests.post(NOTION_PAGES_URL, headers=headers, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e), "title": book.get("title", "")}


def main():
    parser = argparse.ArgumentParser(description="Goodreads <-> Notion Reading Queue sync")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--no-create", action="store_true",
                        help="Do not create Notion pages; report only")
    args = parser.parse_args()

    errors = []

    # Unconfigured is not a failure: skip cleanly, like every other optional
    # part of the startup report.
    required = {
        "NOTION_API_KEY": os.environ.get("NOTION_API_KEY"),
        "PWKM_READING_QUEUE_DB_ID": NOTION_READING_QUEUE_DB_ID,
        "GOODREADS_USER_ID": os.environ.get("GOODREADS_USER_ID"),
        "GOODREADS_RSS_KEY": os.environ.get("GOODREADS_RSS_KEY"),
    }
    if not any(required.values()):
        msg = ("Goodreads sync not configured. Set NOTION_API_KEY, "
               "PWKM_READING_QUEUE_DB_ID, GOODREADS_USER_ID and GOODREADS_RSS_KEY "
               "in .env to enable it.")
        print(json.dumps({"configured": False, "message": msg}) if args.json else f"[{msg}]")
        sys.exit(0)

    # Partially configured IS a failure: someone started and did not finish,
    # and silently skipping would hide that.
    missing = [k for k, v in required.items() if not v]
    if missing:
        _emit_error(args.json, "Goodreads sync misconfigured; missing: " + ", ".join(missing))
        sys.exit(1)

    env = dict(os.environ)

    api_key = env.get("NOTION_API_KEY")
    if not api_key:
        _emit_error(args.json, "NOTION_API_KEY missing from .env")
        sys.exit(1)

    goodreads_user_id = env.get("GOODREADS_USER_ID")
    goodreads_rss_key = env.get("GOODREADS_RSS_KEY")
    if not goodreads_user_id or not goodreads_rss_key:
        _emit_error(args.json,
                    "GOODREADS_USER_ID and/or GOODREADS_RSS_KEY missing from .env")
        sys.exit(1)
    feed_url = build_goodreads_feed_url(goodreads_user_id, goodreads_rss_key)

    try:
        gr_books = fetch_goodreads_currently_reading(feed_url)
    except requests.RequestException as e:
        _emit_error(args.json, f"Goodreads fetch failed: {e}")
        sys.exit(1)

    try:
        nt_books = fetch_notion_currently_reading(api_key)
    except requests.RequestException as e:
        _emit_error(args.json, f"Notion query failed: {e}")
        sys.exit(1)

    diff = reconcile(gr_books, nt_books)

    added = []
    if diff["to_add"] and not args.no_create:
        for book in diff["to_add"]:
            result = create_notion_reading_page(api_key, book)
            if "error" in result:
                errors.append(f"Create failed for '{book['title']}': {result['error']}")
            else:
                added.append({
                    "title": book["title"],
                    "author": book["author"],
                    "notion_url": result.get("url", ""),
                    "page_id": result.get("id", ""),
                })

    if args.json:
        out = {
            "goodreads_currently_reading": gr_books,
            "notion_currently_reading": nt_books,
            "added_to_notion": added,
            "needs_review": diff["needs_review"],
        }
        if errors:
            out["errors"] = errors
        print(json.dumps(out, indent=2))
        return

    # Human-readable
    print(f"Goodreads currently-reading ({len(gr_books)}):")
    for b in gr_books:
        print(f"  - {b['title']} by {b['author']}")
    print()
    print(f"Notion Reading Queue (Status=Reading) ({len(nt_books)}):")
    for b in nt_books:
        print(f"  - {b['title']} by {b['author']}")
    print()

    if args.no_create:
        if diff["to_add"]:
            print(f"To add to Notion ({len(diff['to_add'])}) [--no-create, not created]:")
            for b in diff["to_add"]:
                print(f"  - {b['title']} by {b['author']}")
        else:
            print("To add to Notion: none")
    else:
        if added:
            print(f"Added to Notion ({len(added)}):")
            for b in added:
                print(f"  - {b['title']} by {b['author']}  {b['notion_url']}")
        elif diff["to_add"]:
            print(f"Tried to add ({len(diff['to_add'])}) but all failed; see errors below.")
        else:
            print("Added to Notion: none (already in sync)")

    print()
    if diff["needs_review"]:
        print(f"Needs review ({len(diff['needs_review'])}) "
              "(in Notion as Reading, not on Goodreads shelf):")
        for b in diff["needs_review"]:
            print(f"  - {b['title']} by {b['author']}  {b['notion_url']}")
    else:
        print("Needs review: none")

    if errors:
        print()
        print("Errors:")
        for err in errors:
            print(f"  - {err}")


def _emit_error(as_json: bool, msg: str) -> None:
    """Report an error.

    The message goes to STDERR deliberately. startup.py reads stderr when a
    helper exits non-zero and discards stdout, so a diagnostic printed only to
    stdout is replaced by "Error: Unknown error" in the report. The JSON form
    still goes to stdout for direct callers.
    """
    if as_json:
        print(json.dumps({"error": msg}))
    print(f"Error: {msg}", file=sys.stderr)


if __name__ == "__main__":
    main()
