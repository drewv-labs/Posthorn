from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone
from typing import TYPE_CHECKING

import pytest
from freezegun import freeze_time

if TYPE_CHECKING:
    from posthorn.sugar.to_datetime import to_datetime


def test_to_datetime_aware_datetime():
    """Ensure aware datetimes are returned unchanged."""
    aware = datetime(2023, 1, 1, 12, 0, tzinfo=UTC)
    assert to_datetime(aware) == aware
    assert to_datetime(aware).tzinfo is not None


def test_to_datetime_naive_datetime():
    """Ensure naive datetimes are made timezone-aware (local)."""
    naive = datetime(2023, 1, 1, 12, 0)
    result = to_datetime(naive)
    assert result.tzinfo is not None
    assert result.year == 2023
    assert result.month == 1
    assert result.day == 1
    assert result.hour == 12


def test_to_datetime_date():
    """Ensure dates are converted to midnight local aware datetime."""
    d = date(2023, 1, 1)
    result = to_datetime(d)
    assert isinstance(result, datetime)
    assert result.tzinfo is not None
    assert result.date() == d
    assert result.hour == 0
    assert result.minute == 0
    assert result.second == 0


@pytest.mark.parametrize("iso_str, expected_tz", [
    ("2023-01-01T12:00:00+00:00", UTC),
    ("2023-01-01T12:00:00Z", UTC),
    ("2023-01-01T12:00:00+05:30", timezone(timedelta(hours=5, minutes=30))),
    ("2023-01-01T12:00:00-08:00", timezone(timedelta(hours=-8))),
])
def test_to_datetime_aware_strings(iso_str, expected_tz):
    """Test various ISO 8601 aware string formats."""
    result = to_datetime(iso_str)
    assert result.tzinfo == expected_tz


def test_to_datetime_naive_string():
    """Test naive ISO string conversion to local aware datetime."""
    iso_str = "2023-01-01T12:00:00"
    result = to_datetime(iso_str)
    assert result.tzinfo is not None
    assert result.year == 2023
    assert result.hour == 12


def test_to_datetime_date_only_string():
    """Test that strings containing only dates are handled (via fromisoformat)."""
    iso_str = "2023-01-01"
    result = to_datetime(iso_str)
    assert result.tzinfo is not None
    assert result.date() == date(2023, 1, 1)
    assert result.hour == 0


@pytest.mark.parametrize("invalid_input", [
    "not-a-date",
    "2023-13-01",  # Invalid month
    "2023-01-32",  # Invalid day
    "",           # Empty string
    " ",          # Whitespace string
])
def test_to_datetime_invalid_strings(invalid_input):
    """Ensure malformed strings raise ValueError."""
    with pytest.raises(ValueError):
        to_datetime(invalid_input)


@pytest.mark.parametrize("wrong_type", [
    None,
    123,
    123.456,
    ["2023-01-01"],
    {"date": "2023-01-01"},
])
def test_to_datetime_invalid_types(wrong_type):
    """Ensure invalid types raise TypeError."""
    with pytest.raises(TypeError) as excinfo:
        to_datetime(wrong_type)
    assert "Expected str, date, or datetime" in str(excinfo.value)


def test_to_datetime_boundaries():
    """Attack the function with min/max date values."""
    # Max date
    max_d = date.max
    result_max = to_datetime(max_d)
    assert result_max.date() == max_d
    assert result_max.tzinfo is not None

    # Min date
    min_d = date.min
    result_min = to_datetime(min_d)
    assert result_min.date() == min_d
    assert result_min.tzinfo is not None


@freeze_time("2026-09-26 12:00:00")
def test_to_datetime_with_freeze():
    """
    Verify behavior under a frozen time context.
    Note: to_datetime doesn't call datetime.now(),
    but we ensure no side effects or unexpected shifts occur.
    """
    naive = datetime(2026, 9, 26, 12, 0)
    result = to_datetime(naive)
    assert result.tzinfo is not None
    assert result.year == 2026
    assert result.month == 9
    assert result.day == 26
