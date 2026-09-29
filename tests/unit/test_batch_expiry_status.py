"""Unit tests for pharmacy batch expiry classification."""

from datetime import date

import pytest

from src.pharmaviyum.api.v1.pharmacy_entities import _batch_expiry_status


@pytest.mark.unit
@pytest.mark.parametrize(
    ("days", "expected_status"),
    [
        (-1, "red"),
        (0, "red"),
        (7, "red"),
        (8, "yellow"),
        (30, "yellow"),
        (31, "green"),
    ],
)
def test_batch_expiry_status_boundaries(
    days: int, expected_status: str
) -> None:
    today = date(2026, 9, 29)

    days_to_expiry, status = _batch_expiry_status(
        date.fromordinal(today.toordinal() + days), today
    )

    assert days_to_expiry == days
    assert status == expected_status
