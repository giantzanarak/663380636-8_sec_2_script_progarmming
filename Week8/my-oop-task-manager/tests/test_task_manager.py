# tests/test_task_manager.py
import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest

from src.task import Task
from src.task_manager import TaskManager


class TestTaskManager(unittest.TestCase):
    """Tests for the TaskManager class. Each test uses its own temporary JSON file."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "temp_tasks.json")
        self.manager = self._new_manager()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _new_manager(self):
        # Hide the messages TaskManager prints so the test output stays readable
        with contextlib.redirect_stdout(io.StringIO()):
            return TaskManager(data_file=self.test_file)

    def _quiet(self, func, *args):
        with contextlib.redirect_stdout(io.StringIO()):
            return func(*args)

    def _write_file(self, content):
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(content)

    def test_initial_state_empty(self):
        self.assertEqual(self.manager.tasks, [])
        self.assertEqual(self.manager.next_id, 1)

    def test_add_task(self):
        task = self._quiet(self.manager.add_task, "Complete OOP Lab")
        self.assertIsInstance(task, Task)
        self.assertEqual((task.id, task.description, task.completed), (1, "Complete OOP Lab", False))
        self.assertEqual(self.manager.next_id, 2)

    def test_add_empty_task_is_rejected(self):
        self.assertIsNone(self._quiet(self.manager.add_task, "   "))
        self.assertEqual(self.manager.tasks, [])

    def test_complete_task(self):
        self._quiet(self.manager.add_task, "Task 1")
        self._quiet(self.manager.add_task, "Task 2")
        self.assertTrue(self._quiet(self.manager.complete_task, 1))
        self.assertTrue(self.manager.tasks[0].completed)
        self.assertFalse(self.manager.tasks[1].completed)
        self.assertFalse(self._quiet(self.manager.complete_task, 999))

    def test_delete_task(self):
        self._quiet(self.manager.add_task, "Task to delete")
        self._quiet(self.manager.add_task, "Task to keep")
        self.assertTrue(self._quiet(self.manager.delete_task, 1))
        self.assertEqual([t.id for t in self.manager.tasks], [2])
        self.assertFalse(self._quiet(self.manager.delete_task, 999))

    def test_ids_are_not_reused_after_delete(self):
        self._quiet(self.manager.add_task, "A")
        self._quiet(self.manager.add_task, "B")
        self._quiet(self.manager.delete_task, 2)
        self.assertEqual(self._quiet(self.manager.add_task, "C").id, 3)

    def test_data_persistence_reload(self):
        self._quiet(self.manager.add_task, "Persistent Task 1")
        self._quiet(self.manager.add_task, "Persistent Task 2")
        self._quiet(self.manager.complete_task, 1)

        reloaded = self._new_manager()
        self.assertEqual(len(reloaded.tasks), 2)
        self.assertIsInstance(reloaded.tasks[0], Task)
        self.assertTrue(reloaded.tasks[0].completed)
        self.assertEqual(reloaded.next_id, 3)

    def test_corrupted_file_starts_empty(self):
        self._write_file("{ not valid json")
        self.assertEqual(self._new_manager().tasks, [])

    def test_empty_file_starts_empty(self):
        self._write_file("")
        self.assertEqual(self._new_manager().tasks, [])

    def test_invalid_entries_are_skipped(self):
        self._write_file(json.dumps([
            {"id": 1, "description": "valid", "completed": True},
            {"description": "missing id"},
            "not a dict",
        ]))
        manager = self._new_manager()
        self.assertEqual([t.id for t in manager.tasks], [1])
        self.assertEqual(manager.next_id, 2)


if __name__ == '__main__':
    unittest.main()
