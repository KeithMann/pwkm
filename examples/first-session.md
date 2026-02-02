# First Session Guide

What to expect and how to structure your first PWKM session with Claude.

---

## Before You Start

Ensure you have:
- [ ] Claude Desktop installed with MCP servers configured
- [ ] Notion workspace with PWKM Hub created
- [ ] Memory Base document with initial content
- [ ] At least one project page created
- [ ] Tasks database with a few sample tasks

---

## Starting the Session

### Option 1: Full Startup (Recommended)

Say to Claude:
> "Let's start a PWKM session. Please run the startup protocol."

Claude will:
1. Verify the current date
2. Check your calendar
3. Load the PWKM Hub
4. Check task status
5. Present a startup summary

### Option 2: Project-Focused Start

Say to Claude:
> "I'm working on [Project Name] today."

Claude will:
1. Load your Memory Base
2. Fetch the project page
3. Summarize current status
4. Ask where you'd like to start

---

## What to Expect

### First Time Loading
Claude will read through your Memory Base and project pages. This takes a moment but provides comprehensive context.

### The Startup Report
You'll see something like:
```
## Session Startup - February 2, 2026

**Calendar**: Team meeting 2-3pm, dentist 5pm

**Tasks**:
- Overdue: None
- Due Today: Weekly review
- This Week: Project milestone (Feb 5)

**Ready to work on**: Based on your priorities, 
the project milestone seems most urgent.
```

---

## Working Through the Session

### Making Progress
As you work, Claude maintains context about:
- What you've discussed
- Decisions made
- Where you are in the project

### Capturing Work
Periodically, Claude may update:
- The project page with progress
- Running summary with session notes
- Tasks as they're completed

### Asking Questions
Feel free to ask Claude about:
- "What did we decide about X?"
- "How does this connect to [other project]?"
- "What's the status of [task]?"

---

## Ending the Session

### Quick End
> "That's all for now."

Claude will summarize what was accomplished.

### Documented End
> "Let's wrap up this session."

Claude will:
1. Update running summary
2. Note any open items
3. Suggest next steps
4. Update relevant Notion pages

---

## Common First Session Activities

### Option A: System Setup
- Review and refine Memory Base
- Create additional project pages
- Set up task database

### Option B: Real Work
- Pick highest priority project
- Work on actual deliverable
- Experience the context-loading in action

### Option C: Exploration
- Ask Claude about the system
- Try different commands
- Understand the protocols

---

## Tips for Success

1. **Be patient** with first-time loading—context is being built
2. **Speak naturally**—Claude understands intent
3. **Update as you go**—keeping Notion current compounds value
4. **Ask for clarification** if Claude seems off-track
5. **Provide feedback**—helps Claude calibrate

---

## Troubleshooting

### "Claude doesn't see my Notion pages"
- Check that pages are shared with the Notion integration
- Verify API key in Claude Desktop config

### "Context seems incomplete"
- Try explicitly asking Claude to load Memory Base
- Check that Memory Base is linked in PWKM Hub

### "Tasks aren't showing"
- Verify CSV file path in task_manager.py
- Run `python task_manager.py list` to check

---

## Next Steps After First Session

1. Refine Memory Base based on what Claude needed to know
2. Add more projects if relevant
3. Begin running summary practice
4. Explore tiered protocol loading
