"""TaskService — the only mutator of task state.

Routes call into this service; the service calls into the repository. The
service owns the next-order computation, reorder semantics, and any future
cross-cutting concerns (logging, events).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from app.domain import InvalidTaskError, Task
from app.persistence import TaskRepository


class TaskNotFoundError(LookupError):
    """Raised when an operation targets a task id that does not exist."""


class ReorderError(ValueError):
    """Raised when ``reorder_tasks`` is given an id set that does not match storage."""


class TaskService:
    def __init__(self, repo: TaskRepository) -> None:
        self.repo = repo

    def list_tasks(self) -> list[Task]:
        """Return tasks ordered pending-first, done-last, by ``order`` within each group."""
        tasks = self.repo.list()
        return sorted(tasks, key=lambda t: (t.status == "done", t.order))

    def add_task(self, *, title: str, description: str = "") -> Task:
        existing = self.repo.list()
        next_order = max((t.order for t in existing), default=-1) + 1
        task = Task.create(title=title, description=description, order=next_order)
        self.repo.add(task)
        return task

    def update_task(
        self,
        task_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> Task:
        current = self.repo.get(task_id)
        if current is None:
            raise TaskNotFoundError(task_id)
        new_title = title.strip() if title is not None else current.title
        if title is not None and not new_title:
            raise InvalidTaskError("title must be non-empty")
        updated = replace(
            current,
            title=new_title,
            description=description if description is not None else current.description,
            status=status if status is not None else current.status,
            updated_at=datetime.now(tz=UTC),
        )
        self.repo.update(updated)
        return updated

    def delete_task(self, task_id: str) -> None:
        self.repo.delete(task_id)

    def reorder_tasks(self, task_ids: list[str]) -> None:
        existing = self.repo.list()
        existing_ids = {t.id for t in existing}
        if set(task_ids) != existing_ids:
            raise ReorderError("reorder ids do not match existing tasks")
        by_id = {t.id: t for t in existing}
        now = datetime.now(tz=UTC)
        reordered = [
            replace(by_id[task_id], order=i, updated_at=now)
            for i, task_id in enumerate(task_ids)
        ]
        self.repo.replace_all(reordered)
