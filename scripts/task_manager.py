"""
PWKM Task Manager
Manages tasks via CSV export from Notion database.

Usage:
    python task_manager.py status              # Show overdue and today's tasks
    python task_manager.py complete "Task"     # Mark task complete, reschedule if recurring
    python task_manager.py reschedule "Task" "2026-02-15"  # Reschedule task
    python task_manager.py list                # List all tasks
"""

import csv
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Configuration - adjust these paths for your setup
CSV_PATH = Path(r"F:\users\keith\OneDrive - KJM\Documents\pwkm\notion\tasks.csv")
BACKUP_DIR = CSV_PATH.parent / "backups"

def load_tasks():
    """Load tasks from CSV file."""
    if not CSV_PATH.exists():
        print(f"Error: CSV file not found at {CSV_PATH}")
        sys.exit(1)
    
    tasks = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(row)
    return tasks

def save_tasks(tasks, fieldnames):
    """Save tasks to CSV file with backup."""
    # Create backup
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"tasks_backup_{timestamp}.csv"
    
    if CSV_PATH.exists():
        import shutil
        shutil.copy(CSV_PATH, backup_path)
    
    # Save updated tasks
    with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tasks)
    
    print(f"Saved. Backup at: {backup_path}")

def parse_date(date_str):
    """Parse date string to datetime object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except ValueError:
        return None

def format_date(dt):
    """Format datetime to string."""
    return dt.strftime("%Y-%m-%d")

def get_next_occurrence(current_date, recurrence):
    """Calculate next occurrence based on recurrence pattern."""
    recurrence = recurrence.lower().strip() if recurrence else ""
    
    if recurrence == "daily":
        return current_date + timedelta(days=1)
    elif recurrence == "weekly":
        return current_date + timedelta(weeks=1)
    elif recurrence == "biweekly":
        return current_date + timedelta(weeks=2)
    elif recurrence == "monthly":
        # Add one month (handle month boundaries)
        month = current_date.month + 1
        year = current_date.year
        if month > 12:
            month = 1
            year += 1
        day = min(current_date.day, 28)  # Safe for all months
        return current_date.replace(year=year, month=month, day=day)
    elif recurrence == "quarterly":
        month = current_date.month + 3
        year = current_date.year
        while month > 12:
            month -= 12
            year += 1
        day = min(current_date.day, 28)
        return current_date.replace(year=year, month=month, day=day)
    else:
        return None

def cmd_status():
    """Show overdue and today's tasks."""
    tasks = load_tasks()
    today = datetime.now().date()
    
    overdue = []
    due_today = []
    upcoming = []  # Next 7 days
    
    for task in tasks:
        due_date = parse_date(task.get('Due Date', ''))
        if not due_date:
            continue
        
        due = due_date.date()
        status = task.get('Status', '').lower()
        
        if status in ['done', 'complete', 'completed']:
            continue
        
        if due < today:
            overdue.append((task, due))
        elif due == today:
            due_today.append((task, due))
        elif due <= today + timedelta(days=7):
            upcoming.append((task, due))
    
    print(f"\n=== Task Status as of {today} ===\n")
    
    if overdue:
        print("⚠️  OVERDUE:")
        for task, due in sorted(overdue, key=lambda x: x[1]):
            days = (today - due).days
            print(f"  [{due}] {task.get('Task', 'Unnamed')} ({days} days overdue)")
    else:
        print("✓ No overdue tasks")
    
    print()
    
    if due_today:
        print("📅 DUE TODAY:")
        for task, due in due_today:
            print(f"  • {task.get('Task', 'Unnamed')}")
    else:
        print("✓ Nothing due today")
    
    print()
    
    if upcoming:
        print("📆 UPCOMING (next 7 days):")
        for task, due in sorted(upcoming, key=lambda x: x[1]):
            weekday = due.strftime("%a")
            print(f"  [{due} {weekday}] {task.get('Task', 'Unnamed')}")

def cmd_complete(task_name):
    """Mark a task complete. Reschedule if recurring."""
    tasks = load_tasks()
    fieldnames = list(tasks[0].keys()) if tasks else []
    
    # Find matching task
    matches = [t for t in tasks if task_name.lower() in t.get('Task', '').lower()]
    
    if not matches:
        print(f"No task found matching '{task_name}'")
        return
    
    if len(matches) > 1:
        print(f"Multiple matches found:")
        for i, t in enumerate(matches, 1):
            print(f"  {i}. {t.get('Task')} (Due: {t.get('Due Date', 'None')})")
        print("Please be more specific.")
        return
    
    task = matches[0]
    task_idx = tasks.index(task)
    
    recurrence = task.get('Recurrence', '')
    current_due = parse_date(task.get('Due Date', ''))
    
    if recurrence and current_due:
        # Recurring task - reschedule
        next_date = get_next_occurrence(current_due, recurrence)
        if next_date:
            tasks[task_idx]['Due Date'] = format_date(next_date)
            print(f"✓ Completed: {task.get('Task')}")
            print(f"  Rescheduled ({recurrence}): {format_date(next_date)}")
        else:
            print(f"Unknown recurrence pattern: {recurrence}")
            return
    else:
        # One-time task - mark done
        if 'Status' in fieldnames:
            tasks[task_idx]['Status'] = 'Done'
        print(f"✓ Completed: {task.get('Task')}")
    
    save_tasks(tasks, fieldnames)

def cmd_reschedule(task_name, new_date_str):
    """Reschedule a task to a new date."""
    tasks = load_tasks()
    fieldnames = list(tasks[0].keys()) if tasks else []
    
    # Validate new date
    new_date = parse_date(new_date_str)
    if not new_date:
        print(f"Invalid date format: {new_date_str}")
        print("Use YYYY-MM-DD format (e.g., 2026-02-15)")
        return
    
    # Find matching task
    matches = [t for t in tasks if task_name.lower() in t.get('Task', '').lower()]
    
    if not matches:
        print(f"No task found matching '{task_name}'")
        return
    
    if len(matches) > 1:
        print(f"Multiple matches found:")
        for i, t in enumerate(matches, 1):
            print(f"  {i}. {t.get('Task')} (Due: {t.get('Due Date', 'None')})")
        print("Please be more specific.")
        return
    
    task = matches[0]
    task_idx = tasks.index(task)
    old_date = task.get('Due Date', 'None')
    
    tasks[task_idx]['Due Date'] = format_date(new_date)
    print(f"✓ Rescheduled: {task.get('Task')}")
    print(f"  From: {old_date}")
    print(f"  To:   {format_date(new_date)}")
    
    save_tasks(tasks, fieldnames)

def cmd_list():
    """List all tasks."""
    tasks = load_tasks()
    today = datetime.now().date()
    
    print(f"\n=== All Tasks ({len(tasks)} total) ===\n")
    
    for task in sorted(tasks, key=lambda t: t.get('Due Date', 'Z')):
        due_str = task.get('Due Date', '')
        status = task.get('Status', '')
        recurrence = task.get('Recurrence', '')
        
        flags = []
        if recurrence:
            flags.append(f"🔄{recurrence}")
        if status.lower() in ['done', 'complete']:
            flags.append("✓")
        
        due_date = parse_date(due_str)
        if due_date and due_date.date() < today and status.lower() not in ['done', 'complete']:
            flags.append("⚠️OVERDUE")
        
        flag_str = " ".join(flags)
        print(f"[{due_str or 'No date'}] {task.get('Task', 'Unnamed')} {flag_str}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        cmd_status()
    elif command == "complete" and len(sys.argv) >= 3:
        cmd_complete(" ".join(sys.argv[2:]))
    elif command == "reschedule" and len(sys.argv) >= 4:
        cmd_reschedule(sys.argv[2], sys.argv[3])
    elif command == "list":
        cmd_list()
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
