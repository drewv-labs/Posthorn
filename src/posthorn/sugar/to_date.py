from __future__ import annotations

from datetime import date, datetime


def to_date(d: str | date | datetime) -> date:
    """
    Normalizes a string, date, or datetime into a strict date object.
    Supports ISO 8601 strings (e.g., 'YYYY-MM-DD' or full timestamps).
    """
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        # 3.11+ natively handles the 'Z' suffix and variable precision,
        # but string replace ensures compatibility across edge cases.
        return datetime.fromisoformat(d.replace("Z", "+00:00")).date()

    raise TypeError(f"Expected str, date, or datetime; got {type(d).__name__}")
