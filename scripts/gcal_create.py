#!/usr/bin/env python3
"""
Google Calendar Event Creator

Creates events on Google Calendar via the API.
OAuth credentials are read from .env file in the same directory.

Usage:
    python gcal_create.py --summary "Meeting" --start "2026-01-13T11:00" --end "2026-01-13T12:00"
    python gcal_create.py --summary "All day event" --date "2026-01-13"
    python gcal_create.py --auth  # Force re-authorization (also initializes OAuth for gcal_query.py)

First run will open browser for OAuth authorization.
The token file (gcal_token.json) is shared with gcal_query.py.
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
    print("  pip install python-dotenv google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)

# Scopes required for calendar access
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

# Paths
SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / '.env'
TOKEN_FILE = SCRIPT_DIR / 'gcal_token.json'

# Default timezone — change this to your local timezone
DEFAULT_TZ = os.getenv('PWKM_TIMEZONE', 'America/New_York')


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


def create_event(summary, start, end, description=None, location=None, calendar_id='primary'):
    """Create a calendar event."""
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

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
        calendar_id=args.calendar
    )

    if args.json:
        print(json.dumps(event, indent=2))


if __name__ == '__main__':
    main()
