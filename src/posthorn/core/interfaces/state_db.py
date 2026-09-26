from __future__ import annotations

from typing import Any, Protocol

from ..models import JobPost


class StateDB(Protocol):
    """Structural type for state database adapters."""

    @property
    def name(self) -> str:
        """Database name"""
        ...

    def update(self, job_post: JobPost, context: dict[str, Any]) -> None:
        ...
