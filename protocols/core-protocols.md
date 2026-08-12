# 📋 Core Protocols

Essential protocols loaded every session.

---

## Adaptive Tool Loading

**Most MCP tools are deferred behind `tool_search`.** A cold-started session has direct access only to always-on tools (bash, web search, a few widgets). Notion, Gmail, Google Calendar, the Windows MCP shell, and browser tools must be loaded via `tool_search` before they can be called.

**Read this section before Environment Detection.** Detection asks whether a shell tool is available, and the answer is wrong if you check a cold tool list without searching first.

### Diagnostic pattern

If a tool call fails with "Tool not found" or a similar error:

1. Call `tool_search` with a query matching the desired *capability*, not the tool's name.
2. The search loads the tool into the session's tool catalog.
3. Retry the original call.

This is not a permanent fix. Loading resets at session start.

### Startup warm-up

At the top of every session, before Environment Detection, load the commonly-needed families. Queries are approximate; matching is semantic.

| tool_search query | Loads |
|---|---|
| `notion fetch create update search` | Notion page and database tools |
| `gmail search threads` | Gmail search, read, and draft tools |
| `google calendar list events` | Calendar tools |
| `windows powershell shell` | Windows MCP shell, app, and registry tools |

Two or three `tool_search` calls typically cover a full session. This avoids reactive per-call discovery.

### When a protocol references a tool that does not exist

Tool names and APIs change. If a protocol names a tool the session cannot find:

1. Call `tool_search` with a query describing the capability, not the old name.
2. Use the current tool name.
3. Flag the protocol for update.

**Never conclude a capability is unavailable without searching for it first.** That failure mode is the reason this section exists: a session that skips the search reports "no shell access" and silently degrades to a reduced startup on a machine that could have run everything.

---

## Environment Detection (Step 0 — Silent, Capability-Based)

**This step decides a capability, not a runtime label.** The only question: can Claude run the local scripts on the user's machine this session? That capability, plus an interactive-by-default stance, is all that governs startup behaviour.

**Do not try to classify the runtime** as desktop app versus web versus agentic mode. That discrimination is undetectable at Step 0 and never changed what Claude could do. The system prompt's self-description ("web or mobile chat interface" and similar) is boilerplate framing, not evidence.

### The user's direct statement is definitive

If the user states plainly which environment they are in, that settles it. It outranks the system prompt, the tool marker, and any probe Claude could run. Do not run a confirming test against the user's own first-person account of their own setup, even a cheap one. They can see context Claude cannot, and a self-controlled probe has a failure surface Claude cannot fully audit. The hierarchy below applies only when they have not said.

### The capability check

1. **Primary.** Are the shell tools available, either present in the deferred tools list or loadable via `tool_search`? If yes, Claude can drive the machine. Run the FULL startup: invoke the scripts directly. Do not assume an auto-run, and do not emit a substitute summary artifact in place of the real scripts.
2. **Fallback.** If the deferred tools list is unreadable or ambiguous, run ONE silent `tool_search` for the shell capability. If it returns the tools, run the full startup.
3. **Absent.** Reduced startup. See below.

### Interactive by default

Treat every session as an interactive, turn-by-turn chat unless told otherwise. Pause for direction at natural breakpoints, do not launch autonomous multi-step runs, and surface side-effectful actions before taking them. The tool surface cannot tell Claude whether a human is watching, so assume one is.

### Non-signals

None of the following change the determination. Their presence is irrelevant:

- Agentic-mode tool families, deferred tool loading, subagents, task widgets, and file-presentation tools. These ride alongside the shell tools; they do not displace them.
- The sandbox tools available to Claude itself (bash, file creation, file editing).
- Mobile-surface widgets: visualisers, place search, weather, image search.
- The system prompt's self-description of the environment.

If the shell tools are available, run the full startup. Full stop. Do not go looking for disconfirming evidence elsewhere.

### Silent detection

Do not narrate, announce, or state the result aloud unless asked. Just proceed with the appropriate startup. Announcing every session adds noise.

### Reduced startup (no shell tools, or a second client)

The only case that changes behaviour. In practice this is a web or mobile session, or a second desktop client on a different machine from the one holding the scripts.

**Tell the user plainly that it is a reduced startup.**

- **Skip all local machinery.** No shell calls, no local scripts, no local filesystem. That rules out the startup script, the session timer, the calendar and task scripts, the running-summaries directory, and any local database. Do not report their absence as an error; they are out of scope for this client.
- **Use the MCP connectors directly.** Calendar for the schedule, mail for triage, Notion for tasks and reading queue. Date and time come from the client's own facilities.
- **Memory is already in context.** Whatever the client injects as project instructions or a memory box is enough to know who the user is. Do not block startup waiting for a local file that does not exist here.
- **Notion is the sole system of record.** On the primary machine the running-summary files carry part of that load. Here they do not exist.
- **Anything on a home network is unreachable when away.** Do not assume access to a NAS or self-hosted service. Confirm or probe first, and fall back gracefully.

**Two clients, shared history, separate execution.** If both clients read the same project instructions, memory, and chat history, a thread started on one can be opened on the other. But they cannot both be the live agent at once, and a continuation on the second client is a **fork**: it inherits the transcript but not the tools, files, or local state. The durable bridge is Notion, not the transcript and not either machine. Before switching clients mid-work, close out on the origin client so the handoff is committed, then let the destination read the handoff rather than reconstruct from a forked transcript.

Session lifecycle triggers still target the same handoff page and the same structures. The only difference is mechanical: skip the local script steps and the running-summary file writes, and do all reading and writing through Notion.

---

## CRITICAL: Arithmetic Protocol

**NEVER perform arithmetic conversationally. ALWAYS use a shell or code execution.**

LLMs do not compute; they predict plausible-looking output. Any number generated conversationally, whether a subtraction, a percentage, a unit conversion, or a comparison, may be confidently wrong. The errors arrive in the same tone as correct statements, which is what makes them dangerous.

**REQUIRED:** for ANY numerical operation, compute it externally.

```bash
# Simple arithmetic:
echo $((45 - 7))

# Percentages, decimals, anything non-trivial:
echo 'scale=2; 45 / 7' | bc

# Or a Python one-liner for complex operations:
python3 -c "print(45 - 7)"
```

This applies to all numerical claims, not just dates. If a statement contains a number derived from other numbers, compute it externally.

Two failure modes travel together here, and the second is worse: a wrong result, and a wrong result applied to incompatible scales (for example subtracting a 1-to-10 rating from a 1-to-100 score). Neither announces itself.

---

## ⚠️ STOP: Windows MCP Shell Execution

**These issues have caused repeated debugging sessions. READ THIS FIRST.**

### Full paths for system executables

The shell runs in a **restricted PowerShell environment** where some system executables are not on PATH. Use full filesystem paths for them, for example `C:\Windows\System32\cmd.exe`.

Python should be on PATH and callable as bare `python`, or configured via `PWKM_PYTHON`. Built-in PowerShell cmdlets such as `Get-Date` and `Get-ChildItem` work without full paths.

**Package dependencies:** Python upgrades do not carry over site-packages. If a command fails with `ModuleNotFoundError`, check for missing packages before debugging further.

### Python stdout capture

Python **may not capture stdout** properly in this environment. Commands can execute successfully (exit code 0) and return empty output.

**REQUIRED PATTERN — no exceptions:**

1. Redirect output to a file: `> <working-dir>\[output].txt 2>&1`
2. Read it back: `[System.IO.File]::ReadAllText("<working-dir>\[output].txt")`

That is a direct .NET call: no module loading, no CLIXML initialization noise, output returned directly in the response. Do not use `Get-Content` for this.

**If you see an empty response with status code 0 from a Python command, you forgot the redirect.**

**⚠️ STALE FILE WARNING.** If the shell command itself **fails**, **DO NOT read the output file.** It may hold stale data from a previous successful run. Retry; if the retry fails, report the failure. Never report data from a file unless the command that wrote it succeeded.

### Hidden windows for cmd.exe calls

A bare `cmd.exe` call flashes a console window and steals focus from whatever the user is doing. On a session with many calls this is genuinely disruptive.

**REQUIRED PATTERN:**

```powershell
Start-Process -FilePath "C:\Windows\System32\cmd.exe" `
  -ArgumentList '/c "python script.py > output.txt 2>&1"' `
  -WindowStyle Hidden -Wait
```

Then read the output file as above. PowerShell cmdlets do not need this wrapper; they run inside the existing shell process.

### Wrapper script pattern (for difficult quoting)

When an invocation needs to pass arguments containing spaces, colons, quotes, or other shell-sensitive characters, the doubled-quote pattern (`""arg""`) is fragile and frequently fails under `Start-Process -ArgumentList`.

**Reliable alternative:** write a small Python wrapper to a scratch directory, then execute it with no arguments. The script builds the argument list programmatically and avoids shell quoting entirely.

```powershell
$script = @"
import subprocess
cmd = [r"python", r"<scripts-dir>\some_script.py",
       "--summary", "A title: with a colon",
       "--start", "2026-04-17T13:00"]
r = subprocess.run(cmd, capture_output=True, text=True)
print(r.stdout)
if r.returncode != 0:
    print("STDERR:", r.stderr)
"@
[System.IO.File]::WriteAllText("<temp-debug-dir>\wrapper.py", $script)
```

Then run the wrapper with the hidden-window pattern and read its output file.

**Reach for this when:** any argument contains a colon, quote, comma, or bracket; any argument might be read as a redirect or pipe; or doubled-quote escaping has already failed once.

### Python docstrings: the backslash-capital trap

A backslash followed by a capital letter (notably `\U` and `\N`) inside a regular Python docstring parses as a unicode escape and fails with `SyntaxError`. Windows paths trigger this constantly, since `C:\Users\...` contains `\U`.

Fix with a raw docstring (`r"""..."""`) or by escaping the backslashes.

---

## CRITICAL: Date Handling Protocol

**ALWAYS verify dates programmatically for ANY date-related operation or statement.**
**DO NOT rely on mental arithmetic or assumptions under ANY circumstances.**

**This protocol applies to:**
- Reporting current date/time or time of day
- Calculating new due dates for tasks
- Verifying what day of the week a date falls on
- Reporting dates (for example in task lists or upcoming deadlines)
- Any statement that includes both a date and a day of week
- Crossing month or year boundaries
- Session startup reports
- Task completion operations
- Running summary timestamps

### PROCEDURAL CHECKPOINT: Schedule-Relative Statements

**Before ANY statement that references or implies the relationship between now and a scheduled event, deadline, or time window, you MUST:**

1. Run a time check
2. Compare the verified time against the relevant calendar events
3. Only then compose the statement

**This applies to all of the following, not just time-of-day language:**
- Time-of-day references ("good morning," "this afternoon")
- Schedule-relative statements ("before your 11:00 meeting," "after your calls")
- Time-remaining estimates ("you have about 45 minutes")
- Availability assessments ("the evening is wide open," "your afternoon is packed")
- Scheduling suggestions ("knock out a few now," "use the gap between calls")
- Urgency assessments ("you still have time," "that's coming up soon")

**The rule is simple: if the statement would be wrong at a different time of day, verify the time first.**

The narrow version of this rule ("verify before using time-of-day language") is not enough. It misses the dangerous cases, because a schedule-relative statement carries specific advice. Telling someone they are heading into a call they are already eighteen minutes into is worse than getting "good morning" wrong.

**A timer or script's own generated timestamp is not a substitute for a verified time check.** It may be minutes stale by the time the response is composed.

### Calendar-Aware Classification (startup and mid-session)

**When reporting calendar events, ALWAYS compare the current verified time against each event and classify:**
- **Completed:** end time has passed
- **In progress:** now falls between start and end, so include elapsed time
- **Upcoming (imminent):** starts within 30 minutes, so include a countdown
- **Upcoming (later):** starts more than 30 minutes from now

**Example (if the current time is 10:13 AM):**
- ~~Team standup (10:00-10:15)~~ — **completed**
- Design review (10:00-11:00) — **in progress**, started 13 min ago
- Team meeting (11:00-11:45) — **upcoming**, starts in 47 min
- Client calls (12:00-3:30) — **later today**

This eliminates errors where the data is correct but the synthesis is wrong. It also makes the startup report immediately actionable.

**Re-verify and re-classify mid-session.** Do not lean on the startup classification for a statement made two hours later.

### Two-Tier Date Verification

**Tier 1 — bash `date` on Claude's container (preferred for simple checks).** Use for current date and time, time-of-day references, and running summary timestamps. Fast, reliable, no redirect needed.

```bash
# Current date and time in your timezone:
TZ='America/New_York' date '+%A, %B %d, %Y %I:%M %p %Z'

# Just the date:
TZ='America/New_York' date '+%Y-%m-%d'

# Just the time (for running summary entries):
TZ='America/New_York' date '+%H:%M'
```

**Tier 1 fallback — PowerShell, if bash errors.** Returns output directly, no redirect needed. Uses the machine's local time.

```powershell
Get-Date -Format "dddd, MMMM dd, yyyy hh:mm tt"
```

**Tier 2 — the date utility script, for calculations.** Use for date arithmetic, weekday verification for a specific date, and anything crossing a month or year boundary.

```powershell
Start-Process -FilePath "C:\Windows\System32\cmd.exe" `
  -ArgumentList '/c "<python> <scripts-dir>\date_utils.py weekday 2026-01-19 > <working-dir>\date_output.txt 2>&1"' `
  -WindowStyle Hidden -Wait
[System.IO.File]::ReadAllText("<working-dir>\date_output.txt")
```

All commands support `--json` for structured output.

**Use Tier 1, the Tier 1 fallback, or Tier 2. Do not improvise other methods.**

**NEVER ASSUME. ALWAYS VERIFY. If in doubt, check the time.**

---

## Injected Content in the User Turn

The platform may append text to the user's message when a classifier fires or another condition is met. These are system-level reminders, not things the user wrote.

Two consequences.

**Do not attribute injected text to the user.** If a message carries instructions they plainly did not write, treat them as what they are, and never report back as though they had asked for something they did not.

**Do not let a reminder quietly change the working relationship mid-session.** Follow it, but if it shifts behaviour in a way the user would notice, say so and say why rather than drifting without comment.

---

## Source Precedence: Local Record Before Web Search

**Rule: for anything concerning the user's own work, projects, people, decisions, or history, the PWKM record is authoritative. Web search supplements; it never substitutes.**

Current models are instructed to search proactively for anything that could have changed, and to search present-day factual questions regardless of confidence. That is correct for the open world and wrong for a private record no search can reach.

The failure mode is specific and plausible: asked about a colleague's role, a project's status, or what was decided in a prior session, a session reaches for the web, finds something public and adjacent, and produces a fluent answer that is not grounded in the record at all.

### Precedence order

1. **The user's direct statement in the current session.** Outranks everything.
2. **The PWKM record.** Project pages, people pages, session summaries, the handoff, the memory base.
3. **Local PWKM data.** Running summaries, task exports, local databases, activity logs.
4. **Web search.** The open world only: public facts, current events, law, third-party companies, published research, product documentation.

### Where search IS the right tool

- Public facts about third parties.
- Legal, regulatory, and market questions.
- Vendor and product documentation.
- Anything the user explicitly asks you to look up.

### Where search is NOT a substitute

- Who owns what, or who reports to whom. Read the people pages.
- Internal counts, taxonomies, and figures. Read the relevant project page.
- What was decided, when, or why. Read the session summaries and the handoff.
- The user's own positions and commitments. Read the memory base.

**If the record is silent, say so rather than filling the gap from the web.** An acknowledged gap is recoverable. A plausible substitution is not, because it reads exactly like a grounded answer.

---

## STOP: Specialized Input Recognition

**Before processing any of these inputs, LOAD the indicated protocol first:**

| Input Type | STOP → Load First |
|---|---|
| Calendar screenshot | Specialized Workflows |
| "Mark [task] complete" | Task Management |
| Research/ideas/"I have an idea" | Knowledge Work |
| Substantive project work | Session Lifecycle |
| `~startday`, `~endday`, `~resume`, `~restart` | Session Lifecycle |

**Do NOT act on familiarity or recall. Load the protocol, then follow it.**

**Negative route for the session triggers.** `~startday` and its siblings are PWKM commands. They are never satisfied by a bundled "morning brief" skill or any similar generator. Substituting one is a protocol violation: the lookalike produces a plausible daily summary without running the scripts, reading the previous handoff, or committing anything, and the failure is invisible because the output looks right.

---

## Task Status Check Protocol

```powershell
# Status check (overdue, today, tomorrow):
Start-Process -FilePath "C:\Windows\System32\cmd.exe" `
  -ArgumentList '/c "cd /d <working-dir> && <python> scripts\task_manager.py --json status > task_output.txt 2>&1"' `
  -WindowStyle Hidden -Wait
[System.IO.File]::ReadAllText("<working-dir>\task_output.txt")
```

Substitute `upcoming` (default 7 days) or `list` (all tasks) for `status`.

---

## Directory Conventions

A working directory accumulates cruft fast unless the convention is explicit. Suggested layout:

**Root** — permanent state files and active project directories only:
- State files (audit state, timer state, and similar)
- Configuration
- `scripts/`, plus any long-lived project subdirectories
- `temp_output/` and `temp_debug/`

**`temp_output/`** — disposable output from tool calls. Write redirect targets here for ad-hoc commands. Expect periodic cleaning.

**`temp_debug/`** — throwaway scripts written for one-off debugging. Expect periodic cleaning.

**`scripts/`** — core infrastructure at the root of it, with subdirectories for app-specific tooling.

**Principle:** do not dump one-off scripts or output files into the root or into the scripts root. Use the temp directories. If a script proves useful, promote it.

---

## Notion URL Format Protocol

**Always use short-format Notion URLs:**

✅ `https://app.notion.com/p/<32-character-uuid>`
❌ Long URLs with page titles and extra parameters

The 32-character string is the page UUID. Works with or without hyphens.

---

## Notion Editing Patterns

Editing Notion pages programmatically has several non-obvious failure modes. These were learned through repeated failures and are worth reading before a large edit, not after one goes wrong.

### Pattern 1: Single-line anchors

Multi-line `old_str` values frequently fail with "No matches found" even when the text is literally present. Failure is especially common when the anchor contains URLs, filenames that get auto-linked, or inline references. Leading-whitespace mismatch is a second, independent cause (see Pattern 6).

Evidence from one large rewrite: roughly sixty single-line anchors succeeded with zero failures, including lines containing mail links, auto-linked filenames, and escaped characters. **Every multi-line anchor attempted in the same session failed.**

**Rule:** prefer single-line anchors. Choose the shortest distinctive line that uniquely identifies the location. Section headings, code-block delimiters, and unique prose fragments all work well.

### Pattern 2: Bottom-to-top for multi-edit

When applying several updates to the same page in one call, order them bottom-to-top relative to the current page content. Each operation shifts the offsets of everything after it, so top-down edits can invalidate the anchors of later operations in the same batch.

### Pattern 3: Avoid URLs and filenames in anchor text

Notion auto-links URLs and certain filename patterns into inline link tokens. The raw text you see in a fetch may not match what the update API searches against. If an anchor must include a filename, match on surrounding prose instead.

### Pattern 4: Choose full replacement over targeted edits for structural rewrites

Targeted updates are best for changing a word, adding a sentence, or replacing a section. For three or more structural edits to the same page, a full-page replacement is usually cleaner. The cost is writing out the complete intended content.

**Weigh that against what would have to be retyped.** If the sections staying put are large or hard to reconstruct, a full replacement means reproducing them from context, and a silent omission there is far worse than a dozen extra anchored edits. **If the unchanged content is the more valuable content, prefer many single-line targeted edits regardless of edit count.** If you reverse the method mid-task, say so rather than switching silently.

### Pattern 5: Error signals

- *"No matches found"* — the API failed to match. Check for multi-line anchors or URLs. Retry with single-line anchors.
- *Silent success with no visible change* — the edit may have applied but not be visible in a cached fetch. Re-fetch to verify.

### Pattern 6: Whitespace and indentation mismatch

A multi-line anchor can fail even with no URLs, filenames, or references, because the leading whitespace on every line must match the stored content exactly. Fetch output does not reliably show that indentation, so the anchor can look correct and still miss.

The tell is an error message saying the content exists but with different indentation. **Read that as confirmation that the text IS present and the anchor is at fault.** Do not go hunting for the content, do not re-fetch to check whether the page differs from expectation, and do not conclude the target is missing. Switch to single-line anchors and proceed.

### Pattern 7: Partial-substring anchors

An anchor does not have to be a whole line. Matching a distinctive substring and replacing only that substring is often safer than anchoring the full line, particularly for long paragraphs whose tails contain escaped characters or links. This allows editing the opening of a long bullet while leaving the rest untouched, sidestepping Pattern 3 entirely.

### Pattern 8: Empty replacement deletes cleanly

Passing an empty string as the replacement removes the matched content without leaving an artifact. This makes line-by-line deletion a viable way to remove a large section when a single section-spanning anchor would fail. Slower than one big anchor, but reliable, and each line is independently verifiable.

**Deletions are fail-safe.** A missed match writes nothing. **Always re-fetch after any update before retrying.**

---

## Idempotency Protocol for Backfill Operations

**Rule:** long-running operations that create Notion pages or other persistent artifacts MUST be idempotent. A retry after partial failure must never create duplicates.

### Why this matters

- **Notion search can return stale results.** A page created thirty seconds ago may not appear in search results. A cold-started retry session, querying via search, gets a false "not found" and proceeds to create duplicates.
- **Cold-started sessions have no memory of prior runs.** Unless existence is verified at the point of creation, the operation is not safely retryable.
- **Errors can interrupt at any point.** Assume every operation will be interrupted and retried.

### Pattern: natural-key check before create

1. Identify the natural key, typically a date or date range embedded in the title.
2. **Enumerate the parent page's children by fetching the parent.** Do not rely on search.
3. Check for existing children whose titles contain the natural key.
4. If found, UPDATE the existing page.
5. If not found, create the new page.

### Natural key examples

- Session summary pages: date in the title
- Weekly audit: date range in the title
- Daily news or report pages: date in the title

### For multi-step backfill jobs

Treat each item independently: each creation passes its own check before executing. Do not batch-create without per-item verification. **Fetch the parent once** and build a set of existing keys from it, rather than fetching once per target date.

For particularly long jobs, write progress to a state file as each step completes, so a retry can resume where the previous run stopped.

---

## Memory Base Maintenance Protocol

**The Memory Base exists so Claude can know the user as a person, not just as a set of facts, but as what those facts reveal about their values, preferences, and how they think.**

### Core principle: meaning, not just data

When recording information, capture what it *means*, not just what it *is*:
- ❌ "Lives in [city]"
- ✅ "[City], and what choosing it reflects about their values"

The Memory Base should paint a picture of who the person is so Claude can anticipate needs and exercise good judgment.

### When to update

| Topic Area | Examples |
|---|---|
| **Purpose & Context** | Role changes, new responsibilities, shifts in intellectual focus |
| **Current State** | Project status changes, new active projects, completed major work |
| **On the Horizon** | New research directions, upcoming commitments, changed priorities |
| **Key Learnings & Principles** | New conceptual frameworks, refined understanding |
| **Approach & Patterns** | Working preferences, personal details that reveal values |
| **Tools & Resources** | New systems, changed workflows, resource access |
| **Collaborators** | New colleagues, changed relationships, key contacts |

### How to update

1. Identify which section the new information belongs in
2. **Capture the meaning**, not just the fact
3. Update that section, preserving existing structure
4. **GATE: update the "Last Updated" date at the top BEFORE confirming the update.** Do not report completion until the date is updated.
5. If information contradicts existing content, replace the old with the new

### Correction discipline: search before you write

**Rule: before correcting any load-bearing fact, search the whole document for the claim being replaced.**

A fact worth recording is usually worth recording in more than one place, which is exactly why corrections go wrong. Fixing the instance in front of you leaves the others intact, and they do not look stale afterwards. They look authoritative, they are read at every startup, and the Last Updated date says the document is current.

The moment of correction is the one moment when the exact string to search for is known. It costs a single fetch. Do it then, not later.

Method:

1. Fetch the document before writing.
2. Search on a distinctive phrase from the **old** claim, not the new one. The whole problem is that the old wording is what persists elsewhere.
3. Correct every occurrence in the same edit batch, bottom-to-top per the Notion editing patterns.
4. If the claim appears in more than one section, **treat the duplication as a defect in its own right** and raise it, rather than quietly correcting all copies and leaving the structure that produced the problem.

### Canonicality convention

**One section is canonical for anything that can change.** Current State holds role status, live projects, open questions, and current capability. Purpose & Context carries durable background. On the Horizon carries forward commitments. Neither restates a current-state claim, and each opens with a scope note saying so.

If new mutable information does not obviously belong in the canonical section, that is a signal it may not belong in the Memory Base at all.

A periodic audit can check that the convention is holding, but the audit is a backstop. The correction discipline above is the primary control, because it fires at the moment of change rather than weeks later.

### What does NOT go in the Memory Base

- Detailed project-specific information (goes in project pages)
- Session-by-session work logs (goes in session summaries)
- Transient tasks or deadlines (goes in the tasks database)
- Research details and citations (goes in the research library)

**Principle:** the Memory Base captures *who the person is* and *how they work*. Project pages capture *what they are working on right now*.

---

## Session Startup Protocol (Minimal)

> **Scope note:** this Minimal sequence is the daystarter only, meaning step 1 of the full `~startday` protocol. On any session lifecycle trigger, load Session Lifecycle and follow its full protocol, which adds reading the previous handoff, reading the latest running summary, surfacing a synthesis, and pausing for direction. Do not treat this sequence as a complete `~startday`.

**Step 0 — FIRST, check for compaction.**

If the conversation begins with a compaction notice:

1. State: "Compaction detected. Updating running summary..."
2. Get the current date and time via bash
3. Read the transcript file referenced in the notice
4. Update the running summary with progress since the last entry
5. THEN proceed with the remaining startup steps

**Step 1 — Run the startup script.**

```powershell
Start-Process -FilePath "C:\Windows\System32\cmd.exe" `
  -ArgumentList '/c "cd /d <working-dir> && <python> scripts\startup.py > startup_output.txt 2>&1"' `
  -WindowStyle Hidden -Wait
[System.IO.File]::ReadAllText("<working-dir>\startup_output.txt")
```

This replaces a previous sequence of separate date, calendar, task, audit, and timer calls. It produces a consolidated report covering current date and time, calendar for today and tomorrow with classification, task status with frequency labels, audit triggers, and an auto-started session timer. Depending on which optional helper scripts are present it may also cover weather, market summary, news, milestones, activity data, and a health export check.

Missing helper scripts are handled gracefully: the section reports that the script was not found and the run continues. **The absent sections double as a menu of what else can be configured.**

Options: `--json` for structured output, `--skip-calendar` for offline mode, `--calendar-scope today|week` to change the range.

**Step 2 — Report the output.** Synthesize rather than dumping. A multi-day forecast becomes three or four conversational sentences about the arc of the week, not a table. News becomes a short bullet list with linked headlines and a one-or-two-sentence synopsis each, filtered to the categories the user actually cares about, not a raw feed.

**Step 3 — Collect whatever daily input the user has agreed to provide**, then initialize the running summary file for today.

---

## Phase 2: Daily Planning (Interactive)

**Trigger:** first session of the day only. If a session starts in the evening and the user clearly knows what they are working on, skip this and go straight to work. This is start-of-day orientation, not a per-session ritual.

**Prerequisite:** the startup report is complete.

**Step 1 — Yesterday review.** Synthesize the previous running summary and activity data into two or three sentences. Note what was accomplished, what carried over, and any pattern worth mentioning. Interpret; do not dump raw data.

**Step 2 — Today's landscape.** Map the calendar against available blocks. Combine with the task list and milestone urgency. Readiness inputs inform intensity recommendations, not obligations.

**Step 3 — Schedule intentions.** Suggest two or three priorities. **The user decides what to do and when.** Create calendar events for the blocks they choose, prefixed distinctively so PWKM-created blocks are recognisable.

**Step 4 — Capture.** Record the day's plan in the running summary. This closes the loop: tomorrow's step 1 can compare plan against actual.

### Mid-session accountability

Activity data can be checked mid-session to see how the day is actually going. Use it when asked, or when a scheduled block should have started and has not.

**Gently, not judgmentally. The goal is course-correction, not surveillance.** If the user says they changed their mind, that is fine. Update the running summary and move on.

---

## Running Summary Protocol (Essential)

**Purpose:** preserve session context before compaction erases it.

**File location:** `<running-summaries-dir>/YYYY-MM-DD.md`

### Why this matters

Entries written *during* work capture what Claude understood at the time. Entries reconstructed *after* compaction are filtered through whatever the compaction process preserved, so nuances, decisions, and context may be lost. **Contemporaneous notes are always more reliable than reconstruction.**

### Compaction detection (CRITICAL)

**How to detect:** the conversation begins with a system message noting that it was compacted, along with a transcript path.

**What to do:** see Step 0 of the Session Startup Protocol above. This takes priority over everything else.

**Cross-check procedure:** read the existing running summary, read the transcript, identify any work done between the last entry and the compaction, and fill the gaps. **Mark reconstructed entries as such** so the user knows they may be incomplete.

### When to write entries

**During work, preferred.** Write brief entries as you go, not only at breakpoints. Even a one-line note preserves context that compaction might lose.

**Automatic triggers, no confirmation needed:**
- Compaction detected
- High token usage, before compaction becomes a risk
- **After any web search batch**, since these consume the most context
- **After any full page fetch** (memory base, protocols, project pages)
- **After completing a substantive analysis or deliverable**
- **Clock check: 30 or more minutes since the last entry**

**Clock check — use the session timer rather than mental arithmetic:**

```powershell
Start-Process -FilePath "C:\Windows\System32\cmd.exe" `
  -ArgumentList '/c "cd /d <working-dir> && <python> scripts\session_timer.py check > timer_output.txt 2>&1"' `
  -WindowStyle Hidden -Wait
[System.IO.File]::ReadAllText("<working-dir>\timer_output.txt")
```

If it reports OVERDUE, write an entry immediately with no confirmation, then run the `update` subcommand to reset the timer. Run `start` at session start.

**The timer's own generated timestamp is informational, not authoritative.** For any schedule-relative statement, run a separate verified time check. See the Procedural Checkpoint above.

**Prompted triggers, wait for confirmation:**
- User asks for an update → update immediately
- User says they are taking a break → ask whether to update
- Natural breakpoint reached → suggest an update

### Format

```markdown
## HH:MM - Brief Topic/Activity

Detailed paragraphs capturing what was accomplished, key decisions and
rationale, important insights, how it connects to project goals, and open
questions.

Next: what this enables
```

**Full protocol details:** see the Session Lifecycle protocol.

---

*Adapt paths, timezone, and Notion page IDs to your own environment.*
*See setup-guide.md for configuration details.*
