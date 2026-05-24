"""In-memory TaskRepository for tests and `TestConfig` runs."""

from __future__ import annotations

from app.domain import Task

# Module-level alias so `list[Task]` in annotations isn't shadowed by the `list` method.
TaskList = list[Task]


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def list(self) -> TaskList:
        return sorted(self._tasks.values(), key=lambda t: t.order)

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def add(self, task: Task) -> None:
        self._tasks[task.id] = task

    def update(self, task: Task) -> None:
        self._tasks[task.id] = task

    def delete(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)

    def replace_all(self, tasks: TaskList) -> None:
        self._tasks = {t.id: t for t in tasks}
