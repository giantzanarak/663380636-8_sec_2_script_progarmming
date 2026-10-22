# src/task_manager.py
"""
Business logic layer: manages the collection of tasks.

Provides CRUD operations plus search, filter and sort. This layer never calls input() or print();
it returns data (or (success, message) tuples) and the CLI decides how to show it.
"""

import logging
import os

from .data_persistence import DataPersistence
from .task import PRIORITY_LEVELS, DueDateTask, PriorityTask, Task, normalize_tag, parse_date

logger = logging.getLogger(__name__)

SORT_CRITERIA = ("id", "description", "completed", "due_date", "priority")


class TaskManager:
    """Owns the task list and saves every change through DataPersistence."""

    def __init__(self, data_file=os.path.join("data", "tasks.json")):
        self.persistence = DataPersistence(data_file)
        self.tasks = self.persistence.load_tasks()
        self.next_id = self._get_next_task_id()

    def _get_next_task_id(self):
        """Highest existing id + 1 (1 for an empty list)."""
        return max((task.id for task in self.tasks), default=0) + 1

    def _save_changes(self):
        return self.persistence.save_tasks(self.tasks)

    def _add(self, task):
        self.tasks.append(task)
        self.next_id += 1
        self._save_changes()
        logger.info("Added %s", repr(task))
        return task

    # ------------------------------------------------------------------ CRUD

    def add_normal_task(self, description, tags=None):
        """Adds a normal task and returns it."""
        return self._add(Task(self.next_id, description, tags=tags))

    def add_due_date_task(self, description, due_date_str, tags=None):
        """Adds a task with a due date. Raises ValueError for a date that is not YYYY-MM-DD."""
        return self._add(DueDateTask(self.next_id, description, due_date_str, tags=tags))

    def add_priority_task(self, description, priority, tags=None):
        """Adds a task with a priority. Raises ValueError if it is not High/Medium/Low."""
        return self._add(PriorityTask(self.next_id, description, priority, tags=tags))

    def get_task_by_id(self, task_id):
        """Returns the task with this id, or None."""
        return next((task for task in self.tasks if task.id == task_id), None)

    def complete_task(self, task_id):
        """Marks a task as completed. Returns (success, message)."""
        task = self.get_task_by_id(task_id)
        if task is None:
            return False, f"Task with ID {task_id} not found."
        if task.completed:
            return False, f"Task ID {task_id} is already completed."
        task.mark_complete()
        self._save_changes()
        logger.info("Completed task %d", task_id)
        return True, f"Task ID {task_id} marked as completed."

    def delete_task(self, task_id):
        """Deletes a task. Returns (success, message)."""
        task = self.get_task_by_id(task_id)
        if task is None:
            return False, f"Task with ID {task_id} not found."
        self.tasks.remove(task)
        self._save_changes()
        logger.info("Deleted task %d", task_id)
        return True, f"Task ID {task_id} ('{task.description}') deleted."

    def get_all_tasks(self):
        """Returns a copy of the task list."""
        return list(self.tasks)

    # --------------------------------------------------- search / filter / sort

    def search_tasks(self, keyword):
        """
        Case-insensitive partial match on the description or any tag.
        An empty keyword returns an empty list.
        """
        keyword = keyword.strip().lower()
        if not keyword:
            return []
        results = [task for task in self.tasks
                   if keyword in task.description.lower() or any(keyword in tag for tag in task.tags)]
        logger.debug("search '%s' -> %s", keyword, [t.id for t in results])
        return results

    def filter_tasks(self, status=None, due_date_before=None, due_date_after=None,
                     priority_level=None, contains_tags=None):
        """
        Returns the tasks that match ALL given conditions; a condition left as None is ignored.

        Args:
            status: True = completed only, False = pending only.
            due_date_before: DueDateTasks due on or before this date ('YYYY-MM-DD' or date).
            due_date_after: DueDateTasks due on or after this date ('YYYY-MM-DD' or date).
            priority_level: PriorityTasks with this level ('High' / 'Medium' / 'Low').
            contains_tags: a tag or a list of tags; the task must have every one of them.

        Raises:
            ValueError: for an invalid date, an invalid priority, or a date range where after > before.
        """
        result = list(self.tasks)

        if status is not None:
            result = [t for t in result if t.completed == status]

        before = parse_date(due_date_before) if due_date_before else None
        after = parse_date(due_date_after) if due_date_after else None
        if before and after and after > before:
            raise ValueError("'due date after' must be on or before 'due date before'")
        if before or after:
            result = [t for t in result if isinstance(t, DueDateTask)
                      and (before is None or t.due_date <= before)
                      and (after is None or t.due_date >= after)]

        if priority_level:
            level = priority_level.strip().capitalize()
            if level not in PRIORITY_LEVELS:
                raise ValueError(f"priority must be one of {PRIORITY_LEVELS}")
            result = [t for t in result if isinstance(t, PriorityTask) and t.priority == level]

        if contains_tags:
            wanted = [contains_tags] if isinstance(contains_tags, str) else list(contains_tags)
            wanted = [normalize_tag(tag) for tag in wanted if normalize_tag(tag)]
            result = [t for t in result if all(tag in t.tags for tag in wanted)]

        logger.debug("filter -> %s", [t.id for t in result])
        return result

    def sort_tasks(self, criterion="id", reverse=False):
        """
        Returns a new sorted list (the stored order is not changed).

        criterion: 'id', 'description', 'completed', 'due_date' or 'priority'.
        For 'due_date' and 'priority', tasks that do not have that field are always placed
        last (in id order), whether the sort is ascending or descending. Ties are ordered by id.

        Raises:
            ValueError: for an unknown criterion.
        """
        criterion = criterion.strip().lower()
        if criterion == "id":
            return sorted(self.tasks, key=lambda t: t.id, reverse=reverse)
        if criterion == "description":
            return sorted(self.tasks, key=lambda t: (t.description.lower(), t.id), reverse=reverse)
        if criterion == "completed":
            # ascending: pending (False) first, then completed (True)
            return sorted(self.tasks, key=lambda t: (t.completed, t.id), reverse=reverse)

        if criterion == "due_date":
            has_value = lambda t: isinstance(t, DueDateTask)
            key = lambda t: (t.due_date, t.id)
        elif criterion == "priority":
            has_value = lambda t: isinstance(t, PriorityTask)
            # "High" -> 0, "Medium" -> 1, "Low" -> 2, so ascending = most important first
            key = lambda t: (PRIORITY_LEVELS.index(t.priority), t.id)
        else:
            raise ValueError(f"criterion must be one of {SORT_CRITERIA}")

        with_value = sorted((t for t in self.tasks if has_value(t)), key=key, reverse=reverse)
        without_value = sorted((t for t in self.tasks if not has_value(t)), key=lambda t: t.id)
        return with_value + without_value

    def summary(self):
        """Counts of total / completed / pending / overdue tasks."""
        done = sum(1 for t in self.tasks if t.completed)
        overdue = sum(1 for t in self.tasks if isinstance(t, DueDateTask) and t.is_overdue())
        return {"total": len(self.tasks), "completed": done, "pending": len(self.tasks) - done, "overdue": overdue}
