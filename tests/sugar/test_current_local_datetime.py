from __future__ import annotations

from datetime import datetime

from freezegun import freeze_time

from posthorn.sugar.current_local_datetime import current_local_datetime


def test_current_local_datetime_returns_datetime() -> None:
    """Verify the return type is a datetime object."""
    result = current_local_datetime()
    assert isinstance(result, datetime)


def test_current_local_datetime_is_timezone_aware() -> None:
    """Verify the returned datetime is timezone-aware (not naive)."""
    result = current_local_datetime()
    assert result.tzinfo is not None


@freeze_time("2023-10-27 12:00:00")
def test_current_local_datetime_frozen_time() -> None:
    """Verify that the function returns the frozen time relative to local timezone."""
    result = current_local_datetime()

    # When frozen, datetime.now() returns the frozen naive datetime.
    # .astimezone() then assumes this naive datetime is local time.
    assert result.year == 2023
    assert result.month == 10
    assert result.day == 27
    assert result.hour == 12
    assert result.minute == 0
    assert result.second == 0


@freeze_time("2024-02-29 12:00:00")
def test_current_local_datetime_leap_year() -> None:
    """Verify correctness on a leap day."""
    result = current_local_datetime()
    assert result.year == 2024
    assert result.month == 2
    assert result.day == 29


@freeze_time("2023-12-31 23:59:59.999999")
def test_current_local_datetime_year_boundary() -> None:
    """Verify correctness at the very end of the year."""
    result = current_local_datetime()
    assert result.year == 2023
    assert result.month == 12
    assert result.day == 31
    assert result.hour == 23
    assert result.minute == 59
    assert result.second == 59


def test_current_local_datetime_is_recent() -> None:
    """Verify that the returned time is very close to the actual current time."""
    now = datetime.now().astimezone()
    result = current_local_datetime()
    # Allow 1 second difference for execution time
    diff = abs((result - now).total_seconds())
    assert diff < 1.0
