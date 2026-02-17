#!/usr/bin/env python3
"""
Task manager for PWKM system.

Handles:
- Reading and filtering tasks from CSV
- Completing tasks (with automatic recurring date calculation)
- Reporting task status (overdue, due today, upcoming)

Usage:
    python task_manager.py status                    # Overdue, today, tomorrow
    python task_manager.py upcoming 7                # Tasks due in next 7 days
    python task_manager.py list                      # All tasks
    python task_manager.py complete "Task Name"      # Complete a task
    python task_manager.py get "Task Name"           # Get details for one task

All commands support --json flag for structured output.

CSV Format Expected:
    Task Name, Due Date, Category, Frequency, Priority, Status, URL

Configuration:
    Set LOCAL_TIMEZONE env var or edit LOCAL_TZ below. Default: America/Toronto
    Set PWKM_TASKS_CSV env var or edit DEFAULT_CSV_NAME below for CSV location.
    The script auto-detects CSV in its own directory first, then falls back.
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta
from typing import Optional, List, Dict, Any

# Configuration
LOCAL_TZ = ZoneInfo(os.environ.get("LOCAL_TIMEZONE", "America/Toronto"))
DEFAULT_CSV_NAME = "notion_tasks.csv"

def get_csv_path() -> Path:
    """Find CSV file - check env var, then script directory, then parent."""
    # Check environment variable first
    env_path = os.environ.get("PWKM_TASKS_CSV")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p
    
    # Check same directory as script
    script_dir = Path(__file__).parent
    local_csv = script_dir / DEFAULT_CSV_NAME
    if local_csv.exists():
        return local_csv
    
    # Check parent directory
    parent_csv = script_dir.parent / DEFAULT_CSV_NAME
    if parent_csv.exists():
        return parent_csv
    
    # Return local path for error message
    return local_csv

WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6
}

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# =============================================================================
# Date Utilities (incorporated from date_utils.py for self-contained operation)
# =============================================================================

def now_local() -> datetime:
    """Get current datetime in local timezone."""
    return datetime.now(LOCAL_TZ)


def today_local() -> datetime:
    """Get today's date (midnight) in local timezone."""
    n = now_local()
    return datetime(n.year, n.month, n.day)


def parse_date(date_str: str) -> datetime:
    """Parse ISO format date string."""
    return datetime.strptime(date_str, "%Y-%m-%d")


def format_date(dt: datetime) -> str:
    """Format datetime as ISO date."""
    return dt.strftime("%Y-%m-%d")


def get_weekday_name(dt: datetime) -> str:
    """Get the day of week name for a date."""
    return WEEKDAY_NAMES[dt.weekday()]


def nth_weekday_of_month(year: int, month: int, n: int, weekday: int) -> datetime:
    """Find the nth occurrence of a weekday in a given month."""
    first_day = datetime(year, month, 1)
    days_until = (weekday - first_day.weekday()) % 7
    first_occurrence = first_day + timedelta(days=days_until)
    nth_occurrence = first_occurrence + timedelta(weeks=n-1)
    
    if nth_occurrence.month != month:
        raise ValueError(f"No {n}th {WEEKDAY_NAMES[weekday]} in {year}-{month:02d}")
    
    return nth_occurrence


def next_nth_weekday_after(after_date: datetime, n: int, weekday: int) -> datetime:
    """Find the next nth weekday of a month after a given date."""
    next_month = after_date + relativedelta(months=1)
    year, month = next_month.year, next_month.month
    
    try:
        return nth_weekday_of_month(year, month, n, weekday)
    except ValueError:
        next_month = next_month + relativedelta(months=1)
        return nth_weekday_of_month(next_month.year, next_month.month, n, weekday)


def parse_task_name_for_pattern(task_name: str) -> tuple[str, Optional[int], Optional[int]]:
    """
    Extract recurrence pattern from task name.
    
    Handles patterns like:
        "Haircut (First Saturday)"
        "Garden Cleanup (Second Saturday)"
    """
    ordinals = {
        'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
        '1st': 1, '2nd': 2, '3rd': 3, '4th': 4, '5th': 5
    }
    
    import re
    match = re.search(r'\(([^)]+)\)', task_name.lower())
    if match:
        pattern_text = match.group(1).strip()
        parts = pattern_text.split()
        
        if len(parts) == 2:
            ordinal_str, weekday_str = parts
            if ordinal_str in ordinals and weekday_str in WEEKDAYS:
                return ('nth_weekday', ordinals[ordinal_str], WEEKDAYS[weekday_str])
    
    return ('unknown', None, None)


def calculate_next_due_date(current_due: datetime, frequency: str, task_name: str) -> datetime:
    """
    Calculate the next due date for a recurring task.
    Uses both the Frequency field and task name to determine the pattern.
    """
    freq_lower = frequency.lower().strip()
    
    if freq_lower == 'daily':
        return current_due + timedelta(days=1)
    elif freq_lower == 'weekly':
        return current_due + timedelta(days=7)
    elif freq_lower == 'quarterly':
        return current_due + relativedelta(months=3)
    elif freq_lower == 'yearly':
        return current_due + relativedelta(years=1)
    elif freq_lower == 'monthly':
        # Check if task name specifies nth weekday pattern
        pattern_type, n, weekday = parse_task_name_for_pattern(task_name)
        if pattern_type == 'nth_weekday':
            return next_nth_weekday_after(current_due, n, weekday)
        else:
            return current_due + relativedelta(months=1)
    
    raise ValueError(f"Unknown frequency pattern: {frequency}")


# =============================================================================
# Task Management
# =============================================================================

def read_tasks(csv_path: Path) -> List[Dict[str, Any]]:
    """Read all tasks from CSV file."""
    tasks = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            due_date = None
            if row.get('Due Date'):
                try:
                    due_date = parse_date(row['Due Date'])
                except ValueError:
                    pass
            
            tasks.append({
                'name': row.get('Task Name', ''),
                'due_date': due_date,
                'due_date_str': row.get('Due Date', ''),
                'category': row.get('Category', ''),
                'frequency': row.get('Frequency', ''),
                'priority': row.get('Priority', ''),
                'status': row.get('Status', ''),
                'url': row.get('URL', ''),
            })
    
    return tasks


def write_tasks(csv_path: Path, tasks: List[Dict[str, Any]]) -> None:
    """Write all tasks back to CSV file."""
    fieldnames = ['Task Name', 'Due Date', 'Category', 'Frequency', 'Priority', 'Status', 'URL']
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for task in tasks:
            writer.writerow({
                'Task Name': task['name'],
                'Due Date': task['due_date_str'],
                'Category': task['category'],
                'Frequency': task['frequency'],
                'Priority': task['priority'],
                'Status': task['status'],
                'URL': task['url'],
            })


def find_task(tasks: List[Dict[str, Any]], task_name: str) -> Optional[Dict[str, Any]]:
    """Find a task by name (case-insensitive partial match)."""
    task_name_lower = task_name.lower()
    
    for task in tasks:
        if task['name'].lower() == task_name_lower:
            return task
    
    for task in tasks:
        if task_name_lower in task['name'].lower():
            return task
    
    return None


def format_task(task: Dict[str, Any], include_weekday: bool = True) -> str:
    """Format a task for display."""
    parts = [task['name']]
    
    if task['due_date']:
        date_str = task['due_date_str']
        if include_weekday:
            weekday = get_weekday_name(task['due_date'])
            date_str = f"{date_str} ({weekday})"
        parts.append(f"due: {date_str}")
    
    if task['frequency']:
        parts.append(f"[{task['frequency']}]")
    
    return " - ".join(parts)


def task_to_dict(task: Dict[str, Any]) -> Dict[str, Any]:
    """Convert task to JSON-serializable dict."""
    result = {
        'name': task['name'],
        'due_date': task['due_date_str'],
        'category': task['category'],
        'frequency': task['frequency'],
        'priority': task['priority'],
        'status': task['status'],
        'url': task['url'],
    }
    
    if task['due_date']:
        result['weekday'] = get_weekday_name(task['due_date'])
    
    return result


# =============================================================================
# Commands
# =============================================================================

def cmd_status(args):
    """Show overdue, due today, and due tomorrow tasks."""
    tasks = read_tasks(args.csv_path)
    today = today_local()
    tomorrow = today + timedelta(days=1)
    
    overdue = []
    due_today = []
    due_tomorrow = []
    
    for task in tasks:
        if task['due_date'] and task['status'].lower() != 'done':
            if task['due_date'] < today:
                overdue.append(task)
            elif task['due_date'] == today:
                due_today.append(task)
            elif task['due_date'] == tomorrow:
                due_tomorrow.append(task)
    
    if args.json:
        return {
            'today': format_date(today),
            'today_weekday': get_weekday_name(today),
            'overdue': [task_to_dict(t) for t in overdue],
            'due_today': [task_to_dict(t) for t in due_today],
            'due_tomorrow': [task_to_dict(t) for t in due_tomorrow],
        }
    
    lines = []
    lines.append(f"Task Status for {format_date(today)} ({get_weekday_name(today)})")
    lines.append("=" * 50)
    
    if overdue:
        lines.append(f"\n⚠️  OVERDUE ({len(overdue)}):")
        for task in overdue:
            lines.append(f"  • {format_task(task)}")
    
    if due_today:
        lines.append(f"\n📅 DUE TODAY ({len(due_today)}):")
        for task in due_today:
            lines.append(f"  • {format_task(task)}")
    
    if due_tomorrow:
        lines.append(f"\n📆 DUE TOMORROW ({len(due_tomorrow)}):")
        for task in due_tomorrow:
            lines.append(f"  • {format_task(task)}")
    
    if not overdue and not due_today and not due_tomorrow:
        lines.append("\n✅ No tasks due today or tomorrow, and nothing overdue!")
    
    return "\n".join(lines)


def cmd_upcoming(args):
    """Show tasks due in the next N days."""
    tasks = read_tasks(args.csv_path)
    today = today_local()
    end_date = today + timedelta(days=args.days)
    
    upcoming = []
    for task in tasks:
        if task['due_date'] and task['status'].lower() != 'done':
            if today <= task['due_date'] <= end_date:
                upcoming.append(task)
    
    upcoming.sort(key=lambda t: t['due_date'])
    
    if args.json:
        return {
            'today': format_date(today),
            'end_date': format_date(end_date),
            'days': args.days,
            'tasks': [task_to_dict(t) for t in upcoming],
        }
    
    lines = []
    lines.append(f"Tasks due in next {args.days} days ({format_date(today)} to {format_date(end_date)})")
    lines.append("=" * 50)
    
    if upcoming:
        for task in upcoming:
            lines.append(f"  • {format_task(task)}")
    else:
        lines.append("\n✅ No tasks due in this period!")
    
    return "\n".join(lines)


def cmd_list(args):
    """List all tasks."""
    tasks = read_tasks(args.csv_path)
    
    if args.status:
        tasks = [t for t in tasks if t['status'].lower() == args.status.lower()]
    
    if args.json:
        return {
            'count': len(tasks),
            'tasks': [task_to_dict(t) for t in tasks],
        }
    
    lines = []
    lines.append(f"All Tasks ({len(tasks)} total)")
    lines.append("=" * 50)
    
    for task in tasks:
        lines.append(f"  • {format_task(task)}")
    
    return "\n".join(lines)


def cmd_get(args):
    """Get details for a specific task."""
    tasks = read_tasks(args.csv_path)
    task = find_task(tasks, args.task_name)
    
    if not task:
        if args.json:
            return {'error': f"Task not found: {args.task_name}"}
        return f"Error: Task not found: {args.task_name}"
    
    if args.json:
        return task_to_dict(task)
    
    lines = []
    lines.append(f"Task: {task['name']}")
    lines.append("=" * 50)
    lines.append(f"  Due Date:  {task['due_date_str']}" + 
                 (f" ({get_weekday_name(task['due_date'])})" if task['due_date'] else ""))
    lines.append(f"  Category:  {task['category']}")
    lines.append(f"  Frequency: {task['frequency']}")
    lines.append(f"  Priority:  {task['priority']}")
    lines.append(f"  Status:    {task['status']}")
    lines.append(f"  URL:       {task['url']}")
    
    return "\n".join(lines)


def cmd_complete(args):
    """Complete a task and calculate next due date for recurring tasks."""
    tasks = read_tasks(args.csv_path)
    task = find_task(tasks, args.task_name)
    
    if not task:
        if args.json:
            return {'error': f"Task not found: {args.task_name}"}
        return f"Error: Task not found: {args.task_name}"
    
    old_due_date = task['due_date_str']
    old_status = task['status']
    
    freq_lower = (task['frequency'] or '').lower().strip()
    if task['frequency'] and freq_lower != 'one-time':
        if task['due_date']:
            new_due_date = calculate_next_due_date(
                task['due_date'], 
                task['frequency'], 
                task['name']
            )
            task['due_date'] = new_due_date
            task['due_date_str'] = format_date(new_due_date)
        task['status'] = 'To Do'
        action = 'rescheduled'
    else:
        task['status'] = 'Done'
        action = 'completed'
    
    write_tasks(args.csv_path, tasks)
    
    if args.json:
        result = {
            'action': action,
            'task': task['name'],
            'old_due_date': old_due_date,
            'old_status': old_status,
            'new_due_date': task['due_date_str'],
            'new_status': task['status'],
        }
        if task['due_date']:
            result['new_weekday'] = get_weekday_name(task['due_date'])
        return result
    
    if action == 'rescheduled':
        new_weekday = get_weekday_name(task['due_date']) if task['due_date'] else ''
        return (f"✅ Rescheduled: {task['name']}\n"
                f"   Old due date: {old_due_date}\n"
                f"   New due date: {task['due_date_str']} ({new_weekday})\n"
                f"   Status: {task['status']}")
    else:
        return f"✅ Completed: {task['name']}\n   Status: {task['status']}"


def main():
    parser = argparse.ArgumentParser(
        description="Task manager for PWKM system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--csv', dest='csv_path', type=Path, default=None,
                        help='Path to CSV file (auto-detects if not specified)')
    
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # status
    subparsers.add_parser('status', help='Show overdue, due today, and due tomorrow tasks')
    
    # upcoming
    p_upcoming = subparsers.add_parser('upcoming', help='Show tasks due in next N days')
    p_upcoming.add_argument('days', type=int, nargs='?', default=7, help='Number of days (default: 7)')
    
    # list
    p_list = subparsers.add_parser('list', help='List all tasks')
    p_list.add_argument('--status', help='Filter by status (e.g., "To Do", "Done")')
    
    # get
    p_get = subparsers.add_parser('get', help='Get details for a specific task')
    p_get.add_argument('task_name', help='Task name (partial match supported)')
    
    # complete
    p_complete = subparsers.add_parser('complete', help='Complete a task')
    p_complete.add_argument('task_name', help='Task name (partial match supported)')
    
    args = parser.parse_args()
    
    if args.csv_path is None:
        args.csv_path = get_csv_path()
    
    try:
        handlers = {
            'status': cmd_status,
            'upcoming': cmd_upcoming,
            'list': cmd_list,
            'get': cmd_get,
            'complete': cmd_complete,
        }
        
        result = handlers[args.command](args)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(result)
            
    except FileNotFoundError as e:
        error_msg = f"CSV file not found: {args.csv_path}"
        if args.json:
            print(json.dumps({'error': error_msg}), file=sys.stderr)
        else:
            print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if args.json:
            print(json.dumps({'error': str(e)}), file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
