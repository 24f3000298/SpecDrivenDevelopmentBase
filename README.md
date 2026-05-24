# ssd-workshop-spike

A personal task tracker that starts as a flat TODO list and is scaffolded to grow into a Kanban board. The stack is Python end-to-end: Flask + Jinja2 server-side rendering, SQLite via the stdlib `sqlite3` module, and **no JavaScript build pipeline**. Every mutation is a plain HTML form post followed by a 303 redirect.

## v1 scope vs. Kanban roadmap

**v1 (this scaffold) ships:**

- A single TODO view at `/`.
- Add a task (form post), toggle complete (form post), delete (form post), empty state.
- Persistence in a single SQLite file at `instance/tasks.db`.
- Type-checked Python, ruff-linted, full pytest suite covering domain, persistence, services, and routes.

**The next change will add the Kanban board:**

- A new blueprint `app/board/` registered as a sibling of `app/todo/`, mounted under `/board`.
- Multiple status columns (`todo`, `in-progress`, `review`, `done`, …) rendered side by side.
- Drag-to-reorder. The smallest viable JS — most likely **HTMX** loaded as a single CDN `<script>` tag, possibly **Sortable.js** for the drag handle. No build step, no bundler.
- The `_task_row.html` partial becomes (or is reused as) the card template.

### The Kanban seam

The scaffold deliberately exposes three extension points so the board change is **additive**, not a rewrite:

1. **`Task.status` is an open string** (not a closed `Enum`). The persistence layer already round-trips arbitrary statuses; the v1 UI just buckets unknown values into the pending group. See [`app/domain/status.py`](app/domain/status.py).
2. **`TaskService.reorder_tasks(task_ids)`** already exists and the SQLite repository implements `replace_all` as a single transaction. The board view will call this when a card is dragged.
3. **The `todo` blueprint pattern.** A future `board` blueprint registers in `create_app` with one extra line.

The "no JS in v1" decision is documented in [`openspec/changes/scaffold-todo-kanban-app/design.md`](openspec/changes/scaffold-todo-kanban-app/design.md), decision D11. The board change will revisit; this scaffold doesn't lock us out.

## Directory layout

```
app/
  __init__.py          create_app() factory — the only Flask-aware module besides app/todo/
  config.py            BaseConfig / DevConfig / TestConfig / ProdConfig
  domain/              framework-free Task entity, status vocabulary
    task.py
    status.py
  persistence/         TaskRepository protocol + SQLite and in-memory impls
    repository.py
    sqlite_repository.py
    in_memory_repository.py
    schema.sql
  services/            TaskService — the only mutator of task state
    task_service.py
  todo/                Flask blueprint for the v1 view
    __init__.py        Blueprint("todo", __name__)
    routes.py          GET / and POST handlers
  templates/
    base.html
    todo/{index,_task_row,_empty_state}.html
    errors/{404,500}.html
  static/
    styles.css
tests/
  conftest.py          app/client/repo fixtures (uses TestConfig + in-memory repo)
  domain/  persistence/  services/  todo/
instance/              gitignored; SQLite file at runtime
pyproject.toml
Makefile
```

### Import boundaries

The layers are enforced (via `ruff`'s tidy-imports rules) so that:

- `app/domain/**` may not import `flask`, `app.persistence`, `app.services`, `app.todo`.
- `app/persistence/**` may not import `flask`, `app.services`, `app.todo`.
- `app/services/**` may not import `flask` or `app.todo`.
- Only `app/__init__.py` and `app/todo/**` may import `flask`.

If you add `from flask import …` inside `app/domain/`, `make lint` fails.

## Setup

```bash
# Requires Python 3.12+
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Or in one shot:

```bash
make install
```

## Make targets

| Target           | What it does                                                |
|------------------|-------------------------------------------------------------|
| `make install`   | Create `.venv` and install the project with dev extras       |
| `make dev`       | Run the Flask dev server with `--debug` (auto-reload)        |
| `make run`       | Run the Flask server without debug mode                      |
| `make test`      | Run the pytest suite                                         |
| `make lint`      | `ruff check .`                                               |
| `make format`    | `ruff format .`                                              |
| `make typecheck` | `mypy app`                                                   |
| `make check`     | `typecheck` → `lint` → `test` (the CI / pre-push gate)       |
| `make clean`     | Remove cache and build artifacts                             |

## Configuration

Copy `.env.example` to `.env` for local overrides. Recognized variables:

- `SECRET_KEY` — required in production; has a dev-only fallback otherwise.
- `DATABASE_PATH` — absolute path for the SQLite file. Defaults to `<instance>/tasks.db`.
- `FLASK_ENV` — `development` (default), `testing`, or `production`.

### Resetting the dev database

```bash
rm instance/tasks.db
```

The schema is re-applied on the next request.

## Why this scaffold is opinionated

See [`openspec/changes/scaffold-todo-kanban-app/design.md`](openspec/changes/scaffold-todo-kanban-app/design.md) for the long-form rationale (Flask vs Django, stdlib sqlite3 vs SQLAlchemy, why no JS yet, how the layered import rules are enforced, what the migration path looks like).
