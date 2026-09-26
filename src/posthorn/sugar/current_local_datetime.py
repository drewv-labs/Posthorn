from __future__ import annotations

from datetime import datetime


def current_local_datetime() -> datetime:
    """Returns the current timezone-aware local datetime."""
    return datetime.now().astimezone()
