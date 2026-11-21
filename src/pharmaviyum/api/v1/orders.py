from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.db.session import get_db
from src.pharmaviyum.models.order import Order
from src.pharmaviyum.models.patients import Patient, PatientPurchase
from src.pharmaviyum.models.user import User
from src.pharmaviyum.modules.auth.deps import (
    get_current_active_superuser,
    get_current_active_user,
)
from src.pharmaviyum.modules.auth.tenant import resolve_pharmacy_scope
from src.pharmaviyum.schemas.order_schema import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
)
from src.pharmaviyum.services.cache import cache_service

router = APIRouter(prefix="/orders", tags=["Orders"])


def _patient_query(patient_id: int, pharmacy_id: int | None):
    """Build a patient lookup constrained in SQL when a tenant is resolved."""
    statement = select(Patient).where(Patient.id == patient_id)
    if pharmacy_id is not None:
        statement = statement.where(Patient.pharmacy_id == pharmacy_id)
    return statement


def _order_query(order_id: int, pharmacy_id: int | None):
    """Build an order lookup constrained through its owning patient tenant."""
    statement = (
        select(Order)
        .join(Patient, Patient.id == Order.patient_id)
        .where(Order.id == order_id)
    )
    if pharmacy_id is not None:
        statement = statement.where(Patient.pharmacy_id == pharmacy_id)
    return statement


def _purchase_query(receipt_number: str, pharmacy_id: int | None):
    """Build a purchase lookup constrained through its owning patient tenant."""
    statement = (
        select(PatientPurchase)
        .join(Patient, Patient.id == PatientPurchase.patient_id)
        .where(PatientPurchase.receipt_number == receipt_number)
    )
    if pharmacy_id is not None:
        statement = statement.where(Patient.pharmacy_id == pharmacy_id)
    return statement


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    pharmacy_id: int | None = None,
):
    scope = await resolve_pharmacy_scope(pharmacy_id, current_user, db)

    result = await db.execute(_patient_query(data.patient_id, scope))
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
    pharmacy_id: int | None = None,
):
    scope = await resolve_pharmacy_scope(pharmacy_id, current_user, db)

    result = await db.execute(_order_query(order_id, scope))
    order = result.scalar_one_or_none()
    if not order:
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

    result = await db.execute(_order_query(order_id, scope))
    order = result.scalar_one_or_none()
    if not order:
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
        purchase_result = await db.execute(_purchase_query(receipt_number, scope))
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
            patient_result = await db.execute(_patient_query(order.patient_id, scope))
            patient: Patient = patient_result.scalar_one()
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
