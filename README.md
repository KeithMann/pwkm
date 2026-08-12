# PWKM: Personal Work and Knowledge Management

A system for human-AI collaboration in complex, multi-project knowledge work.

## What is PWKM?

PWKM is an integrated architecture that combines:
- **Work management**: Projects, tasks, milestones, deliverables, deadlines
- **Knowledge management**: Research, ideas, themes, theory-building, cross-project synthesis

Built through iterative collaboration between a human knowledge worker and Claude, PWKM addresses the problem of maintaining coherent context across multiple concurrent projects while using AI assistance effectively.

## Why PWKM?

Working with AI assistants creates specific problems:

- **Context fragmentation**: Each conversation starts fresh
- **Knowledge silos**: Insights that bridge projects get lost
- **Discontinuity**: No systematic way to ensure context is loaded
- **Work-knowledge disconnect**: Traditional tools separate project management from knowledge management

PWKM addresses these with a hub-and-spoke architecture, Notion as the single source of truth, and Claude as a collaborator rather than an automation layer.

## Key Principles

1. **Single source of truth**: Notion is authoritative; chat history is secondary
2. **Hub-and-spoke architecture**: A central hub connects specialized components
3. **Tiered protocol loading**: Load only what a given session needs
4. **Integration over automation**: Structure for collaboration, not replacement of thought
5. **Work and knowledge are inseparable**: Projects generate knowledge; knowledge informs projects

## Start here

If you are setting this up for the first time, read in this order. The system
has more parts than you need on day one, and the order below gets you to a
working session before it asks you to understand everything.

1. **[claude-desktop/setup.md](claude-desktop/setup.md)** — what runs locally versus what comes from Claude's built-in connectors. Shorter than you expect.
2. **[docs/setup-guide.md](docs/setup-guide.md)** — Notion structure, scripts, `.env`.
3. **[scripts/.env.example](scripts/.env.example)** — copy to `.env` and set `LOCAL_TIMEZONE` first. It is the one setting whose default is probably wrong for you.
4. **[examples/first-session.md](examples/first-session.md)** — what a session actually looks like.
5. **[docs/pwkm-system-documentation.md](docs/pwkm-system-documentation.md)** — the full picture, once the above works.

## What's Included

### Scripts (`scripts/`)

| Script | Purpose |
|---|---|
| **startup.py** | Startup orchestrator. Replaces a sequence of separate calls with one: date verification, calendar with classification, task status, audit checks, session timer. See the note below about optional sections. |
| **session_timer.py** | Running-summary clock enforcement and weekly/monthly audit tracking. State persists across sessions. |
| **date_utils.py** | Date arithmetic with timezone support, nth-weekday-of-month calculations, recurring task patterns. All commands support `--json`. |
| **task_manager.py** | Task status reporting and completion, with automatic recurring-date calculation. CSV-backed. |
| **gcal_query.py** | Google Calendar query with compact output and `--classify` for DONE/NOW/SOON/LATER against the current time. |
| **gcal_create.py** | Google Calendar event creation over OAuth. |
| **fetch_notion_tasks.py** | Export a Notion tasks database to CSV for fast local querying. |
| **pwkm_env.py** | Shared `.env` loader. Every script calls it before reading configuration. |

**About `startup.py` and optional sections.** The published orchestrator is the
real one, and it calls several helper scripts that are **not** included here:
weather, market data, news, and activity tracking. Those are personal to the
author's setup rather than part of the core system. Missing helpers are handled
gracefully: the section reports that the script was not found and the run
continues. Treat the absent sections as a menu of what you could add, not as
breakage.

### Protocols (`protocols/`)

| Protocol | When to Load | Purpose |
|---|---|---|
| **core-protocols.md** | Every session | Adaptive tool loading, environment detection, arithmetic and date handling, source precedence, startup sequence, Notion editing patterns, idempotency, Memory Base maintenance |
| **session-lifecycle.md** | Substantive work | Session triggers and the handoff, running summaries and fidelity risk, compaction detection and recovery, session summaries, weekly audit |
| **task-management.md** | Task completion | Completion workflow, shell execution patterns, CSV and Notion synchronization, recurring patterns |
| **knowledge-work.md** | Research and ideas | Idea capture, research documentation, project context recognition, session summary import |

Read Adaptive Tool Loading first. Environment detection depends on it, and a
session that skips it will report capabilities as unavailable when they are not.

### Configuration

All configuration lives in `scripts/.env`, copied from
[`scripts/.env.example`](scripts/.env.example). A real environment variable
overrides the file, so you can change one setting for a single run without
editing anything.

**Credentials**

| Variable | Purpose |
|---|---|
| `NOTION_API_KEY` | Notion integration secret |
| `NOTION_DATABASE_ID` | Your tasks database |
| `GOOGLE_CLIENT_ID` | Google OAuth, for the calendar scripts |
| `GOOGLE_CLIENT_SECRET` | Google OAuth, for the calendar scripts |

**Settings**

| Variable | Default | Purpose |
|---|---|---|
| `LOCAL_TIMEZONE` | North American Eastern | Timezone for all date and time operations. **Set this.** |
| `PWKM_PYTHON` | Current interpreter | Interpreter used for `startup.py` subprocess calls |
| `PWKM_STATE_DIR` | Parent of `scripts/` | Session timer, audit state, and running summaries |
| `PWKM_TASKS_CSV` | Beside the scripts | Tasks CSV location; a fallback, since the scripts look beside themselves first |
| `PWKM_HEALTH_DB` | Unset | Optional health database. Unset disables that section rather than erroring |
| `PWKM_SECONDARY_CALENDARS` | Unset | Extra calendars to merge, optionally labelled: `Work=you@work.example.com` |

## Prerequisites

- **Windows** for the shell scripts as published. The protocols and Notion structure are platform-independent; the Python is close but the shell patterns are not.
- **Python 3.10+**
- **Claude Desktop**
- **`uv` / `uvx`**, which runs windows-mcp
- **Notion account** (free tier is fine)

### MCP servers and connectors

One local MCP server, plus connectors enabled in the Claude interface:

- **windows-mcp** — configured locally, in `claude_desktop_config.json`. Runs shell commands and scripts.
- **Notion** — built-in connector.
- **Gmail / Microsoft 365 / Google Calendar** — built-in connectors, optional.

A filesystem MCP server is **not** required; windows-mcp covers file access. A
calendar MCP server is **not** required for the startup report either, because
the calendar scripts call the Google API directly using credentials in `.env`.
See [claude-desktop/setup.md](claude-desktop/setup.md).

## Repository Structure

```
pwkm/
├── docs/                             # Documentation
│   ├── pwkm-system-documentation.md  # Comprehensive guide
│   ├── setup-guide.md                # Installation
│   ├── usage-guide.md                # Daily workflows
│   ├── customization.md              # Adapting it
│   └── scheduling-fetch-tasks.md     # Scheduling the Notion export
├── scripts/                          # Python utilities
│   ├── startup.py                    # Startup orchestrator
│   ├── session_timer.py              # Clock and audit tracking
│   ├── date_utils.py                 # Date calculations
│   ├── task_manager.py               # Task operations
│   ├── gcal_query.py                 # Calendar query
│   ├── gcal_create.py                # Calendar event creation
│   ├── fetch_notion_tasks.py         # Notion to CSV export
│   ├── pwkm_env.py                   # Shared .env loader
│   ├── .env.example                  # Configuration template
│   └── requirements.txt              # Python dependencies
├── claude-desktop/                   # Claude Desktop configuration
├── notion/                           # Notion templates
├── protocols/                        # Protocol documents for Claude
└── examples/                         # Example sessions
```

## Architecture Overview

The system uses **tiered loading** to keep context consumption proportionate:

- **Tier 1, every session:** `startup.py` runs date verification, calendar with classification, task status, audit triggers, and the session timer in one call. Core Protocols loaded from Notion.
- **Tier 2, on demand:** Session Lifecycle, Task Management, and Knowledge Work protocols, loaded when specific inputs or activities trigger them.
- **Tier 3, on request:** Research Library, Work Patterns, Ideas, Recurring Themes, Session Summaries.

Context preservation relies on **running summaries**, local markdown written
during work rather than reconstructed afterwards, backed by a session timer
that enforces update intervals, with compaction detection and transcript
cross-referencing for recovery.

## Related

This repository is the practical companion to the essay "Love Me, Love My AI",
which argues *why* employers should embrace personal AI systems. This repo is
the *how*.

## License

- **Code and scripts**: custom license for personal and internal business use
- **Documentation and templates**: CC BY-NC-ND 4.0

See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).

## Author

Keith Mann

For commercial licensing inquiries: keith@keithmann.com