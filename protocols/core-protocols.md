# Core Protocols

Essential protocols loaded at the start of every PWKM session.

---

## Date Verification Protocol

**Always verify current date at session start.**

Run date verification script:
```
python date_utils.py verify
```

This ensures accurate scheduling and prevents date-related errors.

---

## Session Startup Protocol (Tier 1)

Execute these steps at the start of every session:

1. **Verify Date**: Run date_utils.py verify
2. **Check Calendar**: Fetch today's calendar events
3. **Load Hub**: Fetch PWKM Hub for project registry
4. **Task Status**: Run task_manager.py status
5. **Report**: Present calendar, overdue tasks, today's tasks, upcoming milestones

**Startup Report Format**:
```
## Session Startup - [Date]

**Calendar**: [Today's events]

**Tasks**:
- Overdue: [List or "None"]
- Due Today: [List or "None"]
- This Week: [Key items]

**Ready to work on**: [Suggest based on priorities]
```

---

## Notion URL Format

When referencing Notion pages, use the page ID format:
- Extract ID from URL: `notion.so/Page-Title-abc123def456` → `abc123def456`
- For fetching: Use the full URL or just the ID

---

## Memory Base Maintenance

The Memory Base should be updated when:
- Major milestones are reached
- New projects are added or completed
- Significant insights or frameworks emerge
- Working patterns change

Updates should preserve structure while reflecting current state.

---

## Task Status Check

Quick task check via Python script:
```
python task_manager.py status
```

This shows:
- Overdue tasks (with days overdue)
- Tasks due today
- Upcoming tasks (next 7 days)

---

## Running Summary Basics

During substantive work sessions, maintain a running summary:
- Location: Local markdown file
- Format: Timestamped entries
- Purpose: Preserve context before potential compaction

Basic entry format:
```markdown
## HH:MM - Topic
What was accomplished. Key decisions.
Next: What this enables.
```

---

## Tiered Loading Reference

**Tier 1 (Every Session)**: This document (Core Protocols)

**Tier 2 (On-Demand)**:
| Trigger | Load |
|---------|------|
| Substantive project work | Session Lifecycle |
| Task completion | Task Management |
| Research/ideas | Knowledge Work |
| Specialized work | Specialized Workflows |

**Tier 3 (Explicit Request)**: Research Library, Work Patterns, Ideas, Session Summaries

---

## Protocol Loading Commands

When loading additional protocols, fetch the relevant document:
- Session Lifecycle Protocol
- Task Management Protocol
- Knowledge Work Protocol
- Specialized Workflows Protocol (if applicable)
