# Week 8 Class Activity 2: OOP Fundamentals & Refactoring the CLI Task Manager

The Week 7 CLI Task Manager rewritten with **Object-Oriented Programming**:
a `Task` class for one task and a `TaskManager` class that owns the task list,
saves it to `data/tasks.json` and performs all operations.

## Result (screenshot)

Menu option **2. List Tasks**: one task `Pending` and one task `Completed`.

![List tasks](screenshots/list_tasks.png)

## How to Run

```bash
cd "Class Activity/Week08 - Class Activity 2"
python3 main.py                        # run the CLI
python3 -m unittest discover -v        # run the 18 unit tests
```

Standard library only - nothing to install.

```
--- OOP Task Manager Menu ---
1. Add Task
2. List Tasks
3. Complete Task
4. Delete Task
5. Exit
```

## Class Design

```
Task                                   TaskManager
├─ id: int                             ├─ tasks: list[Task]
├─ description: str                    ├─ next_id: int
├─ completed: bool                     ├─ add_task(description) -> Task | None
├─ mark_complete()                     ├─ list_tasks()
├─ to_dict() -> dict      (save)       ├─ complete_task(task_id) -> bool
├─ from_dict(dict) -> Task (load)      ├─ delete_task(task_id) -> bool
├─ __str__()  -> "ID: 1 | ... "        ├─ get_task(task_id) -> Task | None
└─ __repr__() -> "Task(id=1, ...)"     ├─ _load_tasks()  (JSON -> Task objects)
                                       └─ _save_tasks()  (Task objects -> JSON)
```

| OOP concept | Where |
|-------------|-------|
| **Class & object** | `Task(1, "Write tests")` creates a Task object |
| **Encapsulation** | `TaskManager` hides the list and the file handling; `main.py` only calls its methods. `_load_tasks` / `_save_tasks` are internal (leading `_`) |
| **Constructor** | `__init__` sets attributes; `TaskManager.__init__` also loads the saved tasks |
| **Methods** | `mark_complete()` changes the object's own state |
| **Special methods** | `__str__` for users, `__repr__` for debugging |
| **Class method** | `Task.from_dict()` builds a Task from saved JSON data |

## Project Structure

```
my-oop-task-manager/
├── src/
│   ├── __init__.py
│   ├── task.py           # Task class
│   └── task_manager.py   # TaskManager class (logic + JSON persistence)
├── tests/
│   ├── test_task.py
│   └── test_task_manager.py
├── data/
│   └── tasks.json
├── screenshots/
├── main.py               # CLI menu
└── README.md
```

## Error Handling & Tests

* Non-numeric task ID → "Invalid input. Please enter a number for Task ID."
* Unknown task ID → "Error: Task with ID 9 not found." (methods return `False`)
* Empty description → rejected; invalid menu choice → message and menu again
* `tasks.json` empty, corrupted, not a list, or containing invalid entries → loads what is valid, never crashes
* Saving writes a temporary file and then replaces `tasks.json` (no half-written file)
* `Ctrl+C` / `Ctrl+D` exits cleanly (every change is already saved)

The 18 unit tests cover the Task class, add/complete/delete, reloading from disk, and the
broken-file cases. Each TaskManager test uses its own temporary file, so `data/tasks.json` is never touched.
