# Task Management Protocol

Protocols for task completion, scheduling, and synchronization between CSV and Notion.

---

## Task Database Structure

### CSV Columns
| Column | Description |
|--------|-------------|
| Task | Task name/description |
| Due Date | YYYY-MM-DD format |
| Status | Active, Done, etc. |
| Recurrence | daily, weekly, biweekly, monthly, quarterly, or blank |
| Project | Associated project (optional) |
| Priority | High, Medium, Low (optional) |

### Why CSV?
Notion MCP doesn't support filtered database queries. CSV export enables:
- Single file read vs. 25+ API calls
- Fast status checks at session startup
- Local manipulation with Python scripts

---

## Task Completion Workflow

### For Recurring Tasks

1. **Identify task**: Confirm which task is being completed
2. **Run script**: `python task_manager.py complete "Task Name"`
3. **Script action**: Calculates next occurrence, updates CSV
4. **Update Notion**: Change the due date on the Notion task page
5. **Confirm**: Verify both CSV and Notion reflect new date

### For One-Time Tasks

1. **Identify task**: Confirm which task is being completed
2. **Run script**: `python task_manager.py complete "Task Name"`
3. **Script action**: Marks task as Done in CSV
4. **Update Notion**: Mark task complete or archive
5. **Confirm**: Verify completion in both systems

### Completion Command
```
python task_manager.py complete "Clean Kitchen"
```

Output:
```
✓ Completed: Clean Kitchen
  Rescheduled (weekly): 2026-02-09
```

---

## Recurring Task Patterns

### Supported Recurrence
| Pattern | Behavior |
|---------|----------|
| daily | Next day |
| weekly | +7 days |
| biweekly | +14 days |
| monthly | Same day next month |
| quarterly | +3 months |

### Recurrence Logic
- Calculates from current due date, not completion date
- Monthly uses day 28 max to avoid month-end issues
- Script handles calculation; human confirms reasonableness

---

## Task Rescheduling

### Manual Reschedule
```
python task_manager.py reschedule "Task Name" "2026-02-15"
```

### When to Reschedule
- Task cannot be completed by due date
- Priorities have shifted
- Dependencies not met
- Blocked by external factors

### After Rescheduling
Always update the corresponding Notion page to maintain sync.

---

## Task Status Check

### Daily Check (Session Startup)
```
python task_manager.py status
```

Shows:
- ⚠️ Overdue tasks with days overdue
- 📅 Tasks due today
- 📆 Upcoming tasks (next 7 days)

### Full List
```
python task_manager.py list
```

Shows all tasks with dates and flags.

---

## CSV-Notion Synchronization

### Source of Truth
- **CSV**: For quick reads and script manipulation
- **Notion**: For full task details, notes, project links

### Sync Protocol
After any CSV change:
1. Note which tasks changed
2. Update corresponding Notion pages
3. Verify consistency

### Export Fresh CSV
When Notion has manual changes:
1. Export database to CSV from Notion
2. Replace local CSV file
3. Verify with `task_manager.py list`

---

## Weekly Task Audit

Performed first session of each week:

1. **Review overdue**: Reschedule or complete
2. **Check upcoming**: Realistic given calendar?
3. **Verify sync**: CSV matches Notion
4. **Clean up**: Archive completed one-time tasks
5. **Plan week**: Note key deliverables

---

## Task Creation

### In Notion
1. Add row to Tasks database
2. Set all required fields
3. Export updated CSV

### Quick Add (CSV only)
For temporary tracking, add directly to CSV. Sync to Notion when convenient.

---

## Emergency Task Handling

When task is urgent and not in system:
1. Handle the task
2. Document in running summary
3. Add to system afterward if recurring
4. Note in session summary
