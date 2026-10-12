# Week 11 Class Activity 4: Project Planning & Design - Building an Enhanced Task Manager

A planned and layered version of the Task Manager CLI with **three task types**, **tags**, and
working **search, filter and sort**. The design is documented in [PLAN.md](PLAN.md).

## Results (screenshots)

![Run 1](screenshots/run_1.png)

![Run 2](screenshots/run_2.png)

## How to Run

```bash
cd Week11/enhanced-task-manager-design
python3 main.py                         # CLI (Thai menu)
python3 -m unittest discover -v         # 23 unit tests
```

Standard library only - nothing to install. `data/tasks.json` already contains 6 example tasks.

## Menu

| # | Option | Notes |
|---|--------|-------|
| 1 | Add Normal Task | description + tags |
| 2 | Add Due Date Task | date must be `YYYY-MM-DD` (asks again if wrong) |
| 3 | Add Priority Task | High / Medium / Low (asks again if wrong) |
| 4 | List All Tasks | overdue tasks show `(OVERDUE)`; summary line at the end |
| 5 | Complete Task | by ID |
| 6 | Delete Task | by ID, asks for confirmation |
| 7 | **Search Tasks** | keyword in description **or** tags, case-insensitive |
| 8 | **Filter Tasks** | status, due on/before a date, priority, tags - all combined (AND) |
| 9 | **Sort Tasks** | id / due_date / priority / description, ascending or descending |
| 0 | Exit | |

Example: *Filter → pending + tag `python`* returns tasks 3, 4, 5; *Sort → priority* gives
High → Medium → Low, followed by the tasks that have no priority.

## Project Structure

```
enhanced-task-manager-design/
├── src/
│   ├── task.py              # Task + DueDateTask + PriorityTask (inheritance, polymorphism)
│   ├── data_persistence.py  # JSON load/save, rebuilds the right class from "_type"
│   ├── task_manager.py      # business logic: CRUD, search, filter, sort, summary
│   └── cli_interface.py     # menu, input validation, display
├── tests/
│   ├── test_task.py
│   └── test_task_manager.py
├── data/tasks.json
├── main.py
├── PLAN.md                  # requirements, architecture, class design, decisions
└── README.md
```

## What was implemented

The starter code left `search_tasks`, `filter_tasks` and `sort_tasks` as placeholders. They are now implemented in
[task_manager.py](src/task_manager.py):

* `search_tasks(keyword)` - matches the description or any tag (case-insensitive).
* `filter_tasks(status, due_date_before, priority, tags)` - every given condition must hold; the due date limit
  is inclusive; `tags` can be one tag or a list (all must be present); invalid dates/priorities raise `ValueError`.
* `sort_tasks(criterion, reverse)` - returns a new sorted list (stored order is unchanged); tasks without a
  due date / priority always stay at the end; ties are ordered by id.

Other improvements: `__str__` is built from an overridable `_detail_parts()` hook instead of string splitting,
priority values are validated, overdue detection, safe (atomic) saving, skipping invalid JSON entries,
`Ctrl+C` handling, and unit tests for every feature.
