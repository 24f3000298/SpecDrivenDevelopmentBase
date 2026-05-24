## ADDED Requirements

### Requirement: Project bootstrap

The repository SHALL contain a runnable Flask + Jinja2 application at its root. The following commands MUST all succeed in a fresh virtual environment after `pip install -e .[dev]` (or equivalent):

- `flask --app app run --debug` (or `make dev`) — starts the Flask dev server on port 5000 with auto-reload.
- `pytest` (or `make test`) — runs the test suite headlessly and exits non-zero on failures.
- `ruff check .` (or `make lint`) — runs the linter over `app/` and `tests/`.
- `ruff format .` (or `make format`) — formats the codebase.
- `mypy app` (or `make typecheck`) — type-checks the application package.
- `make check` (or equivalent single script) — composite command that runs typecheck → lint → tests; used by CI and humans before pushing.

Python 3.12+ SHALL be declared as the supported runtime in `pyproject.toml` (`requires-python = ">=3.12"`).

There SHALL be **no JavaScript build step, no `package.json`, no `node_modules`, no Vite, no bundler** in this change.

#### Scenario: Fresh clone is runnable

- **WHEN** a developer clones the repo, creates a venv, runs `pip install -e .[dev]` then `flask --app app run`
- **THEN** the dev server starts and `GET /` returns 200 with the TODO index page (empty state on first run)

#### Scenario: `make check` is the single gate

- **WHEN** a developer runs `make check` on a clean working tree
- **THEN** typecheck, lint, and tests all run, and the command exits 0

#### Scenario: No JS toolchain leaks in

- **WHEN** an audit runs `find . -name package.json -o -name node_modules -o -name vite.config.*` excluding `openspec/`
- **THEN** zero files are returned

### Requirement: Directory layout

The system SHALL organize source code with this top-level structure:

```
app/                       # Python package, importable as `app`
  __init__.py              # create_app() factory
  config.py                # configuration classes (Dev, Test, Prod)
  extensions.py            # shared singletons (optional, for future use)
  domain/                  # framework-free task model
    __init__.py
    task.py                # Task dataclass + factory + InvalidTaskError
    status.py              # KNOWN_STATUSES constant, helpers
  persistence/             # TaskRepository protocol + implementations
    __init__.py
    repository.py          # Protocol/ABC
    sqlite_repository.py
    in_memory_repository.py
    schema.sql             # SQLite schema (versioned)
  services/
    __init__.py
    task_service.py        # TaskService class
  todo/                    # Flask blueprint for the TODO view
    __init__.py            # blueprint object
    routes.py              # GET / and POST handlers
    forms.py               # request parsing/validation (lightweight)
  templates/
    base.html
    todo/
      index.html
      _task_row.html
      _empty_state.html
  static/
    styles.css
tests/
  conftest.py              # pytest fixtures (app, client, repo)
  domain/
    test_task.py
  persistence/
    test_sqlite_repository.py
  services/
    test_task_service.py
  todo/
    test_routes.py
instance/                  # gitignored; SQLite file lives here at runtime
pyproject.toml
README.md
Makefile                   # or scripts in pyproject.toml
.gitignore
```

The layered import rules MUST hold:

- `app/domain/**` MUST NOT import from `flask`, `app.persistence`, `app.services`, `app.todo`, or any Flask-aware module.
- `app/persistence/**` MUST NOT import from `flask`, `app.services`, or `app.todo`.
- `app/services/**` MUST NOT import from `flask` or `app.todo`.
- Only `app/todo/**` and `app/__init__.py` may import from `flask`.

These rules SHALL be enforced by lint configuration (e.g. `ruff`'s `flake8-tidy-imports` banned-module-pattern rules, or `import-linter`).

#### Scenario: Layered imports are enforced

- **WHEN** a developer adds `from flask import request` to a file under `app/domain/`
- **THEN** `ruff check` reports an error and `make check` fails

### Requirement: App factory and blueprint registration

The system SHALL expose a `create_app(config: type | str | None = None) -> Flask` factory in `app/__init__.py` that:

- Instantiates `Flask(__name__, instance_relative_config=True)`.
- Loads configuration from a config class (default `app.config.DevConfig`; `TestConfig` used by tests; `ProdConfig` for production).
- Ensures the `instance/` directory exists.
- Initializes the configured `TaskRepository` (SQLite by default; `InMemoryTaskRepository` in tests) and the `TaskService`, and attaches them to `app.extensions["task_service"]` so blueprints can retrieve them.
- Registers the `todo` blueprint at the URL prefix `""` (root).
- Registers a 404 handler and a 500 handler that render minimal error templates extending `base.html`.

The shell MUST be structured so a future `board` blueprint can be registered with one additional line in `create_app` and a new file under `app/board/`. No existing module's behavior may need to change.

#### Scenario: Service hydration before first request

- **WHEN** the app boots with three tasks already in `instance/tasks.db`
- **THEN** the first `GET /` shows those three tasks (no flash of empty state, no migration error)

#### Scenario: Route error renders the error template

- **WHEN** a route raises an unhandled exception
- **THEN** the 500 handler renders a user-readable error page extending `base.html` and the response status is 500

#### Scenario: Adding a future board blueprint is additive

- **WHEN** a hypothetical future change adds `app/board/__init__.py` and registers it in `create_app`
- **THEN** the diff to existing files is limited to a single new import and a single new `register_blueprint(...)` call

### Requirement: Configuration

The system SHALL provide three config classes in `app/config.py`:

- `BaseConfig`: shared defaults, including `SECRET_KEY` read from the `SECRET_KEY` env var (fallback to a dev-only constant when `FLASK_ENV != "production"`).
- `DevConfig(BaseConfig)`: `DEBUG=True`, SQLite at `instance/tasks.db`.
- `TestConfig(BaseConfig)`: `TESTING=True`, uses `InMemoryTaskRepository` (no SQLite file).
- `ProdConfig(BaseConfig)`: `DEBUG=False`, requires `SECRET_KEY` to be set (raises at boot if missing), SQLite path configurable via `DATABASE_PATH` env var.

Configuration MUST be loaded via `app.config.from_object(...)` inside `create_app`, never imported directly by domain/persistence/service code.

#### Scenario: Prod config refuses to boot without SECRET_KEY

- **WHEN** `create_app(ProdConfig)` is called with `SECRET_KEY` unset in the environment
- **THEN** `create_app` raises a clear configuration error before serving any request

### Requirement: Tooling configuration

The system SHALL include configuration for:

- **`pyproject.toml`**: PEP 621 project metadata, runtime and dev dependencies, optional `[tool.ruff]`, `[tool.mypy]`, and `[tool.pytest.ini_options]` tables.
- **`ruff`**: lint + format. Rule selection MUST include at least `E`, `F`, `I` (imports), `B` (bugbear), and a banned-imports configuration to enforce the layer boundaries above.
- **`mypy`**: configured for the `app/` package with `strict = true` (or close to it: `disallow_untyped_defs`, `warn_unused_ignores`, `no_implicit_optional`).
- **`pytest`**: configured to discover tests under `tests/`, with fixtures for `app`, `client`, and `repo` in `tests/conftest.py`.
- **`.gitignore`** covering `__pycache__/`, `*.pyc`, `.venv/`, `instance/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `dist/`, `build/`, `.coverage`, `*.egg-info/`.
- **`.env.example`** documenting `SECRET_KEY`, `DATABASE_PATH`, `FLASK_ENV`.

#### Scenario: Strict typing catches missing annotation

- **WHEN** a developer adds a function in `app/services/` without type annotations
- **THEN** `mypy app` reports an error and `make check` fails

### Requirement: Documentation

The repository SHALL include a `README.md` that documents, at a minimum:

- One-paragraph description of the app and its v1 scope (TODO list, Flask + Jinja, no JS).
- The Kanban roadmap — what the next change will add (board blueprint, columns, drag-to-reorder via HTMX or progressive enhancement) and how the current scaffolding supports it.
- The directory layout and import rules.
- The available `make` (or script) targets and their purpose.
- The Python version requirement and how to set up the virtual environment.
- How to point at a custom database path and how to reset the dev database.

#### Scenario: README explains the Kanban seam

- **WHEN** a new contributor reads the README
- **THEN** they can identify, without reading source code, that `Task.status` is the seam for future Kanban columns, that `reorder_tasks` is the seam for drag-and-drop, and that `app/todo/` is the sibling of a future `app/board/`
