#!/usr/bin/env python3
"""
Session Timer - Running Summary Clock Check Enforcement

Tracks when Claude's session started and when the running summary was last
updated, providing mechanical enforcement of the 30-minute clock check.

Usage:
    python session_timer.py start                # Record session start
    python session_timer.py update               # Record running summary update
    python session_timer.py check                # Check elapsed times
    python session_timer.py check --json         # JSON output
    python session_timer.py status               # Full status report
    python session_timer.py audit-check          # Check if weekly/monthly audit needed
    python session_timer.py audit-check --json   # JSON output
    python session_timer.py audit-done           # Record weekly audit completion
    python session_timer.py audit-done --monthly # Also record monthly idea review

State files (in parent dir of scripts/):
    session_timer_state.json  - Session timing state
    audit_state.json          - Weekly/monthly audit tracking

Configuration:
    Set LOCAL_TIMEZONE env var or edit TZ_NAME below. Default: America/New_York
    Set PWKM_STATE_DIR env var to override state file location.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ_NAME = os.environ.get("LOCAL_TIMEZONE", "America/New_York")
TZ = ZoneInfo(TZ_NAME)
SCRIPT_DIR = Path(__file__).parent
STATE_DIR = Path(os.environ.get("PWKM_STATE_DIR", str(SCRIPT_DIR.parent)))
STATE_FILE = STATE_DIR / 'session_timer_state.json'
AUDIT_FILE = STATE_DIR / 'audit_state.json'
THRESHOLD_MINUTES = 30


def now():
    return datetime.now(TZ)


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def fmt_time(iso_str):
    """Format ISO string to readable time."""
    dt = datetime.fromisoformat(iso_str)
    return dt.strftime('%I:%M %p').lstrip('0').lower()


def minutes_since(iso_str):
    """Minutes elapsed since an ISO timestamp."""
    dt = datetime.fromisoformat(iso_str)
    delta = now() - dt
    return int(delta.total_seconds() / 60)


def cmd_start(args):
    """Record session start time."""
    state = load_state()
    n = now()
    state['session_start'] = n.isoformat()
    state['last_summary_update'] = n.isoformat()
    state['update_count'] = 0
    save_state(state)
    print(f"Session started at {fmt_time(n.isoformat())}. Timer running.")


def cmd_update(args):
    """Record that running summary was updated."""
    state = load_state()
    if not state.get('session_start'):
        print("Warning: No session started. Starting one now.")
        state['session_start'] = now().isoformat()

    n = now()
    elapsed = minutes_since(state.get('last_summary_update', n.isoformat()))
    state['last_summary_update'] = n.isoformat()
    state['update_count'] = state.get('update_count', 0) + 1
    save_state(state)
    print(f"Running summary update recorded at {fmt_time(n.isoformat())} ({elapsed} min since last).")
    print(f"Total updates this session: {state['update_count']}")


def cmd_check(args):
    """Check elapsed time since last running summary update."""
    state = load_state()

    if not state.get('session_start'):
        if args.json:
            print(json.dumps({"error": "no_session", "message": "No active session. Run 'start' first."}))
        else:
            print("No active session. Run 'start' first.")
        return

    n = now()
    since_start = minutes_since(state['session_start'])
    since_update = minutes_since(state.get('last_summary_update', state['session_start']))
    overdue = since_update >= THRESHOLD_MINUTES

    if args.json:
        result = {
            "current_time": fmt_time(n.isoformat()),
            "session_start": fmt_time(state['session_start']),
            "minutes_since_start": since_start,
            "last_summary_update": fmt_time(state.get('last_summary_update', state['session_start'])),
            "minutes_since_update": since_update,
            "overdue": overdue,
            "update_count": state.get('update_count', 0),
            "threshold_minutes": THRESHOLD_MINUTES,
        }
        print(json.dumps(result))
    else:
        status = "⚠️ OVERDUE" if overdue else "OK"
        print(f"Time: {fmt_time(n.isoformat())}")
        print(f"Session: {since_start} min (started {fmt_time(state['session_start'])})")
        print(f"Last summary: {since_update} min ago ({fmt_time(state.get('last_summary_update', state['session_start']))})")
        print(f"Status: {status} (threshold: {THRESHOLD_MINUTES} min)")
        print(f"Updates this session: {state.get('update_count', 0)}")


def cmd_status(args):
    """Full status report."""
    args.json = False
    cmd_check(args)


def load_audit_state():
    if AUDIT_FILE.exists():
        with open(AUDIT_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_audit_state(state):
    with open(AUDIT_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def cmd_audit_check(args):
    """Check if weekly audit or monthly idea review is needed."""
    audit = load_audit_state()
    n = now()
    today = n.date()
    weekday = today.weekday()

    last_weekly = audit.get('last_weekly_audit')
    if last_weekly:
        last_weekly_date = datetime.fromisoformat(last_weekly).date()
        days_since_weekly = (today - last_weekly_date).days
        weekly_needed = days_since_weekly >= 7
    else:
        weekly_needed = True
        days_since_weekly = None

    last_monthly = audit.get('last_monthly_review')
    first_week = today.day <= 7
    if last_monthly:
        last_monthly_date = datetime.fromisoformat(last_monthly).date()
        monthly_needed = first_week and last_monthly_date.month != today.month
    else:
        monthly_needed = first_week

    if args.json:
        result = {
            'weekly_audit_needed': weekly_needed,
            'days_since_weekly_audit': days_since_weekly,
            'monthly_review_needed': monthly_needed,
            'is_first_week': first_week,
            'today': today.isoformat(),
            'weekday': ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][weekday],
        }
        print(json.dumps(result))
    else:
        if weekly_needed:
            since = f' (last: {days_since_weekly}d ago)' if days_since_weekly else ' (never done)'
            print(f'** WEEKLY AUDIT NEEDED{since}')
        else:
            print(f'Weekly audit: OK (last: {days_since_weekly}d ago)')

        if monthly_needed:
            print('** MONTHLY IDEA REVIEW NEEDED (first week of month)')
        elif first_week:
            print('Monthly idea review: OK (already done this month)')
        else:
            print('Monthly idea review: not due (not first week)')


def cmd_audit_done(args):
    """Record completion of weekly audit (and optionally monthly review)."""
    audit = load_audit_state()
    n = now()
    audit['last_weekly_audit'] = n.isoformat()
    print(f'Weekly audit recorded at {fmt_time(n.isoformat())}.')

    if args.monthly:
        audit['last_monthly_review'] = n.isoformat()
        print(f'Monthly idea review also recorded.')

    save_audit_state(audit)


def main():
    parser = argparse.ArgumentParser(description='Session timer for running summary enforcement')
    parser.add_argument('command', choices=['start', 'update', 'check', 'status', 'audit-check', 'audit-done'],
                        help='Command to execute')
    parser.add_argument('--json', action='store_true', help='JSON output')
    parser.add_argument('--monthly', action='store_true', help='Also record monthly review (for audit-done)')

    args = parser.parse_args()

    commands = {
        'start': cmd_start,
        'update': cmd_update,
        'check': cmd_check,
        'status': cmd_status,
        'audit-check': cmd_audit_check,
        'audit-done': cmd_audit_done,
    }
    commands[args.command](args)


if __name__ == '__main__':
    main()
