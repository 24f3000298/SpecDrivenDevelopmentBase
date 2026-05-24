"""Flask configuration classes.

Imported only by ``app.__init__.create_app``. The domain/persistence/service
layers must not depend on Flask config — they receive their dependencies via
constructor injection.
"""

from __future__ import annotations

import os


class ConfigError(RuntimeError):
    """Raised when required configuration is missing."""


class BaseConfig:
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-only-do-not-use-in-prod")
    DATABASE_PATH: str | None = os.environ.get("DATABASE_PATH") or None
    REPOSITORY: str = "sqlite"  # "sqlite" or "memory"
    DEBUG: bool = False
    TESTING: bool = False


class DevConfig(BaseConfig):
    DEBUG = True


class TestConfig(BaseConfig):
    TESTING = True
    REPOSITORY = "memory"
    SECRET_KEY = "test-secret"


class ProdConfig(BaseConfig):
    DEBUG = False

    def __init__(self) -> None:
        if not os.environ.get("SECRET_KEY"):
            raise ConfigError("SECRET_KEY must be set in the environment for production")
        self.SECRET_KEY = os.environ["SECRET_KEY"]
