from __future__ import annotations

from datetime import date, datetime


def to_datetime(d: str | date | datetime) -> datetime:
    """
    Normalizes a string, date, or datetime into a timezone-aware datetime object.
    Date objects are converted to midnight local time.
    """
    if isinstance(d, datetime):
        # Ensure timezone awareness. If naive, assume local system time.
        return d if d.tzinfo else d.astimezone()
    if isinstance(d, date):
        # Convert date to midnight, then make it local timezone-aware.
        return datetime.combine(d, datetime.min.time()).astimezone()
    if isinstance(d, str):
        dt = datetime.fromisoformat(d.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.astimezone()

    raise TypeError(f"Expected str, date, or datetime; got {type(d).__name__}")
