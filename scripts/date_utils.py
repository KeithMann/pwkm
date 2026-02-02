"""
PWKM Date Utilities
Helper functions for date calculations and verification.

Usage:
    python date_utils.py today          # Show current date with day of week
    python date_utils.py verify         # Verify system date (for Claude startup)
    python date_utils.py add 7          # Add days to today
    python date_utils.py next monday    # Find next occurrence of weekday
"""

import sys
from datetime import datetime, timedelta

WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

def get_today():
    """Return today's date with day of week."""
    today = datetime.now()
    return today, today.strftime("%A")

def verify_date():
    """Verify and display current system date for Claude startup."""
    today, weekday = get_today()
    print(f"Current Date: {today.strftime('%Y-%m-%d')}")
    print(f"Day of Week: {weekday}")
    print(f"ISO Format: {today.isoformat()}")
    return today

def add_days(days):
    """Add days to today and return result."""
    today = datetime.now()
    future = today + timedelta(days=int(days))
    return future, future.strftime("%A")

def next_weekday(target_day):
    """Find the next occurrence of a weekday."""
    target_day = target_day.lower()
    if target_day not in WEEKDAYS:
        print(f"Invalid weekday: {target_day}")
        print(f"Valid options: {', '.join(WEEKDAYS)}")
        return None, None
    
    today = datetime.now()
    current_weekday = today.weekday()  # Monday = 0
    target_weekday = WEEKDAYS.index(target_day)
    
    days_ahead = target_weekday - current_weekday
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    
    next_date = today + timedelta(days=days_ahead)
    return next_date, next_date.strftime("%A")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    if command == "today":
        today, weekday = get_today()
        print(f"{today.strftime('%Y-%m-%d')} ({weekday})")
    
    elif command == "verify":
        verify_date()
    
    elif command == "add" and len(sys.argv) >= 3:
        try:
            days = int(sys.argv[2])
            future, weekday = add_days(days)
            print(f"{future.strftime('%Y-%m-%d')} ({weekday})")
        except ValueError:
            print(f"Invalid number of days: {sys.argv[2]}")
    
    elif command == "next" and len(sys.argv) >= 3:
        target = sys.argv[2]
        result, weekday = next_weekday(target)
        if result:
            print(f"{result.strftime('%Y-%m-%d')} ({weekday})")
    
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
