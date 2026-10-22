# tests/test_task_manager.py
import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest

from src.task import DueDateTask, PriorityTask
from src.task_manager import TaskManager


class TestTaskManager(unittest.TestCase):
    """Each test uses its own temporary JSON file; data/tasks.json is never touched."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.data_file = os.path.join(self.test_dir, "tasks.json")
        self.m = TaskManager(self.data_file)
        self.m.add_normal_task("Read PLAN.md", tags=["study", "week11"])            # 1
        self.m.add_due_date_task("Submit activity", "2026-10-20", tags=["school"])   # 2
        self.m.add_priority_task("Implement search", "High", tags=["python"])       # 3
        self.m.add_priority_task("Write tests", "Low", tags=["python", "testing"])  # 4
        self.m.add_due_date_task("Review Week 10", "2026-10-10", tags=["Python"])   # 5
        self.m.complete_task(1)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def ids(self, tasks):
        return [t.id for t in tasks]

    # --- CRUD ---------------------------------------------------------------

    def test_complete_and_delete_messages(self):
        self.assertEqual(self.m.complete_task(1)[0], False, "already completed")
        self.assertEqual(self.m.complete_task(99)[0], False)
        self.assertTrue(self.m.delete_task(2)[0])
        self.assertFalse(self.m.delete_task(2)[0])
        self.assertEqual(self.ids(self.m.get_all_tasks()), [1, 3, 4, 5])

    def test_persistence_keeps_subclasses(self):
        reloaded = TaskManager(self.data_file)
        self.assertEqual(len(reloaded.tasks), 5)
        self.assertIsInstance(reloaded.get_task_by_id(2), DueDateTask)
        self.assertIsInstance(reloaded.get_task_by_id(3), PriorityTask)
        self.assertTrue(reloaded.get_task_by_id(1).completed)
        self.assertEqual(reloaded.next_id, 6)

    def test_bad_entries_in_file_are_skipped(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump([{"id": 1, "description": "ok"},
                       {"id": 2, "description": "bad date", "_type": "DueDateTask", "due_date": "tomorrow"},
                       {"id": 1, "description": "duplicate id"},
                       "not an object"], f)
        with contextlib.redirect_stdout(io.StringIO()):
            reloaded = TaskManager(self.data_file)
        self.assertEqual(self.ids(reloaded.tasks), [1])

    def test_corrupted_file_starts_empty(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            f.write("{ broken")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(TaskManager(self.data_file).tasks, [])

    # --- search -------------------------------------------------------------

    def test_search_description_and_tags_case_insensitive(self):
        self.assertEqual(self.ids(self.m.search_tasks("PYTHON")), [3, 4, 5])   # tags
        self.assertEqual(self.ids(self.m.search_tasks("submit")), [2])         # description
        self.assertEqual(self.m.search_tasks("   "), [])
        self.assertEqual(self.m.search_tasks("nothing-matches"), [])

    # --- filter -------------------------------------------------------------

    def test_filter_by_status(self):
        self.assertEqual(self.ids(self.m.filter_tasks(status=True)), [1])
        self.assertEqual(self.ids(self.m.filter_tasks(status=False)), [2, 3, 4, 5])

    def test_filter_by_due_date_before(self):
        self.assertEqual(self.ids(self.m.filter_tasks(due_date_before="2026-10-15")), [5])
        self.assertEqual(self.ids(self.m.filter_tasks(due_date_before="2026-10-20")), [2, 5], "the limit date is included")

    def test_filter_by_priority_and_tags(self):
        self.assertEqual(self.ids(self.m.filter_tasks(priority="low")), [4])
        self.assertEqual(self.ids(self.m.filter_tasks(tags="python")), [3, 4, 5])
        self.assertEqual(self.ids(self.m.filter_tasks(tags=["python", "testing"])), [4], "all listed tags required")

    def test_filter_combines_conditions(self):
        self.assertEqual(self.ids(self.m.filter_tasks(status=False, priority="High", tags="python")), [3])
        self.assertEqual(self.ids(self.m.filter_tasks()), [1, 2, 3, 4, 5], "no condition = everything")

    def test_filter_rejects_invalid_values(self):
        with self.assertRaises(ValueError):
            self.m.filter_tasks(due_date_before="31/12/2026")
        with self.assertRaises(ValueError):
            self.m.filter_tasks(priority="urgent")

    # --- sort ---------------------------------------------------------------

    def test_sort_by_id(self):
        self.assertEqual(self.ids(self.m.sort_tasks("id", reverse=True)), [5, 4, 3, 2, 1])

    def test_sort_by_due_date_keeps_tasks_without_date_last(self):
        self.assertEqual(self.ids(self.m.sort_tasks("due_date")), [5, 2, 1, 3, 4])
        self.assertEqual(self.ids(self.m.sort_tasks("due_date", reverse=True)), [2, 5, 1, 3, 4])

    def test_sort_by_priority(self):
        self.assertEqual(self.ids(self.m.sort_tasks("priority")), [3, 4, 1, 2, 5])
        self.assertEqual(self.ids(self.m.sort_tasks("priority", reverse=True)), [4, 3, 1, 2, 5])

    def test_sort_does_not_change_stored_order(self):
        self.m.sort_tasks("priority")
        self.assertEqual(self.ids(self.m.tasks), [1, 2, 3, 4, 5])

    def test_sort_rejects_unknown_criterion(self):
        with self.assertRaises(ValueError):
            self.m.sort_tasks("color")


if __name__ == "__main__":
    unittest.main()
