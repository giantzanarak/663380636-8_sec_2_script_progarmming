"""
Module: task_logic.py
Description: Implements the core business logic for task management operations:
             adding, listing, completing, deleting, and searching tasks.
"""

from typing import Any, Dict, List, Optional

VALID_PRIORITIES = ["Low", "Medium", "High"]
# Shortcuts the user may type instead of the full priority name
PRIORITY_SHORTCUTS = {"l": "Low", "1": "Low", "m": "Medium", "2": "Medium", "h": "High", "3": "High"}


def get_next_task_id(tasks: List[Dict[str, Any]]) -> int:
    """
    Generates an auto-incrementing unique integer ID for a new task.

    Returns:
        int: The next available task ID (starts at 1 if list is empty).
    """
    if not tasks:
        return 1
    return max(task["id"] for task in tasks) + 1


def normalize_priority(priority: str) -> Optional[str]:
    """Returns 'Low' / 'Medium' / 'High' for valid input (name or shortcut), otherwise None."""
    cleaned = priority.strip()
    if cleaned.capitalize() in VALID_PRIORITIES:
        return cleaned.capitalize()
    return PRIORITY_SHORTCUTS.get(cleaned.lower())


def add_task(tasks: List[Dict[str, Any]], description: str, priority: str = "Medium") -> List[Dict[str, Any]]:
    """
    Adds a new task to the task list.

    Args:
        tasks: Current list of tasks.
        description: Text description of the task.
        priority: Priority level ('Low', 'Medium', 'High' or l/m/h, 1/2/3). Defaults to 'Medium'.

    Returns:
        List[Dict[str, Any]]: Updated list of tasks.
    """
    cleaned_desc = description.strip()
    if not cleaned_desc:
        print("[Error] Task description cannot be empty or whitespace only.")
        return tasks

    cleaned_priority = normalize_priority(priority or "Medium")
    if cleaned_priority is None:
        print(f"[Warning] Invalid priority '{priority}'. Defaulting to 'Medium'.")
        cleaned_priority = "Medium"

    task_id = get_next_task_id(tasks)
    tasks.append({
        "id": task_id,
        "description": cleaned_desc,
        "completed": False,
        "priority": cleaned_priority,
    })
    print(f"[OK] Task '{cleaned_desc}' [Priority: {cleaned_priority}] added successfully with ID #{task_id}.")
    return tasks


def list_tasks(tasks: List[Dict[str, Any]], filter_status: Optional[str] = None) -> None:
    """
    Displays tasks formatted in a clear table structure.

    Args:
        tasks: List of tasks to display.
        filter_status: Optional filter ('completed', 'pending', or None for all).
    """
    if not tasks:
        print("\n[Empty] No tasks found. Use 'Add Task' to create one!")
        return

    filtered = tasks
    if filter_status == "completed":
        filtered = [t for t in tasks if t.get("completed", False)]
    elif filter_status == "pending":
        filtered = [t for t in tasks if not t.get("completed", False)]

    if not filtered:
        print(f"\n[Empty] No tasks found matching filter: '{filter_status}'.")
        return

    print("\n" + "=" * 65)
    print(f"{'ID':<6} | {'Status':<12} | {'Priority':<10} | {'Description'}")
    print("-" * 65)
    for task in filtered:
        task_id = f"#{task['id']}"
        status = "[DONE]" if task.get("completed", False) else "[PENDING]"
        print(f"{task_id:<6} | {status:<12} | {task.get('priority', 'Medium'):<10} | {task.get('description', '')}")
    print("=" * 65)

    total = len(tasks)
    completed = sum(1 for t in tasks if t.get("completed", False))
    print(f"Summary: {completed}/{total} task(s) completed.\n")


def _find_task(tasks: List[Dict[str, Any]], task_id: int) -> Optional[Dict[str, Any]]:
    return next((task for task in tasks if task["id"] == task_id), None)


def complete_task(tasks: List[Dict[str, Any]], task_id: int) -> List[Dict[str, Any]]:
    """Marks a task with the given ID as completed."""
    task = _find_task(tasks, task_id)
    if task is None:
        print(f"[Error] Task with ID #{task_id} was not found.")
    elif task.get("completed", False):
        print(f"[Info] Task #{task_id} is already marked as completed.")
    else:
        task["completed"] = True
        print(f"[OK] Task #{task_id} ('{task['description']}') has been marked as COMPLETED.")
    return tasks


def delete_task(tasks: List[Dict[str, Any]], task_id: int) -> List[Dict[str, Any]]:
    """Deletes a task with the given ID from the list."""
    task = _find_task(tasks, task_id)
    if task is None:
        print(f"[Error] Task with ID #{task_id} was not found.")
    else:
        tasks.remove(task)
        print(f"[OK] Task #{task_id} ('{task['description']}') was deleted successfully.")
    return tasks


def search_tasks(tasks: List[Dict[str, Any]], keyword: str) -> None:
    """Searches for tasks whose descriptions contain the keyword (case-insensitive)."""
    cleaned_kw = keyword.strip().lower()
    if not cleaned_kw:
        print("[Error] Search keyword cannot be empty.")
        return

    matches = [t for t in tasks if cleaned_kw in t.get("description", "").lower()]
    if not matches:
        print(f"\n[Search] No tasks found matching query: '{keyword}'.")
        return

    print(f"\n[Search Results] {len(matches)} match(es) for '{keyword}':")
    list_tasks(matches)
