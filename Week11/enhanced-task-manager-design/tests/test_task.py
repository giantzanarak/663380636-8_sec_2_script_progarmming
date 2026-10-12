# tests/test_task.py
import datetime
import unittest

from src.task import DueDateTask, PriorityTask, Task, task_from_dict


class TestTaskModels(unittest.TestCase):

    def test_task_defaults_and_tags(self):
        t = Task(1, "Read", tags=[" study ", "study", ""])
        self.assertFalse(t.completed)
        self.assertEqual(t.tags, ["study"], "tags are trimmed, empty ones dropped, no duplicates")

    def test_mark_complete(self):
        t = Task(1, "Read")
        t.mark_complete()
        self.assertTrue(t.completed)

    def test_due_date_task_parses_date(self):
        t = DueDateTask(2, "Submit", "2026-10-20")
        self.assertEqual(t.due_date, datetime.date(2026, 10, 20))
        with self.assertRaises(ValueError):
            DueDateTask(3, "Bad", "20-10-2026")

    def test_overdue(self):
        t = DueDateTask(2, "Submit", "2026-10-10")
        self.assertTrue(t.is_overdue(today=datetime.date(2026, 10, 13)))
        self.assertFalse(t.is_overdue(today=datetime.date(2026, 10, 1)))
        t.mark_complete()
        self.assertFalse(t.is_overdue(today=datetime.date(2026, 10, 13)), "completed tasks are never overdue")

    def test_priority_validation(self):
        self.assertEqual(PriorityTask(1, "x", "high").priority, "High")
        with self.assertRaises(ValueError):
            PriorityTask(1, "x", "urgent")

    def test_polymorphic_str(self):
        self.assertIn("Due: 2099-01-01", str(DueDateTask(1, "a", "2099-01-01")))
        self.assertIn("Priority: Low", str(PriorityTask(2, "b", "Low", tags=["x"])))
        self.assertTrue(str(PriorityTask(2, "b", "Low", tags=["x"])).endswith("Tags: x"))

    def test_round_trip_through_dict(self):
        for task in (Task(1, "a", True, ["t"]), DueDateTask(2, "b", "2026-01-31"), PriorityTask(3, "c", "Medium")):
            copy = task_from_dict(task.to_dict())
            self.assertIs(type(copy), type(task))
            self.assertEqual(copy.to_dict(), task.to_dict())

    def test_task_from_dict_rejects_bad_data(self):
        with self.assertRaises(ValueError):
            task_from_dict({"id": 1, "description": "x", "_type": "UnknownTask"})
        with self.assertRaises(ValueError):
            task_from_dict({"id": "1", "description": "x"})


if __name__ == "__main__":
    unittest.main()
