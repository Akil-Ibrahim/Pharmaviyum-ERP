"""Request and response contracts for pharmacy POS checkout."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PaymentMethod = Literal["cash", "card_terminal", "online"]


class SaleLineCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=10000)


class SaleCreate(BaseModel):
    pharmacy_id: int = Field(gt=0)
    idempotency_key: str = Field(min_length=8, max_length=100)
    items: list[SaleLineCreate] = Field(min_length=1, max_length=100)
    discount_total: Decimal = Field(
        default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2
    )
    payment_method: PaymentMethod
    cash_received: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=2
    )

    @model_validator(mode="after")
    def unique_products(self):
        ids = [line.product_id for line in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("Each product may appear only once; combine quantities")
        if self.payment_method == "cash" and self.cash_received is None:
            raise ValueError("cash_received is required for cash payments")
        if self.payment_method != "cash" and self.cash_received is not None:
            raise ValueError("cash_received is only valid for cash payments")
        return self


class SaleItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: str
    sku: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    method: str
    status: str
    amount: Decimal
    cash_received: Decimal | None = None
    change_due: Decimal | None = None
    provider_name: str | None
    provider_payment_id: str | None
    created_at: datetime
    settled_at: datetime | None


class SaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    receipt_number: str
    pharmacy_id: int
    subtotal: Decimal
    discount_total: Decimal
    total: Decimal
    status: str
    created_at: datetime
    completed_at: datetime | None
    items: list[SaleItemResponse]
    payments: list[PaymentResponse]
    cash_change: Decimal = Decimal("0.00")

class InventoryReceiptCreate(BaseModel):
    """Validated stock receipt for a single pharmacy lot."""

    pharmacy_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    lot_number: str = Field(min_length=1, max_length=100)
    expiry_date: datetime
    quantity: int = Field(gt=0, le=100000)

    @model_validator(mode="after")
    def expiry_must_not_be_in_past(self):
        from datetime import timezone

        expiry = self.expiry_date
        if expiry.tzinfo is not None:
            expiry = expiry.astimezone(timezone.utc).replace(tzinfo=None)
        if expiry.date() < datetime.utcnow().date():
            raise ValueError("Cannot receive an expired medicine lot")
        return self


class InventoryReceiptResponse(BaseModel):
    inventory_id: int
    pharmacy_id: int
    product_id: int
    lot_number: str
    expiry_date: datetime
    received_quantity: int
    lot_quantity: int
    available_quantity: int
    message: str

