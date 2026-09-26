from datetime import UTC, date, datetime

import pytest
from freezegun import freeze_time

from posthorn.sugar.to_date import to_date


@freeze_time("2026-09-26")
class TestToDate:
    # --- Happy Paths ---

    def test_to_date_with_date_object(self):
        """Validates that a date object is returned as-is."""
        d = date(2023, 5, 20)
        assert to_date(d) == d
        assert isinstance(to_date(d), date)
        assert not isinstance(to_date(d), datetime)

    def test_to_date_with_datetime_object(self):
        """Validates that a datetime object is truncated to a date."""
        dt = datetime(2023, 5, 20, 15, 30, 45, tzinfo=UTC)
        expected = date(2023, 5, 20)
        assert to_date(dt) == expected
        assert isinstance(to_date(dt), date)
        assert not isinstance(to_date(dt), datetime)

    @pytest.mark.parametrize("iso_str, expected", [
        ("2023-05-20", date(2023, 5, 20)),
        ("2023-05-20T12:00:00", date(2023, 5, 20)),
        ("2023-05-20T12:00:00Z", date(2023, 5, 20)),
        ("2023-05-20T12:00:00+00:00", date(2023, 5, 20)),
        ("2023-05-20T12:00:00-05:00", date(2023, 5, 20)),
        ("2023-05-20 12:00:00", date(2023, 5, 20)), # fromisoformat handles space separator
    ])
    def test_to_date_with_valid_iso_strings(self, iso_str, expected):
        """Validates various ISO 8601 compliant strings."""
        assert to_date(iso_str) == expected

    # --- Adversarial / Edge Cases ---

    def test_to_date_leap_year(self):
        """Validates leap year boundary (Feb 29)."""
        assert to_date("2024-02-29") == date(2024, 2, 29)
        with pytest.raises(ValueError):
            to_date("2023-02-29") # Not a leap year

    @pytest.mark.parametrize("bad_str", [
        "",                 # Empty
        "   ",              # Whitespace
        "not-a-date",       # Junk
        "2023-13-01",       # Invalid month
        "2023-01-32",       # Invalid day
        "05-20-2023",       # Wrong format (US)
        "2023/05/20",       # Wrong separator
    ])
    def test_to_date_invalid_strings(self, bad_str):
        """Ensures malformed strings raise ValueError."""
        with pytest.raises(ValueError):
            to_date(bad_str)

    @pytest.mark.parametrize("bad_type", [
        None,
        123,
        123.45,
        ["2023-05-20"],
        {"date": "2023-05-20"},
    ])
    def test_to_date_invalid_types(self, bad_type):
        """Ensures unsupported types raise TypeError."""
        with pytest.raises(TypeError) as excinfo:
            to_date(bad_type)
        assert "Expected str, date, or datetime" in str(excinfo.value)

    def test_to_date_extreme_values(self):
        """Tests boundaries of the date object."""
        min_date = date.min.isoformat()
        max_date = date.max.isoformat()
        assert to_date(min_date) == date.min
        assert to_date(max_date) == date.max

    def test_to_date_timezone_shift_boundary(self):
        """
        Test a datetime string that is on the edge of a date change
        due to timezone offset.
        Note: .date() on a datetime object returns the date component
        WITHOUT adjusting for the offset first.
        """
        # 2023-05-21 01:00 AM UTC is still 2023-05-20 in New York (-4)
        # But fromisoformat().date() returns the date part of the string.
        ts = "2023-05-21T01:00:00-05:00"
        assert to_date(ts) == date(2023, 5, 21)
