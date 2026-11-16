"""Strict schema tests for Pharmacy Edge v1 POS events."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.pharmaviyum.schemas.sync import SyncEventEnvelope

pytestmark = pytest.mark.unit


def _event(payload: dict | None = None) -> dict:
    return {
        "event_id": str(uuid4()),
        "edge_node_id": str(uuid4()),
        "event_type": "pos.sale.created",
        "schema_version": 1,
        "aggregate_type": "sale",
        "aggregate_id": "PV-SCHEMA-1",
        "aggregate_version": 1,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "payload": payload
        or {
            "receipt_number": "PV-SCHEMA-1",
            "status": "completed",
            "subtotal": "20.00",
            "discount_total": "0.00",
            "total": "20.00",
            "inventory_effect": "decrement",
            "items": [
                {
                    "product_sku": "SKU-1",
                    "product_name": "Test Medicine",
                    "quantity": 2,
                    "unit_price": "10.00",
                    "line_total": "20.00",
                    "allocations": [
                        {"lot_number": "LOT-1", "expires_at": "2027-01-01T00:00:00", "quantity": 2}
                    ],
                }
            ],
            "payment": {"method": "cash", "status": "succeeded", "amount": "20.00"},
        },
    }


def test_valid_sale_event_accepts_strict_typed_payload() -> None:
    envelope = SyncEventEnvelope.model_validate(_event())
    assert envelope.aggregate_id == "PV-SCHEMA-1"


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda p: p["items"][0].update(quantity=True), "valid integer"),
        (lambda p: p["items"][0].update(quantity=0), "greater than 0"),
        (lambda p: p["items"][0].update(unit_price="10.0"), "two decimals"),
        (lambda p: p["items"][0].update(line_total="19.99"), "line_total must equal"),
        (lambda p: p["items"][0]["allocations"][0].update(quantity=1), "allocation quantities"),
        (lambda p: p["payment"].update(method="crypto"), "payment.method"),
        (lambda p: p["payment"].update(extra_field="not-allowed"), "Extra inputs"),
        (lambda p: p.update(patient_name="not-allowed"), "Extra inputs"),
    ],
)
def test_invalid_sale_payload_is_rejected(mutate, message: str) -> None:
    event = _event()
    mutate(event["payload"])
    with pytest.raises(ValidationError, match=message):
        SyncEventEnvelope.model_validate(event)


def test_sale_totals_must_reconcile() -> None:
    event = _event()
    event["payload"]["total"] = "19.00"
    with pytest.raises(ValidationError, match="total must equal"):
        SyncEventEnvelope.model_validate(event)


def test_completed_sale_cannot_claim_reserved_stock_or_pending_payment() -> None:
    event = _event()
    event["payload"]["inventory_effect"] = "reserve"
    with pytest.raises(ValidationError, match="completed sale"):
        SyncEventEnvelope.model_validate(event)
