# Notion Structure Guide

How to organize your PWKM system in Notion.

---

## Page Hierarchy

```
PWKM Hub (root page)
├── 🧠 Memory Base
├── 📋 Protocol Documents
│   ├── Core Protocols
│   ├── Session Lifecycle
│   ├── Task Management
│   └── Knowledge Work
├── 🔄 Session Handoff          (required by ~endday / ~startday)
├── 💡 Ideas and Interests
├── 🌀 Recurring Themes
├── 📚 Research Library
│   ├── [Topic Area 1]
│   ├── [Topic Area 2]
│   └── Cross-Reference Index
├── 📊 Work Patterns
├── 📋 Session Summaries        (parent for dated child pages)
│   ├── By Date
│   └── By Project
├── 📁 Projects
│   ├── [Project 1]
│   ├── [Project 2]
│   └── [Project 3]
├── ✅ Tasks Database
└── Optional, only if you use the matching script
    ├── 📖 Reading Queue        (goodreads_sync.py)
    └── 🔍 Environment Drift Log (env_audit.py)
```

### Pages that scripts and protocols depend on

Most of the tree above is organisational preference. Three entries are not:

| Page | Depended on by | What breaks without it |
|---|---|---|
| Session Handoff | `~endday`, `~startday` | The end-of-session protocol has nowhere to write, and the next day's startup has nothing to read |
| Session Summaries (as a parent page) | Session summary protocol, weekly audit | Summaries scatter across the workspace; the idempotency check that prevents duplicates enumerates this page's children |
| Reading Queue | `goodreads_sync.py` | Sync fails, or worse, creates pages with the wrong schema |

**Session Handoff is a single page that gets overwritten**, not a database of dated entries. The per-day running summary files are the audit trail. The handoff exists for transition fidelity between sessions, not as a historical record, and treating it as an archive makes it long enough that the next session skims it.

---

## Database Setup

### Tasks Database

**Properties**:
| Property | Type | Purpose |
|----------|------|---------|
| Task | Title | Task name |
| Due Date | Date | When it's due |
| Status | Select | Active, Done, On Hold |
| Recurrence | Select | daily, weekly, etc. |
| Project | Relation | Link to project |
| Priority | Select | High, Medium, Low |

**Views**:
- Default: All tasks sorted by due date
- Overdue: Filter where Due Date < Today
- By Project: Grouped by project relation

### Reading Queue Database (optional)

Only needed if you use `goodreads_sync.py`. **The property names are not
suggestions**: the script writes to them literally, and a mismatch surfaces as
a Notion API error rather than as anything self-explanatory.

| Property | Type | Notes |
|---|---|---|
| Title | Title | Book title |
| Author | Rich text | |
| Status | Select | Must contain an option named exactly `Reading` |
| Started | Date | Optional; set from the Goodreads shelf-add date |

Put the database ID in `PWKM_READING_QUEUE_DB_ID`.

### Session Summaries Database (optional)

**Properties**:
| Property | Type | Purpose |
|----------|------|---------|
| Title | Title | Session description |
| Date | Date | Session date |
| Projects | Multi-select | Projects worked on |
| Duration | Number | Hours worked |

---

## Linking Conventions

### Internal Links
Use Notion's @ mention to link between pages:
- `@Memory Base` in project pages
- `@[Project Name]` in session summaries
- `@[Theme]` when referencing recurring themes

### Context & Resources Section
Every project page should start with links to:
1. Memory Base
2. Core Protocols
3. Related research
4. Related projects

---

## Icon Conventions

Suggested icons for consistency:
- 🧠 Memory Base
- 📋 Protocols / Tasks
- 💡 Ideas
- 🌀 Themes
- 📚 Research / Library
- 📊 Patterns / Analysis
- 📁 Projects folder
- ✅ Tasks

---

## Page Templates

### Creating Templates in Notion
1. Create a page with desired structure
2. Add to database as template, OR
3. Duplicate when creating new pages

### Recommended Templates
- Project page (use project-template.md)
- Research note
- Session summary
- Idea capture

---

## Maintenance

### Weekly
- Review and clean up recent pages
- Update project statuses
- Archive completed items

### Monthly
- Review Memory Base accuracy, specifically whether any mutable fact has been
  restated outside Current State. Duplication is the defect; a wrong duplicate
  is only its symptom
- Update recurring themes
- Clean up Research Library

### Quarterly
- Major Memory Base update
- Review system effectiveness
- Prune unused structures
