"""Unit tests for deterministic multi-batch FEFO allocation."""

from datetime import date

import pytest

from src.pharmaviyum.services.fefo import allocate_fefo


def test_fefo_consumes_multiple_batches_in_expiry_order() -> None:
    allocations = allocate_fefo(
        [
            {"id": 1, "expiry_date": date(2026, 12, 1), "quantity": 6},
            {"id": 2, "expiry_date": date(2027, 1, 1), "quantity": 20},
        ],
        10,
        today=date(2026, 9, 29),
    )
    assert allocations == [
        {"batch_id": 1, "quantity": 6},
        {"batch_id": 2, "quantity": 4},
    ]


def test_fefo_excludes_expired_batches() -> None:
    allocations = allocate_fefo(
        [
            {"id": 1, "expiry_date": date(2026, 9, 28), "quantity": 100},
            {"id": 2, "expiry_date": date(2026, 12, 1), "quantity": 5},
        ],
        5,
        today=date(2026, 9, 29),
    )
    assert allocations == [{"batch_id": 2, "quantity": 5}]


def test_fefo_raises_when_usable_stock_is_insufficient() -> None:
    with pytest.raises(ValueError, match="insufficient usable FEFO inventory"):
        allocate_fefo(
            [{"id": 1, "expiry_date": date(2026, 12, 1), "quantity": 4}],
            5,
            today=date(2026, 9, 29),
        )


def test_fefo_is_deterministic_for_same_expiry() -> None:
    allocations = allocate_fefo(
        [
            {"id": 2, "expiry_date": date(2027, 1, 1), "quantity": 3},
            {"id": 1, "expiry_date": date(2027, 1, 1), "quantity": 3},
        ],
        4,
        today=date(2026, 9, 29),
    )
    assert allocations == [
        {"batch_id": 1, "quantity": 3},
        {"batch_id": 2, "quantity": 1},
    ]
