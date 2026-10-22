# tests/test_task_manager.py
"""Unit tests for TaskManager (CRUD, persistence, search, filter, sort). Uses a temporary data file."""
import json
import logging
import os
import shutil
import tempfile
import unittest

from src.task import DueDateTask, PriorityTask
from src.task_manager import TaskManager


class TestTaskManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)  # keep test output clean

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.data_file = os.path.join(self.test_dir, "tasks.json")
        m = self.m = TaskManager(self.data_file)
        m.add_normal_task("Write documentation", tags=["study", "urgent"])         # 1
        m.add_due_date_task("Submit source code", "2026-10-30", tags=["github"])   # 2
        m.add_priority_task("Prepare slides", "High", tags=["presentation"])      # 3
        m.add_normal_task("Review PEP 8", tags=["refactor"])                       # 4
        m.add_priority_task("Rehearse demo", "Low", tags=["presentation", "urgent"])  # 5
        m.add_due_date_task("Midterm review", "2026-08-20", tags=["study"])        # 6
        m.complete_task(4)
        m.complete_task(6)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @staticmethod
    def ids(tasks):
        return [t.id for t in tasks]

    # ---------------------------------------------------------- CRUD & storage

    def test_ids_are_unique_and_increasing(self):
        self.assertEqual(self.ids(self.m.tasks), [1, 2, 3, 4, 5, 6])
        self.assertEqual(self.m.next_id, 7)

    def test_complete_and_delete(self):
        self.assertEqual(self.m.complete_task(4)[0], False, "already completed")
        self.assertEqual(self.m.complete_task(99)[0], False)
        self.assertTrue(self.m.delete_task(1)[0])
        self.assertFalse(self.m.delete_task(1)[0])
        self.assertEqual(self.ids(self.m.tasks), [2, 3, 4, 5, 6])

    def test_reload_restores_subclasses_and_state(self):
        reloaded = TaskManager(self.data_file)
        self.assertEqual(len(reloaded.tasks), 6)
        self.assertIsInstance(reloaded.get_task_by_id(2), DueDateTask)
        self.assertIsInstance(reloaded.get_task_by_id(3), PriorityTask)
        self.assertTrue(reloaded.get_task_by_id(6).completed)
        self.assertEqual(reloaded.next_id, 7)

    def test_saved_json_is_indented(self):
        with open(self.data_file, encoding="utf-8") as f:
            self.assertIn('\n    {', f.read())

    def test_corrupted_and_invalid_files(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            f.write("{ broken")
        self.assertEqual(TaskManager(self.data_file).tasks, [])
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump([{"id": 1, "description": "ok"}, {"id": 1, "description": "dup"},
                       {"id": 2, "description": "bad", "_type": "PriorityTask", "priority": "Urgent"}], f)
        self.assertEqual(self.ids(TaskManager(self.data_file).tasks), [1])

    # ------------------------------------------------------------------ search

    def test_search_partial_case_insensitive(self):
        self.assertEqual(self.ids(self.m.search_tasks("PRESENT")), [3, 5])   # tag partial match
        self.assertEqual(self.ids(self.m.search_tasks("review")), [4, 6])    # description
        self.assertEqual(self.m.search_tasks(""), [])
        self.assertEqual(self.m.search_tasks("zzz"), [])

    # ------------------------------------------------------------------ filter

    def test_filter_status(self):
        self.assertEqual(self.ids(self.m.filter_tasks(status=True)), [4, 6])
        self.assertEqual(self.ids(self.m.filter_tasks(status=False)), [1, 2, 3, 5])

    def test_filter_due_date_range(self):
        self.assertEqual(self.ids(self.m.filter_tasks(due_date_before="2026-09-01")), [6])
        self.assertEqual(self.ids(self.m.filter_tasks(due_date_after="2026-09-01")), [2])
        self.assertEqual(self.ids(self.m.filter_tasks(due_date_after="2026-08-20", due_date_before="2026-10-30")), [2, 6],
                         "range limits are inclusive")
        with self.assertRaises(ValueError):
            self.m.filter_tasks(due_date_after="2026-12-01", due_date_before="2026-01-01")

    def test_filter_priority_and_tags(self):
        self.assertEqual(self.ids(self.m.filter_tasks(priority_level="low")), [5])
        self.assertEqual(self.ids(self.m.filter_tasks(contains_tags="URGENT")), [1, 5])
        self.assertEqual(self.ids(self.m.filter_tasks(contains_tags=["presentation", "urgent"])), [5])
        with self.assertRaises(ValueError):
            self.m.filter_tasks(priority_level="urgent")

    def test_filter_combined_conditions(self):
        self.assertEqual(self.ids(self.m.filter_tasks(status=False, contains_tags="study")), [1])
        self.assertEqual(self.ids(self.m.filter_tasks()), [1, 2, 3, 4, 5, 6])

    # -------------------------------------------------------------------- sort

    def test_sort_by_id_and_description(self):
        self.assertEqual(self.ids(self.m.sort_tasks("id", reverse=True)), [6, 5, 4, 3, 2, 1])
        self.assertEqual(self.ids(self.m.sort_tasks("description")), [6, 3, 5, 4, 2, 1])

    def test_sort_by_completed(self):
        self.assertEqual(self.ids(self.m.sort_tasks("completed")), [1, 2, 3, 5, 4, 6])

    def test_sort_by_due_date_tasks_without_date_last(self):
        self.assertEqual(self.ids(self.m.sort_tasks("due_date")), [6, 2, 1, 3, 4, 5])
        self.assertEqual(self.ids(self.m.sort_tasks("due_date", reverse=True)), [2, 6, 1, 3, 4, 5])

    def test_sort_by_priority_high_to_low(self):
        self.assertEqual(self.ids(self.m.sort_tasks("priority")), [3, 5, 1, 2, 4, 6])

    def test_sort_returns_new_list_and_validates(self):
        self.m.sort_tasks("priority")
        self.assertEqual(self.ids(self.m.tasks), [1, 2, 3, 4, 5, 6])
        with self.assertRaises(ValueError):
            self.m.sort_tasks("color")


if __name__ == "__main__":
    unittest.main()
