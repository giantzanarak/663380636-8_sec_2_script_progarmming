# Project Plan & Implementation Notes: Enhanced Task Manager

**Pawat Wongmalasit - 663380636-8**

## 1. Goal
Turn the simple Week 7–8 task list into a complete application: different kinds of tasks, tags,
and tools to find the right tasks quickly (search, filter, sort) - with a design that stays easy to
change and test.

## 2. Requirements

### Functional
| ID | Requirement | Status |
|----|-------------|--------|
| FR1 | Add normal, due-date (YYYY-MM-DD) and priority (High/Medium/Low) tasks | ✅ |
| FR2 | Tags on every task; `add_tag` / `remove_tag`; normalized, no duplicates | ✅ |
| FR3 | List all tasks with type-specific details and an overdue marker | ✅ |
| FR4 | Complete and delete tasks by ID (delete asks for confirmation) | ✅ |
| FR5 | Search description and tags (partial, case-insensitive) | ✅ |
| FR6 | Filter by status, due date before/after, priority, tags - combined with AND | ✅ |
| FR7 | Sort by id, description, completed, due date, priority; ascending/descending | ✅ |
| FR8 | Save to `data/tasks.json` after every change; load on start | ✅ |

### Non-functional
| ID | Requirement | How |
|----|-------------|-----|
| NFR1 | Never crash on bad input or bad data | input loops in the CLI, `ValueError` safety net, invalid JSON entries skipped |
| NFR2 | Data safety | write to a temp file, then `os.replace()` |
| NFR3 | Maintainability | 4 layers with one job each; no `print()` in business logic |
| NFR4 | Testability | 24 unit tests with a temporary data file |
| NFR5 | Observability | `logging` to `logs/task_manager.log` (`--debug` shows it in the terminal) |

## 3. Architecture
```
            ┌──────────────┐
  user ───> │ CLIInterface │  menu, prompts, validation, output
            └──────┬───────┘
                   │ calls methods, gets data / (success, message)
            ┌──────▼───────┐
            │ TaskManager  │  CRUD, search, filter, sort, summary
            └──┬────────┬──┘
               │        │ load / save
   ┌───────────▼──┐  ┌──▼──────────────┐
   │ Task models  │  │ DataPersistence │ ──> data/tasks.json
   └──────────────┘  └─────────────────┘
```

### Class design
```
Task (id, description, completed, tags)
 ├─ mark_complete(), add_tag(), remove_tag(), has_tag()
 ├─ to_dict()        ← overridden by subclasses
 ├─ _detail_parts()  ← overridden by subclasses (used by __str__)
 ├── DueDateTask   + due_date, is_overdue()
 └── PriorityTask  + priority ∈ {High, Medium, Low}
```
`to_dict()` writes a `_type` field; `task_from_dict()` uses the `TASK_TYPES` registry to rebuild the right class.

## 4. Implementation phases
1. **Models** - tags with normalization, validation of dates and priorities, `_detail_parts()` hook for `__str__`.
2. **Persistence** - `_type`-based loading, `setdefault("tags", [])` for old files, skip invalid entries, atomic save.
3. **Business logic** - CRUD returning `(success, message)`; then search → filter → sort, each tested before the next.
4. **CLI** - English menu 0–9, input loops for every field, delete confirmation, `Ctrl+C` handling.
5. **Quality** - logging, unit tests, docstrings, README / PLAN / PRESENTATION, demo data.

## 5. Technical challenges & solutions
| Challenge | Solution |
|-----------|----------|
| **Sorting mixed task types** - a normal task has no `due_date`/`priority`, so `sorted()` would fail or mix them in | Split into "has the field" and "doesn't"; sort the first group, append the second in id order. They stay last in both ascending and descending order |
| **Priority order is not alphabetical** ("High" < "Low" < "Medium" as strings) | `PRIORITY_LEVELS = ["High", "Medium", "Low"]`; sort key is the index |
| **Stable results** | every sort key ends with `id`, so ties always come out in the same order |
| **`__str__` in subclasses** - the starter code split the parent string on `" | Tags:"` to insert fields before the tags | The parent builds the line from `_detail_parts()`, which each subclass overrides - no string surgery |
| **Combining filter conditions** | start from all tasks and narrow the list one condition at a time; `None`/blank = skip |
| **Invalid date range** (after > before) | `ValueError` in the logic; the CLI asks for the range again |
| **Corrupted or hand-edited JSON** | each entry is validated separately; bad entries are logged and skipped instead of losing all data |
| **Logging vs. a clean menu** | INFO goes to a log file, only warnings reach the terminal (unless `--debug`) |

## 6. Testing
* `tests/test_task.py` - tags, validation, overdue, `__str__`, JSON round-trip, old data without tags.
* `tests/test_task_manager.py` - unique IDs, complete/delete, reload, corrupted files, search, every filter
  (including combined conditions and the date range), every sort criterion in both directions.
* Manual CLI checks: invalid menu choice, empty description, `2026-02-30`, wrong priority, non-numeric and
  negative IDs, unknown ID, invalid filter range, unknown sort criterion, cancelled delete.

## 7. Lessons learned
* Planning the layers first made the new features small: search/filter/sort only touched `task_manager.py`
  and one CLI method each.
* Keeping `print()` out of the logic made it easy to unit-test - tests compare lists of IDs.
* Polymorphism removes `if type == ...` checks: saving and printing just call the object's own method.
* Edge cases (tasks without a field, empty input, broken files) take more thought than the "happy path".
* Small, frequent commits make it easy to see and undo each step.

## 8. Future work
* Edit tasks (description, due date, priority, tags) and add/remove tags from the menu.
* A task that has both a due date and a priority (composition instead of separate subclasses).
* Reminders for tasks due today/overdue at start-up.
* SQLite storage behind the same `DataPersistence` interface; export to CSV.
* A GUI (Tkinter) or web interface (Flask) reusing `TaskManager` unchanged.
