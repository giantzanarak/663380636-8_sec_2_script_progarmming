# src/task.py

class Task:
    """
    Represents a single task.

    Attributes:
        id (int): Unique identifier of the task.
        description (str): What needs to be done.
        completed (bool): True when the task is finished, False while it is pending.
    """

    def __init__(self, id: int, description: str, completed: bool = False):
        self.id = id
        self.description = description
        self.completed = completed

    def mark_complete(self):
        """Marks the task as completed."""
        self.completed = True

    def to_dict(self) -> dict:
        """Converts the Task to a dictionary for JSON serialization."""
        return {
            "id": self.id,
            "description": self.description,
            "completed": self.completed
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """
        Creates a Task from a dictionary loaded from JSON (the opposite of to_dict).

        Raises:
            KeyError / TypeError / ValueError: if the dictionary is not a valid task.
        """
        task_id = data["id"]
        description = data["description"]
        if not isinstance(task_id, int) or not isinstance(description, str):
            raise ValueError(f"Invalid task data: {data}")
        return cls(task_id, description, bool(data.get("completed", False)))

    def __str__(self) -> str:
        """Human-readable representation shown in the task list."""
        status = "Completed" if self.completed else "Pending"
        return f"ID: {self.id} | Description: {self.description} | Status: {status}"

    def __repr__(self) -> str:
        """Developer representation used when debugging."""
        return f"Task(id={self.id}, description='{self.description}', completed={self.completed})"
