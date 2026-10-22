# src/cli_interface.py
"""
Presentation layer: shows the menu, reads and validates user input, calls TaskManager
and prints the results. There is no business logic here (Separation of Concerns).
"""

import logging

from .task import PRIORITY_LEVELS, parse_date
from .task_manager import SORT_CRITERIA

logger = logging.getLogger(__name__)

LINE = "-" * 34


class CLIInterface:
    """Command-line interface for the Enhanced Task Manager."""

    def __init__(self, task_manager):
        self.manager = task_manager
        self.actions = {
            "1": self.add_normal_task,
            "2": self.add_due_date_task,
            "3": self.add_priority_task,
            "4": self.list_all_tasks,
            "5": self.complete_task,
            "6": self.delete_task,
            "7": self.search_tasks,
            "8": self.filter_tasks,
            "9": self.sort_tasks,
        }

    # ------------------------------------------------------------- output

    @staticmethod
    def display_menu():
        print("\n" + "=" * 34)
        print("--- Enhanced Task Manager Menu ---")
        print("=" * 34)
        print("1. Add Normal Task")
        print("2. Add Due Date Task")
        print("3. Add Priority Task")
        print("4. List All Tasks")
        print("5. Complete Task")
        print("6. Delete Task")
        print("7. Search Tasks")
        print("8. Filter Tasks")
        print("9. Sort Tasks")
        print("0. Exit")
        print(LINE)

    @staticmethod
    def show_tasks(title, tasks, empty_message):
        if not tasks:
            print(f"\n[Info] {empty_message}")
            return
        print(f"\n--- {title} (Total: {len(tasks)}) ---")
        for task in tasks:
            print(f"  * {task}")
        print("-" * 44)

    # -------------------------------------------------------------- input

    @staticmethod
    def get_task_description():
        while True:
            description = input("Enter task description: ").strip()
            if description:
                return description
            print("[Error] Description cannot be empty. Please try again.")

    @staticmethod
    def get_date(prompt, allow_empty=False):
        """Asks until a valid YYYY-MM-DD date is entered (or blank, if allowed -> None)."""
        while True:
            value = input(prompt).strip()
            if not value and allow_empty:
                return None
            try:
                return parse_date(value).strftime("%Y-%m-%d")
            except ValueError:
                print("[Error] Invalid date. Please use YYYY-MM-DD (e.g. 2026-10-31).")

    @staticmethod
    def get_priority(prompt, allow_empty=False):
        while True:
            value = input(prompt).strip().capitalize()
            if not value and allow_empty:
                return None
            if value in PRIORITY_LEVELS:
                return value
            print("[Error] Invalid priority. Please enter High, Medium or Low.")

    @staticmethod
    def get_tags(prompt="Enter tags (comma-separated, e.g., study,project,urgent - optional): "):
        return [tag.strip() for tag in input(prompt).split(",") if tag.strip()]

    @staticmethod
    def get_yes_no(prompt):
        """Returns True for yes, False for no, None for blank. Asks again for anything else."""
        while True:
            value = input(prompt).strip().lower()
            if value in ("", "y", "yes", "n", "no"):
                return None if value == "" else value in ("y", "yes")
            print("[Error] Please answer yes or no (or leave blank).")

    @staticmethod
    def get_task_id(prompt):
        raw = input(prompt).strip().lstrip("#")
        try:
            task_id = int(raw)
        except ValueError:
            print("[Error] Task ID must be a whole number.")
            return None
        if task_id <= 0:
            print("[Error] Task ID must be a positive number.")
            return None
        return task_id

    # ------------------------------------------------------------ actions

    def add_normal_task(self):
        task = self.manager.add_normal_task(self.get_task_description(), tags=self.get_tags())
        print(f"[Success] Normal Task '{task.description}' added with ID {task.id}.")

    def add_due_date_task(self):
        description = self.get_task_description()
        due_date = self.get_date("Enter due date (YYYY-MM-DD): ")
        task = self.manager.add_due_date_task(description, due_date, tags=self.get_tags())
        note = " - note: this date has already passed" if task.is_overdue() else ""
        print(f"[Success] Due Date Task '{task.description}' (Due: {task.due_date}) added with ID {task.id}.{note}")

    def add_priority_task(self):
        description = self.get_task_description()
        priority = self.get_priority("Enter priority (High/Medium/Low): ")
        task = self.manager.add_priority_task(description, priority, tags=self.get_tags())
        print(f"[Success] Priority Task '{task.description}' (Priority: {task.priority}) added with ID {task.id}.")

    def list_all_tasks(self):
        self.show_tasks("Your Tasks", self.manager.get_all_tasks(), "No tasks yet. Add one from the menu!")
        if self.manager.tasks:
            s = self.manager.summary()
            print(f"Summary: {s['completed']}/{s['total']} completed | {s['pending']} pending | {s['overdue']} overdue")

    def complete_task(self):
        task_id = self.get_task_id("Enter ID of task to complete: ")
        if task_id is not None:
            success, message = self.manager.complete_task(task_id)
            print(f"{'[Success]' if success else '[Info]'} {message}")

    def delete_task(self):
        task_id = self.get_task_id("Enter ID of task to delete: ")
        if task_id is None:
            return
        task = self.manager.get_task_by_id(task_id)
        if task is None:
            print(f"[Info] Task with ID {task_id} not found.")
            return
        if self.get_yes_no(f"Delete '{task.description}'? (yes/no): "):
            success, message = self.manager.delete_task(task_id)
            print(f"{'[Success]' if success else '[Info]'} {message}")
        else:
            print("Deletion cancelled.")

    def search_tasks(self):
        keyword = input("Enter search keyword (in description or tags): ").strip()
        if not keyword:
            print("[Error] Please enter a keyword.")
            return
        self.show_tasks(f"Search results for '{keyword}'", self.manager.search_tasks(keyword),
                        f"No tasks match '{keyword}'.")

    def filter_tasks(self):
        print("\nLeave a field blank to skip that condition. All conditions must match.")
        completed = self.get_yes_no("Filter by completed status (yes/no, leave blank for all): ")
        while True:
            before = self.get_date("Filter by due date before (YYYY-MM-DD, leave blank for all): ", allow_empty=True)
            after = self.get_date("Filter by due date after (YYYY-MM-DD, leave blank for all): ", allow_empty=True)
            if before and after and after > before:
                print("[Error] 'after' date must be on or before the 'before' date. Please enter the range again.")
                continue
            break
        priority = self.get_priority("Filter by priority (High/Medium/Low, leave blank for all): ", allow_empty=True)
        tags = self.get_tags("Filter by tags (comma-separated, task must have ALL, leave blank for all): ")

        results = self.manager.filter_tasks(status=completed, due_date_before=before, due_date_after=after,
                                            priority_level=priority, contains_tags=tags)
        self.show_tasks("Filtered Tasks", results, "No tasks match these filters.")

    def sort_tasks(self):
        while True:
            criterion = input(f"Sort by ({' / '.join(SORT_CRITERIA)}, default: id): ").strip().lower() or "id"
            if criterion in SORT_CRITERIA:
                break
            print(f"[Error] Unknown criterion. Choose one of: {', '.join(SORT_CRITERIA)}.")
        reverse = bool(self.get_yes_no("Reverse order (yes/no, default: no): "))
        order = "descending" if reverse else "ascending"
        self.show_tasks(f"Tasks sorted by {criterion} ({order})", self.manager.sort_tasks(criterion, reverse),
                        "No tasks to sort.")

    # --------------------------------------------------------------- loop

    def run(self):
        print("Welcome to the Enhanced Task Manager!")
        print(f"Loaded {len(self.manager.tasks)} task(s).")
        try:
            while True:
                self.display_menu()
                choice = input("Enter your choice (0-9): ").strip()
                if choice == "0":
                    print("\nGoodbye! All tasks are saved.")
                    break
                action = self.actions.get(choice)
                if action is None:
                    print("[Error] Invalid choice. Please enter a number from 0 to 9.")
                    continue
                try:
                    action()
                except ValueError as e:
                    # last safety net: invalid data that slipped past the prompts
                    print(f"[Error] {e}")
                    logger.warning("Action %s failed: %s", choice, e)
        except (KeyboardInterrupt, EOFError):
            # every change is saved immediately, so it is safe to leave here
            print("\n\nExiting. All tasks are saved.")
