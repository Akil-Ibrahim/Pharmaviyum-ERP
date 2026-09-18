from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.db.session import get_db
from src.pharmaviyum.models.order import Order
from src.pharmaviyum.models.patients import Patient
from src.pharmaviyum.modules.auth.deps import (
    get_current_active_superuser,
    get_current_active_user,
)
from src.pharmaviyum.modules.auth.models import User
from src.pharmaviyum.schemas.order_schema import OrderCreate, OrderResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
):
    del current_user

    result = await db.execute(select(Patient).where(Patient.id == data.patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if not patient.is_active:
        raise HTTPException(status_code=409, detail="Patient is inactive")

    order = Order(patient_id=data.patient_id, total_amount=data.total_amount)
    db.add(order)

    # Orders are not persisted receipt lines yet. Do not mutate the legacy
    # patient aggregate here: pending orders are not realized revenue, and
    # doing so would create a second source of truth alongside PatientPurchase.
    await db.commit()
    await db.refresh(order)
    return order


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    del current_user

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
