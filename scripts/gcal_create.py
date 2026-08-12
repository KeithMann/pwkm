#!/usr/bin/env python3
"""
Google Calendar Event Creator

Creates events on Google Calendar via the API.
OAuth credentials are read from .env file in the same directory.

Usage:
    python gcal_create.py --summary "Meeting" --start "2026-01-13T11:00" --end "2026-01-13T12:00"
    python gcal_create.py --summary "All day event" --date "2026-01-13"
    python gcal_create.py --auth  # Force re-authorization

First run will open browser for OAuth authorization.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"Missing required package: {e}")
    print("\nInstall required packages with:")
    print("  pip install python-dotenv google-auth google-auth-oauthlib google-api-python-client --break-system-packages")
    sys.exit(1)

# Scopes required for calendar access
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

# Paths
DEFAULT_TZ = os.environ.get('LOCAL_TIMEZONE', 'America/New_York')
SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / '.env'
TOKEN_FILE = SCRIPT_DIR / 'gcal_token.json'
CREDENTIALS_FILE = SCRIPT_DIR / 'gcal_credentials.json'


def load_client_config():
    """Load OAuth client configuration from .env file."""
    load_dotenv(ENV_FILE)
    
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("Error: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in .env file")
        print(f"Expected location: {ENV_FILE}")
        print("\nCreate .env file with:")
        print("  GOOGLE_CLIENT_ID=your_client_id_here")
        print("  GOOGLE_CLIENT_SECRET=your_client_secret_here")
        sys.exit(1)
    
    # Build the client config structure that google-auth expects
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
    creds = None
    
    # Load existing token if available
    if TOKEN_FILE.exists() and not force_auth:
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as e:
            print(f"Warning: Could not load existing token: {e}")
    
    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("Refreshing expired token...")
                creds.refresh(Request())
            except Exception as e:
                print(f"Token refresh failed: {e}")
                creds = None
        
        if not creds:
            print("Starting OAuth authorization flow...")
            print("A browser window will open for you to authorize access.")
            
            client_config = load_client_config()
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
            print("Authorization successful!")
    
    # Save credentials for next run
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
    
    return creds


def find_existing_event(service, calendar_id, summary, start, end):
    """Check if an event with matching summary+start+end already exists.

    Returns the existing event dict if a match is found, None otherwise.
    Fails open: if the idempotency check errors for any reason, returns None
    (proceeds to create) rather than blocking the operation.

    Added 2026-04-17 (Phase C) for idempotent batch inserts.
    """
    from datetime import datetime as _dt, timedelta as _td
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from backports.zoneinfo import ZoneInfo

    if 'date' in start:
        # All-day event: query the exact date
        day = start['date']
        tm = _dt.fromisoformat(day).replace(tzinfo=ZoneInfo('UTC'))
        time_min = tm.isoformat()
        time_max = (tm + _td(days=1)).isoformat()
        tz = None
    else:
        tz_name = start.get('timeZone', DEFAULT_TZ)
        tz = ZoneInfo(tz_name)
        start_dt = _dt.fromisoformat(start['dateTime']).replace(tzinfo=tz)
        time_min = (start_dt - _td(minutes=1)).isoformat()
        time_max = (start_dt + _td(minutes=1)).isoformat()

    try:
        resp = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            maxResults=20,
        ).execute()
    except HttpError as e:
        print(f"Warning: idempotency check failed ({e}); proceeding with creation.")
        return None
    except Exception as e:
        print(f"Warning: idempotency check errored ({e}); proceeding with creation.")
        return None

    for ev in resp.get('items', []):
        if ev.get('summary', '') != summary:
            continue
        ev_start = ev.get('start', {})
        ev_end = ev.get('end', {})
        if 'date' in start:
            if ev_start.get('date') == start.get('date') and ev_end.get('date') == end.get('date'):
                return ev
        else:
            try:
                ev_start_dt = _dt.fromisoformat(ev_start.get('dateTime', '').replace('Z', '+00:00'))
                ev_end_dt = _dt.fromisoformat(ev_end.get('dateTime', '').replace('Z', '+00:00'))
                req_start_dt = _dt.fromisoformat(start['dateTime']).replace(tzinfo=tz)
                req_end_dt = _dt.fromisoformat(end['dateTime']).replace(tzinfo=tz)
                if ev_start_dt == req_start_dt and ev_end_dt == req_end_dt:
                    return ev
            except (ValueError, KeyError, TypeError):
                continue

    return None


def create_event(summary, start, end, description=None, location=None, calendar_id='primary', force=False):
    """Create a calendar event. Idempotent by default.

    If an event with matching summary+start+end already exists on the calendar,
    returns the existing event without creating a duplicate. Pass force=True
    to bypass the idempotency check.
    """
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    if not force:
        existing = find_existing_event(service, calendar_id, summary, start, end)
        if existing:
            print(f"Event already exists, skipping creation: {existing.get('htmlLink')}")
            return existing

    event = {
        'summary': summary,
        'start': start,
        'end': end,
    }
    
    if description:
        event['description'] = description
    if location:
        event['location'] = location
    
    try:
        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")
        return event
    except HttpError as error:
        print(f"An error occurred: {error}")
        sys.exit(1)


def parse_datetime(dt_string, is_end=False, all_day_date=None):
    """Parse datetime string into Google Calendar format."""
    
    # All-day event
    if all_day_date:
        return {'date': all_day_date}
    
    # Try parsing various formats
    formats = [
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(dt_string, fmt)
            # Return with timezone (Eastern)
            return {
                'dateTime': dt.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': DEFAULT_TZ
            }
        except ValueError:
            continue
    
    print(f"Error: Could not parse datetime '{dt_string}'")
    print("Expected formats: YYYY-MM-DDTHH:MM or YYYY-MM-DD HH:MM")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Create Google Calendar events')
    parser.add_argument('--summary', '-s', help='Event title/summary')
    parser.add_argument('--start', help='Start datetime (YYYY-MM-DDTHH:MM)')
    parser.add_argument('--end', help='End datetime (YYYY-MM-DDTHH:MM)')
    parser.add_argument('--date', help='Date for all-day event (YYYY-MM-DD)')
    parser.add_argument('--duration', '-d', type=int, help='Duration in minutes (alternative to --end)')
    parser.add_argument('--description', help='Event description')
    parser.add_argument('--location', '-l', help='Event location')
    parser.add_argument('--calendar', '-c', default='primary', help='Calendar ID (default: primary)')
    parser.add_argument('--auth', action='store_true', help='Force re-authorization')
    parser.add_argument('--force', action='store_true', help='Bypass idempotency check (create duplicate if event already exists)')
    parser.add_argument('--json', action='store_true', help='Output result as JSON')
    
    args = parser.parse_args()
    
    # Handle auth-only mode
    if args.auth:
        get_credentials(force_auth=True)
        print("Re-authorization complete.")
        return
    
    # Validate required arguments
    if not args.summary:
        parser.error("--summary is required")
    
    if args.date:
        # All-day event
        start = {'date': args.date}
        end = {'date': args.date}
    elif args.start:
        start = parse_datetime(args.start)
        
        if args.end:
            end = parse_datetime(args.end)
        elif args.duration:
            # Calculate end from duration
            from datetime import timedelta
            # Normalize to space-separated format for parsing
            normalized = args.start.replace('T', ' ')
            start_dt = datetime.strptime(normalized, '%Y-%m-%d %H:%M')
            end_dt = start_dt + timedelta(minutes=args.duration)
            end = {
                'dateTime': end_dt.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': DEFAULT_TZ
            }
        else:
            parser.error("--end or --duration is required with --start")
    else:
        parser.error("Either --date (all-day) or --start (timed event) is required")
    
    event = create_event(
        summary=args.summary,
        start=start,
        end=end,
        description=args.description,
        location=args.location,
        calendar_id=args.calendar,
        force=args.force
    )
    
    if args.json:
        print(json.dumps(event, indent=2))


if __name__ == '__main__':
    main()
