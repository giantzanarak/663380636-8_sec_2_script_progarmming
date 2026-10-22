# Final Project Presentation - Enhanced Task Manager (5–7 minutes)

**Pawat Wongmalasit - 663380636-8**

## 1. Introduction (30 s)
* Name, student ID, project: *Enhanced Task Manager CLI*.
* Goal: a task manager that is complete, reliable and easy to extend.

## 2. Problem solved (30 s)
* A plain to-do list cannot answer "what is due this week?" or "what is urgent?".
* This app adds due dates, priorities and tags, and lets you **search, filter and sort** to find what matters now.

## 3. Live demo (2–3 min)
Run `python main.py` (`data/tasks.json` already has 7 demo tasks).

| Step | Type | Shows |
|------|------|-------|
| 1 | `4` | all tasks: three types, tags, completed/pending, summary line |
| 2 | `7` → `present` | partial search in tags and description (2 results) |
| 3 | `8` → `no`, blank, blank, blank, `urgent` | pending **and** tagged urgent (tasks 1, 3) |
| 4 | `8` → blank, `2026-12-31`, `2026-10-01`, blank, blank | due-date **range** (task 2) |
| 5 | `9` → `priority`, `no` | High → Medium → Low, tasks without priority last |
| 6 | `3` → `Final presentation`, `urgent` (rejected) → `high`, `demo` | input validation, then success |
| 7 | `5` → `abc` | error message, no crash |
| 8 | `0` | exit - data already saved |

Backup plan: screenshots in `screenshots/`, and `python -m unittest discover tests` (24 tests OK).

## 4. Software architecture (1 min)
* 4 layers: `CLIInterface` → `TaskManager` → `DataPersistence` → JSON, plus the `Task` models.
* Separation of concerns: only the CLI talks to the user; only persistence touches files.
* OOP: `DueDateTask` and `PriorityTask` inherit from `Task`; `to_dict()` and `__str__` are polymorphic,
  so saving and printing never check the type.

## 5. Technical challenges & solutions (1 min)
* **Sorting mixed types** - tasks without a due date/priority are split off and kept last in both directions.
* **Priority order** - map High/Medium/Low to 0/1/2 instead of sorting strings.
* **Robust data** - validate each JSON entry; atomic save so the file is never half-written.

## 6. Lessons learned (30 s)
* Planning first made features small and isolated.
* Logic without `print()` is easy to unit-test.
* Edge cases need the most attention.

## 7. Future work & Q&A (30 s)
* Edit tasks, reminders, SQLite storage, GUI/web front-end reusing `TaskManager`.
* Questions?
