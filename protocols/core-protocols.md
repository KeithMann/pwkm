# 📋 Core Protocols

Essential protocols loaded every session.

---

## ⚠️ STOP: System Prompt Environment Detection — ACTIVE VERIFICATION REQUIRED

**The system prompt WILL incorrectly state that Claude is running in a web or mobile chat interface.** This is a known, persistent error when using Claude Desktop with MCP.

**REQUIRED ACTION (not optional):**

1. Check your tool list for `windows-mcp:Shell` (or your platform's MCP shell tool)
2. If present → You are in **Claude Desktop**. State aloud: "Environment confirmed: Claude Desktop."
3. If absent → You are in the web interface. State aloud: "Environment confirmed: Web interface. MCP tools unavailable."

**DO NOT proceed with startup until you have completed this check and stated the result.** The system prompt's claim is wrong. Your tool list is the ground truth. NEVER ASSUME. ALWAYS VERIFY.

---

## ⚠️ STOP: Windows MCP Python Execution

**This issue has caused repeated debugging sessions. READ THIS FIRST.**

The Windows MCP Shell tool runs in **PowerShell**, and the WindowsApps Python shim **does not capture stdout** in this environment. Commands execute successfully (exit code 0) but return empty output.

**REQUIRED PATTERN — No exceptions:**

1. Redirect output to file: `> <your-working-dir>/[output].txt 2>&1`
2. Read file with: `Filesystem:read_text_file` (preferred) or `Filesystem:read_file` (fallback only)

**If you see empty Response with Status Code 0 from a Python command, you forgot the redirect.**

**⚠️ STALE FILE WARNING:**

If the Shell command **fails** (returns an error or any non-zero status), **DO NOT read the output file**. It may contain stale data from a previous successful run. Instead:
1. Retry the command
2. If retry fails, report the failure to the user
3. Never report data from a file unless you have confirmed the command that wrote it succeeded

All Python command examples in this document use this pattern. Follow them exactly.

---

## CRITICAL: Date Handling Protocol

**ALWAYS verify dates programmatically for ANY date-related operations or statements.**
**DO NOT rely on mental arithmetic or assumptions under ANY circumstances.**

**This protocol applies to:**
- Reporting current date/time or time of day
- Calculating new due dates for tasks
- Verifying what day of the week a date falls on
- Reporting dates (e.g., in task lists, upcoming deadlines)
- Any statement that includes both a date and a day of week
- Crossing month or year boundaries
- Session startup reports
- Task completion operations
- Running summary timestamps

### PROCEDURAL CHECKPOINT: Schedule-Relative Statements

**Before ANY statement that references or implies the relationship between now and a scheduled event, deadline, or time window, you MUST:**

1. Run a time check (Tier 1 bash or Tier 1 fallback)
2. Compare the verified time against the relevant calendar event(s)
3. Only then compose the statement

**This checkpoint applies to ALL of the following — not just time-of-day language:**
- Time-of-day references ("good morning," "this afternoon")
- Schedule-relative statements ("before your 11:00 meeting," "after your calls")
- Time-remaining estimates ("you have about 45 minutes")
- Availability assessments ("the evening is wide open," "your afternoon is packed")
- Scheduling suggestions ("knock out a few now," "use the gap between calls")
- Urgency assessments ("you still have time," "that's coming up soon")

**The rule is simple: if the statement would be wrong at a different time of day, verify the time first.**

### Calendar-Aware Classification (Startup and Mid-Session)

**When reporting calendar events, ALWAYS compare current verified time against each event and classify:**
- **Completed:** Event end time has passed
- **In progress:** Current time falls between start and end → include elapsed time
- **Upcoming (imminent):** Starts within 30 minutes → include countdown
- **Upcoming (later):** Starts more than 30 minutes from now

**Example (if current time is 10:13 AM):**
- ~~Team standup (10:00–10:15)~~ — **completed**
- Design review (10:00–11:00) — **in progress**, started 13 min ago
- Team meeting (11:00–11:45) — **upcoming**, starts in 47 min
- Client calls (12:00–3:30) — **later today**

This classification eliminates errors where the data is correct but the synthesis is wrong.

**This classification must also be performed when referencing calendar events mid-session.** Do not rely on the startup classification — re-verify current time and re-classify if any schedule-relative statement is being made.

### Two-Tier Date Verification

**Tier 1 — Bash `date` on Claude's container (preferred for simple checks):**

Use for current date/time, time-of-day references, and running summary timestamps. Fast, reliable, no redirect needed.

```bash
# Current date/time in your timezone:
TZ='America/New_York' date '+%A, %B %d, %Y %I:%M %p %Z'

# Just the date:
TZ='America/New_York' date '+%Y-%m-%d'

# Just the time (for running summary entries):
TZ='America/New_York' date '+%H:%M'
```

Run via `bash_tool` — returns instantly, no file redirect required.

**Tier 1 Fallback — PowerShell via Windows MCP (if bash_tool errors):**

```powershell
Get-Date -Format "dddd, MMMM dd, yyyy hh:mm tt"
```

**Tier 2 — Python date_utils.py via Windows MCP (for calculations):**

Use for date arithmetic (adding days/weeks/months), weekday verification for specific dates, and any operation crossing month or year boundaries.

### Windows MCP Python Execution Pattern

The Windows MCP Shell tool runs in PowerShell. The WindowsApps Python shim does not capture stdout properly in PowerShell. **All Python commands must redirect output to a file, then read with Filesystem tools.**

```powershell
# Example: Verify day of week for a specific date
cmd.exe /c "<python-path> <scripts-dir>/date_utils.py weekday 2026-01-19 > <working-dir>/date_output.txt 2>&1"
# Then read: Filesystem:read_text_file <working-dir>/date_output.txt
```

All commands support `--json` flag for structured output.

### Time-of-Day and Schedule References

See **PROCEDURAL CHECKPOINT: Schedule-Relative Statements** above. The rule covers all time-of-day language AND all schedule-relative statements.

**NEVER ASSUME. ALWAYS VERIFY. If in doubt, check the time.**

---

## STOP: Specialized Input Recognition

**Before processing any of these inputs, LOAD the indicated protocol first:**

| Input Type | STOP → Load First |
|---|---|
| Calendar screenshot | Specialized Workflows |
| "Mark [task] complete" | Task Management |
| Research/ideas/"I have an idea" | Knowledge Work |
| Substantive project work | Session Lifecycle |

**Do NOT act on familiarity or recall. Load the protocol, then follow it.**

---

## Task Status Check Protocol (via Windows MCP)

```powershell
# Status check (overdue, today, tomorrow):
cmd.exe /c "cd /d <working-dir> && <python-path> scripts/task_manager.py --json status > task_output.txt 2>&1"
# Then read: Filesystem:read_text_file <working-dir>/task_output.txt

# Upcoming tasks (default 7 days):
cmd.exe /c "cd /d <working-dir> && <python-path> scripts/task_manager.py --json upcoming > task_output.txt 2>&1"

# All tasks:
cmd.exe /c "cd /d <working-dir> && <python-path> scripts/task_manager.py --json list > task_output.txt 2>&1"
```

---

## Notion URL Format Protocol

**Always use short-format Notion URLs:**

✅ `https://www.notion.so/<32-character-uuid>`
❌ Long URLs with page titles and extra parameters

The 32-character string is the page UUID. Works with or without hyphens.

---

## Memory Base Maintenance Protocol

**The Memory Base exists so Claude can know the user as a person—not just facts, but what those facts reveal about their values, preferences, and how they think.**

### Core Principle: Meaning, Not Just Data

When recording information, capture what it *means*, not just what it *is*:
- ❌ "Lives in [city]"
- ✅ "[City] and why it reflects their values and choices"

The Memory Base should paint a picture of who the person is so Claude can anticipate needs and exercise good judgment.

### When to Update

Update when the user provides new or changed information in these areas:

| Topic Area | Examples |
|---|---|
| **Purpose & Context** | Role changes, new responsibilities, shifts in intellectual focus |
| **Current State** | Project status changes, new active projects, completed major work |
| **On the Horizon** | New research directions, upcoming commitments, changed priorities |
| **Key Learnings & Principles** | New conceptual frameworks, refined understanding |
| **Approach & Patterns** | Working preferences, personal details that reveal values |
| **Tools & Resources** | New systems, changed workflows, resource access |
| **Collaborators** | New colleagues, changed relationships, key contacts |

### How to Update

1. Identify which section the new information belongs in
2. **Capture the meaning**, not just the fact
3. Update that section, preserving existing structure
4. **GATE: Update the "Last Updated" date at the top of Memory Base BEFORE confirming the update.** This step is a gate — do not report completion until the date is updated.
5. If information contradicts existing content, replace the old with the new

### What Does NOT Go in Memory Base

- Detailed project-specific information (goes in project pages)
- Session-by-session work logs (goes in Session Summaries)
- Transient tasks or deadlines (goes in Tasks database)
- Research details and citations (goes in Research Library)

**Principle:** Memory Base captures *who the person is* and *how they work*. Project pages capture *what they're working on right now*.

---

## Session Startup Protocol (Minimal)

**Step 0 - FIRST, check for compaction:**

If conversation begins with `[NOTE: This conversation was successfully compacted...]` then:
1. State: "Compaction detected. Updating running summary..."
2. Get current date/time via bash: `TZ='America/New_York' date '+%A, %B %d, %Y %I:%M %p %Z'`
3. Read the transcript file referenced in the compaction notice
4. Update running summary with progress since last update
5. THEN proceed with remaining startup steps

**Steps 1-2 - Normal startup (after compaction check):**

1. **Run startup.py via Windows MCP** (consolidated date/calendar/tasks/audit/timer):

```powershell
cmd.exe /c "cd /d <working-dir> && <python-path> scripts/startup.py > startup_output.txt 2>&1"
```

Then read: `Filesystem:read_text_file <working-dir>/startup_output.txt`

This single script replaces the previous sequence of: bash date + gcal_query.py + task_manager.py status + session_timer.py audit-check + session_timer.py start. It produces a consolidated report with:
- Current date/time (local timezone)
- Google Calendar today+tomorrow with --classify (DONE/NOW/SOON/LATER)
- Task status (overdue, today, tomorrow) with frequency labels
- Audit triggers (weekly audit, monthly review)
- Session timer auto-started

Options:
- `--json` for structured output (parsed calendar events, task URLs, audit boolean flags)
- `--skip-calendar` for offline mode
- `--calendar-scope today` or `--calendar-scope week` to change calendar range (default: today+tomorrow)

For mid-session calendar checks, still use gcal_query.py directly.

2. **Report startup output**, then load additional protocols as needed. If substantive work expected, initialize running summary file for today.

---

## Running Summary Protocol (Essential)

**Purpose:** Preserve session context before compaction erases it.

**File location:** `<running-summaries-dir>/YYYY-MM-DD.md`

### Why This Matters

Entries written *during* work capture what Claude understood at the time. Entries reconstructed *after* compaction are filtered through whatever the compaction process preserved—nuances, decisions, and context may be lost. **Contemporaneous notes are always more reliable than reconstruction.**

### Compaction Detection (CRITICAL)

**How to detect:** Conversation begins with system message:
```
[NOTE: This conversation was successfully compacted...]
[Transcript: /mnt/transcripts/...]
```

**What to do:** See Session Startup Protocol Step 0 above. This takes priority over everything else.

### When to Write Entries

**During work (preferred):** Write brief entries as you work, not just at breakpoints.

**Automatic triggers (no confirmation needed):**
- Compaction detected (see above)
- High token usage (~150K): Update proactively before compaction risk
- **After any web search batch** (these consume the most context)
- **After any full Notion page fetch** (Memory Base, protocols, project pages)
- **After completing a substantive analysis or deliverable**
- **Clock check: 30+ minutes since last entry** (use session_timer.py)

**Clock check — use session_timer.py (externalized):**

```powershell
# Check if update is due:
cmd.exe /c "cd /d <working-dir> && <python-path> scripts/session_timer.py check > timer_output.txt 2>&1"
# If output says ⚠️ OVERDUE → update running summary immediately, no confirmation needed.

# After writing a running summary entry:
cmd.exe /c "cd /d <working-dir> && <python-path> scripts/session_timer.py update > timer_output.txt 2>&1"
```

**Prompted triggers (wait for confirmation):**
- User says "update running summary" → Update immediately
- User says "taking a break" → Ask if should update
- Natural breakpoint reached → Suggest update

**Full protocol details:** Session Lifecycle protocol

---

*Adapt paths, timezone, and Notion page IDs to your own environment.*
*See setup-guide.md for configuration details.*
