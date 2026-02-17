# 📋 Task Management

Protocols for task completion and CSV management. Load when completing tasks.

---

## Task Completion Protocol

**When user reports completing a task:**

### Preferred Method: Windows MCP (Local Execution)

**Step 1: Run task_manager.py via Windows MCP:**

```powershell
# Command pattern (run via cmd.exe to avoid PowerShell alias issues):
cmd.exe /c "cd /d <working-dir> && <python-path> scripts/task_manager.py --json complete ""[task name]"" > task_output.txt 2>&1"

# Then read the output:
# Filesystem:read_text_file <working-dir>/task_output.txt
```

**Step 2: Update Notion** (REQUIRED - do not skip):
- Search for the task page in Notion
- Update the Due Date property to the new_due_date from the script output
- Status remains "To Do" for recurring tasks

**For multiple tasks:** Complete all task_manager.py calls first, then batch the Notion updates.

**Key notes:**
- Must use `cmd.exe` wrapper — PowerShell struggles with WindowsApps aliases in pipelines
- Always use `--json` flag to avoid Unicode encoding issues with emojis
- Use double quotes (`""task name""`) for task names containing parentheses
- Output goes to `task_output.txt`, then read via Filesystem tool
- **Both CSV and Notion must be updated** — CSV is the working copy, Notion is the source of truth

### Fallback Method: Claude's Container

If Windows MCP unavailable, copy scripts to Claude's container:

```bash
# Copy files from user's machine:
Filesystem:copy_file_user_to_claude <scripts-dir>/task_manager.py
Filesystem:copy_file_user_to_claude <scripts-dir>/date_utils.py
Filesystem:copy_file_user_to_claude <working-dir>/notion_tasks.csv

# Copy to writable directory and run:
cp /mnt/user-data/uploads/*.py /home/claude/
cp /mnt/user-data/uploads/notion_tasks.csv /home/claude/
cd /home/claude && python task_manager.py complete "Task Name"

# Then manually update user's CSV via Filesystem:write_file
```

### Recurring Patterns

| Pattern | Example | Calculation |
|---|---|---|
| Weekly | Clean Kitchen | +7 days |
| Monthly nth-weekday | Haircut (First Saturday) | Next occurrence of that weekday pattern |
| Quarterly | Seasonal task | +3 months |
| Yearly | Annual review | +1 year |

---

## Tasks Export System Reference

### Directory Structure

```
<working-dir>/
├── scripts/
│   ├── fetch_notion_tasks.py   # Notion API export
│   ├── date_utils.py           # Date calculations
│   ├── task_manager.py         # Task operations
│   └── .env                    # API credentials
├── notion_tasks.csv            # Task data
└── task_output.txt             # Script output (Windows MCP)
```

### Python Environment

- **Path:** Configured via `PWKM_PYTHON` env var or system PATH
- **Required packages:** python-dateutil, tzdata (see requirements.txt)

### CSV Format

Columns: Task Name, Due Date, Category, Frequency, Priority, Status, URL

### Why CSV Instead of Notion API

- Notion MCP doesn't support SQL queries or filtered views
- Individual fetches would require 25+ API calls at startup
- CSV provides complete data in single file read
- Already sorted by due date

---

*Adapt paths and environment variables to your own setup.*
*See setup-guide.md for configuration details.*
