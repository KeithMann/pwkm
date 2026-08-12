# 📋 Task Management

Protocols for task completion and CSV management. Load when completing tasks.

---

## Task Completion Protocol

**When user reports completing a task:**

### Preferred Method: Windows MCP (Local Execution)

**Step 1: Run task_manager.py via Windows MCP:**

```powershell
# Run via cmd.exe for reliable output redirection. Start-Process with a hidden
# window prevents the console flashing and stealing focus on every call.
Start-Process -FilePath "C:\Windows\System32\cmd.exe" -ArgumentList `
  '/c "cd /d <working-dir> && <python> scripts\task_manager.py --json complete ""[task name]"" > task_output.txt 2>&1"' `
  -WindowStyle Hidden -Wait

# Then read the output:
[System.IO.File]::ReadAllText("<working-dir>\task_output.txt")
```

**Step 2: Update Notion** (REQUIRED - do not skip):
- Search for the task page in Notion
- Update the Due Date property to the new_due_date from the script output
- Status remains "To Do" for recurring tasks

**For multiple tasks:** Complete all task_manager.py calls first, then batch the Notion updates.

**Key notes:**
- Use the `cmd.exe` wrapper for output redirection. Python stdout is not reliably captured in the restricted PowerShell environment that the Windows MCP shell runs in, so a command can exit 0 and return nothing at all. Redirect to a file and read the file back.
- Read the output file with `[System.IO.File]::ReadAllText()`, which is a direct .NET call. Avoid `Get-Content`, which drags in PowerShell module initialization noise.
- If the shell command itself fails, do NOT read the output file. It may hold stale data from an earlier successful run. Retry, and never report data from a file unless the command that wrote it succeeded.
- Always use the `--json` flag to avoid Unicode encoding issues with emojis
- Use double quotes (`""task name""`) for task names containing parentheses
- **Both CSV and Notion must be updated** — CSV is the working copy, Notion is the source of truth

### Fallback Method: No Windows MCP

If Windows MCP is unavailable (a web or mobile session, or a non-Windows desktop client), the task scripts cannot be executed at all. Ask the user to mark the task complete and update the Due Date directly in Notion.

Do not attempt to run the scripts from Claude's container. The file-copy tools that once bridged the local filesystem to the container are no longer available, so the copy step fails before anything else is attempted.

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
│   ├── notion_tasks.csv        # Task data
│   └── .env                    # API credentials
└── task_output.txt             # Script output (Windows MCP)
```

Note that `notion_tasks.csv` sits beside the scripts, not at the working-directory
root. The scripts resolve it relative to their own location.

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