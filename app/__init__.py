"""Flask app factory.

The factory wires the chosen ``TaskRepository`` and ``TaskService`` into the
Flask app, then registers the ``todo`` blueprint. This is the only module
besides ``app/todo/`` permitted to import Flask directly.
"""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, render_template

from app.config import BaseConfig, DevConfig, ProdConfig, TestConfig
from app.persistence import InMemoryTaskRepository, SQLiteTaskRepository, TaskRepository
from app.services import TaskService

_ENV_TO_CONFIG: dict[str, type[BaseConfig]] = {
    "development": DevConfig,
    "testing": TestConfig,
    "production": ProdConfig,
}


def _resolve_config(config: type | str | None) -> BaseConfig:
    if isinstance(config, type):
        return config()  # type: ignore[no-any-return]
    if isinstance(config, str):
        cls = _ENV_TO_CONFIG.get(config.lower())
        if cls is None:
            raise ValueError(f"Unknown config name: {config!r}")
        return cls()
    env = os.environ.get("FLASK_ENV", "development").lower()
    return _ENV_TO_CONFIG.get(env, DevConfig)()


def _build_repository(cfg: BaseConfig, instance_path: Path) -> TaskRepository:
    if cfg.REPOSITORY == "memory":
        return InMemoryTaskRepository()
    db_path = Path(cfg.DATABASE_PATH) if cfg.DATABASE_PATH else (instance_path / "tasks.db")
    return SQLiteTaskRepository(db_path)


def create_app(config: type | str | None = None) -> Flask:
    flask_app = Flask(__name__, instance_relative_config=True)
    cfg = _resolve_config(config)
    flask_app.config.from_object(cfg)

    instance_path = Path(flask_app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)

    repo = _build_repository(cfg, instance_path)
    flask_app.extensions["task_service"] = TaskService(repo)

    from app.todo import bp as todo_bp

    flask_app.register_blueprint(todo_bp)

    @flask_app.errorhandler(404)
    def _not_found(_e: object) -> tuple[str, int]:
        return render_template("errors/404.html"), 404

    @flask_app.errorhandler(500)
    def _server_error(_e: object) -> tuple[str, int]:
        return render_template("errors/500.html"), 500

    return flask_app
