# 📋 Session Lifecycle

Protocols for session documentation and context preservation. Load when doing substantive work, when approaching compaction, or on any session trigger.

---

## Session Triggers

Four tokens drive the session lifecycle. They are PWKM commands, not requests for a bundled skill.

| Trigger | Meaning |
|---|---|
| `~startday` | First session of a day. Expects an overnight or longer gap, and that `~endday` closed the previous session. |
| `~endday` | Last session of a day. Expects an overnight or longer gap before the next one. |
| `~resume` | Same-day restart after a break. |
| `~restart` | Same-day close before a break. |

**Negative route.** `~startday` is never satisfied by a "morning brief" skill or any similar daily-summary generator. Substituting one is a protocol violation, and a quiet one: the lookalike produces a plausible report without running the scripts, reading the previous handoff, or committing anything, so the failure is invisible in the output.

The end-of-session protocols (`~endday` and `~restart`) are functionally identical, as are the start-of-session ones (`~startday` and `~resume`). The operational difference is the synthesis step: `~startday` surfaces a synthesis of the previous handoff at the close of the startup report, while `~resume` simply re-establishes context internally and acknowledges where things stand.

---

## `~startday` Protocol

**Purpose:** run the standard startup, then re-establish context from the previous day's handoff so the user can resume yesterday's work or pivot deliberately.

1. **Run the standard startup** per Core Protocols. Environment detection, date verification, the startup script, calendar and task scan with overdue items, and whatever else that script is configured to cover. Report as usual.
2. **Read the previous handoff** from the Session Handoff page. This is what `~endday` produced at the close of the previous session.
3. **Read the most recent running summary**, typically the highest-dated file in the running-summaries directory. Use it to supplement where the handoff is terse and to recover details the handoff abstracted away.
4. **Surface a two-to-three paragraph synthesis** at the close of the startup report. Draw primarily from the handoff's state and next-session sections. Answer three questions: where did the previous session leave off, what is the prioritized next step, and what remains open or unresolved. Link the handoff page so the user can drill in.
5. **Pause for direction.** They may continue the previous thread, pivot, or deal with startup items first. Wait for the cue.

**Key principles:**
- Do not narrate the protocol. Execute and report.
- The handoff is the primary source; the running summary is supplementary detail.
- If the handoff is stale, meaning its date does not match the previous session date, flag the discrepancy and ask before proceeding.
- If no running summary exists for the previous session date, note that and use the handoff alone.

---

## `~endday` Protocol

**Purpose:** commit final context for the day so tomorrow's `~startday` picks up cleanly.

### Day reconciliation (optional, interactive)

This is the first action of `~endday` and of `~restart`, before the handoff steps below. **It is optional machinery**: it exists to feed a day-planning loop that learns patterns from data and explained deviations rather than from pre-set rules. Skip the whole subsection if you are not running that loop.

- Pull the day's actual shape from whatever activity trail is available. Read it as an **ordered sequence, not a category rollup**: focused or self-directed work, obligated work such as meetings, passive or leisure time, rest, and life or household activity. The transitions between these are the signal, so raw event order matters more than the totals.
- Note the morning readiness inputs as they stood, and how the day was loaded.
- For any notable divergence between what was expected and what happened, capture the reason from the user and tag it. **When the cause is ambiguous, ask rather than guess.** Mislabeling is how the loop learns garbage.
- Append the capture block below to today's running summary.

Early on there is no suggestion to diverge from, so the step is lighter: capture the day's shape plus the reason behind any notable choice. Once soft day-plan suggestions are in play it becomes plan-versus-actual.

**Tag vocabulary.** Controlled vocabulary is enforced on `tag` only, because that field is the signal-versus-noise separator.

| Tag | Meaning |
|---|---|
| `exogenous` | An external demand unrelated to the user's state |
| `endogenous` | An internal state worth modelling, for example feeling foggy after a nap |
| `ambiguous` | A plausible but unprobed cause. The safety valve. |
| `discretionary` | A genuinely free choice |

**`discretionary` is a positive no-cause claim, not a catch-all.** Use it only where an energy or external-demand cause was actively considered and rejected. If you suspect a cause you have not fully probed, use `ambiguous` instead, so it is flagged for follow-up rather than buried. **Retain the free-text reason even for `discretionary`**, since a pattern across such days may later justify re-tagging. The tag is a revisable hypothesis, not a verdict.

### Day Reconciliation Capture Format

Append one fenced block per day to the running summary, under a `## Day Reconciliation` heading. Everything except `tag` stays free-text so the activity taxonomy can be discovered rather than fixed prematurely. Optional fields may be left blank. The block is designed to be harvested into a database later, or ingested by a subordinate model, without migration.

```yaml
date: YYYY-MM-DD
readiness:
  rested_rating:
  sleep_score:
  day_load:
day_shape:               # coarse, ordered, from the activity trail
  - HH:MM-HH:MM <class>: <free-text>   # class is discovered, e.g. focused | obligated | passive | rest | life
suggestions: []          # empty until soft day-plan suggestions begin
divergences:
  - planned:
    actual:
    reason:
    tag:                 # exogenous | endogenous | ambiguous | discretionary
```

### Handoff procedure

1. **Write the final running summary entry** for today's session. Note that the session ended here and that a handoff is being composed. This keeps the running summary as the canonical chronology of the day.
2. **Compose the complete handoff document**, seven sections:
    - **Session arc:** when it started, what shape it took, wall-clock versus interaction time
    - **Actions taken:** concrete things done, with page IDs and file paths
    - **Discussion threads:** substantive topics, with decisions or open questions per thread
    - **State / context:** where each active piece of work stands at session end
    - **Open / next session:** prioritized list of what to pick up
    - **Procedural checkpoint failures:** any environment, date, or protocol issues that surfaced (omit if none)
    - **Pointers:** file paths, page IDs, anything the next session will need quickly
3. **Replace the contents** of the Session Handoff page. The previous handoff is overwritten. The per-day running summary files preserve the audit trail; **the handoff page exists for transition fidelity, not historical record.**
4. **Create the session summary** for today, following the Session Summary Protocol below.
   Run the idempotency check first, then **link the page into both hub indexes in this same
   step**: the reverse-chronological index under the correct month, and every project bucket
   named in the title. Creating the page without indexing it only converts a missing-page gap
   into an unfindable-page gap.
5. **Confirm** that the handoff and the session summary are both in place so the session can
   end cleanly.

**Why the handoff comes first.** If this procedure is interrupted partway, a missing handoff
causes the next session to read a stale one and silently resume the wrong day. A missing
session summary is caught by the weekly audit. The artifact that fails silently goes first.

**Key principles:**
- The handoff should be self-contained. Tomorrow's session should not need to read anything else to understand where things are.
- Pointers are critical. Include paths and IDs for everything tomorrow might need.
- **Open / next session should be prioritized, not merely listed.** Tomorrow's synthesis depends on that section being usable.
- Record procedural checkpoint failures even when minor. The accumulated pattern is diagnostic.

---

## Running Summary Protocol

**Purpose:** capture detailed session progress in real time to preserve context.

### Why this matters: fidelity risk

Entries written *during* work capture what Claude understood at the time. Entries reconstructed *after* compaction are filtered through whatever the compaction process preserved, so nuances, decisions, and context may be lost.

**Contemporaneous notes are always more reliable than reconstruction.**

This is why running summaries feed session summaries, which feed the durable documents. The chain of fidelity matters.

### File location

**Directory:** `<running-summaries-dir>/`
**Filename:** `YYYY-MM-DD.md`, based on the session date

### When to update

**During work, preferred.** Write brief entries as you work, not just at breakpoints. Even a one-line note preserves context that compaction might lose. Do not wait for a natural breakpoint if you have done something worth noting.

- **Method A, explicit request.** User asks for an update → update immediately.
- **Method B, break indication.** User says they are taking a break → ask whether to update, wait for confirmation.
- **Method C, natural breakpoint.** Claude identifies a completion point → suggest an update, wait for confirmation.
- **Method D, compaction (automatic).** Update immediately, no confirmation. See the compaction protocol below.
- **Method E, high token usage (automatic).** Update proactively before compaction becomes a risk.
- **Method F, proactive triggers (automatic).** No confirmation needed. Update after any web search batch, after any full page fetch, after completing a substantive analysis or deliverable, and whenever 30 or more minutes have passed since the last entry.

**Clock check.** Run the session timer's `check` subcommand at natural pauses. If it reports overdue, write an entry immediately, then run `update` to reset it. Run `start` at session start. No mental arithmetic required. See Core Protocols for the command syntax and the redirect pattern.

**The timer's own timestamp is informational, not authoritative.** For any schedule-relative statement, run a separate verified time check.

### Date and time for entries

Get timestamps via bash: `TZ='America/New_York' date '+%H:%M'`. Fast and reliable. Reserve the date utility script for arithmetic only.

### Format

```markdown
## HH:MM - Brief Topic/Activity
Detailed paragraph(s) capturing:
- What was accomplished
- Key decisions and rationale
- Important insights
- How it connects to project goals
- Open questions

Next: What this enables
```

**For reconstructed entries, when catching up after compaction:**

```markdown
## HH:MM - Brief Topic [Reconstructed from transcript]
What was accomplished based on transcript review. May be incomplete.
Next: What this enables.
```

**Key principle:** more detail is better. Include enough context for future reference. Flag uncertainty when reconstructing.

### First update of session

**Automatic, preferred.** The startup script creates the file with a standard header if it does not already exist, early in its run. This happens on every session start.

**Manual fallback**, if the startup script was not run:

```markdown
# Session: YYYY-MM-DD
Project: [Primary project or "PWKM"]
Start time: HH:MM AM/PM

---
```

Automatic initialization matters more than it looks. Without it, substantive work often happens before the first manual write, and the session's opening minutes lose contemporaneous fidelity.

### Key principles

1. **Write during work, not just at breakpoints.** Even brief notes preserve context.
2. **Contemporaneous beats reconstructed.** Notes written in the moment are more reliable.
3. **Cross-check at compaction.** Always compare transcript against running summary to find gaps.
4. **Flag uncertainty.** Mark reconstructed entries so the user knows they may be incomplete.

---

## Compaction Detection Protocol

**How to detect:** the conversation begins with a system message noting successful compaction, along with a transcript path.

**When compaction has occurred:**

1. **IMMEDIATELY state:** "Compaction detected. Updating running summary..."
2. **Get today's date via bash.**
3. **Read the existing running summary file**, if any, to see what was already captured.
4. **Read the transcript file** referenced in the notice.
5. **Cross-check:** identify any work done between the last running summary entry and the compaction.
6. **Fill gaps** from the transcript, marking new entries as reconstructed.
7. **THEN** continue with the response.

**This must be automatic.** Do not wait for confirmation.

**Why cross-checking matters:** the compaction-generated summary in context may have lost nuances. The transcript file has the raw conversation. Comparing it against the running summary identifies what was missed, flagged so the user knows those entries may be incomplete.

---

## Session Summary Protocol

**At the end of each working session.** This protocol is invoked by step 4 of the handoff
procedure above. **It is not self-triggering**, and that is worth stating plainly because it
was the source of a real failure: for months this section said "at the end of each working
session" while nothing in the end-of-session procedure referenced it, so in practice the
weekly audit was the only thing that ever created a session summary. When the audit ran late,
summaries silently accumulated.

### One summary per calendar date

A session that runs past midnight produces **one summary per calendar date**, matching the
one-file-per-date convention for running summaries. Do not key summaries to sessions: the
idempotency key is the date string in the title, and the enumerate-before-create pattern
depends on it.

### Same-day summaries are thinner, and that is the accepted trade

A summary written at session end cannot carry hindsight; one written days later sometimes can,
because a question left open on the day may have been answered since. That is a real loss. It
is accepted because a thinner summary that exists beats a richer one that does not, and the
idempotency procedure supports updating an existing page when a later session has more to
add.

### Session Summaries parent page

Always create session summaries as subpages of the designated Session Summaries page: `<your-session-summaries-page-id>`.

**Use the ID directly. Do not search for it and do not try to recall it.** A hallucinated parent page ID scatters summaries across the workspace, and the damage is not obvious until an audit goes looking for them.

### Idempotency (CRITICAL)

Before creating a session summary, follow the enumerate-before-create pattern. This is the session-summary instance of the general idempotency protocol in Core Protocols.

**Natural key:** the target date in the page title.

**For a single summary:**

1. Fetch the Session Summaries parent page.
2. Scan the returned child titles for one containing the target date string.
3. If found, UPDATE the existing page. Do not create a new one.
4. If not found, create it.

**For a multi-day backfill:**

1. Fetch the parent **once**.
2. Build a set of existing date strings from the child titles.
3. For each target date, check the set. Present means skip or update; absent means create.
4. **Do not fetch the parent once per target date.** That defeats the purpose of a single enumeration.

**Do not rely on search alone.** Search can return zero hits on pages created minutes earlier. Fetching the parent returns the actual child list with no index staleness. A retry that trusts a stale zero-hit search will happily create a full set of duplicates.

### Create the page

- **Parent:** `<your-session-summaries-page-id>`
- **Title:** "Project Name - YYYY-MM-DD - Brief Description"
- **Content:** session duration and time of day; what was accomplished, as concrete deliverables; current status; next steps or open questions; decisions made or insights gained; work pattern notes; research notes referenced.

### Link in the hub

Add to both the reverse-chronological session index and the appropriate project section of the sessions-by-project index.

### Integration with the running summary

The final summary should include:

```markdown
## Session Summary
[Polished synthesis]

---

## Running Summary (Detailed Log)
[Complete running summaries copied from file]
```

---

## Weekly Session Summary Audit

**When:** first session of each week, detected by the session timer's `audit-check` at startup. If it reports that a weekly audit is needed, proceed.

**Procedure:** follow your audit checklist document, which is the authoritative step-by-step. Keep that checklist as a separate file rather than duplicating its steps here, so there is one place to change when the procedure changes.

At minimum the audit should cross-reference the week's substantive sessions against the session summaries index, identify gaps, and fill them, applying the idempotency pattern above.

**Monthly idea review** piggybacks on the same mechanism. If it is the first week of the month and the monthly flag is also raised, review captured ideas for items ready to develop (see the Knowledge Work protocol). Record both with the timer's `audit-done` subcommand, adding the monthly flag if the idea review was done.

**Requires a summary:** research or analysis of 30 minutes or more, project work, significant decisions.
**Does not require one:** brief admin exchanges, quick task completions.

---

*Adapt paths, timezone, and Notion page IDs to your own environment.*
*See setup-guide.md for configuration details.*
