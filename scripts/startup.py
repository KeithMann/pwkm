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
    1. Current date/time (Eastern)
    2. Weather (via weather.py; optional)
    3. Google Calendar today+tomorrow with --classify (DONE/NOW/SOON/LATER)
    4. Task status (overdue, today, tomorrow)
    5. Audit triggers (weekly audit, monthly review)
    6. Scheduled task health check (Windows Task Scheduler)
    7. Session timer start

Replaces: manual sequence of bash date + gcal_query.py + task_manager.py +
session_timer.py audit-check + session_timer.py start

JSON mode: Returns structured data for calendar (parsed events), tasks
(with URLs), and audit (boolean flags). Human-readable mode returns
formatted text report.
"""

import os
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo(os.environ.get("LOCAL_TIMEZONE", "America/New_York"))
SCRIPT_DIR = Path(__file__).parent
PYTHON = os.environ.get("PWKM_PYTHON", sys.executable)

# Custom scheduled tasks to monitor for failures.
# Add new task names here as they are created.
MONITORED_TASKS = [
    'FetchNotionTasks',
    'ClaudeTimerNudge',
]


# Samsung Health export staleness nudge (state-based, self-clearing).
# Reads the newest ingested export snapshot in health.db; fires only when the
# data is older than the threshold and clears once a fresh export is ingested.
# The phone-to-NAS export stays manual even after Phase 2 automates ingest.
# Optional. Set PWKM_HEALTH_DB to enable the health staleness check.
HEALTH_DB_PATH = Path(os.environ.get("PWKM_HEALTH_DB", "health.db"))
HEALTH_STALE_THRESHOLD_DAYS = 3


def run_script(script_name, args=None, timeout=15):
    """Run a Python script and capture output. Returns (success, output).
    
    Note: Calendar calls should use timeout=30 to accommodate cold-start
    OAuth token refresh (see get_calendar).
    """
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
    """Get current date/time in Eastern."""
    now = datetime.now(TZ)
    return {
        'date': now.strftime('%A, %B %d, %Y'),
        'time': now.strftime('%I:%M %p').lstrip('0').lower(),
        'iso': now.isoformat(),
        'day_of_week': now.strftime('%A'),
        'tzname': now.strftime('%Z'),
    }

def ensure_running_summary_exists(dt):
    r"""Initialize today's running summary file if it does not exist.

    Creates %AppData%\Claude\running-summaries\YYYY-MM-DD.md with a standard
    session header. Idempotent: if the file already exists, returns False
    and leaves it untouched.

    Added 2026-04-17 per Phase B protocol review: ensures contemporaneous
    note-taking can begin immediately at session start without a manual
    first-write step.
    """
    iso_date = datetime.now(TZ).strftime('%Y-%m-%d')
    summary_dir = Path(os.environ.get('PWKM_STATE_DIR', str(SCRIPT_DIR.parent))) / 'running-summaries'
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_file = summary_dir / f'{iso_date}.md'
    if summary_file.exists():
        return False
    header = (
        f'# Session: {iso_date}\n'
        f'Project: PWKM\n'
        f"Start time: {dt.get('time', '')} {dt.get('tzname', '')}\n"
        '\n---\n\n'
    )
    summary_file.write_text(header, encoding='utf-8')
    return True



def get_calendar(classify=True, scope='today+tomorrow', use_json=False):
    """Get calendar via gcal_query.py.
    
    Args:
        classify: Add DONE/NOW/SOON/LATER status labels
        scope: Date scope - 'today', 'today+tomorrow', 'week', etc.
        use_json: Request structured JSON from gcal_query.py
    """
    args = [scope]
    if classify:
        args.append('--classify')
    if use_json:
        args.append('--json')
    success, output = run_script('gcal_query.py', args, timeout=30)
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


def get_scheduled_task_health():
    """Check Windows Task Scheduler for failed custom tasks.

    Queries schtasks for each task in MONITORED_TASKS and reports any
    with a non-zero Last Result code. Returns a dict with 'success',
    a list of 'failures', and a list of 'healthy' task names.
    """
    schtasks_exe = r'C:\Windows\System32\schtasks.exe'
    failures = []
    healthy = []

    for task_name in MONITORED_TASKS:
        try:
            result = subprocess.run(
                [schtasks_exe, '/query', '/tn', task_name, '/fo', 'LIST', '/v'],
                capture_output=True, text=True, timeout=10,
                encoding='utf-8', errors='replace',
            )
            if result.returncode != 0:
                failures.append({
                    'name': task_name,
                    'error': f'schtasks query failed (rc={result.returncode})',
                })
                continue

            output = result.stdout

            # Parse Last Result
            last_result = None
            match = re.search(r'Last Result:\s+(-?\d+)', output)
            if match:
                last_result = int(match.group(1))

            # Parse Last Run Time
            last_run = None
            match = re.search(r'Last Run Time:\s+(.+)', output)
            if match:
                last_run = match.group(1).strip()

            if last_result is not None and last_result != 0:
                failures.append({
                    'name': task_name,
                    'last_result': last_result,
                    'last_run': last_run,
                })
            else:
                healthy.append(task_name)

        except subprocess.TimeoutExpired:
            failures.append({'name': task_name, 'error': 'Query timed out'})
        except FileNotFoundError:
            return {
                'success': False,
                'output': 'schtasks.exe not found',
                'failures': [],
                'healthy': [],
            }
        except Exception as e:
            failures.append({'name': task_name, 'error': str(e)})

    return {
        'success': True,
        'failures': failures,
        'healthy': healthy,
    }



def get_weather(use_json=False):
    """Get weather via weather.py."""
    args = []
    if use_json:
        args.append('--json')
    success, output = run_script('weather.py', args if args else None)
    if success and use_json:
        try:
            return {'success': True, 'data': json.loads(output)}
        except json.JSONDecodeError:
            return {'success': True, 'output': output}
    return {'success': success, 'output': output}


def get_market(use_json=False):
    """Get market summary via market.py. Timeout 60s (yfinance batch download)."""
    args = []
    if use_json:
        args.append('--json')
    success, output = run_script('market.py', args if args else None, timeout=60)
    if success and use_json:
        try:
            return {'success': True, 'data': json.loads(output)}
        except json.JSONDecodeError:
            return {'success': True, 'output': output}
    return {'success': success, 'output': output}



def get_milestones():
    """Check milestones.json for approaching or overdue milestones."""
    milestones_file = SCRIPT_DIR / 'milestones.json'
    if not milestones_file.exists():
        return {'success': True, 'alerts': [], 'output': 'No milestones file.'}

    try:
        with open(milestones_file, 'r', encoding='utf-8') as f:
            milestones = json.load(f)
    except Exception as e:
        return {'success': False, 'output': f'Error reading milestones: {e}'}

    today = datetime.now(TZ).date()
    alerts = []
    for ms in milestones:
        try:
            ms_date = datetime.strptime(ms['date'], '%Y-%m-%d').date()
            days = (ms_date - today).days
            if days < 0:
                alerts.append({**ms, 'days': days, 'status': 'OVERDUE'})
            elif days <= 14:
                alerts.append({**ms, 'days': days, 'status': 'APPROACHING'})
        except (ValueError, KeyError):
            continue

    # Sort: overdue first (most negative), then approaching (soonest first)
    alerts.sort(key=lambda x: x['days'])

    if alerts:
        lines = []
        for a in alerts:
            if a['status'] == 'OVERDUE':
                lines.append(f"  \u26a0\ufe0f OVERDUE ({abs(a['days'])}d): {a['name']} [{a.get('project', '')}]")
            else:
                lines.append(f"  \u23f0 {a['days']}d: {a['name']} [{a.get('project', '')}]")
            if a.get('prep_tasks'):
                for pt in a['prep_tasks']:
                    lines.append(f"      - {pt}")
        output = '\n'.join(lines)
    else:
        output = '  No milestones within 14 days.'

    return {'success': True, 'alerts': alerts, 'output': output}



def get_incubating_ideas():
    """Check incubating_ideas.json for ideas ready to revisit."""
    ideas_file = SCRIPT_DIR / 'incubating_ideas.json'
    if not ideas_file.exists():
        return {'success': True, 'ready': [], 'output': ''}

    try:
        with open(ideas_file, 'r', encoding='utf-8') as f:
            ideas = json.load(f)
    except Exception as e:
        return {'success': False, 'output': f'Error reading ideas: {e}'}

    today = datetime.now(TZ).date()
    ready = []
    for idea in ideas:
        try:
            revisit = datetime.strptime(idea['revisit'], '%Y-%m-%d').date()
            if revisit <= today:
                days_ago = (today - revisit).days
                ready.append({**idea, 'days_ready': days_ago})
        except (ValueError, KeyError):
            continue

    if ready:
        lines = []
        for r in ready:
            if r['days_ready'] == 0:
                lines.append(f"  \U0001f4a1 Ready today: {r['idea']} [{r.get('project', '')}]")
            else:
                lines.append(f"  \U0001f4a1 Ready ({r['days_ready']}d ago): {r['idea']} [{r.get('project', '')}]")
            if r.get('notes'):
                lines.append(f"      {r['notes']}")
        output = '\n'.join(lines)
    else:
        output = ''

    return {'success': True, 'ready': ready, 'output': output}

def get_news(use_json=False):
    """Get news headlines via news.py."""
    args = ['--limit', '5']
    if use_json:
        args.append('--json')
    success, output = run_script('news.py', args)
    if success and use_json:
        try:
            return {'success': True, 'data': json.loads(output)}
        except json.JSONDecodeError:
            return {'success': True, 'output': output}
    return {'success': success, 'output': output}




def get_activitywatch():
    """Get yesterday's ActivityWatch data via activitywatch.py. JSON only."""
    success, output = run_script('activitywatch.py', timeout=30)
    if success:
        try:
            return {'success': True, 'data': json.loads(output)}
        except json.JSONDecodeError:
            return {'success': False, 'output': 'JSON parse error'}
    return {'success': False, 'output': output}


def get_health_staleness():
    """Samsung Health export staleness check (state-based, self-clearing).

    Reads the newest export snapshot recorded in health.db and reports how many
    days behind it is. The nudge fires only when days_behind >= threshold and
    clears automatically once a fresh export is ingested. The phone-to-NAS export
    stays manual even after Phase 2 automates the ingest step, so this stays useful.
    """
    import sqlite3
    result = {
        'success': False, 'stale': False, 'days_behind': None,
        'last_export': None, 'threshold': HEALTH_STALE_THRESHOLD_DAYS,
    }
    try:
        if not HEALTH_DB_PATH.exists():
            result['output'] = 'health.db not found'
            return result
        conn = sqlite3.connect(str(HEALTH_DB_PATH))
        try:
            row = conn.execute("SELECT MAX(timestamp) FROM export").fetchone()
        finally:
            conn.close()
        if not row or not row[0]:
            result['output'] = 'no exports recorded'
            return result
        ts = row[0]
        try:
            last_date = datetime.fromisoformat(ts[:19]).date()
        except ValueError:
            last_date = datetime.strptime(ts[:10], '%Y-%m-%d').date()
        today = datetime.now(TZ).date()
        days = (today - last_date).days
        result.update({
            'success': True,
            'last_export': last_date.isoformat(),
            'days_behind': days,
            'stale': days >= HEALTH_STALE_THRESHOLD_DAYS,
        })
        return result
    except Exception as e:
        result['output'] = str(e)
        return result


def format_compact_report(dt, weather, market, news, milestones, ideas, calendar, tasks, audit, timer, sched_health, activitywatch=None, health=None):
    """Format a compact human-readable startup report."""
    lines = []
    
    # Header
    lines.append(f"=== STARTUP REPORT: {dt['date']} {dt['time']} ===")
    lines.append("")
    
    # Weather
    lines.append("--- WEATHER ---")
    if weather['success']:
        for wline in weather['output'].split('\n'):
            lines.append(f"  {wline}")
    else:
        lines.append(f"  [Weather unavailable: {weather['output']}]")
    lines.append("")

    # Market
    lines.append("--- MARKET ---")
    if market['success']:
        for mline in market['output'].split('\n'):
            lines.append(f"  {mline}")
    else:
        lines.append(f"  [Market unavailable: {market['output']}]")
    lines.append("")

    # News
    lines.append("--- NEWS ---")
    if news['success']:
        for nline in news['output'].split('\n'):
            lines.append(f"  {nline}")
    else:
        lines.append(f"  [News unavailable: {news['output']}]")
    lines.append("")

    # Milestones
    if milestones.get('alerts'):
        lines.append("--- MILESTONES ---")
        for mline in milestones['output'].split('\n'):
            lines.append(f"  {mline}")
        lines.append("")

    # Incubating Ideas
    if ideas.get('ready'):
        lines.append("--- IDEAS READY TO REVISIT ---")
        for iline in ideas['output'].split('\n'):
            lines.append(f"  {iline}")
        lines.append("")

    # Calendar
    lines.append("--- CALENDAR ---")
    if calendar['success']:
        lines.append(calendar['output'])
    else:
        lines.append(f"  [Calendar unavailable: {calendar['output']}]")
    lines.append("")
    
    # Tasks
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
    
    # Audit
    lines.append("--- AUDITS ---")
    if audit['success']:
        for audit_line in audit['output'].split('\n'):
            lines.append(f"  {audit_line}")
    else:
        lines.append(f"  [Audit check unavailable: {audit['output']}]")
    lines.append("")
    
    # Health export staleness (nudge only when behind; self-clearing)
    if health and health.get('success') and health.get('stale'):
        lines.append("--- HEALTH EXPORT ---")
        lines.append(f"  \u26a0\ufe0f Samsung export {health['days_behind']}d behind (last: {health['last_export']}, threshold {health['threshold']}d)")
        lines.append("     Export from phone, then run: ingest.py -> aggregates.py (writes to health.db; Notion sync retired June 7, 2026)")
        lines.append("")

    # Scheduled task health
    lines.append("--- SCHEDULED TASKS ---")
    if sched_health['success']:
        if sched_health['failures']:
            lines.append("  ** FAILURES DETECTED:")
            for f in sched_health['failures']:
                if 'last_result' in f:
                    lines.append(f"    - {f['name']}: Last Result {f['last_result']} (ran {f.get('last_run', 'unknown')})")
                else:
                    lines.append(f"    - {f['name']}: {f.get('error', 'unknown error')}")
        else:
            lines.append(f"  All {len(sched_health['healthy'])} monitored tasks healthy.")
    else:
        lines.append(f"  [Health check unavailable: {sched_health.get('output', 'unknown')}]")
    lines.append("")
    
    # ActivityWatch (yesterday)
    lines.append("--- ACTIVITYWATCH ---")
    if activitywatch and activitywatch.get('success'):
        aw = activitywatch['data']
        lines.append(f"  [Yesterday: {aw.get('day_of_week', '?')}, {aw.get('date', '?')}]")
        lines.append(f"  Active: {aw.get('active_minutes', 0)} min")
        sessions = aw.get('sessions', [])
        if sessions:
            first = sessions[0]['start']
            last = sessions[-1]['end']
            lines.append(f"  Sessions: {len(sessions)} ({first} - {last})")
        cats = aw.get('categories', [])
        if cats:
            top = [f"{c['category']} ({c['minutes']}m)" for c in cats[:5]]
            lines.append(f"  Top: {', '.join(top)}")
        tod = aw.get('time_of_day_minutes', {})
        if tod:
            tod_str = ', '.join(f"{k}: {v}m" for k, v in tod.items())
            lines.append(f"  Time of day: {tod_str}")
    elif activitywatch:
        lines.append(f"  [Unavailable: {activitywatch.get('output', 'unknown')}]")
    else:
        lines.append("  [Not queried]")
    lines.append("")
    
    # Timer
    lines.append("--- SESSION ---")
    if timer['success']:
        for timer_line in timer['output'].split('\n'):
            lines.append(f"  {timer_line}")
    else:
        lines.append(f"  [Timer error: {timer['output']}]")
    
    return '\n'.join(lines)


def format_json_report(dt, weather, market, news, milestones, ideas, calendar, tasks, audit, timer, sched_health, activitywatch=None, health=None):
    """Format a JSON startup report."""
    # Use structured audit data if available, otherwise parse text
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
        'weather': weather,
        'market': market,
        'news': news,
        'milestones': milestones,
        'calendar': calendar,
        'tasks': tasks,
        'audit': audit_data,
        'scheduled_tasks': sched_health,
        'session_timer': {'success': timer['success'], 'output': timer['output']},
        'activitywatch': activitywatch,
        'health': health,
    }
    return json.dumps(report, indent=2, default=str)


def main():
    # Ensure UTF-8 output (Windows defaults to cp1252 which chokes on replacement chars)
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    # Clean up stale output files before doing anything.
    # Belt-and-suspenders: shell redirect should truncate, but this ensures
    # no stale data survives if the script is called differently.
    output_dir = Path(__file__).parent.parent
    # Note: startup_output.txt is NOT listed here because it's opened by
    # the shell redirect (>) before Python starts. Deleting it would orphan
    # the file handle and lose all output.
    stale_files = ['gcal_output.txt', 'task_output.txt',
                   'timer_output.txt', 'date_output.txt']
    for fname in stale_files:
        f = output_dir / fname
        if f.exists():
            try:
                f.unlink()
            except OSError:
                pass  # Best effort; don't fail startup over cleanup

    parser = argparse.ArgumentParser(description='Consolidated session startup')
    parser.add_argument('--json', action='store_true', help='JSON output')
    parser.add_argument('--skip-calendar', action='store_true',
                       help='Skip calendar API call')
    parser.add_argument('--calendar-scope', default='today+tomorrow',
                       help="Calendar scope: 'today', 'today+tomorrow', 'week', or YYYY-MM-DD (default: today+tomorrow)")
    args = parser.parse_args()
    
    # 1. Date/time
    dt = get_datetime()

    # 1b. Initialize today's running summary file if it doesn't exist
    ensure_running_summary_exists(dt)
    
    # 2. Weather
    weather = get_weather(use_json=args.json)

    # 3. Market
    market = get_market(use_json=args.json)

    # 4. News
    news = get_news(use_json=args.json)

    # 5. ActivityWatch (yesterday)
    activitywatch = get_activitywatch()

    # 6. Milestones
    milestones = get_milestones()

    # 7. Incubating ideas
    ideas = get_incubating_ideas()

    # 8. Calendar
    if args.skip_calendar:
        calendar = {'success': False, 'output': 'Skipped (--skip-calendar)'}
    else:
        calendar = get_calendar(scope=args.calendar_scope, use_json=args.json)
    
    # 9. Tasks
    tasks = get_tasks()
    
    # 10. Audit triggers
    audit = get_audit_status(use_json=args.json)
    
    # 11. Scheduled task health
    sched_health = get_scheduled_task_health()
    
    # 12. Start session timer
    timer = start_session_timer()
    
    # 13. Health export staleness
    health = get_health_staleness()

    # Output
    if args.json:
        report = format_json_report(dt, weather, market, news, milestones, ideas, calendar, tasks, audit, timer, sched_health, activitywatch, health)
    else:
        report = format_compact_report(dt, weather, market, news, milestones, ideas, calendar, tasks, audit, timer, sched_health, activitywatch, health)
    print(report)
    sys.stdout.flush()


if __name__ == '__main__':
    main()
