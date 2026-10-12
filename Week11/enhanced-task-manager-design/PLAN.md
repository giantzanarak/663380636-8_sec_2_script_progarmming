# Project Plan: Enhanced Task Manager CLI

## 1. Introduction
The Week 7–8 Task Manager only stored a description and a done/pending status. This version
adds **task types** (due-date and priority tasks), **tags**, and **search / filter / sort**, while
keeping a clean layered design so each part can be changed and tested on its own.

## 2. Requirements

### 2.1 Functional requirements
| ID | Requirement |
|----|-------------|
| FR1 | Add a normal task, a task with a due date (YYYY-MM-DD), or a task with a priority (High/Medium/Low) |
| FR2 | Any task can have zero or more tags |
| FR3 | List all tasks with their type-specific details; overdue tasks are marked |
| FR4 | Mark a task as completed; delete a task (with confirmation) |
| FR5 | Search by keyword in the description **or** tags (case-insensitive) |
| FR6 | Filter by status, due date (on or before), priority and tags - conditions are combined with AND |
| FR7 | Sort by id, due date, priority or description, ascending or descending |
| FR8 | Tasks are saved to `data/tasks.json` after every change and loaded on start |

### 2.2 Non-functional requirements
| ID | Requirement |
|----|-------------|
| NFR1 | **Robustness** - invalid input never crashes the program; a missing/corrupted data file starts an empty list; invalid entries are skipped |
| NFR2 | **Data safety** - saving writes a temporary file and replaces `tasks.json`, so the file is never half-written |
| NFR3 | **Maintainability** - presentation, logic and storage are separate modules (Separation of Concerns) |
| NFR4 | **Extensibility** - adding a new task type only needs a new subclass registered in `TASK_TYPES` |
| NFR5 | **Testability** - business logic has no `input()`/`print()` and is covered by unit tests |
| NFR6 | Standard library only; Thai text supported (UTF-8 JSON, `ensure_ascii=False`) |

## 3. Architecture

### 3.1 Layers
```
            user
             │  keyboard / screen
┌────────────▼─────────────┐
│ CLIInterface             │  Presentation: menu, prompts, validation, display
│ src/cli_interface.py     │
└────────────┬─────────────┘
             │ method calls (returns tasks / (success, message))
┌────────────▼─────────────┐
│ TaskManager              │  Business logic: CRUD, search, filter, sort, summary
│ src/task_manager.py      │
└──────┬────────────┬──────┘
       │ uses       │ load / save
┌──────▼──────┐ ┌───▼──────────────────┐
│ Task models │ │ DataPersistence      │  Data layer: JSON <-> objects
│ src/task.py │ │ src/data_persistence │
└─────────────┘ └───┬──────────────────┘
                    ▼
             data/tasks.json
```

### 3.2 Directory structure
```
enhanced-task-manager-design/
├── src/
│   ├── task.py              # Task, DueDateTask, PriorityTask, task_from_dict
│   ├── data_persistence.py  # DataPersistence
│   ├── task_manager.py      # TaskManager
│   └── cli_interface.py     # CLIInterface
├── tests/                   # unittest suites
├── data/tasks.json
├── main.py                  # wires TaskManager + CLIInterface together
├── PLAN.md                  # this document
└── README.md
```

### 3.3 Module responsibilities
| Module | Knows about | Does **not** know about |
|--------|-------------|-------------------------|
| `task.py` | one task's data and behaviour | files, other tasks, the user |
| `data_persistence.py` | JSON format, file path | menus, searching |
| `task_manager.py` | the task collection and its rules | `input()` / `print()`, file format |
| `cli_interface.py` | menus, prompts, formatting | how tasks are stored |

## 4. Class Design (inheritance & polymorphism)
```
Task
├─ id, description, completed, tags
├─ mark_complete(), add_tag(), remove_tag(), has_tag()
├─ to_dict()          ← overridden
├─ _detail_parts()    ← overridden (used by __str__)
│
├── DueDateTask(Task)   + due_date: date, is_overdue()
│     to_dict() adds "due_date";  _detail_parts() -> "Due: 2026-10-20 (OVERDUE)"
│
└── PriorityTask(Task)  + priority: "High" | "Medium" | "Low"
      to_dict() adds "priority";  _detail_parts() -> "Priority: High"
```
Each saved dict has a `_type` field; `task_from_dict()` looks it up in `TASK_TYPES` to rebuild the right class.
`DataPersistence.save_tasks()` simply calls `task.to_dict()` on every object - polymorphism means it never
needs to check the type.

## 5. Design decisions & challenges
| Challenge | Decision |
|-----------|----------|
| Sorting mixed task types by due date / priority | Tasks that have the field are sorted; tasks without it are always placed **after** them (ordered by id), in both directions |
| Priority order is not alphabetical | `PRIORITY_LEVELS = ["High", "Medium", "Low"]`; the index is the sort key |
| Ties when sorting | secondary key is `id`, so the result is stable and predictable |
| Several filter conditions | combined with AND; an empty condition is ignored |
| Old or hand-edited JSON | each entry is validated; bad ones are reported and skipped instead of crashing |
| Logic must be testable | `TaskManager` returns data or `(success, message)`; only the CLI prints |

## 6. Future enhancements
* Edit a task (description, due date, priority, tags)
* Reminders for tasks due today / overdue at start-up
* Recurring tasks (a new subclass, e.g. `RecurringTask`)
* Export to CSV, or SQLite storage behind the same `DataPersistence` interface
