# src/data_persistence.py
"""
Data layer: saves Task objects to JSON and loads them back.
All file I/O lives here (Separation of Concerns).
"""

import json
import logging
import os

from .task import task_from_dict

logger = logging.getLogger(__name__)

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class DataPersistence:
    """Loads and saves the task list in a JSON file."""

    def __init__(self, data_file=os.path.join("data", "tasks.json")):
        # A relative path is resolved from the project folder, so the app can be started from anywhere
        self.data_file = data_file
        self._path = data_file if os.path.isabs(data_file) else os.path.join(PROJECT_DIR, data_file)

    def get_file_path(self):
        return self._path

    def load_tasks(self):
        """
        Loads tasks from JSON. A missing, empty or corrupted file gives an empty list;
        invalid entries (bad type, bad date, duplicate id...) are skipped with a warning.
        """
        if not os.path.exists(self._path):
            logger.info("No data file at %s - starting with an empty list.", self._path)
            return []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            raw_tasks = json.loads(content) if content else []
        except json.JSONDecodeError as e:
            logger.warning("tasks.json is corrupted (%s) - starting with an empty list.", e)
            return []
        except OSError as e:
            logger.warning("Could not read %s (%s) - starting with an empty list.", self._path, e)
            return []

        if not isinstance(raw_tasks, list):
            logger.warning("tasks.json does not contain a list - starting with an empty list.")
            return []

        tasks, seen_ids = [], set()
        for item in raw_tasks:
            try:
                if not isinstance(item, dict):
                    raise ValueError("entry is not an object")
                task = task_from_dict(item)
                if task.id in seen_ids:
                    raise ValueError(f"duplicate id {task.id}")
            except (ValueError, TypeError) as e:
                logger.warning("Skipping invalid task entry (%s): %s", e, item)
                continue
            seen_ids.add(task.id)
            tasks.append(task)
        logger.info("Loaded %d task(s) from %s", len(tasks), self._path)
        return tasks

    def save_tasks(self, tasks):
        """
        Saves all tasks (each object's own to_dict() - polymorphism) with indent=4.
        Writes a temporary file first and then replaces tasks.json, so the data file
        is never left half-written. Returns True on success.
        """
        temp_path = self._path + ".tmp"
        try:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump([task.to_dict() for task in tasks], f, indent=4, ensure_ascii=False)
            os.replace(temp_path, self._path)
            logger.debug("Saved %d task(s) to %s", len(tasks), self._path)
            return True
        except OSError as e:
            logger.error("Could not save tasks: %s", e)
            return False
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
