from __future__ import annotations

from datetime import UTC

import pytest

from app.domain import KNOWN_STATUSES, InvalidTaskError, Task


def test_create_fills_defaults() -> None:
    task = Task.create(title="Buy milk")

    assert task.title == "Buy milk"
    assert task.description == ""
    assert task.status == "todo"
    assert task.order == 0
    assert task.id  # non-empty
    assert len(task.id) == 32  # uuid4().hex
    assert task.created_at.tzinfo == UTC
    assert task.created_at == task.updated_at


def test_create_trims_title_whitespace() -> None:
    task = Task.create(title="   Ship v1  ")
    assert task.title == "Ship v1"


def test_create_rejects_empty_title() -> None:
    with pytest.raises(InvalidTaskError):
        Task.create(title="")


def test_create_rejects_whitespace_only_title() -> None:
    with pytest.raises(InvalidTaskError):
        Task.create(title="   \t\n  ")


def test_create_rejects_too_long_title() -> None:
    with pytest.raises(InvalidTaskError):
        Task.create(title="x" * 201)


def test_create_accepts_max_length_title() -> None:
    task = Task.create(title="x" * 200)
    assert len(task.title) == 200


def test_create_rejects_too_long_description() -> None:
    with pytest.raises(InvalidTaskError):
        Task.create(title="ok", description="d" * 2001)


def test_create_accepts_max_length_description() -> None:
    task = Task.create(title="ok", description="d" * 2000)
    assert len(task.description) == 2000


def test_status_forward_compatible() -> None:
    """The factory accepts statuses beyond the v1 todo/done pair."""
    task = Task.create(title="t", status="in-progress")
    assert task.status == "in-progress"


def test_known_statuses_include_kanban_columns() -> None:
    """Documenting the v1 known set; preservation of unknowns is tested elsewhere."""
    assert "todo" in KNOWN_STATUSES
    assert "done" in KNOWN_STATUSES
    assert "in-progress" in KNOWN_STATUSES


def test_task_is_immutable() -> None:
    task = Task.create(title="t")
    with pytest.raises((AttributeError, TypeError)):
        task.title = "changed"  # type: ignore[misc]


def test_ids_are_unique() -> None:
    a = Task.create(title="a")
    b = Task.create(title="b")
    assert a.id != b.id
