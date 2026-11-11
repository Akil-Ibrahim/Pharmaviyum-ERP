"""Request and response contracts for Edge synchronization ingress."""

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
        allowed_event_types = {
            "pos.sale.created",
            "pos.sale.cancelled",
            "pos.payment.succeeded",
            "pos.payment.failed",
        }
        if self.event_type not in allowed_event_types:
            raise ValueError("Unsupported event_type for synchronization contract v1")
        if self.schema_version != 1 or self.aggregate_type != "sale":
            raise ValueError("Unsupported schema version or aggregate type for v1")
        expected_aggregate_version = 1 if self.event_type == "pos.sale.created" else 2
        if self.aggregate_version != expected_aggregate_version:
            raise ValueError("Unexpected aggregate version for POS event type")

        def require_shape(
            value: Any,
            *,
            required: set[str],
            allowed: set[str],
            label: str,
        ) -> dict[str, Any]:
            if not isinstance(value, dict):
                raise ValueError(f"{label} must be an object")
            keys = set(value)
            if not required.issubset(keys) or not keys.issubset(allowed):
                raise ValueError(f"{label} does not match the approved v1 schema")
            return value

        if self.event_type == "pos.sale.created":
            sale = require_shape(
                self.payload,
                required={
                    "receipt_number",
                    "status",
                    "subtotal",
                    "discount_total",
                    "total",
                    "inventory_effect",
                    "items",
                    "payment",
                },
                allowed={
                    "receipt_number",
                    "status",
                    "subtotal",
                    "discount_total",
                    "total",
                    "inventory_effect",
                    "items",
                    "payment",
                },
                label="pos.sale.created payload",
            )
            if not isinstance(sale["items"], list):
                raise ValueError("sale items must be an array")
            for item in sale["items"]:
                line = require_shape(
                    item,
                    required={
                        "product_sku",
                        "product_name",
                        "quantity",
                        "unit_price",
                        "line_total",
                        "allocations",
                    },
                    allowed={
                        "product_sku",
                        "product_name",
                        "quantity",
                        "unit_price",
                        "line_total",
                        "allocations",
                    },
                    label="sale item",
                )
                if not isinstance(line["allocations"], list):
                    raise ValueError("sale item allocations must be an array")
                for allocation in line["allocations"]:
                    require_shape(
                        allocation,
                        required={
                            "lot_number",
                            "expires_at",
                            "quantity",
                        },
                        allowed={
                            "lot_number",
                            "expires_at",
                            "quantity",
                        },
                        label="sale lot allocation",
                    )
            require_shape(
                sale["payment"],
                required={"method", "status", "amount"},
                allowed={"method", "status", "amount"},
                label="sale payment",
            )
        elif self.event_type in {
            "pos.payment.succeeded",
            "pos.payment.failed",
        }:
            payment = require_shape(
                self.payload,
                required={
                    "receipt_number",
                    "sale_status",
                    "payment_status",
                    "amount",
                    "provider_name",
                    "inventory_effect",
                    "allocations",
                },
                allowed={
                    "receipt_number",
                    "sale_status",
                    "payment_status",
                    "amount",
                    "provider_name",
                    "inventory_effect",
                    "allocations",
                },
                label="payment event payload",
            )
            if not isinstance(payment["allocations"], list):
                raise ValueError("payment allocations must be an array")
            for allocation in payment["allocations"]:
                require_shape(
                    allocation,
                    required={"product_sku", "lot_number", "quantity"},
                    allowed={"product_sku", "lot_number", "quantity"},
                    label="payment lot allocation",
                )
        else:
            cancelled = require_shape(
                self.payload,
                required={
                    "receipt_number",
                    "sale_status",
                    "inventory_effect",
                    "released_allocations",
                },
                allowed={
                    "receipt_number",
                    "sale_status",
                    "inventory_effect",
                    "released_allocations",
                },
                label="sale cancellation payload",
            )
            if not isinstance(cancelled["released_allocations"], list):
                raise ValueError("released allocations must be an array")
            for allocation in cancelled["released_allocations"]:
                require_shape(
                    allocation,
                    required={"product_sku", "lot_number", "quantity"},
                    allowed={"product_sku", "lot_number", "quantity"},
                    label="released lot allocation",
                )

        if str(self.payload.get("receipt_number", "")) != self.aggregate_id:
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
