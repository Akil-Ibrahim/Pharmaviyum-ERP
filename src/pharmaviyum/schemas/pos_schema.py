from pydantic import BaseModel, Field


class POSItem(BaseModel):
    product_id: int = Field(gt=0)
    batch_id: int | None = Field(default=None, gt=0)
    packs: int = Field(default=0, ge=0)
    blisters: int = Field(default=0, ge=0)
    units: int = Field(default=0, ge=0)
    prescription_id: int | None = Field(default=None, gt=0)
    unit_price: float | None = Field(default=None, ge=0)


class POSTransactionCreate(BaseModel):
    pharmacy_id: int = Field(gt=0)
    patient_id: int = Field(gt=0)
    payment_method: str = Field(pattern="^(cash|card)$")
    items: list[POSItem] = Field(min_length=1, max_length=50)


class POSTransactionResponse(BaseModel):
    order_id: int
    receipt_number: str
    status: str
    payment_method: str
    payment_status: str
    total_amount: float
    item_count: int
    inventory_updated: bool
    patient_history_updated: bool
    audit_created: bool

class POSReturnItemCreate(BaseModel):
    order_item_id: int = Field(gt=0)
    quantity_units: int = Field(gt=0)


class POSReturnCreate(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    refund_method: str = Field(pattern="^(cash|card)$")
    items: list[POSReturnItemCreate] = Field(min_length=1, max_length=50)


class POSReturnResponse(BaseModel):
    return_id: int
    order_id: int
    status: str
    refund_method: str
    total_amount: float
    item_count: int
