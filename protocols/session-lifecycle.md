# 📋 Session Lifecycle

Protocols for session documentation and context preservation. Load when doing substantive work or approaching compaction.

---

## Running Summary Protocol

**Purpose:** Capture detailed session progress in real-time to preserve context.

### Why This Matters: Fidelity Risk

Entries written *during* work capture what Claude understood at the time. Entries reconstructed *after* compaction are filtered through whatever the compaction process preserved—nuances, decisions, and context may be lost.

**Contemporaneous notes are always more reliable than reconstruction.**

This is why running summaries feed session summaries, which feed PWKM documents. The chain of fidelity matters.

### File Location

**Directory:** `<running-summaries-dir>/`
**Filename:** `YYYY-MM-DD.md` (based on session date)

### When to Update

**During work (preferred):**

Write brief entries as you work, not just at breakpoints. Even a one-line note preserves context that compaction might lose. Don't wait for a "natural breakpoint" if you've done something worth noting.

**Method A - Explicit Request:** User says "Update the running summary" → Update immediately

**Method B - Break Indication:** User says "taking a break" → Ask if should update, wait for confirmation

**Method C - Natural Breakpoint:** Claude identifies completion point → Suggest update, wait for confirmation

**Method D - Compaction Event (Automatic):** When compaction occurs → Update immediately, no confirmation needed (see Compaction Detection Protocol below)

**Method E - High Token Usage (Automatic):** At ~150K tokens → Update proactively before compaction

**Method F - Proactive Triggers (Automatic):** No confirmation needed. Update running summary after:
- Any **web search batch** (these consume the most context)
- Any **full Notion page fetch** (Memory Base, protocols, project pages)
- Completing a **substantive analysis or deliverable**
- **Clock check: 30+ minutes** since last running summary entry

**Clock check — use session_timer.py (externalized):**

Run `session_timer.py check` at natural conversational pauses. If it reports ⚠️ OVERDUE (30+ min since last update), write a running summary entry immediately, then run `session_timer.py update` to reset the timer. No mental arithmetic or timestamp comparison required.

At session start: run `session_timer.py start`. After each running summary write: run `session_timer.py update`.

See Core Protocols for full command syntax (Windows MCP redirect pattern required).

### Date/Time for Running Summaries

Always get timestamps for running summary entries via bash: `TZ='America/New_York' date '+%H:%M'`

This is fast and reliable. Reserve Python date_utils.py for date arithmetic only.

### Format

```markdown
## HH:MM - Brief Topic/Activity
Detailed paragraph(s) capturing:
- What we accomplished
- Key decisions and rationale
- Important insights
- How it connects to project goals
- Open questions

Next: What this enables
```

**For reconstructed entries (when catching up after compaction):**

```markdown
## HH:MM - Brief Topic [Reconstructed from transcript]
What was accomplished based on transcript review. May be incomplete.
Next: What this enables.
```

**Key principle:** More detail is better. Include enough context for future reference. Flag uncertainty when reconstructing.

### First Update of Session

Create new file with header:

```markdown
# Session: YYYY-MM-DD
Project: [Primary project or "PWKM"]
Start time: HH:MM AM/PM

---
```

### Key Principles

1. **Write during work, not just at breakpoints** — even brief notes preserve context
2. **Contemporaneous > reconstructed** — notes written in the moment are more reliable
3. **Cross-check at compaction** — always compare transcript against running summary to find gaps
4. **Flag uncertainty** — mark reconstructed entries with `[Reconstructed from transcript]` so the user knows they may be incomplete

---

## Compaction Detection Protocol

**How to detect compaction:** Conversation begins with system message:

```
[NOTE: This conversation was successfully compacted...]
[Transcript: /mnt/transcripts/...]
```

**When Claude observes compaction has occurred:**

1. **IMMEDIATELY state:** "Compaction detected. Updating running summary..."
2. **Get today's date via bash:** `TZ='America/New_York' date '+%A, %B %d, %Y %I:%M %p %Z'`
3. **Read existing running summary file** (if any) to see what was already captured
4. **Read the transcript file** referenced in the compaction notice
5. **Cross-check:** Identify any work done between last running summary entry and compaction
6. **Fill gaps** from transcript, marking new entries as `[Reconstructed from transcript]`
7. **THEN** continue with response

**This must be automatic** - no waiting for confirmation.

**Why cross-checking matters:** The compaction-generated summary in context may have lost nuances. The transcript file has the raw conversation. By comparing against the running summary file, Claude can identify what was missed and reconstruct it—flagged appropriately so the user knows those entries may be incomplete.

---

## Session Summary Protocol

**At end of each working session:**

### Session Summaries Parent Page

Always create session summaries as subpages of your designated Session Summaries page in Notion.

### Create Session Summary Page

- **Parent:** `<your-session-summaries-page-id>`
- **Title:** "Project Name - YYYY-MM-DD - Brief Description"
- **Content:**
    - Session duration and time of day
    - What was accomplished (concrete deliverables)
    - Current status/progress
    - Next steps or open questions
    - Decisions made or insights gained
    - Work pattern notes
    - Research notes referenced

### Link in Session Summaries Hub

Add to both:
- Reverse chronological "Session Index"
- Appropriate project section in "Sessions by Project"

### Integration with Running Summary

Final Notion summary should include:

```markdown
## Session Summary
[Polished synthesis]

---

## Running Summary (Detailed Log)
[Complete running summaries copied from file]
```

---

## Weekly Session Summary Audit

**When:** First session of each week (detected automatically by `session_timer.py audit-check`)

**Trigger:** The `audit-check` command is run at startup (Core Protocols). If it reports `** WEEKLY AUDIT NEEDED`, proceed with the audit.

**Scope:** Previous Monday through Sunday

1. Calculate date range for previous week
2. Use `recent_chats` with date filters
3. Cross-reference against Session Summaries Hub
4. Identify gaps (substantive sessions without summaries)
5. Fill gaps if needed
6. **If first week of month** and `** MONTHLY IDEA REVIEW NEEDED` is also flagged: review Ideas and Interests for items ready to develop (see Knowledge Work protocol)
7. Record completion: `session_timer.py audit-done` (add `--monthly` flag if idea review was also done)

**Requires summary:** Research/analysis (30+ min), project work, significant decisions
**Does not require:** Brief admin exchanges, quick task completions

---

*Adapt paths, timezone, and Notion page IDs to your own environment.*
*See setup-guide.md for configuration details.*
