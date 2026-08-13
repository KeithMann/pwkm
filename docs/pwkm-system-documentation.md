# Building a Personal Work and Knowledge Management System with Claude and Notion

**A Case Study in Human-AI Collaboration for Complex, Multi-Project Work**

By Keith Mann

---

## Abstract

This document describes a Personal Work and Knowledge Management (PWKM) system
built through iterative collaboration between a human knowledge worker and Claude, Anthropic's AI assistant. The system addresses a fundamental challenge in knowledge work: maintaining coherent context across multiple concurrent projects while leveraging AI assistance effectively, integrating both work management (projects, tasks, deadlines) and knowledge management (research, ideas, themes, theory-building) in a unified architecture.

The result is not just a set of tools, but an integrated architecture that embodies principles from systems thinking, cognitive science, and knowledge management theory. This case study documents the system's structure, the principles that guided its design, its evolution, and provides templates for others to adapt.

**Scope of the claim**: this is a case study of one system in daily use, not a
survey of the field. An informal search at the time of first writing did not
turn up a closely comparable published architecture, but that search was not
systematic, it was never repeated, and the personal-knowledge-management and
AI-tooling landscape has moved a great deal since. Nothing here should be read
as a claim of novelty or priority. What is offered is a worked example,
described in enough detail to be adapted, tested, or argued with.

---

## Table of Contents

1. The Problem Space
2. Design Principles
3. System Architecture
4. The Evolution: How We Got Here
5. Key Components Explained
6. How It Works in Practice
7. Template for Adaptation
8. Lessons Learned
9. Theoretical Foundations
10. Future Directions

---

## The Problem Space

### The Challenge of Multi-Project Knowledge Work

Knowledge workers today often juggle multiple concurrent projects, each with:
- Its own context and background
- Connections to other projects
- Evolving state and history
- Research materials and references
- Distinct but overlapping intellectual themes

When working with AI assistants like Claude, this creates specific challenges:

**Context Fragmentation**: Each conversation starts fresh. Without structure, users spend significant time re-establishing context, explaining background, and reconstructing connections between projects.

**Knowledge Silos**: Work on Project A happens in one conversation, Project B in another, and insights that bridge them get lost.

**Discontinuity**: Even with AI memory features, there's no systematic way to ensure comprehensive context loading or to track how knowledge evolves across sessions.

**Redundant Explanation**: Without a single source of truth, the same information gets explained repeatedly across different conversations.

**Work-Knowledge Disconnect**: Traditional project management focuses on tasks and deliverables, while knowledge management focuses on information and insights. Knowledge work requires integration of both—projects generate knowledge, knowledge informs projects, but systems rarely bridge this gap effectively.

### The Specific Context

The system was developed for managing multiple concurrent research and creative projects:
- **Professional research work**
- **Academic collaboration**
- **Personal writing**
- **Programming projects**
- **Cross-cutting research themes**

Each project has:
- Different timelines and deadlines
- Distinct collaborators and audiences
- Unique intellectual themes
- Overlapping conceptual frameworks
- Varying priorities and states

The traditional approach—separate chats for each project, manual context recreation, fragmented notes—was inefficient and intellectually unsatisfying.

### What Was Needed

An integrated system that would:
1. **Maintain comprehensive context** across all projects
2. **Make connections explicit** between related work
3. **Provide consistent structure** without constraining flexibility
4. **Serve as single source of truth** while leveraging AI capabilities
5. **Scale gracefully** as new projects emerge
6. **Support both deep focus and cross-project synthesis**
7. **Integrate work management and knowledge management** rather than treating them as separate domains

---

## Design Principles

The system that emerged embodies several key principles, drawn from systems thinking, cognitive science, and practical experience:

### 1. Single Source of Truth

**Principle**: Documentation in Notion is authoritative; chat history is secondary.

**Rationale**: Conversations are unstructured and ephemeral. Documents are structured and persistent. By making Notion the source of truth, we ensure consistency and reduce the need to reconstruct context.

**Implementation**: Every important decision, insight, and state change gets documented in Notion. Claude loads context from Notion, not from trying to remember previous conversations.

**Why Notion specifically**: Notion provides a rich interface for *both* human and AI to work with content. The human can view, edit, reorganize, and annotate documents directly—Notion isn't just storage for Claude's outputs. This makes it a genuine collaborative workspace where both parties can contribute, review each other's work, and maintain shared understanding.

### 2. Hub-and-Spoke Architecture

**Principle**: Central hub connects to specialized components rather than point-to-point links.

**Rationale**: As complexity grows, point-to-point connections create spaghetti. A hub provides coherent organization while allowing components to evolve independently.

**Implementation**: The PWKM Hub serves as the central point, linking to:
- Core documents (Memory Base, protocols, etc.)
- Individual project pages
- Cross-cutting research
- Session histories
- Work patterns and ideas

### 3. Context & Resources Pattern

**Principle**: Every project page begins with explicit links to relevant context.

**Rationale**: Humans and AI both benefit from explicit structure. Rather than expecting implicit connections to be remembered, make them visible and clickable.

**Implementation**: Each project page has a "Context & Resources" section at the top that links to:
- Core PWKM documents (Memory Base, protocols)
- Related research and projects
- Key intellectual themes relevant to that project

### 4. Emergent Rather Than Designed

**Principle**: Let structure emerge from actual needs rather than imposing a predetermined framework.

**Rationale**: Knowledge work is creative and unpredictable. Overly rigid systems become constraints. The best structure emerges from practice.

**Implementation**: We started with basic needs (track projects, capture ideas) and added structure incrementally as patterns became clear. The Memory Base emerged after several sessions revealed recurring themes. The comprehensive Session Startup Protocol developed from observing what information was needed at the beginning of each session.

### 5. Integration Over Automation

**Principle**: The system creates structure for collaboration, not automation of thought.

**Rationale**: The goal isn't to have AI work autonomously, but to enhance human-AI collaboration. Structure reduces friction without eliminating human judgment.

**Implementation**: Claude loads context automatically when projects are mentioned, but doesn't make decisions about what to work on or how to approach problems. The human remains in control while the AI provides informed assistance.

### 6. Theory-Grounded Structure

**Principle**: The architecture reflects how humans actually think and organize knowledge.

**Rationale**: Systems that work with human cognition are more effective than those that impose artificial structure.

**Implementation**: The system embodies concepts from:
- **Systems thinking** (Ackoff): Synthesis over analysis, understanding through context
- **Theory-building** (Naur/Ryle): Knowledge as integrated understanding, not just facts
- **Situated action** (Suchman): Context matters, plans are resources not determinants

### 7. Work and Knowledge as Inseparable

**Principle**: Don't treat work management and knowledge management as separate domains.

**Rationale**: In knowledge work, work generates insights and insights inform work. Artificial separation creates friction.

**Implementation**: The PWKM system integrates:
- **Work dimension**: Projects, tasks, milestones, deliverables, deadlines
- **Knowledge dimension**: Research, ideas, themes, theory-building, cross-project synthesis

### 8. Tiered Protocol Loading

**Principle**: Load only what's needed for the current session type.

**Rationale**: Loading everything every time wastes tokens and time. Different sessions need different context.

**Implementation**: Protocols organized into tiers:
- **Tier 1 (Always)**: Core protocols, date verification, calendar, tasks
- **Tier 2 (On-demand)**: Session lifecycle, task management, knowledge work, specialized workflows
- **Tier 3 (Explicit request)**: Research library, work patterns, session summaries

### 9. Mechanical Enforcement

**Principle**: Externalize checks to scripts rather than relying on Claude's memory or mental arithmetic.

**Rationale**: Claude cannot reliably track elapsed time, remember to perform periodic checks, or maintain state across compaction boundaries. Scripts with persistent state files provide mechanical enforcement.

**Implementation**:
- `session_timer.py` tracks 30-minute running summary clock via JSON state files
- `startup.py` consolidates 5-6 separate startup checks into one call
- `gcal_query.py --classify` compares events against current time mechanically
- `date_utils.py` handles all date arithmetic (Claude never does mental date math)
- Audit triggers tracked persistently in `audit_state.json`

### 10. Configuration Over Forking

**Principle**: Where two environments differ, make the difference a configuration
value rather than a second copy of the code.

**Rationale**: A fork is a promise to maintain two things that will drift apart.
Once a script exists in a personal variant and a published variant, every later
fix has to be made twice, and the one nobody runs daily is the one that rots.
The discipline is to keep a single implementation and push every environmental
difference outward into configuration.

**Implementation**: The published scripts and the author's live scripts are
byte-identical. Everything that differs between them lives in `.env` or in a
gitignored JSON file: locations, calendar identifiers, feed lists, database
identifiers, activity categories, file paths. Where a setting needs more than a
bare value, the convention is `Label=Value` rather than a parallel variable, so
that adding a second calendar does not mean adding a second code path.

**Corollary, on absence**: a setting can be absent for more than one reason, and
the reasons are not interchangeable. Absent by design, absent by failure, and
present but not asked for are three different situations. The ActivityWatch
integration therefore reads as a tri-state (`on`, `off`, or unset) rather than a
boolean, and `off` performs no probe at all, because the probe is itself the
access being declined.

---

## System Architecture

### Overview

The system consists of three layers:

1. **Foundation Layer**: Core documents that provide persistent context
2. **Project Layer**: Individual project pages with specific content and state
3. **Integration Layer**: Protocols and tools that connect everything

```
┌─────────────────────────────────────────────────────────┐
│                   PWKM HUB (Central Hub)                │
│                                                         │
│  ┌────────────────────────────────────────────────┐     │
│  │         FOUNDATION LAYER                       │     │
│  │  • Memory Base (comprehensive context)         │     │
│  │  • Protocol Documents (modular protocols)      │     │
│  │  • Recurring Themes (cross-project patterns)   │     │
│  │  • Research Library (readings)                 │     │
│  │  • Session Summaries (history)                 │     │
│  │  • Work Patterns (productivity insights)       │     │
│  │  • Ideas and Interests (emerging thinking)     │     │
│  │  • Tasks Database (deliverables tracking)      │     │
│  └────────────────────────────────────────────────┘     │
│                                                         │
│  ┌────────────────────────────────────────────────┐     │
│  │         PROJECT LAYER                          │     │
│  │  Each project page contains:                   │     │
│  │  • Context & Resources (links to foundation)   │     │
│  │  • Project overview and status                 │     │
│  │  • Current work and next steps                 │     │
│  │  • Research connections                        │     │
│  │  • Session history                             │     │
│  └────────────────────────────────────────────────┘     │
│                                                         │
│  ┌────────────────────────────────────────────────┐     │
│  │         INTEGRATION LAYER                      │     │
│  │  • Tiered Startup Protocol                     │     │
│  │  • Running Summary Protocol                    │     │
│  │  • Task Management (Python + CSV)              │     │
│  │  • Context loading automation                  │     │
│  │  • Cross-project search                        │     │
│  │  • Idea capture workflow                       │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### Foundation Layer Components

#### 1. Memory Base

**Purpose**: Comprehensive background context about the person, their work, and approach.

**Contents**:
- Purpose & Context (role, intellectual focus, work scope)
- Current State (active projects, recent developments)
- On the Horizon (planned directions)
- Key Learnings & Principles (recurring themes, frameworks)
- Approach & Patterns (working methods, preferences)
- Tools & Resources (workflow, resource access)

**Why it matters**: This is the single richest source of context. When Claude loads the Memory Base, it gains understanding of not just what you're working on, but how you think, what matters to you, and how different projects connect.

**Usage**: Loaded at the start of every session via the startup protocol. Provides stable background that persists across conversations.

#### 2. Protocol Documents (Modular)

**Purpose**: Documented protocols for common workflows, organized for tiered loading.

**Structure**:
- **Core Protocols** (always loaded): Date handling, task status checks, Notion URL format, Memory Base maintenance, session startup essentials, running summary basics
- **Session Lifecycle** (on-demand): Full running summary protocol, compaction handling, session documentation
- **Task Management** (on-demand): Task completion workflows, CSV management, recurring task patterns
- **Knowledge Work** (on-demand): Idea capture, research documentation, theme identification
- **Specialized Workflows** (on-demand): Domain-specific workflows

**Why it matters**: Reduces cognitive load by standardizing routine processes. Tiered loading means only relevant protocols consume context tokens.

#### 3. Recurring Themes

**Purpose**: Cross-cutting intellectual themes that appear across multiple projects.

**Contents**: Documented patterns identified across work.

**Why it matters**: Makes implicit connections explicit. Shows how disparate projects relate to deeper intellectual commitments.

#### 4. Research Library

**Purpose**: Tracking papers, books, and research materials across projects.

**Contents**: Hierarchical organization by project area with subsections for readings. Includes cross-reference index showing which materials apply to multiple projects.

#### 5. Session Summaries / Running Summaries

**Purpose**: Historical record of work sessions.

**Implementation**: Two complementary approaches:
- **Running Summaries**: Markdown files written during work sessions, capturing progress contemporaneously. Stored locally for quick access.
- **Session Summaries**: Notion pages for significant sessions, with dual indexing (chronological + by project).

**Why Running Summaries**: Entries written *during* work capture what was understood at the time. Entries reconstructed *after* compaction may lose nuance. Contemporaneous notes are more reliable.

#### 6. Tasks Database

**Purpose**: Track tasks and deadlines across all projects.

**Implementation**: Notion database exported to CSV for efficient checking. Python script (`task_manager.py`) handles task completion and rescheduling.

**Why CSV**: one local file read is faster than querying the Notion API at every
startup, and it works offline. The original rationale no longer holds: filtered
database queries were unsupported when this was written, but are supported now
and are used elsewhere in the system, for example by `goodreads_sync.py`. The
CSV export is retained for speed and offline availability, not because filtering
is unavailable.

### Project Layer

Each project has a dedicated page with standardized structure. Importantly, **Notion serves as a collaborative workspace for both human and AI**—not merely a storage location for Claude's documents. The human can view, edit, reorganize, and annotate content directly in Notion's interface, making it a true shared working environment.

#### Project Page Structure

```markdown
# [Project Name]

## Context & Resources
- Links to Memory Base and Core Protocols
- Links to related research documents
- Links to related projects
- Key intellectual themes (from Memory Base)

## Project Overview
- Purpose and scope
- Key participants (if collaborative)
- Positioning within broader work

## Current Status
- Recent accomplishments
- Active work streams
- Current state

## Next Steps
- Immediate actions
- Medium-term goals
- Open questions

## Research Materials
- Links to relevant Research Library sections
- Project-specific readings

## Session History
- Links to session summaries
- Timeline of work

## Notes and Ideas
- Emerging insights
- Connections to other work
- Questions for exploration
```

#### Project Subpages

Project pages frequently contain **subpages** created by either the human or Claude as work progresses. These provide dedicated space for content that would clutter the main project page.

**Examples of subpages:**
- **Draft documents**: Working drafts of deliverables (articles, reports, proposals)
- **Research notes**: Detailed notes on specific papers, books, or sources
- **Meeting notes**: Records of conversations with collaborators
- **Analysis documents**: Deep dives into specific aspects of the project
- **Reference materials**: Collected information on specific subtopics
- **Outlines and structures**: Detailed planning documents
- **Archive sections**: Completed or deprecated content preserved for reference

**Why subpages matter:**
- Keep the main project page scannable and navigable
- Allow deep work on specific aspects without losing context
- Enable the human to reorganize, rename, or archive content easily
- Support collaboration—human can edit Claude's drafts, Claude can build on human's notes
- Provide version history through Notion's built-in page history

### Integration Layer

#### Tiered Startup Protocol

**Tier 1 (Every Session)**:

A single script, `startup.py`, performs the whole sequence in one call and prints
a consolidated report: verified date and time, weather, market summary, news
headlines, milestone alerts, calendar for today and tomorrow with DONE / NOW /
SOON / LATER classification, task status including overdue items, audit
triggers, health-export status, scheduled-task health, and the previous day's
activity trail. It also starts the session timer and creates the day's running
summary file if one does not already exist.

Claude then fetches Core Protocols and the Memory Base from Notion and reports
the result. Consolidation is the point: the checks happen whether or not the
assistant remembers to make them. See Design Principle 9.

**Tier 2 (Load On-Demand)**:

| Trigger | Load |
|---------|------|
| Substantive project work | Session Lifecycle |
| "Mark [task] complete" | Task Management |
| Research/ideas/"I have an idea" | Knowledge Work |
| Specialized input (e.g., screenshots) | Specialized Workflows |
| First session of week | Check if weekly audit needed |
| Approaching compaction | Session Lifecycle |

**Tier 3 (Explicit Request Only)**:
- Research Library, Work Patterns, Ideas, Recurring Themes, Session Summaries
- Only fetch when session work requires them

**Benefit**: Each session loads only the protocols it needs. Completing a single
task does not pay the cost of loading the research library.

#### Running Summary Protocol

**Purpose**: Preserve session context before compaction erases it.

**File location**: Local markdown files organized by date.

**When to Write**:
- During work (preferred): Brief entries as you work, not just at breakpoints
- At natural breakpoints: More detailed entries
- High token usage (~150K): Update proactively before compaction risk
- Compaction detected: Cross-check transcript against running summary, fill gaps

**Entry Format**:
```markdown
## HH:MM - Brief Topic
What was accomplished. Key decisions. How it connects to goals.
Next: What this enables.
```

#### Task Management

**Python scripts** handle task operations:
- `task_manager.py`: Task completion, rescheduling, status checks
- `date_utils.py`: Date calculations, day-of-week verification

**Workflow**:
1. Run task_manager.py via command line
2. Script updates local CSV
3. Update Notion task page with new due date
4. Both CSV and Notion stay synchronized

#### Script Inventory

Fourteen scripts ship with the reference implementation. Only the first six are
required; the rest extend the startup report or automate a recurring
reconciliation, and each degrades quietly when unconfigured.

**Core**
- `startup.py`: the consolidated daystarter. Calls the helpers below, prints one
  report, starts the session timer, creates the day's running summary file.
- `pwkm_env.py`: shared configuration loader. Standard library only.
- `date_utils.py`: date arithmetic and weekday verification.
- `session_timer.py`: the 30-minute running summary clock and the audit triggers.
- `task_manager.py`: task completion and rescheduling against the CSV.
- `fetch_notion_tasks.py`: exports the Notion tasks database to CSV.

**Calendar**
- `gcal_query.py`: reads the calendar, with `--classify` for DONE / NOW / SOON /
  LATER. Merges secondary calendars, including free/busy-only ones.
- `gcal_create.py`: creates events, used for day planning blocks.

**Startup report sections (each optional)**
- `weather.py`: local forecast from a configured Environment Canada feed.
- `market.py`: index summary and holdings that moved beyond a threshold.
- `news.py`: RSS headlines, with feeds and exclusion filters in a config file.
- `activitywatch.py`: the previous day's activity trail. Tri-state, see Design
  Principle 10.

**Reconciliation**
- `goodreads_sync.py`: reconciles a reading shelf against a Notion database.
- `env_audit.py`: checks the configuration itself and reports what is missing,
  malformed, or set but unused.

#### Configuration

Configuration lives in `scripts/.env`, loaded by `pwkm_env.py`. `.env.example`
documents every variable and, for each one, which script actually reads it.
`env_audit.py` checks a real configuration against that list.

Three rules govern how configuration behaves:

**The real environment wins.** A variable already set in the process environment
takes precedence over the file. The file supplies defaults; it does not override
a deliberate choice made outside it.

**Structured configuration goes in JSON, not `.env`.** Anything with internal
structure, such as the news feed list or the activity category rules, lives in
its own JSON file. An `.example` version ships with the repository and the real
one is gitignored, so personal configuration never reaches a commit.

**Optional means optional, but misconfigured does not.** An optional section that
is simply not configured exits cleanly and is omitted from the report. An
optional section that is configured incorrectly exits non-zero and says why, on
**stderr**, because `startup.py` reads stderr rather than stdout when a helper
fails. Silence and breakage must not look alike.

#### Day Reconciliation

At the close of a working day the session is reconciled against what actually
happened. The activity trail is read as an ordered sequence rather than a
category rollup, because the transitions between kinds of work carry more signal
than the totals. Where the day diverged from what was expected, the reason is
captured from the human and tagged: `exogenous` for an external demand,
`endogenous` for an internal state worth modelling, `discretionary` for a genuine
free choice, and `ambiguous` where a cause is suspected but has not been probed.

The result is appended to the running summary as a YAML block, which keeps it
harvestable later without a migration.

The purpose is a day-planning loop whose rules are discovered rather than
ordained. Rather than setting productivity rules in advance and measuring
compliance, the system accumulates labelled cases and lets the patterns emerge.
This only works if the tags are honest, which is why `ambiguous` exists: a
mislabelled cause is worse than an unlabelled one, because it enters the record
looking like evidence.

---

## The Evolution: How We Got Here

Understanding how this system emerged reveals important lessons about building effective human-AI collaboration systems.

### Phase 1: Initial Setup

**What we did**:
- Created basic PWKM Hub in Notion
- Set up Project Registry (table of active projects)
- Started session summary practice
- Created Ideas and Interests document

**What we learned**:
- Manually tracking projects in a table worked well
- Session summaries proved valuable for continuity
- But context still fragmented across conversations
- Cross-project connections weren't visible

### Phase 2: Context Consolidation

**What we did**:
- Created Memory Base
- Consolidated comprehensive background in single document
- Documented approach, principles, tools, status

**Breakthrough moment**: Realized the Memory Base could be *the* integration point for all project work.

### Phase 3: Protocol Development

**What we did**:
- Implemented comprehensive Session Startup Protocol
- Created Session Summary Protocol with dual indexing
- Implemented Tasks Export Protocol (CSV-based)
- Tested all protocols in practice

**What we learned**:
- Automated startup dramatically improved session efficiency
- Dual indexing (temporal + thematic) better than single index
- CSV export much faster than multiple API calls

### Phase 4: Tiered Architecture

**What we did**:
- Recognized that loading everything every session was wasteful
- Reorganized protocols into modular documents
- Implemented tiered loading based on session type
- Added running summaries for compaction resilience

**Key insight**: Different sessions need different context. A quick task completion doesn't need research library loaded.

### Phase 5: Ongoing Refinement

**Current state (August 2026)**:
- The system is in daily use and has been stable for months
- New projects integrate using the established patterns
- Protocols are still refined regularly, almost always in response to a specific
  failure rather than in the abstract
- A repository review in August 2026 found that the published *setup path* had
  been broken for months in ways the author could not see, because his own
  machine was already configured. The system worked; the instructions for
  building it did not. That is a general hazard for anyone publishing a personal
  system, and it is why the repository now ships a configuration audit script
  (`env_audit.py`)

---

## Key Components Explained

### The Memory Base: Comprehensive Context

#### Structure

The Memory Base is organized into sections:

1. **Purpose & Context** - Who you are, what you do, intellectual focus
2. **Current State** - Active projects, recent developments, immediate context
3. **On the Horizon** - Planned directions, emerging interests
4. **Key Learnings & Principles** - Recurring themes, frameworks, insights
5. **Approach & Patterns** - How you work, preferences, methods
6. **Tools & Resources** - Workflow, access to materials

#### What Gets Included

The Memory Base contains information at different levels of abstraction:

**Concrete facts**:
- Role and professional context
- Active projects and their status
- Timeline and availability

**Intellectual themes**:
- Recurring patterns across your work
- Core intellectual commitments
- Frameworks that guide your thinking

**Working preferences**:
- Depth vs. breadth orientation
- Communication style
- Decision-making principles

**Conceptual frameworks**:
- Key mental models
- Analogies or explanatory devices
- Theoretical foundations

#### How It Evolves

The Memory Base is a "living document" that updates as:
- Major milestones are reached
- New themes are identified
- Conceptual frameworks emerge
- Methods evolve
- Projects shift status

### Context & Resources Pattern

#### The Pattern

Every project page begins with this structure:

```markdown
## Context & Resources

### Core PWKM Documents
- 🧠 Claude Memory Base - Comprehensive background context
- 📋 Core Protocols - Essential workflows

### Related Research
- [Project-specific research documents]
- [Cross-references to related projects]
- [Links to themes and ideas]

### Key Intellectual Themes (from Memory Base)
- [2-4 most relevant themes for this project]
```

#### Why This Works

**Immediate visibility**: Context appears at the top of every project page.

**Explicit connections**: Rather than assuming relationships will be remembered, make them visible and clickable.

**Consistent structure**: Same pattern across all projects reduces cognitive load.

**Single source linkage**: All projects link to the same Memory Base, ensuring consistency.

---

## How It Works in Practice

### Typical Session Flow

#### Starting a Project Session

**You say**: "Working on [Project Name] today"

**Claude does automatically**:
1. Recognizes project mention
2. Fetches Memory Base from Notion
3. Fetches project page from Notion
4. Notes related research
5. Reviews recent session summaries
6. Synthesizes context

**Claude responds**: "I've loaded the [Project] context. [Current status summary]. Where would you like to start?"

**Total time**: ~10 seconds
**Context loaded**: Comprehensive

#### Starting a Full PWKM Session

**You say**: Start the session or trigger startup protocol

**Claude runs Tiered Startup**:
1. Verifies current date
2. Checks calendar
3. Fetches PWKM Hub
4. Runs task status check
5. Presents startup report

**Value**: Complete situational awareness. Nothing forgotten. Ready to work on highest-priority items with full context.

#### Working Across Sessions

**Day 1** - Draft outline:
- Work session on project
- Create outline structure
- Update running summary during work

**Day 4** - Continue drafting:
- "Continuing [Project] work"
- Claude loads Memory Base + Project page
- Notes session history
- "Last time you created the outline. Ready to draft Section 1?"

**Continuity maintained without repeating context each time.**

#### Capturing Ideas

**You say**: "I have an idea about [topic]"

**Claude does** (following Idea Capture Protocol):
1. Asks clarifying questions
2. Explores what sparked it
3. Discusses applications
4. Identifies core theme
5. Documents in Ideas and Interests
6. Suggests connections to active projects

**Idea captured systematically, not lost.**

---

## Template for Adaptation

> **Note**: Ready-to-use Notion templates, Python scripts, protocol documents, and configuration examples are available from the [PWKM GitHub repository](https://github.com/keithmann/pwkm). The templates below describe the structure; the repository provides working implementations you can import directly.

This section provides concrete templates others can use to build similar systems.

### Prerequisites

**Platform Requirements**:
- **Windows** for the shell scripts as published. Administrator access is not needed.
- **Claude Desktop** application, for the local shell server. What decides the
  startup path is whether the `windows-mcp` server is reachable, not which
  interface is in use. A session without it runs a reduced startup that skips
  the local scripts and works through the Notion, calendar, and mail connectors
  instead. That covers web and mobile sessions, and also a Claude Desktop client
  on macOS, which shares project instructions and chat history with the Windows
  client but none of its tools, files, or local state. See the reduced-startup
  section of the core protocols.
- **Python 3.10+** installed and on PATH
- **`uv` / `uvx`**, which runs windows-mcp

**MCP servers and connectors**:
One server is configured locally; the rest are connectors enabled in the Claude interface.
- **windows-mcp** (local): shell commands, Python script execution, local file access
- **Notion** (connector): all Notion integration
- **Gmail / Microsoft 365 / Google Calendar** (connectors, optional)

A filesystem MCP server is **not** required. A calendar MCP server is **not**
required for the startup report: `gcal_query.py` and `gcal_create.py` call the
Google Calendar API directly using OAuth credentials from `.env`. Claude's
calendar connector and the scripts' calendar access are independent paths that
fail independently.

**Accounts and Services**:
- **Notion account** (free tier works fine)
- **A Claude plan supporting Projects and connectors** (plan features have changed over time; check current documentation)
- **Google account** (only if you want calendar in the startup report)

**Other Requirements**:
- **Multiple concurrent projects or work streams** (this system shines with complexity)
- **Willingness to invest setup time** (~4-6 hours) and maintain structure (~15-20 min/week)
- **Commitment to documentation** (the system's value compounds over time)

### Step 1: Create the PWKM Hub

Create a Notion page that will serve as your central hub.

**Recommended structure**:
```markdown
# [Your Name]'s PWKM Hub

Central hub for integrated work and knowledge management system.

---

## Quick Navigation

### Core Documents
- 🧠 Memory Base
- 📋 Protocol Documents
- 💡 Ideas and Interests
- 🌀 Recurring Themes
- 📚 Research Library
- 📊 Work Patterns
- 📋 Session Summaries

### Project Pages
[Links to individual project pages]

---

## Active Projects

[Embed a table database with columns: Project, Priority, Status, Next Deadline]

---

## System Overview

This PWKM system integrates work management (projects, tasks, deadlines) with knowledge management (research, ideas, themes, theory-building) in a unified architecture.
```

### Step 2: Create the Memory Base

This is the most important document. Take time to make it comprehensive.

**Template**:
```markdown
# Memory Base

Central reference document containing structured knowledge about [your name] and their work.

**Last Updated**: [Date]

---

## Purpose & Context

[Who you are, what you do, your role]
[Your core intellectual focus or mission]
[Scope of your work]

---

## Current State

[Active projects - list them]
[Recent developments - what's happening now]
[Current priorities]

---

## On the Horizon

[Planned work]
[Emerging interests]
[Future directions]

---

## Key Learnings & Principles

### Recurring Intellectual Themes

[Identify 3-5 themes that appear across your work]

### Notable Conceptual Frameworks

[Key mental models or frameworks you use]

---

## Approach & Patterns

### How You Work

[Your working methods]
[Preferences]
[Communication style]

### Practical Details

[Timezone, schedule constraints]
[Current availability]

---

## Tools & Resources

[What tools you use]
[How they fit together]
[Resource access]

---

## Usage Guidelines

[How to use this document]
[When to update it]
```

### Step 3: Create Protocol Documents

Organize protocols into modular documents for tiered loading.

**Core Protocols** (always loaded):
- Date handling requirements
- Task status check commands
- Memory Base maintenance guidelines
- Session startup essentials

**Session Lifecycle** (on-demand):
- Running summary protocol
- Compaction detection and handling
- Session documentation standards

**Task Management** (on-demand):
- Task completion workflow
- Recurring task patterns
- CSV/Notion synchronization

**Knowledge Work** (on-demand):
- Idea capture protocol
- Research documentation
- Theme identification

### Step 4: Create Project Page Template

```markdown
# [Project Name]

**Status**: [Status]
**Priority**: [High/Medium/Low]
**Last Updated**: [Date]

---

## Context & Resources

### Core PWKM Documents
- [Link to Memory Base]
- [Link to Core Protocols]

### Related Research
- [Links to related materials]

### Key Intellectual Themes
- [Relevant themes from Memory Base]

---

## Project Overview

[What this project is about]
[Why it matters]

---

## Current Status

[What you've done recently]
[Current state]

---

## Next Steps

[What needs to happen next]
[Open questions]

---

## Session History

[Links to session summaries]
```

### Step 5: Set Up Task Management

1. Create Tasks database in Notion
2. Set up Python scripts for task operations
3. Configure CSV export for efficient status checks
4. Document the workflow in Task Management protocol

### Step 6: Configure the Scripts

The scripts are written to be environment-neutral, so nearly everything specific
to you is a configuration value rather than an edit.

1. Copy `scripts/.env.example` to `scripts/.env`
2. Fill in what applies: Notion integration token and database identifiers,
   Google Calendar credentials, your timezone, your location for weather, any
   secondary calendars using the `Label=Value` syntax
3. Copy the `.example` JSON files alongside them and edit those for anything with
   internal structure, such as news feeds and activity categories
4. Leave anything you do not want blank. Unconfigured optional sections are
   omitted from the startup report rather than failing
5. Run `env_audit.py` and resolve what it reports
6. Confirm `.env` and your real JSON config files are gitignored before your
   first commit

### Step 7: Start Using and Refining

**Week 1**: Focus on structure
- Create the core documents
- Set up first project pages
- Begin running summary practice

**Week 2**: Focus on patterns
- Notice what questions get asked repeatedly
- Start documenting workflows as protocols

**Week 3**: Focus on connections
- Add cross-references between projects
- Identify emerging themes

**Week 4**: Focus on refinement
- Adjust structure based on what works
- Optimize for your actual workflow

---

## Lessons Learned

### 1. Structure Enables Flexibility

Good structure reduces cognitive load on routine aspects, freeing mental energy for creative work.

### 2. Explicit is Better Than Implicit

Make connections and context visible rather than assuming they'll be remembered. Both humans and AI benefit from explicit structure.

### 3. Single Source of Truth Matters

One authoritative place for each piece of information reduces errors and time spent searching.

### 4. Protocols Beat Ad Hoc

Documented workflows are more efficient than reinventing process each time.

### 5. Emergence Over Design

Let structure emerge from practice rather than imposing predetermined frameworks.

### 6. Integration Beats Automation

The goal is enhancing collaboration, not automating humans away.

### 7. Context Persistence is Valuable

Preserving context across sessions multiplies effectiveness.

### 8. Tiered Loading Saves Resources

Not every session needs every protocol. Load what's needed.

### 9. Running Summaries Beat Reconstruction

Notes written during work are more reliable than notes reconstructed after the fact.

### 10. The System Must Serve the Work

Regularly ask "is this helping?" Prune what doesn't serve the work.

---

## Theoretical Foundations

### Systems Thinking (Russell Ackoff)

**Key principle**: Understand things through their context and relationships, not by decomposing them into parts.

**Application**: Hub-and-spoke architecture provides context for understanding individual projects. Each project is understood through its relationships rather than in isolation.

### Theory-Building (Peter Naur / Gilbert Ryle)

**Key principle**: Knowledge work is about building and maintaining theories in human minds, not just producing artifacts.

**Application**: Memory Base captures not just facts but understanding—the theories that guide the work.

### Situated Action (Lucy Suchman)

**Key principle**: Action is situated in context; plans are resources for action, not determinants.

**Application**: Flexible protocols provide guidance but adapt to situation. They're resources, not rigid scripts.

### Cognitive Load Theory

**Key principle**: Working memory is limited; reduce extraneous load to free capacity for germane processing.

**Application**: External structure in Notion reduces burden on working memory. Consistent patterns mean one approach to remember, not many.

### Distributed Cognition (Hutchins)

**Key principle**: Cognition happens across people and artifacts, not just in individual minds.

**Application**: The system distributes cognition across human, AI, and documents. Capabilities emerge from the interaction.

### The Memex Vision (Vannevar Bush)

**Key principle**: Enable associative trails through information that mirror how humans think.

**Application**: Context & Resources creates trails between related materials. The link structure supports associative thinking.

---

## Future Directions

### Potential Enhancements

1. **Automated Theme Detection**: AI analysis of session summaries to suggest emerging themes
2. **Work Pattern Analysis**: Systematic analysis of productivity patterns over time
3. **Research Synthesis**: AI-assisted synthesis across readings
4. **Project Health Monitoring**: Automatic detection of projects needing attention
5. **Cross-Project Recommendation**: Proactive suggestions for synthesis opportunities

### Open Questions

1. How does this scale beyond one person?
2. What's the right level of structure?
3. How to handle deprecated projects?
4. Integration with other tools?
5. How to measure effectiveness?

---

## Conclusion

### What We've Built

The system has four load-bearing parts:

**Foundation**: Memory Base provides comprehensive persistent context
**Structure**: Hub-and-spoke with consistent project patterns
**Integration**: Tiered protocols and natural language enable smooth workflow
**Theory**: Grounded in systems thinking, cognitive science, knowledge management

### Why It Matters

This demonstrates:
- **AI as cognitive partner**: Not replacing humans but augmenting capability
- **Architecture over automation**: Structure that supports collaboration
- **Theory-grounded design**: Principles from cognitive science work in practice
- **Work-knowledge integration**: Unified management of projects and understanding

### The Broader Principle

**Persistent context** + **Explicit structure** + **Flexible protocols** + **Work-knowledge integration** = **Effective human-AI collaboration**

This pattern applies regardless of specific tools. The principles translate.

---

## License and Usage

This document and associated materials are part of the PWKM reference implementation.

**Code and Scripts**: Custom license allowing personal and internal business use. Commercial redistribution prohibited without permission.

**Documentation and Templates**: Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0).

The PWKM methodology, architecture, and associated concepts remain the intellectual property of the author. This release provides a reference implementation for personal use but does not transfer rights to the underlying methodology.

For commercial licensing inquiries, contact the author.

---

**Document Version**: 5.0
**Original Date**: December 24, 2025
**Updated**: August 13, 2026

**Changes in v5.0**:

A review found that the document had drifted from the system it describes. Some
of the drift was factual and some was tonal.

*Corrections*
- The version block itself, which still claimed February 2026 after the document
  had been edited in August
- Removed the novelty claim from the Abstract, and the self-assessment from the
  Conclusion and from Phase 5. The Phase 5 status is now dated and records the
  August 2026 finding that the published setup path had been broken for months
- Resolved a contradiction between Design Principle 9 and the Tiered Startup
  section, which still described the manual sequence that `startup.py` replaced
- Corrected the stated rationale for the CSV task export, which cited a Notion
  limitation that no longer exists
- Removed an unverifiable token-count figure
- Corrected the reduced-startup description. The startup path is decided by
  whether `windows-mcp` is reachable, not by which interface is in use, and it
  covers a macOS desktop client as well as web and mobile sessions

*Additions*
- Design Principle 10, Configuration Over Forking, with the tri-state treatment
  of absence
- A Script Inventory covering all fourteen published scripts. Six of them were
  undocumented here, though they appeared in the repository README
- A Configuration section covering `.env`, the shared loader, precedence,
  structured JSON configuration, and the conventions that keep an unconfigured
  section distinguishable from a broken one
- A Day Reconciliation section
- Step 6 of the adaptation template. The template previously ran from hub
  creation to daily use without a configuration step

**Changes in v4.0**:
- Added consolidated startup via `startup.py` (replaces multi-step manual sequence)
- Added mechanical enforcement principle and `session_timer.py`
- Added calendar-aware classification (`gcal_query.py --classify`)
- Updated running summary protocol with proactive triggers and externalized clock
- Added `date_utils.py` nth-weekday calculations for recurring task patterns
- Updated task_manager.py with task-name pattern parsing
- Added weekly audit and monthly review tracking via persistent state files

**Changes in v3.0**:
- Reorganized for tiered protocol architecture
- Added running summary protocol
- Updated to reflect modular protocol documents
- Genericized examples for broader applicability
- Updated licensing for open-source release
- Streamlined theoretical foundations section
