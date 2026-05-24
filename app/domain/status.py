"""Open task-status vocabulary.

Status is intentionally a plain ``str`` (not an Enum) so that future Kanban
columns can be added without touching call sites that already preserve the
value losslessly. See ``openspec/changes/scaffold-todo-kanban-app/design.md``
decision D7.
"""

from __future__ import annotations

KNOWN_STATUSES: tuple[str, ...] = (
    "todo",
    "done",
    "in-progress",
    "review",
    "blocked",
)

STATUS_TODO = "todo"
STATUS_DONE = "done"
