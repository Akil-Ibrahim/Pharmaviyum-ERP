from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1)
    sku: str = Field(..., min_length=1)
    description: Optional[str] = None
    price: float = 0.0
    stock: int = 0


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    sku: str
    description: Optional[str] = None
    price: float
    stock: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
