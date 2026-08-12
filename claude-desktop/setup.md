# Claude Desktop MCP Setup

PWKM needs far less local configuration than it once did. Most of what used to
require a locally-installed MCP server is now supplied by Claude's built-in
connectors, which you enable in the Claude interface rather than in a config
file.

**This repository's `config-example.json` therefore contains exactly one
server.** If you have seen an older version listing four, that configuration
no longer reflects a working setup, and two of its package names never existed.

## What comes from where

| Capability | How you get it |
|---|---|
| Notion pages and databases | Built-in Notion connector, enabled in Claude |
| Email | Built-in Gmail or Microsoft 365 connector |
| Calendar (for Claude to read directly) | Built-in Google Calendar connector |
| Running shell commands and scripts | **windows-mcp**, configured locally |
| Calendar (for the PWKM scripts) | Not an MCP server at all. `gcal_query.py` and `gcal_create.py` talk to the Google Calendar API directly using OAuth credentials in `.env`. |

That last row is the one people get wrong. The scripts do not go through a
calendar MCP server, so you do not need one for PWKM's startup report to
include your calendar. You need Google OAuth credentials in `.env`.

## Prerequisites

- Claude Desktop installed
- Python 3.10 or newer
- `uv` / `uvx` installed, which is what runs windows-mcp
- A Notion account
- A Google account, only if you want calendar in the startup report

## Configuration location

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

## Step 1: Enable the connectors

In Claude, enable the connectors you want. At minimum, Notion. This is done in
the interface, not in a config file, and it is where the majority of PWKM's
integration now comes from.

In Notion, share your PWKM pages with the connection so it can see them. A
page that has not been shared is invisible rather than forbidden, which reads
as an empty workspace rather than an error.

## Step 2: Configure windows-mcp

Copy `config-example.json` into your Claude Desktop config location, or merge
its `mcpServers` block into the file if you already have one. There are no
placeholders to replace.

```json
{
  "mcpServers": {
    "windows-mcp": {
      "command": "uvx",
      "args": ["windows-mcp"]
    }
  }
}
```

Restart Claude Desktop afterwards.

## Step 3: Google OAuth, if you want calendar in the startup report

1. Go to the [Google Cloud Console](https://console.cloud.google.com)
2. Create a project, or select an existing one
3. Enable the Google Calendar API
4. Create OAuth 2.0 credentials, type **Desktop app**
5. Put the client ID and secret in `scripts/.env` as `GOOGLE_CLIENT_ID` and
   `GOOGLE_CLIENT_SECRET`

The first run of `gcal_query.py` opens a browser to authorize. Run it from a
normal terminal for that first run, not through Claude, since it needs a
browser it can hand you.

## Step 4: Verify

Restart Claude Desktop, start a conversation, and check the two halves
separately, because they fail independently:

- **Connectors:** ask Claude to fetch a specific Notion page by ID.
- **windows-mcp:** ask Claude to run `python --version` in a shell.

Then run the startup script itself. Sections whose optional helper scripts are
absent will say so and the run will continue; that is expected, not a failure.

## Troubleshooting

**windows-mcp does not appear.** Confirm `uvx` is installed and on PATH by
running `uvx --version` in a terminal. Then restart Claude Desktop fully;
reloading the window is not enough.

**Claude says it has no shell access even though windows-mcp is configured.**
Tools are often deferred until searched for. See the Adaptive Tool Loading
section of `protocols/core-protocols.md`. This is the single most common
false negative in setup.

**Notion returns nothing for a page you can see.** The page is probably not
shared with the connection. Sharing is per-page and inherited by children, so
share the top of your PWKM tree.

**Calendar works in Claude but not in the startup report, or vice versa.**
These are two independent paths. The connector serves Claude; `.env`
credentials serve the scripts. Fixing one does not fix the other.

## Security notes

- Never commit your real config file or your `.env`
- `.env` holds live credentials; `.env.example` holds placeholders
- Check `.gitignore` covers `.env` before your first commit