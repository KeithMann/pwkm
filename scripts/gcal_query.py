#!/usr/bin/env python3
"""
Google Calendar Query - Compact Output

Returns calendar events in a compact format suitable for context-constrained
AI sessions. Only outputs the fields that matter: time, summary, location.

Uses the same OAuth credentials as gcal_create.py.

Usage:
    python gcal_query.py today              # Today's events
    python gcal_query.py tomorrow            # Tomorrow's events
    python gcal_query.py today+tomorrow      # Today and tomorrow (startup default)
    python gcal_query.py week                # Next 7 days
    python gcal_query.py 2026-02-10          # Specific date
    python gcal_query.py 2026-02-10 2026-02-14  # Date range
    python gcal_query.py today --json        # JSON output
    python gcal_query.py today --raw         # Full API response (debugging)
    python gcal_query.py today --classify    # Classify events vs current time
    python gcal_query.py today --classify --json  # Classified JSON output
    python gcal_query.py --auth              # Re-authorize OAuth token (no date_spec needed)
"""

import os
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from dotenv import load_dotenv
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"Missing required package: {e}")
    sys.exit(1)

# Load .env before any module-level os.environ read below. Doing this
# later, or inside a function, is too late: the constants are evaluated
# at import time. See pwkm_env.py.
from pwkm_env import load_env

load_env()

SCOPES = ['https://www.googleapis.com/auth/calendar.events']
SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / '.env'
TOKEN_FILE = SCRIPT_DIR / 'gcal_token.json'
CREDENTIALS_FILE = SCRIPT_DIR / 'gcal_credentials.json'
TZ_NAME = os.environ.get("LOCAL_TIMEZONE", "America/New_York")
TZ = ZoneInfo(TZ_NAME)

# Secondary calendars merged into default (primary) queries.
# Keith has free/busy-only access to the Harness calendar, so its events
# arrive as untitled busy blocks unless titles are supplied separately
# (e.g. pasted from the Harness Slack calendar bot at startup).
# Comma-separated calendar IDs. Useful for calendars you have free/busy-only
# access to, where titles must be supplied another way.
_SECONDARY = os.environ.get('PWKM_SECONDARY_CALENDARS', '').strip()
SECONDARY_CALENDARS = [c.strip() for c in _SECONDARY.split(',') if c.strip()]
CAL_LABELS = {c: c.split('@')[0] for c in SECONDARY_CALENDARS}


def load_client_config():
    """Load OAuth client configuration from .env file."""
    import os
    load_dotenv(ENV_FILE)
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    if not client_id or not client_secret:
        print("Error: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in .env file")
        print(f"Expected location: {ENV_FILE}")
        sys.exit(1)
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"]
        }
    }


def get_credentials(force_auth=False):
    """Get valid credentials, refreshing or re-authorizing as needed."""
    load_dotenv(ENV_FILE)
    creds = None

    if TOKEN_FILE.exists() and not force_auth:
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception:
            pass

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            print("Starting OAuth authorization flow...")
            print("A browser window will open for you to authorize access.")
            client_config = load_client_config()
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
            print("Authorization successful!")

    with open(TOKEN_FILE, 'w') as f:
        f.write(creds.to_json())

    return creds

def resolve_dates(args):
    """Resolve date arguments to (start, end) datetime range."""
    today = datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0)
    
    if args.date_spec == 'today':
        start = today
        end = today + timedelta(days=1)
    elif args.date_spec == 'tomorrow':
        start = today + timedelta(days=1)
        end = today + timedelta(days=2)
    elif args.date_spec in ('today+tomorrow', 'startup'):
        start = today
        end = today + timedelta(days=2)
    elif args.date_spec == 'week':
        start = today
        end = today + timedelta(days=7)
    else:
        try:
            start = datetime.strptime(args.date_spec, '%Y-%m-%d').replace(tzinfo=TZ)
            if args.end_date:
                end = datetime.strptime(args.end_date, '%Y-%m-%d').replace(tzinfo=TZ) + timedelta(days=1)
            else:
                end = start + timedelta(days=1)
        except ValueError:
            print(f"Error: Invalid date '{args.date_spec}'. Use YYYY-MM-DD, 'today', 'tomorrow', or 'week'.")
            sys.exit(1)
    
    return start, end


def format_time(dt_str, date_str=None):
    """Format a datetime or date string compactly."""
    if date_str:
        return "all-day"
    if dt_str:
        dt = datetime.fromisoformat(dt_str)
        try:
            return dt.strftime('%#I:%M %p').lower()
        except ValueError:
            return dt.strftime('%-I:%M %p').lower()
    return "?"


def classify_event(event, now):
    """Classify an event relative to the current time."""
    start_info = event.get('start', {})
    end_info = event.get('end', {})
    
    if start_info.get('date'):
        event_date = datetime.strptime(start_info['date'], '%Y-%m-%d').date()
        today = now.date()
        if event_date < today:
            return {'status': 'completed', 'detail': ''}
        elif event_date == today:
            return {'status': 'in_progress', 'detail': 'all day'}
        else:
            days_until = (event_date - today).days
            return {'status': 'upcoming_later', 'detail': f'in {days_until}d'}
    
    start_dt = datetime.fromisoformat(start_info['dateTime'])
    end_dt = datetime.fromisoformat(end_info['dateTime'])
    
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=TZ)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=TZ)
    
    if now >= end_dt:
        return {'status': 'completed', 'detail': ''}
    elif now >= start_dt:
        elapsed = int((now - start_dt).total_seconds() / 60)
        return {'status': 'in_progress', 'detail': f'started {elapsed} min ago'}
    else:
        minutes_until = int((start_dt - now).total_seconds() / 60)
        if minutes_until <= 30:
            return {'status': 'upcoming_imminent', 'detail': f'in {minutes_until} min'}
        else:
            if minutes_until < 60:
                return {'status': 'upcoming_later', 'detail': f'in {minutes_until} min'}
            else:
                hours = minutes_until // 60
                mins = minutes_until % 60
                if mins == 0:
                    return {'status': 'upcoming_later', 'detail': f'in {hours}h'}
                else:
                    return {'status': 'upcoming_later', 'detail': f'in {hours}h {mins}m'}


STATUS_LABELS = {
    'completed': 'DONE',
    'in_progress': 'NOW',
    'upcoming_imminent': 'SOON',
    'upcoming_later': 'LATER',
}


def format_event_compact(event, classify=False, now=None):
    """Format a single event as a compact one-liner."""
    start = event.get('start', {})
    end = event.get('end', {})
    
    start_time = format_time(start.get('dateTime'), start.get('date'))
    end_time = format_time(end.get('dateTime'), end.get('date'))
    summary = event.get('summary', '(no title)')
    location = event.get('location', '')
    
    if start_time == 'all-day':
        line = f"  all-day: {summary}"
    else:
        line = f"  {start_time}-{end_time}: {summary}"
    
    if location:
        line += f" [{location}]"
    
    if classify and now:
        cls = classify_event(event, now)
        label = STATUS_LABELS[cls['status']]
        detail = f" ({cls['detail']})" if cls['detail'] else ''
        line += f"  [{label}{detail}]"
    
    return line


def query_events(start, end, calendar_id='primary'):
    """Query calendar events in the given range."""
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy='startTime',
        timeZone=TZ_NAME
    ).execute()
    
    return events_result.get('items', [])


def query_secondary_events(start, end, cal_id, label):
    """Query a secondary calendar. Free/busy-only calendars return events
    without titles; fall back to the freebusy endpoint on error."""
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    tagged = []
    try:
        items = service.events().list(
            calendarId=cal_id,
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy='startTime',
            timeZone=TZ_NAME,
        ).execute().get('items', [])
        for ev in items:
            if not ev.get('summary'):
                ev['summary'] = f'({label} busy)'
            ev['_calendar'] = label
            tagged.append(ev)
        return tagged
    except HttpError:
        # Fall back to free/busy (guaranteed for freeBusyReader access).
        try:
            body = {
                'timeMin': start.isoformat(),
                'timeMax': end.isoformat(),
                'timeZone': TZ_NAME,
                'items': [{'id': cal_id}],
            }
            fb = service.freebusy().query(body=body).execute()
            busy = fb.get('calendars', {}).get(cal_id, {}).get('busy', [])
            for b in busy:
                s = datetime.fromisoformat(b['start'].replace('Z', '+00:00')).astimezone(TZ)
                e = datetime.fromisoformat(b['end'].replace('Z', '+00:00')).astimezone(TZ)
                tagged.append({
                    'start': {'dateTime': s.isoformat()},
                    'end': {'dateTime': e.isoformat()},
                    'summary': f'({label} busy)',
                    '_calendar': label,
                })
        except HttpError as err2:
            print(f"[warn] could not query {cal_id}: {err2}", file=sys.stderr)
        return tagged


def merge_and_sort(events):
    """Sort merged events by start time (all-day first within a day)."""
    def _key(ev):
        s = ev.get('start', {})
        if s.get('dateTime'):
            dt = datetime.fromisoformat(s['dateTime'])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TZ)
            return dt
        if s.get('date'):
            return datetime.strptime(s['date'], '%Y-%m-%d').replace(tzinfo=TZ)
        return datetime.now(TZ)
    return sorted(events, key=_key)


def output_compact(events, start, end, classify=False):
    """Output events grouped by date in compact format."""
    now = datetime.now(TZ) if classify else None
    
    if not events:
        print(f"No events {start.strftime('%Y-%m-%d')} to {(end - timedelta(days=1)).strftime('%Y-%m-%d')}")
        return
    
    if classify:
        print(f"As of {now.strftime('%I:%M %p').lstrip('0').lower()}:")
    
    by_date = {}
    for event in events:
        start_info = event.get('start', {})
        if start_info.get('dateTime'):
            dt = datetime.fromisoformat(start_info['dateTime'])
            date_key = dt.strftime('%Y-%m-%d %a')
        elif start_info.get('date'):
            date_key = f"{start_info['date']} {datetime.strptime(start_info['date'], '%Y-%m-%d').strftime('%a')}"
        else:
            date_key = 'unknown'
        
        by_date.setdefault(date_key, []).append(event)
    
    for date_key in sorted(by_date.keys()):
        print(f"{date_key}:")
        for event in by_date[date_key]:
            print(format_event_compact(event, classify=classify, now=now))


def output_json(events, classify=False):
    """Output events as compact JSON."""
    now = datetime.now(TZ) if classify else None
    compact = []
    for event in events:
        start = event.get('start', {})
        end = event.get('end', {})
        entry = {
            'time': format_time(start.get('dateTime'), start.get('date')),
            'end': format_time(end.get('dateTime'), end.get('date')),
            'summary': event.get('summary', '(no title)'),
        }
        if event.get('location'):
            entry['location'] = event['location']
        if classify and now:
            cls = classify_event(event, now)
            entry['status'] = cls['status']
            if cls['detail']:
                entry['status_detail'] = cls['detail']
        compact.append(entry)
    
    result = {'events': compact}
    if classify:
        result['as_of'] = now.strftime('%I:%M %p').lstrip('0').lower()
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description='Query Google Calendar (compact output)')
    parser.add_argument('date_spec', nargs='?', help="'today', 'tomorrow', 'week', or YYYY-MM-DD (not required with --auth)")
    parser.add_argument('end_date', nargs='?', help='End date for range (YYYY-MM-DD)')
    parser.add_argument('--calendar', '-c', default='primary', help='Calendar ID')
    parser.add_argument('--json', action='store_true', help='Output as compact JSON')
    parser.add_argument('--raw', action='store_true', help='Output full API response')
    parser.add_argument('--classify', action='store_true', help='Classify events vs current time (DONE/NOW/SOON/LATER)')
    parser.add_argument('--output', '-o', help='Write output to file instead of stdout')
    parser.add_argument('--no-secondary', action='store_true', help='Exclude secondary calendars (e.g. Harness) from default query')
    parser.add_argument('--auth', action='store_true', help='Force re-authorization (no date_spec required). Must be run from a regular terminal, not MCP shell.')
    
    args = parser.parse_args()

    # Handle auth-only mode
    if args.auth:
        get_credentials(force_auth=True)
        print("Re-authorization complete.")
        return

    # Require date_spec if not in auth mode
    if not args.date_spec:
        parser.error("date_spec is required unless --auth is used")

    # Clear output file immediately to prevent stale data if the API call
    # fails or times out.
    if args.output:
        with open(args.output, 'w') as f:
            pass

    start, end = resolve_dates(args)
    events = query_events(start, end, args.calendar)
    # For the default (primary) calendar, also merge secondary calendars
    # (e.g. Harness) unless suppressed with --no-secondary.
    if args.calendar == 'primary' and not args.no_secondary:
        for cal_id in SECONDARY_CALENDARS:
            events += query_secondary_events(
                start, end, cal_id, CAL_LABELS.get(cal_id, cal_id))
        events = merge_and_sort(events)
    
    import io
    if args.output:
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
    
    if not args.json and not args.raw:
        print(f"[Generated: {datetime.now(TZ).strftime('%Y-%m-%d %I:%M %p %Z')}]")

    if args.raw:
        print(json.dumps(events, indent=2))
    elif args.json:
        output_json(events, classify=args.classify)
    else:
        output_compact(events, start, end, classify=args.classify)
    
    if args.output:
        sys.stdout = old_stdout
        with open(args.output, 'w') as f:
            f.write(buf.getvalue())


if __name__ == '__main__':
    main()