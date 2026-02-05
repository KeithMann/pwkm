# PWKM Usage Guide

This guide covers daily workflows and patterns for using PWKM effectively.

## Session Types

PWKM supports different session types, each with appropriate context loading:

### Quick Check Sessions

For brief interactions (task updates, quick questions):

```
Quick check - just need to update a task status.
```

Claude will:
- Verify the current date
- Load task data
- Skip heavy context loading

### Standard Work Sessions

For typical work sessions:

```
Starting a work session. Please run the standard startup.
```

Claude will:
- Verify date
- Fetch Memory Base
- Check calendar
- Run task status
- Load relevant project context

### Deep Work Sessions

For focused project work:

```
Deep work session on [Project Name]. Load full context.
```

Claude will:
- Run standard startup
- Fetch the specific project page
- Load any project-specific protocols
- Review recent session summaries for that project

## Daily Workflow

### Morning Startup

1. Start a new conversation
2. Share your work calendar (screenshot or list)
3. Ask for startup:
   ```
   Good morning. Here's my calendar for today. Please run startup.
   ```

4. Claude provides:
   - Tasks due today/tomorrow/overdue
   - Calendar overview
   - Suggested priorities

### During the Day

**Task Completion:**
```
I finished the quarterly report task.
```
Claude updates both Notion and the local CSV.

**Quick Questions:**
```
What's the status of the Foo project?
```
Claude retrieves from Memory Base or project page.

**Research/Analysis:**
```
I need to analyze the vendor responses. Let's work through them.
```
Claude loads relevant context and collaborates.

### Session Handoff

When ending a session or before context gets full:

```
Let's do a session summary before we wrap up.
```

Claude creates a summary including:
- What was accomplished
- Decisions made
- Open items
- Cross-project connections discovered
- Suggested Memory Base updates

## Working with Tasks

### Checking Status

```
What tasks are due this week?
```

```
Show me overdue tasks.
```

```
What's on my plate for today?
```

### Creating Tasks

```
Add a task: "Review vendor proposal" due Friday, high priority, work category.
```

### Completing Tasks

```
Mark "Weekly report" as done.
```

For recurring tasks, Claude automatically calculates the next due date.

### Rescheduling

```
Push the "Quarterly review" task to next Monday.
```

## Working with Projects

### Project Updates

```
Let's update the project status for the Foo project.
```

Claude fetches the project page and helps you update milestones, status, and notes.

### Cross-Project Synthesis

```
Are there any connections between my Bar research and the Foo project?
```

Claude reviews both projects and identifies thematic links.

### Project Planning

```
Help me plan the next phase of the Foo project.
```

Claude loads project context and collaborates on planning.

## Working with Knowledge

### Capturing Insights

When you have an insight during conversation:

```
This is important - let's capture this in the Memory Base under Key Learnings.
```

### Research Sessions

```
I need to research the history of foobar. Let's build an annotated bibliography.
```

Claude helps with web searches, source evaluation, and knowledge capture.

### Theory Building

```
I've been thinking about the relationship between foo and bar. Let's explore this.
```

Claude engages as a thinking partner, helping develop and refine ideas.

## Handling Long Conversations

### Context Awareness

Claude monitors context usage. When approaching limits:

```
We're getting close to context limits. Should we summarize and continue in a new session?
```

### Compaction Recovery

If the conversation compacts (context overflow), Claude will:
1. Recognize the compaction occurred
2. Fetch Memory Base to restore context
3. Review the compaction summary
4. Continue work with minimal disruption

### Multi-Session Projects

For work spanning multiple sessions:

1. End each session with a summary
2. Start the next session referencing the previous:
   ```
   Continuing our work on the vendor analysis from yesterday.
   ```
3. Claude loads relevant context and picks up where you left off

## Calendar Integration

### Sharing Your Calendar

Screenshot your calendar or paste the schedule:

```
Here's my calendar for today:
9:00 - Team standup
10:00 - Client call: Acme Corp
12:00 - Lunch
2:00 - Vendor call: TechCo
```

### Calendar-Aware Planning

```
Given my calendar, when should I work on the proposal?
```

Claude identifies free blocks and suggests scheduling.

## Tips for Effective Use

### Be Explicit About Context Needs

Instead of: "Let's work on my project"
Say: "Let's work on the Foo project. Please load the project page."

### Use Session Types Appropriately

Don't load full context for a quick task update. Don't skimp on context for deep work.

### Maintain Your Memory Base

Periodically review and update your Memory Base:
```
Let's review the Memory Base and update anything that's changed.
```

### Trust the System

PWKM is designed to handle context management. Let Claude:
- Decide what to load based on session type
- Manage task state across systems
- Track cross-project connections

### Provide Feedback

When something doesn't work well:
```
That startup took too long. Let's streamline it for quick sessions.
```

Help refine the protocols based on actual usage.

## Common Patterns

### Monday Planning

```
It's Monday. Let's review the week ahead - calendar, tasks, and project priorities.
```

### Friday Wrap-up

```
End of week. Let's summarize what got done and set up for next week.
```

### Project Milestone Check

```
The Foo project is due in 6 weeks. Let's review the timeline and make sure we're on track.
```

### Research Deep Dive

```
I have 2 hours blocked for research. Let's make progress on the Bar notes.
```

## Troubleshooting

### Claude Seems to Have Lost Context

```
You seem to have lost context. Please fetch the Memory Base and let's resync.
```

### Task Data Seems Stale

```
When was the task CSV last updated? Let's refresh it.
```

### Protocol Not Being Followed

```
You skipped the date verification. Please follow the protocol.
```

Claude will acknowledge and correct.
