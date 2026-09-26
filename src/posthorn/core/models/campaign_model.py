from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class Campaign:
    """Session configuration for a targeted polling run."""
    name: str
    keywords: list[str]
    locations: list[str] = dataclasses.field(default_factory=lambda: ["United States"])
