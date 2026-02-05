# Customizing PWKM

PWKM is a reference implementation designed to be adapted to your specific needs. This guide covers common customizations.

## Philosophy of Customization

PWKM embodies certain principles, but the specific implementation should fit your work:

**Keep:**
- Single source of truth (Notion as authoritative)
- Protocol-driven consistency
- Separation of work management and knowledge management
- Human-AI collaboration (not automation)

**Adapt:**
- Specific protocols and checklists
- Database schemas and properties
- Session types and workflows
- Tool integrations

## Customizing the Hub

### Adding Sections

The hub template includes common sections, but add what you need:

- **Reading List**: Track books, papers, articles
- **Contacts**: Key people and relationships
- **Reference**: Quick-access information
- **Archives**: Completed projects, historical data

### Removing Sections

If you don't need certain sections (e.g., you don't do research), remove them. A simpler hub is easier to maintain.

### Hub Views

Consider adding filtered views:
- Active projects only
- This week's priorities
- Stalled items needing attention

## Customizing the Task System

### Database Properties

The reference implementation includes:
- Task Name (title)
- Due Date
- Category (Work/Personal/Household)
- Frequency (One-time, Weekly, Monthly, etc.)
- Priority (High/Medium/Low)
- Status (To Do/In Progress/Done)

**Add properties for your needs:**
- Project (relation to projects database)
- Estimated time
- Energy level required
- Context/location
- Delegated to

**Remove properties you don't use.** Simpler is better.

### Categories

Customize categories to match your life:
- Work / Personal / Side Project
- Client A / Client B / Internal
- Health / Finance / Learning / Social

### Frequencies

Add recurring patterns you actually use:
- Biweekly
- First Monday of month
- Quarterly
- Annual

Update `date_utils.py` to handle new patterns.

### Task Views

Create Notion views for your workflow:
- Today's tasks
- This week
- By project
- By category
- Waiting/blocked items

## Customizing Protocols

### Protocol Structure

Each protocol should include:
1. **Purpose**: Why this protocol exists
2. **When to use**: Trigger conditions
3. **Steps**: What to do
4. **Verification**: How to confirm it worked

### Creating New Protocols

Common additions:
- **Email processing**: Daily inbox review workflow
- **Meeting prep**: Before important meetings
- **Weekly review**: End-of-week reflection
- **Monthly planning**: Longer-term planning cadence
- **Project kickoff**: Starting new projects

### Modifying Existing Protocols

Start with the reference protocols, then:
1. Use them as-is for a few weeks
2. Note friction points
3. Adjust incrementally
4. Document why you changed things

### Protocol Loading Strategy

The tiered loading approach:
- **Always load**: Core protocols, date verification
- **Standard sessions**: Memory Base, task status
- **On-demand**: Project-specific, specialized workflows

Adjust tiers based on your typical session patterns.

## Customizing the Memory Base

### Sections

The reference includes:
- Purpose & Context
- Current State
- On the Horizon
- Key Learnings
- Tools & Resources

**Add sections like:**
- Communication preferences
- Decision log
- Recurring meeting notes
- Personal principles/values

### Update Cadence

Decide how often to update each section:
- **Daily**: Current state, active work
- **Weekly**: On the horizon, learnings
- **Monthly**: Purpose, tools, principles

### Memory Base Size

Keep it focused. If the Memory Base gets too large:
- Archive older learnings
- Summarize instead of listing everything
- Create separate pages for deep topics (linked, not inline)

## Customizing for Your Tools

### Different Note Systems

**Obsidian instead of Notion:**
- Use markdown files instead of Notion pages
- Filesystem MCP for all access
- Adapt database concepts to folder structures or frontmatter

**Roam/Logseq:**
- Leverage bidirectional links
- Adapt protocols for outline-based structure

### Different Calendars

**Outlook:**
- Modify calendar integration approach
- Screenshot workflow may differ

**Apple Calendar:**
- Use appropriate MCP or API access

### Different Task Managers

**Todoist/Things/TickTick:**
- Adapt scripts for their APIs
- Modify task properties to match
- May need different CSV schema

## Customizing Scripts

### Adding Scripts

Common additions:
- Email summary fetcher
- Meeting notes template generator
- Time tracking integration
- Backup/export utilities

### Modifying Existing Scripts

**fetch_notion_tasks.py:**
- Add/remove properties
- Change sort order
- Filter by status or category
- Output to different location

**task_manager.py:**
- Add commands (archive, defer, delegate)
- Modify completion behavior
- Add reporting features

**date_utils.py:**
- Add timezone support for your location
- Add custom recurring patterns
- Modify date formats

### Script Location

Keep scripts where Claude can access them via Filesystem MCP. Common locations:
- With Claude Desktop config
- In a dedicated tools directory
- In the PWKM repo (for version control)

## Customizing Session Patterns

### Session Types

Create types that match your work:
- **Sprint planning**: Start of sprint
- **Client prep**: Before client meetings
- **Creative session**: Writing, design work
- **Admin block**: Email, expenses, scheduling

### Startup Sequences

Customize what loads for each session type:

| Session Type | Memory Base | Tasks | Calendar | Project |
|--------------|-------------|-------|----------|---------|
| Quick check  | No          | Yes   | No       | No      |
| Standard     | Yes         | Yes   | Yes      | No      |
| Deep work    | Yes         | Yes   | Yes      | Yes     |
| Planning     | Yes         | Yes   | Yes      | All     |

### Time-Based Patterns

Build protocols around your schedule:
- Morning routine
- Post-lunch reset
- End-of-day wrap
- Weekend review

## Advanced Customizations

### Multiple Workspaces

If you have separate contexts (day job + side project):
- Separate Notion workspaces
- Separate Memory Bases
- Context-switching protocol

### Team Adaptation

Adapting PWKM for team use:
- Shared vs. personal Memory Bases
- Project handoff protocols
- Collaborative task management

### Integration Depth

Start simple, add integrations as needed:
1. Basic: Notion + Filesystem
2. Standard: Add Calendar
3. Advanced: Add email, Slack, time tracking
4. Full: Custom APIs, automation

## Migration Path

### From Existing Systems

1. **Inventory** your current tools and workflows
2. **Map** them to PWKM concepts
3. **Migrate** incrementally (one area at a time)
4. **Parallel run** old and new systems briefly
5. **Retire** old systems once confident

### Evolving Your PWKM

Your system will evolve. Plan for it:
- Version your protocols
- Document changes and why
- Review quarterly: what's working, what's not
- Prune unused features

## Getting Help

### Community

Share your customizations and learn from others:
- GitHub discussions on the PWKM repo
- Claude/AI productivity communities

### Debugging

When something doesn't work:
1. Check if it's a tool issue (MCP, API) or protocol issue
2. Simplify to isolate the problem
3. Test components individually
4. Review recent changes

### Contributing Back

If you develop useful customizations:
- Consider contributing to the reference repo
- Document your approach for others
- Share what worked and what didn't
