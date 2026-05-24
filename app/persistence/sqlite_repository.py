"""SQLite-backed TaskRepository.

A new connection is opened per call. SQLite handles cross-process locking via
WAL mode (set on every connection). The schema is applied lazily on the first
connection if the `tasks` table doesn't exist.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from app.domain import Task

# Module-level alias so `list[Task]` in annotations isn't shadowed by the `list` method.
TaskList = list[Task]

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_task(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        status=row["status"],
        order=row["order_index"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _task_to_params(task: Task) -> dict[str, object]:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "order_index": task.order,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


class SQLiteTaskRepository:
    """Concrete `TaskRepository` (PEP 544 structural)."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        schema_sql = _SCHEMA_PATH.read_text()
        with _connect(self._db_path) as conn:
            conn.executescript(schema_sql)

    def list(self) -> TaskList:
        with _connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT id, title, description, status, order_index, "
                "       created_at, updated_at "
                "FROM tasks ORDER BY order_index ASC"
            ).fetchall()
        return [_row_to_task(r) for r in rows]

    def get(self, task_id: str) -> Task | None:
        with _connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT id, title, description, status, order_index, "
                "       created_at, updated_at "
                "FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return _row_to_task(row) if row else None

    def add(self, task: Task) -> None:
        with _connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO tasks "
                "(id, title, description, status, order_index, created_at, updated_at) "
                "VALUES (:id, :title, :description, :status, :order_index, "
                ":created_at, :updated_at)",
                _task_to_params(task),
            )
            conn.commit()

    def update(self, task: Task) -> None:
        with _connect(self._db_path) as conn:
            conn.execute(
                "UPDATE tasks SET "
                "  title = :title, "
                "  description = :description, "
                "  status = :status, "
                "  order_index = :order_index, "
                "  updated_at = :updated_at "
                "WHERE id = :id",
                _task_to_params(task),
            )
            conn.commit()

    def delete(self, task_id: str) -> None:
        with _connect(self._db_path) as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()

    def replace_all(self, tasks: TaskList) -> None:
        with _connect(self._db_path) as conn:
            try:
                conn.execute("BEGIN")
                conn.execute("DELETE FROM tasks")
                conn.executemany(
                    "INSERT INTO tasks "
                    "(id, title, description, status, order_index, created_at, updated_at) "
                    "VALUES (:id, :title, :description, :status, :order_index, "
                    ":created_at, :updated_at)",
                    [_task_to_params(t) for t in tasks],
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
