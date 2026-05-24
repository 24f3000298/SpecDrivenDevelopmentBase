## Purpose

Defines the core task domain — the `Task` entity shape, the `TaskRepository` persistence contract, and the `TaskService` mutation API. Status and ordering are designed to support a future Kanban board without changes to call sites that don't render unknown statuses.

## Requirements

### Requirement: Task entity shape

The system SHALL model every task as a Python dataclass (or attrs class / Pydantic model — implementation choice) with the following fields:

- `id`: string, globally unique (UUID v4, generated via `uuid.uuid4().hex`).
- `title`: string, non-empty after trimming, max 200 characters.
- `description`: string, optional, max 2000 characters; defaults to `""`.
- `status`: string. v1 accepts `"todo"` and `"done"`. The type MUST be modeled so additional values (e.g. `"in-progress"`, `"review"`, `"blocked"`) can be stored and read back without code changes in non-display call sites.
- `order`: integer. Determines display order. Lower values render first.
- `created_at`: `datetime` in UTC, set at creation, never mutated afterward.
- `updated_at`: `datetime` in UTC, refreshed on every mutation.

The system SHALL NOT permit constructing `Task` objects with missing or malformed fields; a factory (e.g. `Task.create(...)`) MUST enforce these invariants and raise a domain-specific exception (e.g. `InvalidTaskError`) on violation.

The `Task` class MUST live in a framework-free module (no Flask, no `sqlite3` imports).

#### Scenario: Creating a task fills defaults

- **WHEN** a caller invokes the task factory with only `title="Buy milk"`
- **THEN** the returned `Task` has a UUID `id`, `status == "todo"`, an `order` integer, equal `created_at` and `updated_at` (both UTC), and `description == ""`

#### Scenario: Rejecting an empty title

- **WHEN** a caller invokes the task factory with `title="   "`
- **THEN** the factory raises `InvalidTaskError` and no task is created

#### Scenario: Status is forward-compatible

- **WHEN** a stored task is loaded with `status="in-progress"`
- **THEN** the repository returns it without error, even though the v1 UI does not yet render that column

### Requirement: TaskRepository persistence contract

The system SHALL expose a `TaskRepository` protocol (or ABC) in a framework-free module that defines, at minimum:

- `list() -> list[Task]` — returns all tasks.
- `get(task_id: str) -> Task | None` — returns a task by id, or `None` if absent.
- `add(task: Task) -> None` — inserts a new task.
- `update(task: Task) -> None` — updates an existing task (matched by `id`).
- `delete(task_id: str) -> None` — removes a task by id; no-op if absent.
- `replace_all(tasks: list[Task]) -> None` — atomically overwrites the persisted collection (used by reorder).

The system SHALL ship a `SQLiteTaskRepository` implementation backed by a single SQLite file at `instance/tasks.db` (path configurable). The schema MUST live in a versioned migration step so future schema changes can be detected and applied.

Route handlers, templates, and the task service MUST NOT execute SQL directly; all persistence MUST go through the repository.

#### Scenario: Round-trip through SQLite

- **WHEN** the app calls `repo.add(t1); repo.add(t2); repo.add(t3)`, the process restarts, and the app calls `repo.list()`
- **THEN** the returned list contains the same three tasks with identical field values (titles, statuses, orders, timestamps preserved to second precision)

#### Scenario: Missing database file is initialized

- **WHEN** the configured database path does not exist on startup
- **THEN** the repository creates the file and applies the schema, and `list()` returns `[]`

#### Scenario: Repository is swappable

- **WHEN** a test substitutes an `InMemoryTaskRepository` for the SQLite one
- **THEN** the task service and all route handlers continue to work unchanged

### Requirement: Task service API

The system SHALL expose a single `TaskService` (callable from route handlers) that is the only mutator of task state. The service MUST provide:

- `add_task(title: str, description: str = "") -> Task`
- `update_task(task_id: str, *, title: str | None = None, description: str | None = None, status: str | None = None) -> Task`
- `delete_task(task_id: str) -> None`
- `reorder_tasks(task_ids: list[str]) -> None` — accepts a permutation of task ids and rewrites `order` accordingly.
- `list_tasks() -> list[Task]` — returns tasks sorted by display order (see `todo-view` spec for ordering rules).

The service MUST persist every mutation through the configured `TaskRepository`. The service MUST be initialized with the repository injected (constructor argument or factory), not imported as a global.

#### Scenario: Adding a task

- **WHEN** a route handler calls `service.add_task(title="Ship v1")`
- **THEN** the returned task has `status == "todo"`, the next `order` value (max + 1), and is retrievable via `repo.get(task.id)`

#### Scenario: Toggling completion

- **WHEN** `service.update_task(task_id, status="done")` is called on a `"todo"` task
- **THEN** the task's `status` becomes `"done"`, its `updated_at` advances, and the change is persisted

#### Scenario: Reorder is purely an `order` rewrite

- **WHEN** `service.reorder_tasks([id3, id1, id2])` is called on a set of three tasks
- **THEN** the three tasks' `order` values are rewritten so that `id3 < id1 < id2`, and no other fields change

### Requirement: Status field is Kanban-ready

The system SHALL treat `status` as an open string at the storage and service layers. A `KNOWN_STATUSES` constant (tuple/frozenset) lists `"todo"`, `"done"`, `"in-progress"`, `"review"`, `"blocked"`. The v1 list view MAY treat unknown statuses as pending for *display* purposes, but the service and repository MUST preserve them losslessly.

#### Scenario: Unknown status survives a write/read cycle

- **WHEN** a task is inserted with `status="blocked"`, the process restarts, and the task is loaded
- **THEN** the loaded task still has `status == "blocked"`
