"""Request and response contracts for Edge synchronization ingress."""

import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    field_validator,
    model_validator,
)


class EdgeNodeProvisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    pharmacy_id: int = Field(gt=0)
    display_name: str = Field(min_length=2, max_length=120)


class EdgeNodeProvisionResponse(BaseModel):
    node_id: UUID
    pharmacy_id: int
    display_name: str
    credential: str
    credential_notice: str = "Store this credential securely; it is shown only once."


class _SyncPayloadModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


def _money(value: str, *, field_name: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc
    if not parsed.is_finite() or parsed < 0 or parsed.as_tuple().exponent != -2:
        raise ValueError(
            f"{field_name} must be a non-negative amount with two decimals"
        )
    return parsed


class SyncLotAllocation(_SyncPayloadModel):
    lot_number: str = Field(min_length=1, max_length=100)
    expires_at: datetime | None
    quantity: StrictInt = Field(gt=0, le=1_000_000)


class SyncSaleItem(_SyncPayloadModel):
    product_sku: str = Field(min_length=1, max_length=100)
    product_name: str = Field(min_length=1, max_length=255)
    quantity: StrictInt = Field(gt=0, le=1_000_000)
    unit_price: str
    line_total: str
    allocations: list[SyncLotAllocation] = Field(max_length=1000)

    @model_validator(mode="after")
    def validate_amount_and_allocations(self) -> "SyncSaleItem":
        unit_price = _money(self.unit_price, field_name="unit_price")
        line_total = _money(self.line_total, field_name="line_total")
        if line_total != unit_price * self.quantity:
            raise ValueError("line_total must equal unit_price multiplied by quantity")
        if sum(item.quantity for item in self.allocations) != self.quantity:
            raise ValueError("lot allocation quantities must equal sale item quantity")
        return self


class SyncSalePayment(_SyncPayloadModel):
    method: Literal["cash", "card_terminal", "online"]
    status: Literal["succeeded", "pending"]
    amount: str

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: str) -> str:
        _money(value, field_name="payment.amount")
        return value


class SyncSaleCreatedPayload(_SyncPayloadModel):
    receipt_number: str = Field(min_length=1, max_length=100)
    status: Literal["completed", "awaiting_payment"]
    subtotal: str
    discount_total: str
    total: str
    inventory_effect: Literal["decrement", "reserve"]
    items: list[SyncSaleItem] = Field(min_length=1, max_length=1000)
    payment: SyncSalePayment

    @model_validator(mode="after")
    def validate_totals_and_state(self) -> "SyncSaleCreatedPayload":
        subtotal = _money(self.subtotal, field_name="subtotal")
        discount = _money(self.discount_total, field_name="discount_total")
        total = _money(self.total, field_name="total")
        payment_amount = _money(self.payment.amount, field_name="payment.amount")
        item_total = sum(
            (_money(item.line_total, field_name="line_total") for item in self.items),
            Decimal("0.00"),
        )
        if subtotal != item_total:
            raise ValueError("subtotal must equal the sum of sale item line totals")
        if total != subtotal - discount:
            raise ValueError("total must equal subtotal minus discount_total")
        if payment_amount != total:
            raise ValueError("payment.amount must equal sale total")
        if self.status == "completed":
            if (
                self.inventory_effect != "decrement"
                or self.payment.status != "succeeded"
            ):
                raise ValueError(
                    "completed sale must decrement stock and have succeeded payment"
                )
        elif self.inventory_effect != "reserve" or self.payment.status != "pending":
            raise ValueError(
                "awaiting-payment sale must reserve stock and have pending payment"
            )
        return self


class SyncPaymentAllocation(_SyncPayloadModel):
    product_sku: str = Field(min_length=1, max_length=100)
    lot_number: str = Field(min_length=1, max_length=100)
    quantity: StrictInt = Field(gt=0, le=1_000_000)


class SyncPaymentEventPayload(_SyncPayloadModel):
    receipt_number: str = Field(min_length=1, max_length=100)
    sale_status: Literal["completed", "cancelled"]
    payment_status: Literal["succeeded", "failed"]
    amount: str
    provider_name: str = Field(min_length=1, max_length=80)
    inventory_effect: Literal["commit_reservation", "release_reservation"]
    allocations: list[SyncPaymentAllocation] = Field(max_length=1000)

    @model_validator(mode="after")
    def validate_payment_state(self) -> "SyncPaymentEventPayload":
        _money(self.amount, field_name="amount")
        if self.payment_status == "succeeded":
            if (
                self.sale_status != "completed"
                or self.inventory_effect != "commit_reservation"
            ):
                raise ValueError(
                    "successful payment must complete sale and commit reservation"
                )
        elif (
            self.sale_status != "cancelled"
            or self.inventory_effect != "release_reservation"
        ):
            raise ValueError("failed payment must cancel sale and release reservation")
        return self


class SyncSaleCancelledPayload(_SyncPayloadModel):
    receipt_number: str = Field(min_length=1, max_length=100)
    sale_status: Literal["cancelled"]
    inventory_effect: Literal["release_reservation"]
    released_allocations: list[SyncPaymentAllocation] = Field(max_length=1000)


class SyncEventEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    edge_node_id: UUID
    event_type: str = Field(min_length=3, max_length=120)
    schema_version: int = Field(ge=1)
    aggregate_type: str = Field(min_length=1, max_length=80)
    aggregate_id: str = Field(min_length=1, max_length=100)
    aggregate_version: int = Field(ge=1)
    occurred_at: datetime
    payload: dict[str, Any]

    @model_validator(mode="after")
    def validate_initial_pos_payload(self) -> "SyncEventEnvelope":
        payload_models: dict[str, type[_SyncPayloadModel]] = {
            "pos.sale.created": SyncSaleCreatedPayload,
            "pos.sale.cancelled": SyncSaleCancelledPayload,
            "pos.payment.succeeded": SyncPaymentEventPayload,
            "pos.payment.failed": SyncPaymentEventPayload,
        }
        payload_model = payload_models.get(self.event_type)
        if payload_model is None:
            raise ValueError("Unsupported event_type for synchronization contract v1")
        if self.schema_version != 1 or self.aggregate_type != "sale":
            raise ValueError("Unsupported schema version or aggregate type for v1")
        expected_version = 1 if self.event_type == "pos.sale.created" else 2
        if self.aggregate_version != expected_version:
            raise ValueError("Unexpected aggregate version for POS event type")

        # JSON-mode validation parses ISO timestamps while preserving strict
        # primitive types (notably bool is never accepted as an integer).
        validated = payload_model.model_validate_json(json.dumps(self.payload))
        receipt_number = getattr(validated, "receipt_number", None)
        if receipt_number != self.aggregate_id:
            raise ValueError("aggregate_id must match the POS receipt_number")
        if len(json.dumps(self.payload, separators=(",", ":"))) > 262144:
            raise ValueError("Event payload exceeds the 256 KiB limit")
        return self

    @field_validator("occurred_at")
    @classmethod
    def require_timezone_aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone offset")
        return value.astimezone(timezone.utc)


class SyncEventAcknowledgement(BaseModel):
    event_id: UUID
    status: str
    duplicate: bool = False
