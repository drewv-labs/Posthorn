from __future__ import annotations

from typing import Protocol

from .models import (
    AlertCarrierConfig,
    Campaign,
    JobPost,
)


class AlertCarrierAdapter(Protocol):
    """Structural type for outbound notification adapters."""

    @classmethod
    def from_config(cls, config: AlertCarrierConfig) -> AlertCarrierAdapter:
        """Factory method to create a carrier from a configuration."""
        ...

    @property
    def name(self) -> str:
        """Carrier's name"""
        ...

    async def dispatch(self, job: JobPost, campaign: Campaign) -> None:
        """Transmits the payload to the carrier's destination (Telegram, Discord, etc.)."""
        ...
