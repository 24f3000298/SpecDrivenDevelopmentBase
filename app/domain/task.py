"""The framework-free Task entity.

Imports only stdlib — never Flask, sqlite3, or anything from upper layers.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.status import STATUS_TODO

MAX_TITLE_LEN = 200
MAX_DESCRIPTION_LEN = 2000


class InvalidTaskError(ValueError):
    """Raised when task fields violate domain invariants."""


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
    def create(
        cls,
        *,
        title: str,
        description: str = "",
        order: int = 0,
        status: str = STATUS_TODO,
    ) -> Task:
        title = title.strip()
        if not title:
            raise InvalidTaskError("title must be non-empty")
        if len(title) > MAX_TITLE_LEN:
            raise InvalidTaskError(f"title exceeds {MAX_TITLE_LEN} characters")
        if len(description) > MAX_DESCRIPTION_LEN:
            raise InvalidTaskError(f"description exceeds {MAX_DESCRIPTION_LEN} characters")
        now = datetime.now(tz=UTC)
        return cls(
            id=uuid.uuid4().hex,
            title=title,
            description=description,
            status=status,
            order=order,
            created_at=now,
            updated_at=now,
        )
