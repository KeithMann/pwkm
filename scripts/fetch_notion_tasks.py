#!/usr/bin/env python3
"""
Fetch tasks from Notion database and export to CSV

This script exports your Tasks & To-Dos database from Notion to a local CSV file.
The CSV is used by task_manager.py for quick task lookups without API calls.

Configuration:
    Reads NOTION_API_KEY and NOTION_DATABASE_ID. Either set them as real
    environment variables, or put them in a .env file beside this script:
        NOTION_API_KEY=your_api_key_here
        NOTION_DATABASE_ID=your_database_id_here
    The real environment wins if both are present. See .env.example.

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

from pwkm_env import load_env

SCRIPT_DIR = Path(__file__).parent

# Populate os.environ from .env (if present) without overriding real
# environment variables. Replaces a bespoke parser that loaded .env into a
# local dict only, so nothing else in the system could see the values.
load_env()

# Configuration
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
OUTPUT_FILE = "notion_tasks.csv"  # Saved in the same directory as the script

if not NOTION_API_KEY or not DATABASE_ID:
    missing = [
        name
        for name, value in (
            ("NOTION_API_KEY", NOTION_API_KEY),
            ("NOTION_DATABASE_ID", DATABASE_ID),
        )
        if not value
    ]
    raise SystemExit(
        "Missing required configuration: " + ", ".join(missing) + "\n"
        "Set them as environment variables, or add them to a .env file at:\n"
        "  " + str(SCRIPT_DIR / ".env") + "\n"
        "See .env.example for the expected format."
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
