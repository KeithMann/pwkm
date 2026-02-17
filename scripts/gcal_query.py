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

Configuration:
    Set LOCAL_TIMEZONE env var or edit LOCAL_TZ_NAME below. Default: America/New_York
    Requires Google Calendar API credentials (see setup-guide.md).
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from dotenv import load_dotenv
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"Missing required package: {e}")
    sys.exit(1)

SCOPES = ['https://www.googleapis.com/auth/calendar.events']
SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / '.env'
TOKEN_FILE = SCRIPT_DIR / 'gcal_token.json'
LOCAL_TZ_NAME = os.environ.get("LOCAL_TIMEZONE", "America/New_York")
TZ = ZoneInfo(LOCAL_TZ_NAME)


def get_credentials():
    """Get valid credentials, refreshing if needed."""
    load_dotenv(ENV_FILE)
    
    if not TOKEN_FILE.exists():
        print("Error: No token file. Run gcal_create.py --auth first.")
        sys.exit(1)
    
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    
    if not creds or not creds.valid:
        print("Error: Invalid credentials. Run gcal_create.py --auth to re-authorize.")
        sys.exit(1)
    
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
            # Windows uses %#I, Linux uses %-I
            return dt.strftime('%#I:%M %p').lower()
        except ValueError:
            return dt.strftime('%-I:%M %p').lower()
    return "?"


def classify_event(event, now):
    """Classify an event relative to the current time.
    
    Returns a dict with:
        status: 'completed' | 'in_progress' | 'upcoming_imminent' | 'upcoming_later'
        detail: human-readable detail string (e.g., 'started 13 min ago', 'in 47 min')
    """
    start_info = event.get('start', {})
    end_info = event.get('end', {})
    
    # All-day events: classify based on date only
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
    
    # Timed events
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
        timeZone=LOCAL_TZ_NAME
    ).execute()
    
    return events_result.get('items', [])


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
    parser.add_argument('date_spec', help="'today', 'tomorrow', 'week', or YYYY-MM-DD")
    parser.add_argument('end_date', nargs='?', help='End date for range (YYYY-MM-DD)')
    parser.add_argument('--calendar', '-c', default='primary', help='Calendar ID')
    parser.add_argument('--json', action='store_true', help='Output as compact JSON')
    parser.add_argument('--raw', action='store_true', help='Output full API response')
    parser.add_argument('--classify', action='store_true', help='Classify events vs current time (DONE/NOW/SOON/LATER)')
    parser.add_argument('--output', '-o', help='Write output to file instead of stdout')
    
    args = parser.parse_args()
    start, end = resolve_dates(args)
    events = query_events(start, end, args.calendar)
    
    import io
    if args.output:
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
    
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
