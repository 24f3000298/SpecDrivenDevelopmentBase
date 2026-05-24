## Why

We need a working starting point for a personal task-tracking app. Starting today with a TODO list keeps the first iteration small enough to ship, but the longer-term goal is a Kanban-style board (multiple columns, statuses, drag-to-reorder, labels). The team is Python-first — we want the whole stack in Python with **server-side rendered HTML via Jinja templates**, no JavaScript build pipeline, no SPA framework, no Vite. Designing the scaffold now — domain model, persistence seam, route/template boundaries — with Kanban in mind avoids a painful rewrite later when we promote tasks from a flat list to columns on a board.

## What Changes

- Bootstrap a new **Flask + Jinja2** application at the repository root, served with the Flask dev server in development and a WSGI server (gunicorn/waitress) in production.
- No JavaScript build step. No npm, no Vite, no React. Pages are server-rendered HTML; interactivity uses standard HTML forms with the Post/Redirect/Get pattern. A future, optional sprinkle of HTMX is the only JS we'd entertain, and it is **out of scope** for this change.
- Add a Kanban-aware **task domain model** from day one: every task has a `status` field (initially `todo` and `done`, extensible to `in-progress`, `review`, `blocked`, etc.) and ordering metadata, even though the v1 UI only renders a flat list.
- Add a **`TaskRepository` interface** with a SQLite-backed implementation (via `sqlite3` from the stdlib) behind it, so a future Postgres or API-backed implementation can be dropped in without touching routes or templates.
- Add a **task service layer** (single source of truth for mutations) with a narrow CRUD + reorder API that the future board view will reuse unchanged.
- Ship a minimal **TODO UI**: a base layout template, an index page with an add-task form, a list of tasks with toggle-complete and delete forms, and an empty state.
- Establish **project conventions**: `pyproject.toml`, virtual environment, `ruff` for lint+format, `mypy` for type checking, `pytest` for tests, and a single CI-friendly `make check` (or `nox`/`hatch` script) that runs typecheck → lint → tests.
- Add a **README** describing the architecture and the Kanban roadmap.

This change deliberately does **not** ship the Kanban board, drag-and-drop, columns, labels, due dates, authentication, or HTMX — those are follow-up changes that build on this scaffold.

## Capabilities

### New Capabilities
- `task-management`: Core task domain — create, read, update, delete, and reorder tasks. Each task carries a status field designed to support multiple Kanban columns later. Includes the persistence contract (`TaskRepository`), the SQLite implementation, and the task service that the route handlers call.
- `todo-view`: The v1 user-facing surface — server-rendered Jinja pages for a single flat list of tasks with add, complete (toggle status), delete, and empty-state UX. Will later coexist with a board view (Jinja template + routes) that reads from the same task service.
- `app-shell`: The wrapping application — Flask app factory, blueprint registration, configuration, base layout template, static assets, error handling, and the top-level wiring of service ↔ routes ↔ templates. The shell is what a future "Board" blueprint will plug into alongside the existing "Todo" blueprint.

### Modified Capabilities
<!-- None — this is a greenfield scaffold; no existing specs to modify. -->

## Impact

- **Code**: Creates the entire backend tree (no existing app code today). Adds `pyproject.toml`, `app/` package, `templates/`, `static/`, `tests/`, and dev tooling configs.
- **Dependencies (new, runtime)**: `flask`, `jinja2` (transitively via Flask), `gunicorn` (production WSGI; optional locally), `python-dotenv` (env loading).
- **Dependencies (new, dev)**: `pytest`, `pytest-flask` (or just Flask's `app.test_client()`), `ruff`, `mypy`, `types-Flask` if needed.
- **Tooling**: Python 3.12+ becomes a project requirement. Adds `make` targets (or equivalent script entries): `dev`, `run`, `test`, `lint`, `format`, `typecheck`, `check`.
- **No backend service besides Flask + SQLite**, no auth, no network calls outbound, no JS toolchain. Persistence is a single SQLite file at `instance/tasks.db`. The `TaskRepository` interface is the seam where a future Postgres- or API-backed implementation will plug in.
- **Forward compatibility**: The `Task.status` and `Task.order` fields are the explicit hooks for the future Kanban board change; route handlers and templates in v1 must not assume `status` is binary.
