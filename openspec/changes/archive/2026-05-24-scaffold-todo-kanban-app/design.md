## Context

This is a greenfield repo. Today it contains only an empty `README.md` and an `openspec/` directory. The product intent (per the proposal) is to ship a TODO app *now* and evolve it into a Kanban board *next*. The team is Python-first and explicitly wants **server-side rendered HTML via Jinja templates**, **no JavaScript build pipeline**, **no SPA framework**, **no Vite, no npm**. The dominant risks are:

1. Over-fitting v1 to "flat list of strings" and paying for it when columns and drag-and-drop arrive.
2. Reaching for Django or a heavy ORM when the v1 surface is one entity and one route file.
3. Pretending a real-world Kanban board needs *zero* JS forever — drag-and-drop will eventually want something. The right move is to defer that decision without painting ourselves into a corner.

Stakeholders: a single developer (the user) iterating in a workshop / spike context. No team conventions to inherit, no infra constraints beyond "Python".

## Goals / Non-Goals

**Goals:**

- A runnable Flask + Jinja2 app at the repo root after this change is implemented, with a single `make check` gate.
- A task domain model whose `status` and `order` fields make the future Kanban board a *feature addition*, not a rewrite.
- A `TaskRepository` seam so the same service code works against SQLite today and a different store later (Postgres, an HTTP API, an in-memory test double).
- A directory layout that names the seams explicitly: `domain/`, `persistence/`, `services/`, `todo/` (blueprint), `templates/todo/`, with a clear path to add `board/` and `templates/board/` later.
- A minimal, accessible TODO UI rendered entirely server-side with standard HTML forms and the Post/Redirect/Get pattern.
- Strict typing (`mypy --strict`-ish) and a fast linter/formatter (`ruff`) so the contributor loop is obvious and tight.

**Non-Goals:**

- The Kanban board itself (columns, drag-to-reorder, swimlanes, WIP limits). That is a separate follow-up change.
- Authentication, multi-user support, real-time updates, websockets, or any non-trivial server feature.
- An ORM. SQLAlchemy is well known and tempting, but for one entity and one table it adds more vocabulary than value. Plain `sqlite3` with a thin repository is more honest about scope.
- HTMX, Alpine, Stimulus, or *any* client-side library — even progressive enhancement. The proposal explicitly says no JS in this change. The board change will revisit.
- Django, FastAPI, Starlette, Litestar. Flask is the right size for a v1 SSR scaffold.
- Async. Flask sync routes are fine. If async is ever needed, we can switch to Quart or FastAPI, but that would be a different scaffold.
- A migration framework (Alembic). One `schema.sql` applied on first boot is enough for v1; a real migration tool comes when the schema starts changing.

## Decisions

### D1. Web framework: Flask 3.x

Chosen over Django, FastAPI, Starlette, Litestar, Quart, Pyramid.

- **Why Flask**: smallest scaffolding overhead for SSR + Jinja; the app factory + blueprint pattern is exactly the shape we need to bolt on a future `board` blueprint; sync request handling matches our (zero) concurrency requirements.
- **Why not Django**: too much for one entity. Admin, ORM, migrations, contrib — all unused. The Kanban board doesn't justify it either; we'd be paying for Django's batteries even after the board lands.
- **Why not FastAPI/Starlette**: SSR is possible (via Jinja2Templates) but the framework's value is mostly in async + JSON APIs; we have neither.
- **Why not Quart**: async with no async use case is dead weight.

### D2. Templating: Jinja2 (bundled with Flask)

No choice to make here — Flask ships Jinja. Decisions inside Jinja:

- **Base template**: `templates/base.html` defines `<head>`, header, `{% block main %}{% endblock %}`, footer.
- **Partials**: `_task_row.html`, `_empty_state.html` named with a leading underscore. The `_task_row.html` partial is the unit a future board column will reuse to render a card.
- **Autoescape**: on (Flask default for `.html` templates).
- **No template inheritance gymnastics**: at most `extends` + a few named blocks. No macros until something repeats three times.

### D3. Persistence: stdlib `sqlite3` behind a `TaskRepository` protocol

Chosen over SQLAlchemy ORM, SQLAlchemy Core, Peewee, Tortoise, raw JSON file, shelve, TinyDB.

- **Why stdlib sqlite3**: zero new vocabulary. The repository is ~60 lines. SQLite handles every realistic v1 scale and is the most portable on-disk format we could pick.
- **Why a `Protocol` (PEP 544) instead of an ABC**: structural typing fits Python better here. Tests can pass an `InMemoryTaskRepository` without inheriting; mypy still checks shape.
- **Why not SQLAlchemy**: the value is for many entities, complex relationships, query composition. None apply to v1. When the board change adds labels, columns-as-entities, or the API-backed implementation lands, we'll revisit. Swapping the implementation behind the protocol is the explicit point of this design.
- **Schema versioning**: a single `schema.sql` applied if the `tasks` table doesn't exist. We accept that schema migrations are a future problem; when they arrive we'll either add Alembic (if we move to SQLAlchemy) or a hand-rolled `migrations/` directory.

**Database file location**: `instance/tasks.db` (Flask's per-deploy "instance folder"). Gitignored. The instance folder is created by `create_app` if missing.

**Corrupt-data policy**: if the schema doesn't match expectations, raise a clear `RuntimeError` at startup rather than silently dropping rows. Localhost-only v1 — we'd rather fail loud.

### D4. Service layer between routes and repository

Routes call `TaskService`; the service calls `TaskRepository`. The service owns:

- Generating UUIDs and timestamps (so the domain stays pure).
- Computing the next `order` value on insert.
- Computing the new `order` map on reorder.
- Wrapping the repository in any future cross-cutting concerns (logging, events, future cache).

The repository owns *only* persistence — SQL, no business logic.

- **Why this split**: it's the seam where a future "emit an event when a task moves to `done`" or "publish a board-state update" feature will live, without bloating either the routes or the repository.

### D5. Routes via a single `todo` Blueprint

Blueprint registered at root URL prefix `""`:

- `GET /` → render TODO index.
- `POST /tasks` → add a task.
- `POST /tasks/<task_id>/toggle` → toggle between `"todo"` and `"done"`.
- `POST /tasks/<task_id>/delete` → delete.
- (Reserved for future) `POST /tasks/reorder` → reorder.

All mutations are POST + 303 redirect to `GET /` (Post/Redirect/Get). No GET endpoints mutate state.

- **Why blueprint not flat routes**: blueprints are the seam for adding the `board` blueprint later without touching `todo` routes.
- **Why 303 not 302**: 303 is the spec-correct redirect after a POST. Browsers will treat 302 the same in practice, but 303 is the clear signal.

### D6. The `Task` domain object stays framework-free

`app/domain/task.py` imports only stdlib. No Flask, no `sqlite3`, no `request`-context. The factory raises `InvalidTaskError` on bad input. Timestamps are `datetime` in UTC.

- **Why**: the same domain code will be used by tests, by a future board, possibly by a CLI script. Coupling it to Flask or to the DB driver would force a rewrite later.

```python
@dataclass(frozen=True, slots=True)
class Task:
    id: str
    title: str
    description: str
    status: str
    order: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, *, title: str, description: str = "", order: int = 0, status: str = "todo") -> "Task":
        title = title.strip()
        if not title:
            raise InvalidTaskError("title must be non-empty")
        if len(title) > 200:
            raise InvalidTaskError("title exceeds 200 characters")
        if len(description) > 2000:
            raise InvalidTaskError("description exceeds 2000 characters")
        now = datetime.now(tz=timezone.utc)
        return cls(
            id=uuid.uuid4().hex,
            title=title, description=description,
            status=status, order=order,
            created_at=now, updated_at=now,
        )
```

Updates produce a new `Task` (frozen dataclass) — no mutation in place.

### D7. `status` is an open string with a known-values constant

```python
KNOWN_STATUSES: tuple[str, ...] = ("todo", "done", "in-progress", "review", "blocked")
```

- The column is `TEXT NOT NULL` in SQLite — open.
- Display code MAY bucket unknown values as "pending"; persistence MUST preserve them losslessly.
- **Why not a Python `Enum`**: closed enums force a code change every time we add a column. The constant + open string keeps autocomplete-ish ergonomics (search hits land on `KNOWN_STATUSES`) without locking the schema.

### D8. `order` is an integer, recomputed on insert/reorder

- v1 inserts at the bottom: `order = (SELECT COALESCE(MAX(order), -1) FROM tasks) + 1`.
- `reorder_tasks(task_ids)` rewrites `order` to dense integer positions.
- **Why not fractional/LexoRank**: not needed for v1; the board change can switch when drag-and-drop performance matters. The interface (`reorder_tasks(ids)`) hides the implementation, so this swap is local.

### D9. Tooling: ruff + mypy + pytest, orchestrated by `make check`

- **`ruff`**: lint + format in one tool. Replaces flake8, black, isort, pyupgrade. Fast enough that `make check` stays under a few seconds.
- **`mypy`**: strict-ish; the domain layer's type guarantees are how we keep Kanban-readiness honest.
- **`pytest`**: with a `conftest.py` exposing fixtures `app` (Flask test app with `TestConfig`), `client` (test client), `repo` (in-memory repo).
- **`make check`**: `mypy → ruff check → pytest` in that order. Cheapest signal first.
- **Why a Makefile and not just scripts in `pyproject.toml`**: discoverability. `make help` is universally understood; one entry per task; works without activating the venv if the venv binaries are on PATH.

### D10. Layer boundary enforcement

We name the layers, and we enforce them:

- `app/domain/**` must not import `flask`, `app.persistence`, `app.services`, `app.todo`.
- `app/persistence/**` must not import `flask`, `app.services`, `app.todo`.
- `app/services/**` must not import `flask`, `app.todo`.
- Only `app/todo/**` and `app/__init__.py` may import `flask`.

Enforcement options considered:

- **`ruff`'s `flake8-tidy-imports` banned-pattern rules** — primary choice; one config block in `pyproject.toml`.
- **`import-linter`** — fallback if ruff's pattern matching can't express what we need.

### D11. No JS, even progressive

The proposal is explicit. v1 ships with:

- Plain HTML `<form>` elements with POST + 303 redirect for every mutation.
- A small `static/styles.css` with CSS variables for color tokens.
- Zero `<script>` tags.

When drag-and-drop lands with the board view, the smallest viable JS will be considered then — most likely **HTMX**, possibly **Sortable.js** as a one-off. That decision is explicitly **out of scope here**.

## Risks / Trade-offs

- **[Risk] No JS means no in-place updates; every action is a full page reload.** → Mitigation: keep the page small, keep the layout stable so scroll position is preserved (Flask sends `Location` headers; browsers handle the rest). Document this as a known v1 UX limitation in the README.
- **[Risk] SQLite + plain `sqlite3` is fine until concurrent writers appear.** → Mitigation: v1 is single-user, localhost. The `TaskRepository` seam is exactly the unlock for swapping to a server-backed store later. Set SQLite `PRAGMA journal_mode=WAL` and `PRAGMA foreign_keys=ON` at connection time.
- **[Risk] Schema evolution without a migration tool is fragile.** → Mitigation: v1 has one table. When the second schema change lands, we'll add Alembic (or hand-rolled migrations) before that PR merges. Don't add it now.
- **[Risk] Layer enforcement via lint patterns can be noisy.** → Mitigation: scope the rule narrowly to the four edges that actually matter; don't try to enforce a strict DAG everywhere.
- **[Trade-off] `dataclasses` with frozen + slots is verbose to "update" (need to rebuild).** Accepted: the safety of immutability is worth the few extra `dataclasses.replace(...)` calls.
- **[Trade-off] No async means we can't trivially add long-polling or SSE later.** Accepted: v1 doesn't need them. If we ever do, Flask can use `gunicorn --worker-class gevent` or we switch to Quart. Not a v1 problem.
- **[Trade-off] No HTMX means delete/toggle reloads the page.** Accepted: this is the literal interpretation of "no JS". The board change will revisit; this scaffold doesn't lock us out.

## Migration Plan

This is a greenfield scaffold; no migration from existing code. Local "deployment" is `flask --app app run`. Rollback is `git revert`. There's no production target in this change.

The relevant *future* migrations this design enables:

1. **Add Kanban board view**: a new `app/board/` blueprint and `templates/board/`, registered in `create_app` with one line. The `_task_row.html` partial becomes (or is reused as) a card template. `Task.status` and `TaskService.reorder_tasks` are already there. `domain/`, `persistence/`, and `services/` should not need changes.
2. **Introduce HTMX for partial swaps**: add HTMX via a `<script>` tag in `base.html`; views opt in by returning template *partials* on `HX-Request` headers. No build step, no bundler — consistent with the "no JS toolchain" rule even though we'd be allowing a single CDN-sourced library.
3. **Swap SQLite for Postgres or an HTTP API**: implement `PostgresTaskRepository` (or `ApiTaskRepository`) against the same `TaskRepository` protocol. Swap the binding in `create_app`. Services, routes, templates unchanged. Add Alembic at this point.
4. **Schema migrations**: when the second schema change lands, introduce Alembic (or equivalent) *before* shipping it. The instance DB is a dev-only artifact, so the first "migration" can be `rm instance/tasks.db && restart`.

## Open Questions

- **Make vs `scripts` in pyproject.toml vs `nox`/`hatch run`**: defaulting to `Makefile` for discoverability and zero-extra-deps. If the user prefers an `nox` task runner, swap during implementation — the spec only requires that `make check` (or its equivalent) exists.
- **Should `TaskRepository` be a `Protocol` or an `abc.ABC`?**: defaulting to `Protocol` (structural). Easier to mock, fewer inheritance traps. Open to flipping if mypy ergonomics push back.
- **Production WSGI server**: `gunicorn` is the default we'd document, but v1 doesn't deploy anywhere. Listed as a dev-dependency hint, not wired up.
- **Test depth in v1**: thorough on `domain/` (pure logic), `persistence/` (round-trip), `services/` (mutation semantics). Light on routes (one happy-path per endpoint + one validation failure). The board change will demand more route-level coverage when forms get richer.
