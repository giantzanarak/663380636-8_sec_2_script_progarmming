# tests/test_task.py
import unittest

from src.task import Task


class TestTaskClass(unittest.TestCase):
    """Tests for the Task class."""

    def test_task_initialization(self):
        t = Task(1, "Read OOP textbook")
        self.assertEqual(t.id, 1)
        self.assertEqual(t.description, "Read OOP textbook")
        self.assertFalse(t.completed, "completed should default to False")

    def test_task_initialization_with_completed_true(self):
        t = Task(2, "Submit lab report", completed=True)
        self.assertTrue(t.completed)

    def test_mark_complete(self):
        t = Task(3, "Practice Python coding")
        t.mark_complete()
        self.assertTrue(t.completed)

    def test_to_dict(self):
        t = Task(10, "Refactor CLI code")
        self.assertEqual(t.to_dict(), {"id": 10, "description": "Refactor CLI code", "completed": False})

    def test_from_dict_round_trip(self):
        original = Task(4, "Write README", completed=True)
        copy = Task.from_dict(original.to_dict())
        self.assertEqual(repr(copy), repr(original))

    def test_from_dict_rejects_invalid_data(self):
        with self.assertRaises(KeyError):
            Task.from_dict({"description": "no id"})
        with self.assertRaises(ValueError):
            Task.from_dict({"id": "1", "description": "id is a string"})

    def test_str_representation(self):
        self.assertEqual(str(Task(1, "Write tests")), "ID: 1 | Description: Write tests | Status: Pending")
        self.assertIn("Completed", str(Task(2, "Review PR", completed=True)))

    def test_repr_representation(self):
        self.assertEqual(repr(Task(5, "Fix bug", completed=True)), "Task(id=5, description='Fix bug', completed=True)")


if __name__ == '__main__':
    unittest.main()
