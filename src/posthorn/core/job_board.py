from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Protocol

from .models import Campaign, JobPost


class JobBoardConfig(Protocol):
    """Type Linking"""


class JobBoardAdapter(Protocol):
    """Structural type for inbound data sources."""

    @classmethod
    def from_config(cls, config: JobBoardConfig) -> JobBoardAdapter:
        """Factory method to create a job board adapter from a configuration."""
        ...

    @property
    def name(self) -> str:
        """Returns the name of the job board adapter."""
        ...

    async def poll(self, campaign: Campaign) -> AsyncGenerator[JobPost, None]:
        """Yields normalized job posts matching the campaign parameters."""
        ...
