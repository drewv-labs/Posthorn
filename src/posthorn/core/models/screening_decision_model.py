from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScreeningDecision:
    """Strict structured output for the optional AI job screening feature."""
    is_relevant: bool
    reason: str
