# Scheduling fetch_notion_tasks.py

The `fetch_notion_tasks.py` script exports your Notion Tasks & To-Dos database to a local CSV file. For best results, run this script automatically each day so Claude always has current task data.

## Prerequisites

1. Python 3.8+ installed
2. Required packages: `pip install requests python-dateutil tzdata`
3. A `.env` file configured with your Notion API credentials (see `scripts/.env.example`)

## Windows Task Scheduler

### Create a Scheduled Task

1. Open **Task Scheduler** (search for it in Start menu)
2. Click **Create Basic Task** in the right panel
3. Configure:
   - **Name:** PWKM Fetch Notion Tasks
   - **Description:** Daily export of Notion tasks to CSV
   - **Trigger:** Daily, at a time before you typically start work (e.g., 6:00 AM)
   - **Action:** Start a program

4. For the program/script, enter your Python path:
   ```
   C:\Users\YOUR_USERNAME\AppData\Local\Microsoft\WindowsApps\python.exe
   ```

5. For arguments:
   ```
   C:\Users\YOUR_USERNAME\AppData\Roaming\Claude\scripts\fetch_notion_tasks.py
   ```
   (Adjust the path to wherever you've placed the scripts)

6. For "Start in":
   ```
   C:\Users\YOUR_USERNAME\AppData\Roaming\Claude\scripts
   ```

7. Check "Open the Properties dialog..." before finishing

### Configure Task Properties

In the Properties dialog:

1. **General tab:**
   - Check "Run whether user is logged on or not"
   - Check "Run with highest privileges" (optional, but can help with permissions)

2. **Conditions tab:**
   - Uncheck "Start the task only if the computer is on AC power" if you use a laptop

3. **Settings tab:**
   - Check "Run task as soon as possible after a scheduled start is missed"
   - Check "If the task fails, restart every: 1 hour" (optional)

## macOS / Linux (cron)

Add a cron job to run the script daily:

```bash
# Edit crontab
crontab -e

# Add this line (runs at 6:00 AM daily)
0 6 * * * /usr/bin/python3 /path/to/pwkm/scripts/fetch_notion_tasks.py >> /path/to/pwkm/scripts/fetch.log 2>&1
```

## Manual Execution

You can always run the script manually:

```bash
# Windows
python C:\Users\YOUR_USERNAME\AppData\Roaming\Claude\scripts\fetch_notion_tasks.py

# macOS/Linux
python3 /path/to/pwkm/scripts/fetch_notion_tasks.py
```

## Verifying It Works

After running (manually or scheduled), check:

1. The `notion_tasks.csv` file exists in the scripts directory
2. The file contains your current tasks, sorted by due date
3. The timestamp in the console output (or log file) shows the expected time

## Troubleshooting

### "Module not found" errors
Ensure you're using the correct Python installation and have installed the required packages.

### ".env file not found" error
Create a `.env` file in the scripts directory based on `.env.example`.

### "401 Unauthorized" error
Your Notion API key may be invalid or expired. Generate a new one at https://www.notion.so/my-integrations.

### "Database not found" error
Ensure your Notion integration has access to the database:
1. Open your Tasks & To-Dos database in Notion
2. Click the "..." menu → "Add connections"
3. Select your integration

### Tasks missing from export
The script only exports tasks where Status is not "Done". Check your Notion database filters.
