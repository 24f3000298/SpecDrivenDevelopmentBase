## 1. Project bootstrap

- [x] 1.1 Create `pyproject.toml` with PEP 621 metadata: name `ssd-workshop-spike`, version `0.0.1`, `requires-python = ">=3.12"`, runtime dependencies (`flask`, `python-dotenv`), and an `[project.optional-dependencies].dev` group (`pytest`, `ruff`, `mypy`)
- [x] 1.2 Add `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.ruff.format]`, `[tool.mypy]`, `[tool.pytest.ini_options]` tables in `pyproject.toml`
- [x] 1.3 Configure `ruff` lint rules: enable `E`, `F`, `I`, `B`, `UP`, `SIM`, `RUF`; target Python 3.12
- [x] 1.4 Configure `ruff` banned-import patterns enforcing layer boundaries: `flask` and `app.persistence|app.services|app.todo` banned in `app/domain/**`; `flask`, `app.services`, `app.todo` banned in `app/persistence/**`; `flask`, `app.todo` banned in `app/services/**`
- [x] 1.5 Configure `mypy`: `strict = true`, `python_version = "3.12"`, `packages = ["app"]`, `ignore_missing_imports = false`
- [x] 1.6 Configure `pytest`: `testpaths = ["tests"]`, `pythonpath = ["."]`, `addopts = "-ra"`
- [x] 1.7 Create `.gitignore` covering `__pycache__/`, `*.pyc`, `.venv/`, `instance/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `dist/`, `build/`, `.coverage`, `*.egg-info/`, `.env`
- [x] 1.8 Create `.env.example` listing `SECRET_KEY`, `DATABASE_PATH`, `FLASK_ENV` with safe placeholder values
- [x] 1.9 Create a `Makefile` with targets `install`, `dev`, `run`, `test`, `lint`, `format`, `typecheck`, `check`, `clean`, `help`; `check` runs `typecheck` → `lint` → `test`
- [x] 1.10 Verify a fresh `python -m venv .venv && source .venv/bin/activate && pip install -e .[dev]` succeeds

## 2. Domain layer (`app/domain/`)

- [x] 2.1 Create `app/__init__.py` (empty placeholder; the factory comes in step 7)
- [x] 2.2 Create `app/domain/__init__.py` re-exporting `Task`, `InvalidTaskError`, `KNOWN_STATUSES`
- [x] 2.3 Create `app/domain/status.py` with `KNOWN_STATUSES: tuple[str, ...] = ("todo", "done", "in-progress", "review", "blocked")`
- [x] 2.4 Create `app/domain/task.py` with frozen `@dataclass(slots=True)` `Task`, `InvalidTaskError` exception, and `Task.create(...)` factory enforcing: trimmed non-empty title, title ≤ 200 chars, description ≤ 2000 chars, UUID hex id, UTC `created_at`/`updated_at`, default `status="todo"`, default `description=""`
- [x] 2.5 Verify `app/domain/` imports only stdlib (no `flask`, no `sqlite3`)

## 3. Domain tests (`tests/domain/`)

- [x] 3.1 Create `tests/__init__.py`, `tests/domain/__init__.py`
- [x] 3.2 Create `tests/domain/test_task.py` covering: factory defaults, trims whitespace, empty/whitespace-only title raises `InvalidTaskError`, title length cap, description length cap, `created_at == updated_at` on creation, status forward-compat (accepts `"in-progress"`)
- [x] 3.3 Verify `pytest tests/domain` passes

## 4. Persistence layer (`app/persistence/`)

- [x] 4.1 Create `app/persistence/__init__.py` re-exporting `TaskRepository`, `SQLiteTaskRepository`, `InMemoryTaskRepository`
- [x] 4.2 Create `app/persistence/repository.py` with a `TaskRepository` `Protocol` declaring `list`, `get`, `add`, `update`, `delete`, `replace_all`
- [x] 4.3 Create `app/persistence/schema.sql` defining the `tasks` table (`id TEXT PRIMARY KEY`, `title TEXT NOT NULL`, `description TEXT NOT NULL DEFAULT ''`, `status TEXT NOT NULL`, `order_index INTEGER NOT NULL`, `created_at TEXT NOT NULL`, `updated_at TEXT NOT NULL`) — note `order` is reserved in SQL so use `order_index` in storage and map to `order` in code
- [x] 4.4 Create `app/persistence/sqlite_repository.py` implementing `TaskRepository` against a path-configurable SQLite file; on first use, ensure the parent directory exists and apply `schema.sql` if the table is missing; set `PRAGMA journal_mode=WAL` and `PRAGMA foreign_keys=ON`
- [x] 4.5 Implement row ↔ `Task` mapping with timestamp serialization as ISO-8601 UTC strings; handle the `order` ↔ `order_index` rename at the mapping boundary
- [x] 4.6 Implement `replace_all` as a single transaction (`BEGIN; DELETE; INSERT...; COMMIT`)
- [x] 4.7 Create `app/persistence/in_memory_repository.py` implementing the same protocol against a list, suitable for tests

## 5. Persistence tests (`tests/persistence/`)

- [x] 5.1 Create `tests/persistence/__init__.py`
- [x] 5.2 Create `tests/persistence/test_sqlite_repository.py` using a temp-dir SQLite file fixture (via `tmp_path`): round-trip `add → list`, `get` hit + miss, `update` changes fields and bumps `updated_at`, `delete` removes, `replace_all` rewrites order, missing-database-file initializes schema, unknown `status` survives round-trip
- [x] 5.3 Create `tests/persistence/test_in_memory_repository.py` covering interface parity (same scenarios, different backend)
- [x] 5.4 Verify `pytest tests/persistence` passes

## 6. Service layer (`app/services/`)

- [x] 6.1 Create `app/services/__init__.py` re-exporting `TaskService`
- [x] 6.2 Create `app/services/task_service.py` with `TaskService(repo: TaskRepository)` and methods `list_tasks`, `add_task`, `update_task`, `delete_task`, `reorder_tasks`
- [x] 6.3 `add_task`: computes next `order` as `max(order)+1` (or `0` if empty) by querying the repo, then `Task.create(...)` and `repo.add(...)`
- [x] 6.4 `update_task`: fetches via `repo.get`, raises `TaskNotFoundError` if missing, returns a new `Task` via `dataclasses.replace` with updated fields and refreshed `updated_at`, persists via `repo.update`
- [x] 6.5 `reorder_tasks`: takes an `list[str]` of ids, fetches all tasks, rewrites `order` to dense integer positions matching the input order, calls `repo.replace_all`; raises if the ids don't match the existing set
- [x] 6.6 `list_tasks`: returns `repo.list()` sorted by `(status == "done", order)` — pending first, done last, ordered within each group
- [x] 6.7 Verify `app/services/` does not import `flask`

## 7. Service tests (`tests/services/`)

- [x] 7.1 Create `tests/services/__init__.py`
- [x] 7.2 Create `tests/services/test_task_service.py` using `InMemoryTaskRepository`: add → has correct order; update changes fields and `updated_at`; delete removes; reorder rewrites order; `list_tasks` puts done last and sorts by order within each group; unknown status round-trips through the service
- [x] 7.3 Verify `pytest tests/services` passes

## 8. App factory and configuration

- [x] 8.1 Replace `app/__init__.py` with `create_app(config: type | str | None = None) -> Flask` factory using `Flask(__name__, instance_relative_config=True)`
- [x] 8.2 Create `app/config.py` with `BaseConfig`, `DevConfig`, `TestConfig`, `ProdConfig`; `BaseConfig.SECRET_KEY` reads from env with dev fallback; `ProdConfig.__init__` raises if `SECRET_KEY` is unset in env
- [x] 8.3 In `create_app`, ensure `app.instance_path` directory exists; pick `TaskRepository` based on config (`SQLiteTaskRepository` for Dev/Prod, `InMemoryTaskRepository` for Test); construct `TaskService` and store at `app.extensions["task_service"]`
- [x] 8.4 Register a 404 handler and a 500 handler rendering minimal templates extending `base.html`
- [x] 8.5 Register the `todo` blueprint (from step 9) with empty URL prefix
- [x] 8.6 Verify `flask --app app routes` lists the expected endpoints

## 9. Todo blueprint and routes (`app/todo/`)

- [x] 9.1 Create `app/todo/__init__.py` defining `bp = Blueprint("todo", __name__)`
- [x] 9.2 Create `app/todo/routes.py` with handlers for `GET /`, `POST /tasks`, `POST /tasks/<task_id>/toggle`, `POST /tasks/<task_id>/delete`
- [x] 9.3 `GET /` retrieves tasks via `current_app.extensions["task_service"].list_tasks()` and renders `todo/index.html` with the task list
- [x] 9.4 `POST /tasks` reads `request.form["title"]`, trims it, rejects empty (re-renders `index.html` with an inline error and HTTP 400 — or 200 with error flag, pick one and document), otherwise calls `add_task` and returns `redirect(url_for("todo.index"), code=303)`
- [x] 9.5 `POST /tasks/<task_id>/toggle` calls `update_task` to flip between `"todo"` and `"done"`, then redirects 303 to the index
- [x] 9.6 `POST /tasks/<task_id>/delete` calls `delete_task`, then redirects 303 to the index
- [x] 9.7 Verify `app/todo/` is the only place outside `app/__init__.py` that imports `flask`

## 10. Templates and static assets

- [x] 10.1 Create `app/templates/base.html` with `<!doctype html>`, language attr, `<title>`, charset/viewport meta, link to `static/styles.css`, a header containing the app name (link to `/`), a `<main>` with `{% block main %}{% endblock %}`, and a footer
- [x] 10.2 Create `app/templates/todo/index.html` extending `base.html`: heading, add-task `<form>` (POST `/tasks`, inline error rendering if present), then either the empty state include or the task list
- [x] 10.3 Create `app/templates/todo/_task_row.html` rendering one task as a `<li>` with: toggle form, title span with `task--done` class when `status == "done"`, delete form; toggle button label "Mark '{{ task.title }}' as done" / "as not done"; delete button label "Delete '{{ task.title }}'"
- [x] 10.4 Create `app/templates/todo/_empty_state.html` with a friendly empty-state block
- [x] 10.5 Create `app/templates/errors/404.html` and `app/templates/errors/500.html` extending `base.html`
- [x] 10.6 Create `app/static/styles.css` with CSS variables (color tokens, spacing), base resets, a `task--done` class (strike-through + muted), simple layout
- [x] 10.7 Bucket-unknown-status rendering: the index template renders any task whose `status` is not `"done"` in the pending group

## 11. Route tests (`tests/todo/`)

- [x] 11.1 Create `tests/conftest.py` with fixtures `app` (via `create_app(TestConfig)`), `client` (`app.test_client()`), and `repo` (the in-memory repo from `app.extensions["task_service"].repo`)
- [x] 11.2 Create `tests/todo/__init__.py`, `tests/todo/test_routes.py`
- [x] 11.3 Test `GET /` empty: 200, response body contains the empty-state phrase
- [x] 11.4 Test `POST /tasks` happy path: 303 redirect to `/`, following the redirect shows the new task, `repo.list()` contains it
- [x] 11.5 Test `POST /tasks` empty title: no task created, response contains an inline validation message
- [x] 11.6 Test `POST /tasks/<id>/toggle`: status flips, follow-up `GET /` shows the row with `task--done`
- [x] 11.7 Test `POST /tasks/<id>/delete`: task is removed; follow-up `GET /` no longer shows it
- [x] 11.8 Test unknown-status rendering: pre-seed a `"in-progress"` task; `GET /` is 200 and the task appears in the pending group
- [x] 11.9 Test 404: `GET /no-such-route` renders the 404 template

## 12. Documentation

- [x] 12.1 Replace the empty root `README.md` with: one-paragraph product description, v1 scope (TODO list, Flask + Jinja, no JS) vs. Kanban roadmap (board blueprint, columns, future HTMX), directory layout diagram, import-boundary rules, Make target reference, Python + venv setup instructions, "how to reset the dev database" tip (`rm instance/tasks.db`)
- [x] 12.2 Add a "What's the Kanban seam?" section calling out `Task.status`, `TaskService.reorder_tasks`, the blueprint pattern, and `_task_row.html` as the explicit extension points
- [x] 12.3 Document the "no JS in v1" decision and what would be revisited when the board view lands

## 13. Verification gate

- [x] 13.1 Run `make check` from a clean working tree — typecheck, lint, and tests must all pass
- [x] 13.2 Run `flask --app app run` and manually verify in a browser: empty state on first load → add three tasks → reload page → all three persist → toggle one → reload → toggle persists → delete one → reload → deletion persists (verified end-to-end via in-process `app.test_client()` driving a real SQLite-backed DevConfig app across four simulated process restarts; local-port binding was blocked by the harness)
- [x] 13.3 Manually verify the ruff boundary rule: temporarily add `from flask import request` inside `app/domain/task.py`, confirm `ruff check` fails, then revert
- [x] 13.4 Run `find . -path ./.venv -prune -o -path ./openspec -prune -o \( -name package.json -o -name node_modules -o -name 'vite.config.*' \) -print` and confirm zero results (no JS toolchain leaked in)
