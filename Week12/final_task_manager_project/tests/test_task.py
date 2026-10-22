# tests/test_task.py
"""Unit tests for the data models in src/task.py."""
import datetime
import unittest

from src.task import DueDateTask, PriorityTask, Task, task_from_dict


class TestTaskModels(unittest.TestCase):

    def test_tags_are_normalized_and_unique(self):
        t = Task(1, "Read", tags=[" Study ", "study", "", "GitHub"])
        self.assertEqual(t.tags, ["study", "github"])

    def test_add_and_remove_tag(self):
        t = Task(1, "Read")
        self.assertTrue(t.add_tag("Urgent"))
        self.assertFalse(t.add_tag("urgent"), "duplicate after normalizing")
        self.assertTrue(t.has_tag("URGENT"))
        self.assertTrue(t.remove_tag(" urgent "))
        self.assertFalse(t.remove_tag("urgent"))
        self.assertEqual(t.tags, [])

    def test_due_date_validation(self):
        self.assertEqual(DueDateTask(1, "x", "2026-10-30").due_date, datetime.date(2026, 10, 30))
        for bad in ("30-10-2026", "2026-02-30", "tomorrow"):
            with self.assertRaises(ValueError):
                DueDateTask(1, "x", bad)

    def test_overdue(self):
        t = DueDateTask(1, "x", "2026-10-20")
        self.assertTrue(t.is_overdue(today=datetime.date(2026, 10, 23)))
        t.mark_complete()
        self.assertFalse(t.is_overdue(today=datetime.date(2026, 10, 23)))

    def test_priority_validation(self):
        self.assertEqual(PriorityTask(1, "x", "medium").priority, "Medium")
        with self.assertRaises(ValueError):
            PriorityTask(1, "x", "urgent")

    def test_str_shows_type_specific_fields(self):
        self.assertEqual(str(Task(1, "a", tags=["x"])), "ID: 1 | Description: a | Status: Pending | Tags: x")
        self.assertIn("Due: 2099-01-01", str(DueDateTask(2, "b", "2099-01-01")))
        self.assertIn("Priority: High", str(PriorityTask(3, "c", "High")))

    def test_round_trip_keeps_class_and_data(self):
        for task in (Task(1, "a", True, ["t"]), DueDateTask(2, "b", "2026-01-31"), PriorityTask(3, "c", "Low")):
            copy = task_from_dict(task.to_dict())
            self.assertIs(type(copy), type(task))
            self.assertEqual(copy.to_dict(), task.to_dict())

    def test_old_data_without_tags_still_loads(self):
        self.assertEqual(task_from_dict({"id": 1, "description": "old", "completed": False}).tags, [])

    def test_invalid_data_is_rejected(self):
        with self.assertRaises(ValueError):
            task_from_dict({"id": 1, "description": "x", "_type": "Unknown"})
        with self.assertRaises(ValueError):
            task_from_dict({"id": "1", "description": "x"})


if __name__ == "__main__":
    unittest.main()
