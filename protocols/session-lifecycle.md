# Session Lifecycle Protocol

Protocols for managing session continuity, documentation, and compaction handling.

---

## Running Summary Protocol

### Purpose
Preserve session context contemporaneously to survive compaction events.

### File Location
Local markdown files organized by date:
```
/running-summaries/
  2026-02-02-session.md
  2026-02-01-session.md
  ...
```

### When to Write

| Condition | Action |
|-----------|--------|
| During work (preferred) | Brief entries as you work |
| Natural breakpoints | More detailed entries |
| High token usage (~150K) | Update proactively |
| Compaction detected | Cross-check transcript, fill gaps |

### Entry Format

```markdown
## HH:MM - Brief Topic

What was accomplished. Key decisions. How it connects to goals.

Next: What this enables.
```

### Example Entries

```markdown
## 14:30 - PWKM System Documentation Update

Updated PWKM System Documentation to v3.0 for GitHub release:
- Removed employer-specific references
- Updated for tiered protocol architecture
- Added prerequisites section with MCP requirements
- Added project subpages documentation

Next: Create remaining GitHub repository files.

## 15:45 - Protocol Documents Created

Created core-protocols.md and session-lifecycle.md for GitHub repo.
Kept essential content, removed implementation-specific details.

Next: Task management and knowledge work protocols.
```

### Why Contemporary Notes Matter

Entries written *during* work capture understanding at the time. Notes reconstructed *after* compaction may lose nuance or introduce errors. Prefer frequent brief updates over infrequent comprehensive ones.

---

## Compaction Detection

### Signs of Compaction
- Sudden loss of earlier conversation details
- Claude mentions "context window" or "earlier in our conversation"
- Session seems to restart mid-conversation

### Compaction Response Protocol

1. **Acknowledge**: Note that compaction occurred
2. **Locate Transcript**: Check for transcript file if available
3. **Cross-Reference**: Compare transcript with running summary
4. **Fill Gaps**: Update running summary with missing context
5. **Continue**: Resume work with recovered context

### Compaction-Resilient Practices

- Write to running summary frequently during complex work
- Document key decisions immediately
- Keep Notion pages updated (they persist regardless of compaction)
- Don't rely solely on conversation history

---

## Session Documentation

### For Significant Sessions

Create a Notion page in Session Summaries with:
- Date and duration
- Projects worked on
- Key accomplishments
- Decisions made
- Open questions
- Links to artifacts created

### Dual Indexing

Session summaries should be findable by:
1. **Chronological**: When did this happen?
2. **By Project**: What work was done on Project X?

### When to Create Session Summary

- Significant progress on a project
- Important decisions made
- New insights or frameworks developed
- Cross-project synthesis occurred

Quick task completions or simple queries don't need formal session summaries.

---

## Session Handoff

When ending a session that will continue later:

1. Update running summary with current state
2. Note any "in progress" work
3. List immediate next steps
4. Update relevant Notion pages if needed

This ensures the next session can pick up smoothly.

---

## Long Session Management

For sessions extending beyond 2+ hours:

- Take brief running summary breaks every 45-60 minutes
- Note any context that might be lost to compaction
- Consider natural breakpoints for documentation
- Update Notion pages with substantive progress
