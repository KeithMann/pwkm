#!/usr/bin/env python3
"""
Fetch tasks from Notion database and export to CSV

This script exports your Tasks & To-Dos database from Notion to a local CSV file.
The CSV is used by task_manager.py for quick task lookups without API calls.

Configuration:
    API credentials are loaded from a .env file in the same directory.
    Create a .env file with:
        NOTION_API_KEY=your_api_key_here
        NOTION_DATABASE_ID=your_database_id_here

Usage:
    python fetch_notion_tasks.py

Scheduling:
    For best results, run this script daily via Windows Task Scheduler or cron.
    See docs/scheduling-fetch-tasks.md for detailed instructions.
"""

import requests
import csv
from datetime import datetime
import os
from pathlib import Path

# Load environment variables from .env file
def load_env_file(env_path: Path) -> dict:
    """
    Load environment variables from a .env file.

    Simple .env parser that handles KEY=VALUE format.
    For production, consider using python-dotenv package.
    """
    env_vars = {}
    if not env_path.exists():
        raise FileNotFoundError(
            f".env file not found at {env_path}\n"
            f"Please create a .env file based on .env.example"
        )

    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()

    return env_vars

# Get script directory and load .env file
SCRIPT_DIR = Path(__file__).parent
env_vars = load_env_file(SCRIPT_DIR / '.env')

# Configuration from environment variables
NOTION_API_KEY = env_vars.get('NOTION_API_KEY')
DATABASE_ID = env_vars.get('NOTION_DATABASE_ID')
OUTPUT_FILE = "notion_tasks.csv"  # Will be saved in the same directory as the script

# Validate required configuration
if not NOTION_API_KEY or not DATABASE_ID:
    raise ValueError(
        "Missing required configuration!\n"
        "Please ensure .env file contains:\n"
        "  NOTION_API_KEY=...\n"
        "  NOTION_DATABASE_ID=..."
    )

# Notion API endpoint
NOTION_VERSION = "2022-06-28"
QUERY_URL = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

def fetch_all_tasks():
    """Fetch all tasks from Notion database"""
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }
    
    payload = {
        "sorts": [
            {
                "property": "Due Date",
                "direction": "ascending"
            }
        ],
        "page_size": 100
    }
    
    all_results = []
    has_more = True
    start_cursor = None
    
    while has_more:
        if start_cursor:
            payload["start_cursor"] = start_cursor
            
        response = requests.post(QUERY_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        all_results.extend(data.get("results", []))
        
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
    
    return all_results

def extract_task_data(page):
    """Extract relevant task data from a Notion page object"""
    properties = page.get("properties", {})
    
    # Extract task name (title property)
    task_name = ""
    if "Task Name" in properties:
        title_array = properties["Task Name"].get("title", [])
        if title_array:
            task_name = title_array[0].get("plain_text", "")
    
    # Extract due date
    due_date = ""
    if "Due Date" in properties:
        date_obj = properties["Due Date"].get("date")
        if date_obj:
            due_date = date_obj.get("start", "")
    
    # Extract other properties
    category = properties.get("Category", {}).get("select", {}).get("name", "")
    frequency = properties.get("Frequency", {}).get("select", {}).get("name", "")
    priority = properties.get("Priority", {}).get("select", {}).get("name", "")
    status = properties.get("Status", {}).get("select", {}).get("name", "")
    
    # Get page URL
    page_url = page.get("url", "")
    
    return {
        "Task Name": task_name,
        "Due Date": due_date,
        "Category": category,
        "Frequency": frequency,
        "Priority": priority,
        "Status": status,
        "URL": page_url
    }

def export_to_csv(tasks, output_file):
    """Export tasks to CSV file"""
    if not tasks:
        print("No tasks to export")
        return
    
    # Define CSV columns
    fieldnames = ["Task Name", "Due Date", "Category", "Frequency", "Priority", "Status", "URL"]
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tasks)
    
    print(f"Successfully exported {len(tasks)} tasks to {output_file}")

def main():
    try:
        print("Fetching tasks from Notion...")
        pages = fetch_all_tasks()
        
        print(f"Found {len(pages)} tasks")
        
        # Extract task data
        tasks = [extract_task_data(page) for page in pages]
        
        # Get script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, OUTPUT_FILE)
        
        # Export to CSV
        export_to_csv(tasks, output_path)
        
        print(f"\nCSV file saved to: {output_path}")
        print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()
