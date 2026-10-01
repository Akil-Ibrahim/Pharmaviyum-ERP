"""Unit tests for pharmacy batch expiry classification."""

from datetime import date

import pytest

from src.pharmaviyum.api.v1.pharmacy_entities import (
    _batch_expiry_alert,
    _batch_expiry_status,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("days", "expected_status"),
    [
        (-1, "red"),
        (0, "red"),
        (30, "red"),
        (31, "yellow"),
        (60, "yellow"),
        (90, "yellow"),
        (91, "green"),
    ],
)
def test_batch_expiry_status_boundaries(days: int, expected_status: str) -> None:
    today = date(2026, 9, 29)

    days_to_expiry, status = _batch_expiry_status(
        date.fromordinal(today.toordinal() + days), today
    )

    assert days_to_expiry == days
    assert status == expected_status


@pytest.mark.parametrize(
    ("expiry_date", "expected_alert"),
    [
        (date(2026, 9, 28), "expired"),
        (date(2026, 12, 29), "3_months"),
        (date(2027, 6, 29), "9_months"),
        (date(2027, 9, 29), "12_months"),
        (date(2027, 9, 30), "none"),
    ],
)
def test_batch_expiry_alert_horizons(
    expiry_date: date, expected_alert: str
) -> None:
    today = date(2026, 9, 29)

    assert _batch_expiry_alert(expiry_date, today) == expected_alert
