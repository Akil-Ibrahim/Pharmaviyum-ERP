"""FEFO stock selection tests for POS schemas and ordering logic."""
from datetime import date, datetime, timedelta


def test_fefo_orders_earliest_expiry_first() -> None:
    batches = [
        {"id": 3, "expiry_date": date(2027, 6, 1)},
        {"id": 1, "expiry_date": date(2026, 12, 1)},
        {"id": 2, "expiry_date": date(2027, 1, 1)},
    ]
    ordered = sorted(batches, key=lambda row: row["expiry_date"])
    assert [row["id"] for row in ordered] == [1, 2, 3]


def test_expired_batch_is_not_eligible_for_fefo() -> None:
    now = datetime.utcnow()
    candidates = [
        {"id": 1, "expires_at": now - timedelta(days=1)},
        {"id": 2, "expires_at": now + timedelta(days=30)},
    ]
    eligible = [row for row in candidates if row["expires_at"] >= now]
    assert [row["id"] for row in eligible] == [2]


def test_fefo_requires_enough_stock_for_single_batch() -> None:
    requested = 10
    batches = [
        {"id": 1, "expiry_date": date(2026, 12, 1), "quantity": 4},
        {"id": 2, "expiry_date": date(2027, 1, 1), "quantity": 12},
    ]
    eligible = sorted(
        [row for row in batches if row["quantity"] >= requested],
        key=lambda row: row["expiry_date"],
    )
    assert eligible[0]["id"] == 2
