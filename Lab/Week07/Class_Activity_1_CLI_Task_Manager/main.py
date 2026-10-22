"""
Main Entry Point: Task Manager CLI Application
Week 7: Building a Simple CLI Application, Error Handling & Project Structure
"""

import sys

from src import task_data, task_logic


def display_menu() -> None:
    """Displays the interactive CLI menu options."""
    print("\n" + "=" * 34)
    print("        TASK MANAGER CLI          ")
    print("=" * 34)
    print("  1. Add New Task")
    print("  2. List All Tasks")
    print("  3. List Pending Tasks")
    print("  4. List Completed Tasks")
    print("  5. Search Tasks by Keyword")
    print("  6. Mark Task as Completed")
    print("  7. Delete Task")
    print("  8. Save and Exit")
    print("=" * 34)


def prompt_task_id(prompt_text: str) -> int:
    """
    Prompts the user for a task ID.

    Returns:
        int: A valid positive integer task ID.

    Raises:
        ValueError: If the input is not a positive integer.
    """
    raw = input(prompt_text).strip().lstrip("#") # accept '2' or '#2'
    task_id = int(raw)
    if task_id <= 0:
        raise ValueError("Task ID must be a positive integer")
    return task_id


def handle_add(tasks):
    description = input("Enter task description: ").strip()
    if not description:
        print("[Error] Description cannot be empty.")
        return tasks
    priority = input("Enter priority (Low / Medium / High) [Default: Medium]: ").strip() or "Medium"
    count_before = len(tasks)
    tasks = task_logic.add_task(tasks, description, priority)
    if len(tasks) > count_before:
        task_data.save_tasks(tasks) # auto-save after every change
    return tasks


def handle_complete(tasks):
    try:
        task_id = prompt_task_id("Enter ID of task to mark as completed: ")
    except ValueError as ve:
        print(f"[Error] Invalid input: {ve}. Please enter a positive number (e.g. 1, 2, 3).")
        return tasks
    tasks = task_logic.complete_task(tasks, task_id)
    task_data.save_tasks(tasks)
    return tasks


def handle_delete(tasks):
    try:
        task_id = prompt_task_id("Enter ID of task to delete: ")
    except ValueError as ve:
        print(f"[Error] Invalid input: {ve}. Please enter a valid numerical ID.")
        return tasks
    confirm = input(f"Are you sure you want to delete Task #{task_id}? (y/N): ").strip().lower()
    if confirm in ("y", "yes"):
        tasks = task_logic.delete_task(tasks, task_id)
        task_data.save_tasks(tasks)
    else:
        print("Deletion cancelled.")
    return tasks


def main() -> None:
    """Main application loop."""
    print("Welcome to Task Manager CLI!")
    print("Loading existing tasks from storage...")
    tasks = task_data.load_tasks()
    print(f"Loaded {len(tasks)} task(s) successfully.")

    try:
        while True:
            display_menu()
            choice = input("Enter choice (1-8): ").strip()

            if choice == "1":
                tasks = handle_add(tasks)
            elif choice == "2":
                task_logic.list_tasks(tasks)
            elif choice == "3":
                task_logic.list_tasks(tasks, filter_status="pending")
            elif choice == "4":
                task_logic.list_tasks(tasks, filter_status="completed")
            elif choice == "5":
                task_logic.search_tasks(tasks, input("Enter search keyword: "))
            elif choice == "6":
                tasks = handle_complete(tasks)
            elif choice == "7":
                tasks = handle_delete(tasks)
            elif choice == "8":
                print("\nSaving tasks to file...")
                if task_data.save_tasks(tasks):
                    print("[OK] All tasks saved successfully. Goodbye!")
                else:
                    print("[Warning] Could not confirm task save, please check file permissions.")
                break
            else:
                print("[Error] Invalid choice. Please select an option between 1 and 8.")

    except (KeyboardInterrupt, EOFError):
        # Ctrl+C, or the input stream ended (e.g. Ctrl+D): save before leaving instead of crashing
        print("\n\n[Notice] Application interrupted. Emergency saving tasks before exit...")
        task_data.save_tasks(tasks)
        print("[OK] Tasks saved. Exiting safely.")
        sys.exit(0)


if __name__ == "__main__":
    main()
