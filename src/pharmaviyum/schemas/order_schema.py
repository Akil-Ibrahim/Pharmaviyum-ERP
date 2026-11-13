from datetime import datetime

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    patient_id: int = Field(..., gt=0)
    total_amount: float = Field(..., ge=0)


class OrderResponse(BaseModel):
    id: int
    patient_id: int
    total_amount: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(completed|cancelled)$")
