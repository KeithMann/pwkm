# Claude Desktop MCP Setup

This guide walks through configuring Claude Desktop with the MCP servers required for PWKM.

## Prerequisites

- Claude Desktop application installed
- Node.js 18+ (for npx commands)
- Python 3.10+ with uvx (for Windows MCP)
- Notion account with API access
- Google account (for calendar integration)

## Configuration Location

Claude Desktop configuration file location:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

## Step 1: Create Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "New Integration"
3. Name it (e.g., "PWKM Claude Integration")
4. Select your workspace
5. Copy the "Internal Integration Token"
6. In Notion, share your PWKM pages with this integration

## Step 2: Set Up Google Calendar (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable the Google Calendar API
4. Create OAuth 2.0 credentials
5. Note your Client ID and Client Secret

## Step 3: Configure Claude Desktop

1. Copy `config-example.json` to your Claude Desktop config location
2. Replace placeholder values:
   - `YOUR_NOTION_API_KEY` → Your Notion integration token
   - `YOUR_USERNAME` → Your Windows username
   - `YOUR_GOOGLE_CLIENT_ID` → Google OAuth Client ID
   - `YOUR_GOOGLE_CLIENT_SECRET` → Google OAuth Client Secret

3. Adjust filesystem paths to match your setup

## Step 4: Verify Installation

1. Restart Claude Desktop
2. Start a new conversation
3. Ask Claude to verify MCP connections:
   - "Can you access Notion?"
   - "Can you read local files?"
   - "What's on my calendar today?"

## MCP Server Reference

### Notion MCP
- **Purpose**: Read/write Notion pages and databases
- **Required for**: Memory Base, project pages, task database

### Filesystem MCP
- **Purpose**: Read/write local files
- **Required for**: Running summaries, CSV exports, scripts

### Windows MCP
- **Purpose**: Execute shell commands, desktop automation
- **Required for**: Running Python scripts, system commands

### Google Calendar MCP
- **Purpose**: Read calendar events
- **Required for**: Session startup calendar check

## Troubleshooting

### "MCP server not found"
- Ensure Node.js is installed and `npx` is in PATH
- Try running the npx command manually in terminal

### "Permission denied" on filesystem
- Check that paths in config are within allowed directories
- Use forward slashes or escaped backslashes in paths

### Notion connection fails
- Verify API key is correct
- Ensure pages are shared with the integration
- Check Notion-Version header matches

## Security Notes

- Never commit your actual config file with API keys
- Store sensitive values in environment variables if possible
- The config-example.json uses placeholders intentionally
