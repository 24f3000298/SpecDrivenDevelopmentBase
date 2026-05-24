from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from app.domain import Task
from app.persistence import InMemoryTaskRepository


@pytest.fixture()
def repo() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()


def _make(title: str, order: int = 0, status: str = "todo") -> Task:
    return Task.create(title=title, order=order, status=status)


def test_empty_list(repo: InMemoryTaskRepository) -> None:
    assert repo.list() == []


def test_add_and_list(repo: InMemoryTaskRepository) -> None:
    a = _make("a", order=0)
    b = _make("b", order=1)
    repo.add(a)
    repo.add(b)
    assert [t.title for t in repo.list()] == ["a", "b"]


def test_get_hit_and_miss(repo: InMemoryTaskRepository) -> None:
    t = _make("x")
    repo.add(t)
    assert repo.get(t.id) is t  # exact object preserved
    assert repo.get("missing") is None


def test_update_replaces_entry(repo: InMemoryTaskRepository) -> None:
    t = _make("a")
    repo.add(t)

    later = datetime.now(tz=UTC)
    t2 = replace(t, title="b", updated_at=later)
    repo.update(t2)

    got = repo.get(t.id)
    assert got is not None
    assert got.title == "b"
    assert got.updated_at == later


def test_delete_removes(repo: InMemoryTaskRepository) -> None:
    t = _make("x")
    repo.add(t)
    repo.delete(t.id)
    assert repo.get(t.id) is None


def test_delete_missing_is_noop(repo: InMemoryTaskRepository) -> None:
    repo.delete("nope")


def test_replace_all(repo: InMemoryTaskRepository) -> None:
    a = _make("a", order=0)
    b = _make("b", order=1)
    repo.add(a)

    repo.replace_all([b])
    assert [t.title for t in repo.list()] == ["b"]
    assert repo.get(a.id) is None


def test_unknown_status_roundtrips(repo: InMemoryTaskRepository) -> None:
    t = _make("x", status="review")
    repo.add(t)
    got = repo.get(t.id)
    assert got is not None
    assert got.status == "review"
