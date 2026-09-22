from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.db.session import get_db
from src.pharmaviyum.models.order import Order
from src.pharmaviyum.models.patients import Patient, PatientPurchase
from src.pharmaviyum.modules.auth.tenant import resolve_pharmacy_scope
from src.pharmaviyum.modules.auth.deps import (
    get_current_active_superuser,
    get_current_active_user,
)
from src.pharmaviyum.modules.auth.models import User
from src.pharmaviyum.schemas.order_schema import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
)
from src.pharmaviyum.services.cache import cache_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    pharmacy_id: int | None = None,
):
    scope = await resolve_pharmacy_scope(pharmacy_id, current_user, db)

    result = await db.execute(select(Patient).where(Patient.id == data.patient_id))
    patient = result.scalar_one_or_none()
    if not patient or (scope is not None and patient.pharmacy_id != scope):
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
    pharmacy_id: int | None = None,
):
    scope = await resolve_pharmacy_scope(pharmacy_id, current_user, db)

    result = await db.execute(
        select(Order)
        .join(Patient, Patient.id == Order.patient_id)
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order or (scope is not None and order.patient.pharmacy_id != scope):
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    pharmacy_id: int | None = None,
):
    scope = await resolve_pharmacy_scope(pharmacy_id, current_user, db)

    result = await db.execute(
        select(Order)
        .join(Patient, Patient.id == Order.patient_id)
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order or (scope is not None and order.patient.pharmacy_id != scope):
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Order is already {order.status}",
        )

    if data.status == "cancelled":
        order.status = "cancelled"
    else:
        # The current Order model has no line items. Persist completion as a
        # single order-level purchase so revenue enters the same canonical
        # PatientPurchase ledger without inventing product/batch data.
        receipt_number = f"ORDER-{order.id}"
        purchase_result = await db.execute(
            select(PatientPurchase).where(
                PatientPurchase.receipt_number == receipt_number
            )
        )
        if purchase_result.scalar_one_or_none() is None:
            db.add(
                PatientPurchase(
                    patient_id=order.patient_id,
                    receipt_number=receipt_number,
                    category="order",
                    quantity=1,
                    dispensed_packs=1,
                    dispensed_blisters=0,
                    dispensed_units=0,
                    unit_price=order.total_amount,
                    prescription_required=False,
                    purchased_at=order.created_at,
                )
            )
            result = await db.execute(
                select(Patient).where(Patient.id == order.patient_id)
            )
            patient = result.scalar_one()
            patient.visit_count += 1
            patient.last_visit_date = order.created_at
            await cache_service.delete(
                f"patient:{patient.pharmacy_id or 0}:{patient.id}"
            )
            await cache_service.delete(
                f"patient:ai_profile:{patient.pharmacy_id or 0}:{patient.id}"
            )
            await cache_service.delete(
                f"patient:phone:{patient.pharmacy_id or 0}:{patient.phone}"
            )

        order.status = "completed"

    await db.commit()
    await db.refresh(order)
    return order
