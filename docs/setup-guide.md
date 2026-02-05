# PWKM Setup Guide

This guide walks you through setting up your own PWKM system from scratch.

## Prerequisites

Before starting, ensure you have:

- **Windows 11** (macOS/Linux possible with modifications)
- **Python 3.10+** installed and accessible from command line
- **Claude Desktop** application installed
- **Notion account** (free tier works fine)
- **Claude Pro or Team subscription** (for extended conversations)

## Step 1: Set Up Notion

### Create Your PWKM Workspace

1. Log into Notion and create a new page called "PWKM Hub"
2. This will be your central navigation point

### Import the Core Structure

Using the templates in the `notion/` directory of this repository:

1. **Hub**: Create the hub structure following `notion/hub-template.md`
2. **Memory Base**: Create a Memory Base page using `notion/memory-base-template.md`
3. **Tasks Database**: Create a Tasks & To-Dos database using `notion/tasks-database-template.csv` as a reference for the schema

### Create Your First Project

1. Under your Hub, create a "Projects" section
2. Add your first project page using `notion/project-template.md` as a template
3. Link the project from your Hub

### Set Up Notion Integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Name it "PWKM" or similar
4. Copy the "Internal Integration Secret" — this is your API key
5. Go to each PWKM page/database in Notion
6. Click "..." menu → "Add connections" → Select your integration

## Step 2: Install Python Dependencies

```bash
pip install requests python-dateutil tzdata
```

## Step 3: Configure the Scripts

1. Copy the `scripts/` folder to a permanent location, e.g.:
   - Windows: `C:\Users\YOUR_USERNAME\AppData\Roaming\Claude\scripts\`
   - macOS/Linux: `~/.config/claude/scripts/`

2. Create your `.env` file:
   ```bash
   cd /path/to/scripts
   cp .env.example .env
   ```

3. Edit `.env` with your credentials:
   ```
   NOTION_API_KEY=your_notion_api_key_here
   NOTION_DATABASE_ID=your_tasks_database_id_here
   ```

   To find your database ID: Open your Tasks database in Notion, look at the URL:
   `https://notion.so/YOUR_DATABASE_ID?v=...`

4. Test the script:
   ```bash
   python fetch_notion_tasks.py
   ```
   
   You should see output like:
   ```
   Fetching tasks from Notion...
   Found 15 tasks
   Successfully exported 15 tasks to notion_tasks.csv
   ```

## Step 4: Set Up Claude Desktop

### Install MCP Servers

PWKM requires these MCP servers configured in Claude Desktop:

1. **Notion MCP** — For reading/writing Notion pages
2. **Filesystem MCP** — For accessing local files (task CSV, scripts)
3. **Windows MCP** (optional) — For system automation on Windows

### Configure Claude Desktop

1. Locate your Claude Desktop config file:
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. Add MCP server configurations. See `claude-desktop/config-example.json` for a template.

3. Restart Claude Desktop

### Verify MCP Access

Start a new conversation and ask Claude:
- "Can you read my Notion pages?"
- "Can you access files in [your scripts directory]?"

If both work, your MCP setup is complete.

## Step 5: Create Your Protocols

Protocols are instruction documents that tell Claude how to work with your system.

### Core Protocols

Create a "Core Protocols" page in Notion with:
- Date verification requirements
- Task management procedures
- Session startup checklist

See `protocols/core-protocols.md` for a template.

### Session Lifecycle

Create a "Session Lifecycle" page covering:
- Session startup procedure
- Session handoff/summary requirements
- Compaction handling

See `protocols/session-lifecycle.md` for a template.

## Step 6: Configure Your Memory Base

The Memory Base is where Claude stores persistent context about you and your work.

1. Open your Memory Base page in Notion
2. Add sections for:
   - **Purpose & Context**: Your role, responsibilities, key projects
   - **Current State**: What you're actively working on
   - **Key Learnings**: Important insights and decisions
   - **Tools & Resources**: File paths, credentials locations, workflows

3. Note the Notion page ID (from the URL) — you'll reference this in protocols

## Step 7: Schedule Task Sync

For best results, run `fetch_notion_tasks.py` automatically each day.

See `docs/scheduling-fetch-tasks.md` for detailed instructions on:
- Windows Task Scheduler setup
- macOS/Linux cron setup
- Manual execution

## Step 8: First Session

You're ready! Start a conversation with Claude and try:

```
Let's start a PWKM session. Please:
1. Fetch my Memory Base from Notion (page ID: YOUR_PAGE_ID)
2. Check my task status
3. Review my calendar for today
```

See `examples/first-session.md` for a complete example of a first session.

## Troubleshooting

### Claude can't access Notion
- Verify your Notion integration has access to the relevant pages
- Check that the Notion MCP server is configured correctly
- Ensure your API key is valid

### Task script fails
- Check that `.env` file exists and has correct values
- Verify Python can reach the internet
- Ensure the Notion integration has access to your Tasks database

### MCP servers not loading
- Restart Claude Desktop after config changes
- Check config file JSON syntax
- Review Claude Desktop logs for errors

## Next Steps

Once your basic setup is working:

1. Read `docs/usage-guide.md` for daily workflow patterns
2. Read `docs/customization.md` for adapting PWKM to your needs
3. Explore the `protocols/` directory for additional protocol templates
