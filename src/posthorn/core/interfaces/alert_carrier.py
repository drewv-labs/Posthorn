from __future__ import annotations

from typing import Protocol

from ..models import (
    Campaign,
    JobPost,
)


class AlertCarrier(Protocol):
    """Structural type for outbound notification adapters."""

    @property
    def name(self) -> str:
        """Carrier's name"""
        ...

    async def dispatch(self, job: JobPost, campaign: Campaign) -> None:
        """Transmits the payload to the carrier's destination (Telegram, Discord, etc.)."""
        ...
