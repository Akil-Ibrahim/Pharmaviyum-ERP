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
    currency: str = Field(
        default="UAH", min_length=3, max_length=3, pattern=r"^[A-Z]{3}$"
    )
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
    currency: str
    provider_name: str | None
    provider_payment_id: str | None
    created_at: datetime
    settled_at: datetime | None


class SaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    receipt_number: str
    pharmacy_id: int
    currency: str
    subtotal: Decimal
    discount_total: Decimal
    total: Decimal
    status: str
    created_at: datetime
    completed_at: datetime | None
    items: list[SaleItemResponse]
    payments: list[PaymentResponse]
    cash_change: Decimal = Decimal("0.00")
