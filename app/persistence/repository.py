"""Persistence contract.

Any storage backend (SQLite, in-memory, a future HTTP API) must satisfy this
protocol. Services and routes depend on the protocol, not on a concrete
implementation.
"""

from __future__ import annotations

from typing import Protocol

from app.domain import Task

# Module-level alias so `list[Task]` in annotations isn't shadowed by the `list` method.
TaskList = list[Task]


class TaskRepository(Protocol):
    def list(self) -> TaskList: ...

    def get(self, task_id: str) -> Task | None: ...

    def add(self, task: Task) -> None: ...

    def update(self, task: Task) -> None: ...

    def delete(self, task_id: str) -> None: ...

    def replace_all(self, tasks: TaskList) -> None: ...
