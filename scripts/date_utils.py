#!/usr/bin/env python3
"""
Date utilities for PWKM task management.

Handles:
- Current date/time in local timezone
- Day of week verification
- Date arithmetic (add days/months/years)
- Nth weekday of month calculations (First Saturday, Second Saturday, etc.)
- Next occurrence calculations for recurring tasks

Usage:
    python date_utils.py now                              # Current date/time
    python date_utils.py weekday 2026-01-13               # Get day of week
    python date_utils.py add 2026-01-06 7d                # Add 7 days
    python date_utils.py add 2026-01-06 3m                # Add 3 months  
    python date_utils.py add 2026-01-06 1y                # Add 1 year
    python date_utils.py nth-weekday 2026-02 2 saturday   # 2nd Saturday of Feb 2026
    python date_utils.py next-nth 2026-01-10 2 saturday   # Next 2nd Saturday after date
    python date_utils.py next-recurring 2026-01-06 weekly # Next occurrence for weekly task
    python date_utils.py next-recurring 2026-01-10 "second saturday"  # Next 2nd Sat
    python date_utils.py next-recurring 2026-01-01 quarterly          # Add 3 months
    python date_utils.py next-recurring 2026-01-01 yearly             # Add 1 year

All commands support --json flag for structured output.

Configuration:
    Set LOCAL_TIMEZONE environment variable or edit the LOCAL_TZ constant below.
    Default: America/Toronto (Eastern)
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta
from typing import Optional

# Configure your timezone here, or set LOCAL_TIMEZONE env var
LOCAL_TZ = ZoneInfo(os.environ.get("LOCAL_TIMEZONE", "America/Toronto"))

WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6
}

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def now_local() -> datetime:
    """Get current datetime in local timezone."""
    return datetime.now(LOCAL_TZ)


def parse_date(date_str: str) -> datetime:
    """Parse ISO format date string."""
    return datetime.strptime(date_str, "%Y-%m-%d")


def format_date(dt: datetime) -> str:
    """Format datetime as ISO date."""
    return dt.strftime("%Y-%m-%d")


def format_full(dt: datetime) -> str:
    """Format datetime with day name."""
    return dt.strftime("%A, %B %d, %Y")


def get_weekday_name(dt: datetime) -> str:
    """Get the day of week name for a date."""
    return WEEKDAY_NAMES[dt.weekday()]


def add_duration(dt: datetime, duration: str) -> datetime:
    """
    Add a duration to a date.
    
    Supports:
        Nd = N days
        Nw = N weeks
        Nm = N months
        Ny = N years
    """
    if not duration:
        raise ValueError("Duration cannot be empty")
    
    unit = duration[-1].lower()
    try:
        amount = int(duration[:-1])
    except ValueError:
        raise ValueError(f"Invalid duration format: {duration}")
    
    if unit == 'd':
        return dt + timedelta(days=amount)
    elif unit == 'w':
        return dt + timedelta(weeks=amount)
    elif unit == 'm':
        return dt + relativedelta(months=amount)
    elif unit == 'y':
        return dt + relativedelta(years=amount)
    else:
        raise ValueError(f"Unknown duration unit: {unit}. Use d/w/m/y.")


def nth_weekday_of_month(year: int, month: int, n: int, weekday: int) -> datetime:
    """
    Find the nth occurrence of a weekday in a given month.
    
    Args:
        year: The year
        month: The month (1-12)
        n: Which occurrence (1=first, 2=second, etc.)
        weekday: Day of week (0=Monday, 6=Sunday)
    
    Returns:
        datetime of the nth weekday, or raises ValueError if doesn't exist
    """
    first_day = datetime(year, month, 1)
    days_until = (weekday - first_day.weekday()) % 7
    first_occurrence = first_day + timedelta(days=days_until)
    nth_occurrence = first_occurrence + timedelta(weeks=n-1)
    
    if nth_occurrence.month != month:
        raise ValueError(f"No {n}th {WEEKDAY_NAMES[weekday]} in {year}-{month:02d}")
    
    return nth_occurrence


def next_nth_weekday_after(after_date: datetime, n: int, weekday: int) -> datetime:
    """
    Find the next nth weekday of a month after a given date.
    
    Used for recurring tasks like "Second Saturday" - after completing on Jan 10,
    find the Second Saturday of the next month.
    """
    next_month = after_date + relativedelta(months=1)
    year, month = next_month.year, next_month.month
    
    try:
        result = nth_weekday_of_month(year, month, n, weekday)
        return result
    except ValueError:
        next_month = next_month + relativedelta(months=1)
        return nth_weekday_of_month(next_month.year, next_month.month, n, weekday)


def parse_recurring_pattern(pattern: str) -> tuple[str, Optional[int], Optional[int]]:
    """
    Parse a recurring task pattern.
    
    Returns:
        Tuple of (pattern_type, n, weekday) where:
        - pattern_type: 'weekly', 'monthly', 'quarterly', 'yearly', 'nth_weekday'
        - n: occurrence number for nth_weekday patterns (1-5)
        - weekday: weekday number (0-6) for nth_weekday patterns
    """
    pattern_lower = pattern.lower().strip()
    
    if pattern_lower == 'weekly':
        return ('weekly', None, None)
    elif pattern_lower == 'monthly':
        return ('monthly', None, None)
    elif pattern_lower == 'quarterly':
        return ('quarterly', None, None)
    elif pattern_lower == 'yearly':
        return ('yearly', None, None)
    
    # Parse "first saturday", "second saturday", etc.
    ordinals = {
        'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
        '1st': 1, '2nd': 2, '3rd': 3, '4th': 4, '5th': 5
    }
    
    parts = pattern_lower.split()
    if len(parts) == 2:
        ordinal_str, weekday_str = parts
        if ordinal_str in ordinals and weekday_str in WEEKDAYS:
            return ('nth_weekday', ordinals[ordinal_str], WEEKDAYS[weekday_str])
    
    raise ValueError(f"Unknown recurring pattern: {pattern}")


def next_recurring(current_due: datetime, pattern: str) -> datetime:
    """
    Calculate the next due date for a recurring task.
    
    Args:
        current_due: Current due date of the task
        pattern: Recurrence pattern (weekly, quarterly, yearly, "second saturday", etc.)
    
    Returns:
        Next due date
    """
    pattern_type, n, weekday = parse_recurring_pattern(pattern)
    
    if pattern_type == 'weekly':
        return current_due + timedelta(days=7)
    elif pattern_type == 'monthly':
        return current_due + relativedelta(months=1)
    elif pattern_type == 'quarterly':
        return current_due + relativedelta(months=3)
    elif pattern_type == 'yearly':
        return current_due + relativedelta(years=1)
    elif pattern_type == 'nth_weekday':
        return next_nth_weekday_after(current_due, n, weekday)
    
    raise ValueError(f"Unhandled pattern type: {pattern_type}")


def cmd_now(args):
    """Handle 'now' command."""
    dt = now_local()
    if args.json:
        return {
            "date": format_date(dt),
            "time": dt.strftime("%H:%M:%S"),
            "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "weekday": get_weekday_name(dt),
            "timezone": str(LOCAL_TZ),
            "formatted": dt.strftime("%A, %B %d, %Y at %I:%M %p %Z")
        }
    return dt.strftime("%A, %B %d, %Y at %I:%M %p %Z")


def cmd_weekday(args):
    """Handle 'weekday' command."""
    dt = parse_date(args.date)
    weekday = get_weekday_name(dt)
    if args.json:
        return {
            "date": args.date,
            "weekday": weekday,
            "formatted": format_full(dt)
        }
    return f"{args.date} is a {weekday}"


def cmd_add(args):
    """Handle 'add' command."""
    dt = parse_date(args.date)
    result = add_duration(dt, args.duration)
    if args.json:
        return {
            "original": args.date,
            "duration": args.duration,
            "result": format_date(result),
            "weekday": get_weekday_name(result),
            "formatted": format_full(result)
        }
    return f"{format_date(result)} ({get_weekday_name(result)})"


def cmd_nth_weekday(args):
    """Handle 'nth-weekday' command."""
    year, month = map(int, args.year_month.split('-'))
    n = args.n
    weekday = WEEKDAYS.get(args.weekday.lower())
    if weekday is None:
        raise ValueError(f"Unknown weekday: {args.weekday}")
    
    result = nth_weekday_of_month(year, month, n, weekday)
    if args.json:
        return {
            "year_month": args.year_month,
            "n": n,
            "weekday_name": args.weekday,
            "result": format_date(result),
            "formatted": format_full(result)
        }
    return f"{format_date(result)} ({format_full(result)})"


def cmd_next_nth(args):
    """Handle 'next-nth' command."""
    dt = parse_date(args.date)
    n = args.n
    weekday = WEEKDAYS.get(args.weekday.lower())
    if weekday is None:
        raise ValueError(f"Unknown weekday: {args.weekday}")
    
    result = next_nth_weekday_after(dt, n, weekday)
    if args.json:
        return {
            "after_date": args.date,
            "n": n,
            "weekday_name": args.weekday,
            "result": format_date(result),
            "formatted": format_full(result)
        }
    return f"{format_date(result)} ({format_full(result)})"


def cmd_next_recurring(args):
    """Handle 'next-recurring' command."""
    dt = parse_date(args.date)
    result = next_recurring(dt, args.pattern)
    if args.json:
        return {
            "current_due": args.date,
            "pattern": args.pattern,
            "next_due": format_date(result),
            "weekday": get_weekday_name(result),
            "formatted": format_full(result)
        }
    return f"{format_date(result)} ({get_weekday_name(result)})"


def main():
    parser = argparse.ArgumentParser(
        description="Date utilities for PWKM task management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # now
    subparsers.add_parser('now', help='Current date/time in local timezone')
    
    # weekday
    p_weekday = subparsers.add_parser('weekday', help='Get day of week for a date')
    p_weekday.add_argument('date', help='Date in YYYY-MM-DD format')
    
    # add
    p_add = subparsers.add_parser('add', help='Add duration to a date')
    p_add.add_argument('date', help='Date in YYYY-MM-DD format')
    p_add.add_argument('duration', help='Duration: Nd (days), Nw (weeks), Nm (months), Ny (years)')
    
    # nth-weekday
    p_nth = subparsers.add_parser('nth-weekday', help='Find nth weekday of a month')
    p_nth.add_argument('year_month', help='Year and month in YYYY-MM format')
    p_nth.add_argument('n', type=int, help='Which occurrence (1=first, 2=second, etc.)')
    p_nth.add_argument('weekday', help='Day of week (monday, tuesday, etc.)')
    
    # next-nth
    p_next_nth = subparsers.add_parser('next-nth', help='Find next nth weekday after a date')
    p_next_nth.add_argument('date', help='Date in YYYY-MM-DD format')
    p_next_nth.add_argument('n', type=int, help='Which occurrence (1=first, 2=second, etc.)')
    p_next_nth.add_argument('weekday', help='Day of week (monday, tuesday, etc.)')
    
    # next-recurring
    p_recurring = subparsers.add_parser('next-recurring', help='Calculate next due date for recurring task')
    p_recurring.add_argument('date', help='Current due date in YYYY-MM-DD format')
    p_recurring.add_argument('pattern', help='Pattern: weekly, quarterly, yearly, or "second saturday" etc.')
    
    args = parser.parse_args()
    
    try:
        handlers = {
            'now': cmd_now,
            'weekday': cmd_weekday,
            'add': cmd_add,
            'nth-weekday': cmd_nth_weekday,
            'next-nth': cmd_next_nth,
            'next-recurring': cmd_next_recurring,
        }
        
        result = handlers[args.command](args)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(result)
            
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
