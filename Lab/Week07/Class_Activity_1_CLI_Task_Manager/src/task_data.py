"""
Module: task_data.py
Description: Handles data persistence for the Task Manager CLI application.
             Responsible for loading and saving tasks in JSON format.
"""

import json
import os
from typing import Any, Dict, List

# Resolve absolute path to data/tasks.json relative to this module's location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")


def _is_valid_task(item: Any) -> bool:
    """A task must be a dict with an integer 'id' and a string 'description'."""
    return (isinstance(item, dict)
            and isinstance(item.get("id"), int)
            and isinstance(item.get("description"), str))


def load_tasks() -> List[Dict[str, Any]]:
    """
    Loads tasks from the JSON file.

    Returns:
        List[Dict[str, Any]]: A list of task dictionaries. If the file doesn't exist,
                              is empty, or is corrupted, returns an empty list gracefully.
    """
    if not os.path.exists(TASKS_FILE):
        return []

    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            # Handle empty file case
            return []
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"[Warning] tasks.json is corrupted or invalid JSON (Line {e.lineno}, Col {e.colno}).")
        print("          Starting with an empty task list to prevent crash.")
        return []
    except PermissionError:
        print(f"[Error] Permission denied when reading '{TASKS_FILE}'.")
        return []
    except OSError as e:
        print(f"[Error] Could not read '{TASKS_FILE}': {e}")
        return []

    if not isinstance(data, list):
        print("[Warning] tasks.json does not contain a list of tasks. Starting with an empty task list.")
        return []

    # Keep only well-formed tasks and fill in missing optional fields
    tasks = []
    for item in data:
        if not _is_valid_task(item):
            print(f"[Warning] Skipping invalid task entry: {item}")
            continue
        item.setdefault("completed", False)
        item.setdefault("priority", "Medium")
        tasks.append(item)
    return tasks


def save_tasks(tasks: List[Dict[str, Any]]) -> bool:
    """
    Saves the list of tasks to the JSON file.
    Writes to a temporary file first and then replaces tasks.json, so the existing
    file is never left half-written if something goes wrong.

    Args:
        tasks: List of task dictionaries to persist.

    Returns:
        bool: True if saving succeeded, False otherwise.
    """
    temp_file = TASKS_FILE + ".tmp"
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=4, ensure_ascii=False)
        os.replace(temp_file, TASKS_FILE)
        return True
    except PermissionError:
        print(f"[Error] Permission denied when writing to '{TASKS_FILE}'.")
        return False
    except OSError as e:
        print(f"[Error] Failed to save tasks to file: {e}")
        return False
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
