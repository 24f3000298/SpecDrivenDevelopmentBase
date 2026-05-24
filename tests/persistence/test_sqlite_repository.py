from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.domain import Task
from app.persistence import SQLiteTaskRepository


@pytest.fixture()
def repo(tmp_path: Path) -> SQLiteTaskRepository:
    return SQLiteTaskRepository(tmp_path / "tasks.db")


def _make(title: str, order: int = 0, status: str = "todo") -> Task:
    return Task.create(title=title, order=order, status=status)


def test_missing_db_file_initializes_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "subdir" / "tasks.db"
    assert not db_path.exists()

    repo = SQLiteTaskRepository(db_path)

    assert db_path.exists()
    assert repo.list() == []


def test_add_and_list_roundtrip(repo: SQLiteTaskRepository) -> None:
    t1 = _make("first", order=0)
    t2 = _make("second", order=1)
    repo.add(t1)
    repo.add(t2)

    listed = repo.list()
    assert [t.id for t in listed] == [t1.id, t2.id]
    assert listed[0].title == "first"
    assert listed[1].title == "second"


def test_get_hit_and_miss(repo: SQLiteTaskRepository) -> None:
    t = _make("only")
    repo.add(t)

    assert repo.get(t.id) is not None
    assert repo.get("nonexistent") is None


def test_update_changes_fields_and_updated_at(repo: SQLiteTaskRepository) -> None:
    t = _make("title-a")
    repo.add(t)

    later = datetime.now(tz=UTC)
    t2 = replace(t, title="title-b", status="done", updated_at=later)
    repo.update(t2)

    got = repo.get(t.id)
    assert got is not None
    assert got.title == "title-b"
    assert got.status == "done"
    # ISO-8601 round-trip should preserve to microsecond precision.
    assert got.updated_at == later


def test_delete_removes_task(repo: SQLiteTaskRepository) -> None:
    t = _make("doomed")
    repo.add(t)
    repo.delete(t.id)
    assert repo.get(t.id) is None
    assert repo.list() == []


def test_delete_missing_is_noop(repo: SQLiteTaskRepository) -> None:
    repo.delete("nonexistent")  # must not raise


def test_replace_all_rewrites_order(repo: SQLiteTaskRepository) -> None:
    a = _make("a", order=0)
    b = _make("b", order=1)
    c = _make("c", order=2)
    repo.add(a)
    repo.add(b)
    repo.add(c)

    # Permute: c, a, b
    repo.replace_all(
        [
            replace(c, order=0),
            replace(a, order=1),
            replace(b, order=2),
        ]
    )

    listed = repo.list()
    assert [t.title for t in listed] == ["c", "a", "b"]


def test_unknown_status_roundtrips(repo: SQLiteTaskRepository) -> None:
    t = _make("blocked-thing", status="blocked")
    repo.add(t)

    got = repo.get(t.id)
    assert got is not None
    assert got.status == "blocked"


def test_persists_across_repository_instances(tmp_path: Path) -> None:
    db_path = tmp_path / "tasks.db"
    repo_a = SQLiteTaskRepository(db_path)
    repo_a.add(_make("survivor"))

    repo_b = SQLiteTaskRepository(db_path)
    listed = repo_b.list()
    assert len(listed) == 1
    assert listed[0].title == "survivor"
