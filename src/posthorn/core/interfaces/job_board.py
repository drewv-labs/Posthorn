from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Protocol

from ..models import Campaign, JobPost


class JobBoard(Protocol):
    """Structural type for inbound data sources."""

    @property
    def name(self) -> str:
        """Returns the name of the job board adapter."""
        ...

    # Dropped 'async' here!
    def poll(self, campaign: Campaign) -> AsyncGenerator[JobPost, None]:
        """Yields normalized job posts matching the campaign parameters."""
        ...
