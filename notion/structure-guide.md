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
├── 💡 Ideas and Interests
├── 🌀 Recurring Themes
├── 📚 Research Library
│   ├── [Topic Area 1]
│   ├── [Topic Area 2]
│   └── Cross-Reference Index
├── 📊 Work Patterns
├── 📋 Session Summaries
│   ├── By Date
│   └── By Project
├── 📁 Projects
│   ├── [Project 1]
│   ├── [Project 2]
│   └── [Project 3]
└── ✅ Tasks Database
```

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
- Review Memory Base accuracy
- Update recurring themes
- Clean up Research Library

### Quarterly
- Major Memory Base update
- Review system effectiveness
- Prune unused structures
