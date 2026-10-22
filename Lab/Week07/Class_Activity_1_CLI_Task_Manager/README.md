# Week 7 Class Activity 1: Building a Simple CLI Application

A command-line **Task Manager** for adding, listing, searching, completing and deleting tasks.
Tasks are saved to `data/tasks.json` automatically, and invalid input is handled without crashing.

## Result (screenshot)

Menu option **2. List All Tasks**: one task `[DONE]` and one task `[PENDING]`.

![List all tasks](screenshots/list_all_tasks.png)

## How to Run

```bash
cd Lab/Week07/Class_Activity_1_CLI_Task_Manager
python3 main.py
```

No extra packages are needed (standard library only).

```
==================================
        TASK MANAGER CLI
==================================
  1. Add New Task
  2. List All Tasks
  3. List Pending Tasks
  4. List Completed Tasks
  5. Search Tasks by Keyword
  6. Mark Task as Completed
  7. Delete Task
  8. Save and Exit
==================================
```

## Project Structure

```
my-task-manager/
├── src/
│   ├── __init__.py      # makes 'src' a Python package
│   ├── task_data.py     # data layer: load/save data/tasks.json
│   └── task_logic.py    # business logic: add, list, complete, delete, search
├── data/
│   └── tasks.json       # saved tasks
├── screenshots/
├── main.py              # presentation layer: menu loop and input validation
├── .gitignore
└── README.md
```

Each task is a dictionary:

```json
{"id": 1, "description": "Finish Script Programming Week 7 activity", "completed": true, "priority": "High"}
```

## Error Handling

| Situation | What the program does |
|-----------|-----------------------|
| Menu choice is not 1-8 | `[Error] Invalid choice...` and shows the menu again |
| Task ID is not a number (`abc`) or is 0 / negative | catches `ValueError`, asks for a positive number |
| Task ID does not exist | `[Error] Task with ID #99 was not found.` |
| Empty description / search keyword | rejected with an error message |
| Invalid priority | falls back to `Medium` (also accepts `l/m/h` or `1/2/3`) |
| Delete | asks for confirmation `(y/N)` first |
| `tasks.json` missing, empty, broken JSON, or wrong structure | starts with an empty list (invalid entries are skipped) instead of crashing |
| Cannot write the file (`PermissionError` / `OSError`) | prints an error, program keeps running |
| `Ctrl+C` or end of input (`Ctrl+D`) | saves the tasks before exiting |

Saving writes to a temporary file first and then replaces `tasks.json`, so a crash while saving
cannot leave a half-written data file. Every change (add, complete, delete) is saved immediately.

## Debugging in VS Code

1. Open `main.py` and click left of a line number (e.g. inside `handle_complete`) to set a **breakpoint**.
2. Press **F5** → "Python File". Use **F10** (Step Over), **F11** (Step Into), **Shift+F11** (Step Out).
3. Inspect `tasks` and `task_id` in the **Variables** panel and the call chain in **Call Stack**.
