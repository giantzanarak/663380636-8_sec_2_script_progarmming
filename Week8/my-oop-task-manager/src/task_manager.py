# src/task_manager.py

import json
import os
from typing import List, Optional

from .task import Task

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TaskManager:
    """
    Manages the collection of Task objects: loading/saving them as JSON and
    adding, listing, completing and deleting tasks.
    """

    def __init__(self, data_file: str = os.path.join("data", "tasks.json")):
        """
        Args:
            data_file: JSON file path, relative to the project folder (or an absolute path).
        """
        self.data_file = data_file
        self._file_path = data_file if os.path.isabs(data_file) else os.path.join(PROJECT_DIR, data_file)
        self.tasks: List[Task] = self._load_tasks()
        self.next_id: int = self._get_next_task_id()

    def _get_next_task_id(self) -> int:
        """Next unique ID = highest existing ID + 1 (or 1 for an empty list)."""
        return max((task.id for task in self.tasks), default=0) + 1

    def _load_tasks(self) -> List[Task]:
        """Loads tasks from the JSON file and turns each dictionary back into a Task object."""
        if not os.path.exists(self._file_path):
            return []
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            raw_tasks = json.loads(content) if content else []
        except json.JSONDecodeError:
            print("Warning: tasks.json is corrupted. Starting with an empty task list.")
            return []
        except OSError as e:
            print(f"Warning: could not read {self._file_path} ({e}). Starting with an empty task list.")
            return []

        if not isinstance(raw_tasks, list):
            print("Warning: tasks.json does not contain a list. Starting with an empty task list.")
            return []

        tasks = []
        for item in raw_tasks:
            try:
                tasks.append(Task.from_dict(item))
            except (KeyError, TypeError, ValueError):
                print(f"Warning: skipping invalid task entry: {item}")
        return tasks

    def _save_tasks(self) -> bool:
        """
        Saves all tasks to the JSON file. Writes a temporary file first and then replaces
        the real one, so tasks.json is never left half-written.
        """
        temp_path = self._file_path + ".tmp"
        try:
            os.makedirs(os.path.dirname(self._file_path), exist_ok=True)
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump([task.to_dict() for task in self.tasks], f, indent=4, ensure_ascii=False)
            os.replace(temp_path, self._file_path)
            return True
        except OSError as e:
            print(f"Error: could not save tasks ({e}).")
            return False
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def get_task(self, task_id: int) -> Optional[Task]:
        """Returns the task with this ID, or None if it does not exist."""
        return next((task for task in self.tasks if task.id == task_id), None)

    def add_task(self, description: str) -> Optional[Task]:
        """Adds a new pending task and returns it (None if the description is empty)."""
        description = description.strip()
        if not description:
            print("Task description cannot be empty.")
            return None
        new_task = Task(self.next_id, description)
        self.tasks.append(new_task)
        self.next_id += 1
        self._save_tasks()
        print(f"Task '{description}' added with ID {new_task.id}.")
        return new_task

    def list_tasks(self):
        """Prints all tasks."""
        if not self.tasks:
            print("No tasks found.")
            return
        print("\n--- Your Tasks ---")
        for task in self.tasks:
            print(task)
        print("------------------")

    def complete_task(self, task_id: int) -> bool:
        """Marks a task as completed. Returns False if the task does not exist."""
        task = self.get_task(task_id)
        if task is None:
            print(f"Error: Task with ID {task_id} not found.")
            return False
        if task.completed:
            print(f"Task ID {task_id} is already completed.")
        else:
            task.mark_complete()
            self._save_tasks()
            print(f"Task ID {task_id} marked as completed.")
        return True

    def delete_task(self, task_id: int) -> bool:
        """Deletes a task by its ID. Returns False if the task does not exist."""
        task = self.get_task(task_id)
        if task is None:
            print(f"Error: Task with ID {task_id} not found.")
            return False
        self.tasks.remove(task)
        self._save_tasks()
        print(f"Task ID {task_id} deleted successfully.")
        return True
