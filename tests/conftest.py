from __future__ import annotations

from typing import cast

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.config import TestConfig
from app.persistence import InMemoryTaskRepository
from app.services import TaskService


@pytest.fixture()
def app() -> Flask:
    flask_app = create_app(TestConfig)
    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture()
def service(app: Flask) -> TaskService:
    return cast(TaskService, app.extensions["task_service"])


@pytest.fixture()
def repo(service: TaskService) -> InMemoryTaskRepository:
    return cast(InMemoryTaskRepository, service.repo)
