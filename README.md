# PWKM: Personal Work and Knowledge Management

A sophisticated system for human-AI collaboration in complex, multi-project knowledge work.

## What is PWKM?

PWKM is an integrated architecture that combines:
- **Work management**: Projects, tasks, milestones, deliverables, deadlines
- **Knowledge management**: Research, ideas, themes, theory-building, cross-project synthesis

Built through iterative collaboration between a human knowledge worker and Claude (Anthropic's AI assistant), PWKM addresses the fundamental challenge of maintaining coherent context across multiple concurrent projects while leveraging AI assistance effectively.

## Why PWKM?

When working with AI assistants, knowledge workers face specific challenges:

- **Context Fragmentation**: Each conversation starts fresh
- **Knowledge Silos**: Insights that bridge projects get lost
- **Discontinuity**: No systematic way to ensure comprehensive context loading
- **Work-Knowledge Disconnect**: Traditional tools separate project management from knowledge management

PWKM solves these problems through a hub-and-spoke architecture with Notion as the single source of truth and Claude as an intelligent collaborator.

## Key Principles

1. **Single Source of Truth**: Notion is authoritative; chat history is secondary
2. **Hub-and-Spoke Architecture**: Central hub connects specialized components
3. **Tiered Protocol Loading**: Load only what's needed for each session type
4. **Integration Over Automation**: Structure for collaboration, not replacement of thought
5. **Work and Knowledge as Inseparable**: Projects generate knowledge; knowledge informs projects

## What's Included

### Scripts (`scripts/`)

| Script | Purpose |
|---|---|
| **startup.py** | Consolidated startup orchestrator — replaces 5-6 separate tool calls with one. Runs date verification, calendar query with classification, task status, audit checks, and session timer in a single invocation. |
| **session_timer.py** | Running summary 30-minute clock enforcement and weekly/monthly audit tracking. Persistent state across sessions. |
| **date_utils.py** | Date arithmetic with timezone support, nth-weekday-of-month calculations, recurring task date patterns. All commands support `--json` output. |
| **task_manager.py** | Task status reporting, completion with automatic recurring date calculation, CSV-based storage. Parses task names for nth-weekday recurrence patterns. |
| **gcal_query.py** | Google Calendar query with compact output and `--classify` flag for DONE/NOW/SOON/LATER event classification against current time. |
| **gcal_create.py** | Google Calendar event creation with OAuth. |
| **fetch_notion_tasks.py** | Export Notion tasks database to CSV for efficient local querying. |

### Protocols (`protocols/`)

| Protocol | When to Load | Purpose |
|---|---|---|
| **core-protocols.md** | Every session | Environment detection, date handling, startup sequence, running summary essentials, Memory Base maintenance, specialized input recognition |
| **session-lifecycle.md** | Substantive work | Running summary protocol with fidelity risk management, compaction detection and recovery, session summaries, weekly audit triggers |
| **task-management.md** | Task completion | Task completion workflow, Windows MCP execution patterns, CSV/Notion synchronization, recurring task patterns |
| **knowledge-work.md** | Research/ideas | Idea capture, research documentation, project context recognition, Memory Base loading, session summary import |

### Configuration

All scripts support environment variable configuration:

| Variable | Default | Purpose |
|---|---|---|
| `LOCAL_TIMEZONE` | `America/Toronto` | Timezone for all date/time operations |
| `PWKM_PYTHON` | `sys.executable` | Python interpreter path (for startup.py subprocess calls) |
| `PWKM_TASKS_CSV` | Auto-detect | Path to tasks CSV file |
| `PWKM_STATE_DIR` | `scripts/../` | Directory for session timer and audit state files |

## Prerequisites

- **Windows 11** with administrator access
- **Claude Desktop** application with MCP support
- **Python 3.10+**
- **Notion account** (free tier works)
- **Claude Pro or Team account**

### Required MCP Servers

- Notion MCP
- Filesystem MCP
- Windows MCP
- Google Calendar MCP

## Getting Started

1. Read [docs/pwkm-system-documentation.md](docs/pwkm-system-documentation.md) for the complete system overview
2. Follow [docs/setup-guide.md](docs/setup-guide.md) for installation
3. Import the Notion templates from the `notion/` directory
4. Configure Claude Desktop using examples in `claude-desktop/`
5. Start your first PWKM session!

## Repository Structure

```
pwkm/
├── docs/                    # Documentation
│   ├── pwkm-system-documentation.md  # Comprehensive guide
│   ├── setup-guide.md       # Installation instructions
│   ├── usage-guide.md       # Daily workflows
│   └── customization.md     # Adapting to your needs
├── scripts/                 # Python utilities
│   ├── startup.py           # Consolidated startup orchestrator
│   ├── session_timer.py     # Running summary clock + audit tracking
│   ├── date_utils.py        # Date calculations
│   ├── task_manager.py      # Task operations
│   ├── gcal_query.py        # Calendar query (with --classify)
│   ├── gcal_create.py       # Calendar event creation
│   ├── fetch_notion_tasks.py # Notion → CSV export
│   └── requirements.txt     # Python dependencies
├── claude-desktop/          # Claude Desktop configuration
├── notion/                  # Notion templates (Markdown export)
├── protocols/               # Protocol documents for Claude
│   ├── core-protocols.md    # Essential (every session)
│   ├── session-lifecycle.md # Context preservation
│   ├── task-management.md   # Task completion workflows
│   └── knowledge-work.md    # Research and ideas
└── examples/                # Example sessions and workflows
```

## Architecture Overview

The system uses a **tiered startup** approach to minimize token consumption:

- **Tier 1 (Every Session):** `startup.py` runs date verification, calendar with classification, task status, audit triggers, and session timer — all in one script call. Core Protocols loaded from Notion.
- **Tier 2 (On-Demand):** Session Lifecycle, Task Management, Knowledge Work protocols loaded only when triggered by specific inputs or activities.
- **Tier 3 (Explicit Request):** Research Library, Work Patterns, Ideas, Recurring Themes, Session Summaries.

Context preservation relies on **running summaries** (local markdown files written during work) backed by a **session timer** that mechanically enforces 30-minute update intervals, with automatic compaction detection and transcript cross-referencing for recovery.

## Related

This repository is the practical companion to the essay "Love Me, Love My AI" which argues *why* employers should embrace personal AI systems. This repo provides *how* to build one.

## License

- **Code and Scripts**: Custom license for personal and internal business use
- **Documentation and Templates**: CC BY-NC-ND 4.0

See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) for details.

## Author

Keith Mann

For commercial licensing inquiries: keith@keithmann.com
