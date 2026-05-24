from __future__ import annotations

import pytest

from app.domain import InvalidTaskError
from app.persistence import InMemoryTaskRepository
from app.services import ReorderError, TaskNotFoundError, TaskService


@pytest.fixture()
def service() -> TaskService:
    return TaskService(InMemoryTaskRepository())


def test_add_task_assigns_next_order(service: TaskService) -> None:
    a = service.add_task(title="a")
    b = service.add_task(title="b")
    c = service.add_task(title="c")

    assert (a.order, b.order, c.order) == (0, 1, 2)


def test_add_task_status_defaults_to_todo(service: TaskService) -> None:
    t = service.add_task(title="x")
    assert t.status == "todo"


def test_update_task_changes_fields_and_bumps_updated_at(service: TaskService) -> None:
    t = service.add_task(title="a")
    original_updated = t.updated_at

    updated = service.update_task(t.id, status="done", title="b")

    assert updated.status == "done"
    assert updated.title == "b"
    assert updated.updated_at >= original_updated
    assert updated.created_at == t.created_at


def test_update_missing_raises(service: TaskService) -> None:
    with pytest.raises(TaskNotFoundError):
        service.update_task("nope", title="x")


def test_update_rejects_empty_title(service: TaskService) -> None:
    t = service.add_task(title="ok")
    with pytest.raises(InvalidTaskError):
        service.update_task(t.id, title="   ")


def test_delete_task(service: TaskService) -> None:
    t = service.add_task(title="x")
    service.delete_task(t.id)
    assert service.list_tasks() == []


def test_delete_missing_is_noop(service: TaskService) -> None:
    service.delete_task("nope")


def test_reorder_rewrites_order(service: TaskService) -> None:
    a = service.add_task(title="a")
    b = service.add_task(title="b")
    c = service.add_task(title="c")

    service.reorder_tasks([c.id, a.id, b.id])

    listed = service.list_tasks()
    assert [t.title for t in listed] == ["c", "a", "b"]
    assert [t.order for t in listed] == [0, 1, 2]


def test_reorder_rejects_mismatched_ids(service: TaskService) -> None:
    a = service.add_task(title="a")
    service.add_task(title="b")

    with pytest.raises(ReorderError):
        service.reorder_tasks([a.id])  # missing b


def test_list_tasks_puts_done_last(service: TaskService) -> None:
    a = service.add_task(title="a")  # order 0
    service.add_task(title="b")  # order 1
    service.add_task(title="c")  # order 2

    service.update_task(a.id, status="done")

    listed = service.list_tasks()
    assert [t.title for t in listed] == ["b", "c", "a"]


def test_list_tasks_unknown_status_sorts_with_pending(service: TaskService) -> None:
    a = service.add_task(title="a")  # order 0
    service.add_task(title="b")  # order 1

    service.update_task(a.id, status="in-progress")

    listed = service.list_tasks()
    # 'in-progress' != 'done', so it stays in the pending group sorted by order
    assert [t.title for t in listed] == ["a", "b"]


def test_unknown_status_roundtrips_through_service(service: TaskService) -> None:
    t = service.add_task(title="x")
    service.update_task(t.id, status="blocked")

    listed = service.list_tasks()
    assert listed[0].status == "blocked"
