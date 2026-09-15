from datetime import datetime

from pydantic import BaseModel


class OrderCreate(BaseModel):
    client_id: int
    total_amount: float


class OrderResponse(BaseModel):
    id: int
    client_id: int
    total_amount: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
