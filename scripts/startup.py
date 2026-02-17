#!/usr/bin/env python3
"""
Startup Orchestrator - Consolidated session startup report

Runs all startup checks in sequence and produces a single combined report,
replacing 5-6 separate tool calls with one.

Usage:
    python startup.py                  # Full startup report (human-readable)
    python startup.py --json           # JSON output for structured parsing
    python startup.py --skip-calendar  # Skip calendar API call (offline mode)
    python startup.py --calendar-scope today  # Today only (default: today+tomorrow)

What it does:
    1. Current date/time (local timezone)
    2. Google Calendar today+tomorrow with --classify (DONE/NOW/SOON/LATER)
    3. Task status (overdue, today, tomorrow)
    4. Audit triggers (weekly audit, monthly review)
    5. Session timer start

Replaces: manual sequence of bash date + gcal_query.py + task_manager.py +
session_timer.py audit-check + session_timer.py start

JSON mode: Returns structured data for calendar (parsed events), tasks
(with URLs), and audit (boolean flags). Human-readable mode returns
formatted text report.

Configuration:
    Set LOCAL_TIMEZONE env var or edit TZ_NAME below. Default: America/New_York
    Set PWKM_PYTHON env var for Python interpreter path if not on PATH.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ_NAME = os.environ.get("LOCAL_TIMEZONE", "America/New_York")
TZ = ZoneInfo(TZ_NAME)
SCRIPT_DIR = Path(__file__).parent
# Use PWKM_PYTHON env var, or fall back to 'python' on PATH
PYTHON = os.environ.get("PWKM_PYTHON", sys.executable)


def run_script(script_name, args=None, timeout=15):
    """Run a Python script and capture output. Returns (success, output)."""
    cmd = [PYTHON, str(SCRIPT_DIR / script_name)]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(SCRIPT_DIR.parent),
            encoding='utf-8',
            errors='replace'
        )
        output = result.stdout.strip()
        if result.returncode != 0:
            error = result.stderr.strip() if result.stderr else 'Unknown error'
            return False, f"Error: {error}"
        return True, output
    except subprocess.TimeoutExpired:
        return False, f"Timeout ({timeout}s)"
    except FileNotFoundError:
        return False, f"Script not found: {script_name}"
    except Exception as e:
        return False, f"Exception: {e}"


def get_datetime():
    """Get current date/time in local timezone."""
    now = datetime.now(TZ)
    return {
        'date': now.strftime('%A, %B %d, %Y'),
        'time': now.strftime('%I:%M %p').lstrip('0').lower(),
        'iso': now.isoformat(),
        'day_of_week': now.strftime('%A'),
    }


def get_calendar(classify=True, scope='today+tomorrow', use_json=False):
    """Get calendar via gcal_query.py."""
    args = [scope]
    if classify:
        args.append('--classify')
    if use_json:
        args.append('--json')
    success, output = run_script('gcal_query.py', args)
    if success and use_json:
        try:
            return {'success': True, 'data': json.loads(output)}
        except json.JSONDecodeError:
            return {'success': True, 'output': output}
    return {'success': success, 'output': output}


def get_tasks():
    """Get task status via task_manager.py."""
    success, output = run_script('task_manager.py', ['--json', 'status'])
    if success:
        try:
            return {'success': True, 'data': json.loads(output)}
        except json.JSONDecodeError:
            return {'success': True, 'output': output}
    return {'success': False, 'output': output}


def get_audit_status(use_json=False):
    """Check audit triggers via session_timer.py."""
    args = ['audit-check']
    if use_json:
        args.append('--json')
    success, output = run_script('session_timer.py', args)
    if success and use_json:
        try:
            return {'success': True, 'data': json.loads(output)}
        except json.JSONDecodeError:
            return {'success': True, 'output': output}
    return {'success': success, 'output': output}


def start_session_timer():
    """Start session timer via session_timer.py."""
    success, output = run_script('session_timer.py', ['start'])
    return {'success': success, 'output': output}


def format_compact_report(dt, calendar, tasks, audit, timer):
    """Format a compact human-readable startup report."""
    lines = []
    
    lines.append(f"=== STARTUP REPORT: {dt['date']} {dt['time']} ===")
    lines.append("")
    
    lines.append("--- CALENDAR ---")
    if calendar['success']:
        lines.append(calendar['output'])
    else:
        lines.append(f"  [Calendar unavailable: {calendar['output']}]")
    lines.append("")
    
    lines.append("--- TASKS ---")
    if tasks['success']:
        if 'data' in tasks:
            data = tasks['data']
            if data.get('overdue'):
                lines.append("  OVERDUE:")
                for t in data['overdue']:
                    freq = f" [{t['frequency']}]" if t.get('frequency') else ''
                    lines.append(f"    - {t['name']} (due {t['due_date']}, {t.get('weekday', '')}){freq}")
            if data.get('due_today'):
                lines.append("  TODAY:")
                for t in data['due_today']:
                    freq = f" [{t['frequency']}]" if t.get('frequency') else ''
                    lines.append(f"    - {t['name']}{freq}")
            if data.get('due_tomorrow'):
                lines.append("  TOMORROW:")
                for t in data['due_tomorrow']:
                    freq = f" [{t['frequency']}]" if t.get('frequency') else ''
                    lines.append(f"    - {t['name']}{freq}")
            if not data.get('overdue') and not data.get('due_today') and not data.get('due_tomorrow'):
                lines.append("  No overdue, today, or tomorrow tasks.")
        else:
            lines.append(f"  {tasks['output']}")
    else:
        lines.append(f"  [Tasks unavailable: {tasks['output']}]")
    lines.append("")
    
    lines.append("--- AUDITS ---")
    if audit['success']:
        for audit_line in audit['output'].split('\n'):
            lines.append(f"  {audit_line}")
    else:
        lines.append(f"  [Audit check unavailable: {audit['output']}]")
    lines.append("")
    
    lines.append("--- SESSION ---")
    if timer['success']:
        lines.append(f"  {timer['output']}")
    else:
        lines.append(f"  [Timer error: {timer['output']}]")
    
    return '\n'.join(lines)


def format_json_report(dt, calendar, tasks, audit, timer):
    """Format a JSON startup report."""
    if 'data' in audit:
        audit_data = {'success': True, **audit['data']}
    else:
        audit_data = {'success': audit['success']}
        if audit['success']:
            audit_text = audit.get('output', '')
            audit_data['weekly_audit_needed'] = '** WEEKLY AUDIT NEEDED' in audit_text
            audit_data['monthly_review_needed'] = '** MONTHLY IDEA REVIEW NEEDED' in audit_text
            audit_data['raw'] = audit_text
        else:
            audit_data['error'] = audit.get('output', 'Unknown error')
    
    report = {
        'datetime': dt,
        'calendar': calendar,
        'tasks': tasks,
        'audit': audit_data,
        'session_timer': {'success': timer['success'], 'output': timer['output']},
    }
    return json.dumps(report, indent=2, default=str)


def main():
    parser = argparse.ArgumentParser(description='Consolidated session startup')
    parser.add_argument('--json', action='store_true', help='JSON output')
    parser.add_argument('--skip-calendar', action='store_true',
                       help='Skip calendar API call')
    parser.add_argument('--calendar-scope', default='today+tomorrow',
                       help="Calendar scope: 'today', 'today+tomorrow', 'week', or YYYY-MM-DD (default: today+tomorrow)")
    args = parser.parse_args()
    
    dt = get_datetime()
    
    if args.skip_calendar:
        calendar = {'success': False, 'output': 'Skipped (--skip-calendar)'}
    else:
        calendar = get_calendar(scope=args.calendar_scope, use_json=args.json)
    
    tasks = get_tasks()
    audit = get_audit_status(use_json=args.json)
    timer = start_session_timer()
    
    if args.json:
        print(format_json_report(dt, calendar, tasks, audit, timer))
    else:
        print(format_compact_report(dt, calendar, tasks, audit, timer))


if __name__ == '__main__':
    main()
