# src/task.py
"""
Data models for the Task Manager.

Task is the base class; DueDateTask and PriorityTask inherit from it (inheritance) and
override to_dict() and _detail_parts() to add their own fields (polymorphism).
"""

import datetime

DATE_FORMAT = "%Y-%m-%d"
PRIORITY_LEVELS = ["High", "Medium", "Low"]  # most important first


def parse_date(value):
    """
    Converts a 'YYYY-MM-DD' string (or a datetime.date) into a datetime.date.

    Raises:
        ValueError: if the string is not a valid YYYY-MM-DD date.
        TypeError: if the value is neither a string nor a date.
    """
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        return datetime.datetime.strptime(value.strip(), DATE_FORMAT).date()
    raise TypeError("date must be a 'YYYY-MM-DD' string or a datetime.date")


def normalize_tag(tag):
    """Tags are stored trimmed and lower-case, so 'Python ' and 'python' are the same tag."""
    return str(tag).strip().lower()


class Task:
    """A basic task with an id, a description, a completion status and tags."""

    TYPE_NAME = "Task"

    def __init__(self, id, description, completed=False, tags=None):
        self.id = id
        self.description = description
        self.completed = completed
        self.tags = []
        for tag in tags or []:
            self.add_tag(tag)

    def mark_complete(self):
        """Marks the task as completed."""
        self.completed = True

    def add_tag(self, tag):
        """Adds a normalized tag. Empty tags and duplicates are ignored. Returns True if added."""
        tag = normalize_tag(tag)
        if tag and tag not in self.tags:
            self.tags.append(tag)
            return True
        return False

    def remove_tag(self, tag):
        """Removes a tag if present. Returns True if it was removed."""
        tag = normalize_tag(tag)
        if tag in self.tags:
            self.tags.remove(tag)
            return True
        return False

    def has_tag(self, tag):
        """True if the task has this tag (case-insensitive)."""
        return normalize_tag(tag) in self.tags

    def to_dict(self):
        """Converts the task to a dict for JSON. '_type' tells the loader which class to rebuild."""
        return {
            "id": self.id,
            "description": self.description,
            "completed": self.completed,
            "tags": list(self.tags),
            "_type": self.TYPE_NAME,
        }

    def _detail_parts(self):
        """Extra fields shown by __str__; subclasses override this to add their own."""
        return []

    def __str__(self):
        status = "Completed" if self.completed else "Pending"
        parts = [f"ID: {self.id}", f"Description: {self.description}", f"Status: {status}"]
        parts += self._detail_parts()
        if self.tags:
            parts.append(f"Tags: {', '.join(self.tags)}")
        return " | ".join(parts)

    def __repr__(self):
        return (f"{self.TYPE_NAME}(id={self.id}, description='{self.description}', "
                f"completed={self.completed}, tags={self.tags})")


class DueDateTask(Task):
    """A task with a due date (stored as datetime.date)."""

    TYPE_NAME = "DueDateTask"

    def __init__(self, id, description, due_date, completed=False, tags=None):
        super().__init__(id, description, completed, tags)
        self.due_date = parse_date(due_date)

    def is_overdue(self, today=None):
        """True if the due date has passed and the task is not completed."""
        return not self.completed and self.due_date < (today or datetime.date.today())

    def to_dict(self):
        data = super().to_dict()
        data["due_date"] = self.due_date.strftime(DATE_FORMAT)
        return data

    def _detail_parts(self):
        due = f"Due: {self.due_date.strftime(DATE_FORMAT)}"
        return [due + (" (OVERDUE)" if self.is_overdue() else "")]

    def __repr__(self):
        return (f"DueDateTask(id={self.id}, description='{self.description}', "
                f"due_date='{self.due_date.strftime(DATE_FORMAT)}', completed={self.completed}, tags={self.tags})")


class PriorityTask(Task):
    """A task with a priority level: High, Medium or Low."""

    TYPE_NAME = "PriorityTask"

    def __init__(self, id, description, priority, completed=False, tags=None):
        super().__init__(id, description, completed, tags)
        priority = str(priority).strip().capitalize()
        if priority not in PRIORITY_LEVELS:
            raise ValueError(f"priority must be one of {PRIORITY_LEVELS}, got '{priority}'")
        self.priority = priority

    def to_dict(self):
        data = super().to_dict()
        data["priority"] = self.priority
        return data

    def _detail_parts(self):
        return [f"Priority: {self.priority}"]

    def __repr__(self):
        return (f"PriorityTask(id={self.id}, description='{self.description}', "
                f"priority='{self.priority}', completed={self.completed}, tags={self.tags})")


# Maps the '_type' value saved in JSON back to the class
TASK_TYPES = {cls.TYPE_NAME: cls for cls in (Task, DueDateTask, PriorityTask)}


def task_from_dict(data):
    """
    Rebuilds a Task / DueDateTask / PriorityTask from a dict loaded from JSON.

    Raises:
        ValueError / TypeError: if the data is not a valid task.
    """
    fields = dict(data)
    type_name = fields.pop("_type", "Task")
    fields.setdefault("tags", [])  # older files may not have tags
    cls = TASK_TYPES.get(type_name)
    if cls is None:
        raise ValueError(f"unknown task type '{type_name}'")
    if not isinstance(fields.get("id"), int) or not isinstance(fields.get("description"), str):
        raise ValueError("task needs an integer 'id' and a string 'description'")
    return cls(**fields)
