from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.pharmaviyum.db.session import get_db
from src.pharmaviyum.models.patients import PatientPurchase
from src.pharmaviyum.modules.auth.deps import CurrentSuperuser

router = APIRouter(prefix="/patient-purchases", tags=["Patient Purchases"])


@router.get("/")
async def list_patient_purchases(
    _: CurrentSuperuser,
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[dict[str, Any]]:
    result = await db.execute(
        select(PatientPurchase)
        .options(selectinload(PatientPurchase.product), selectinload(PatientPurchase.batch))
        .order_by(PatientPurchase.purchased_at.desc(), PatientPurchase.id.desc())
        .offset(skip)
        .limit(limit)
    )
    purchases = result.scalars().all()
    return [
        {
            "id": purchase.id,
            "patient_id": purchase.patient_id,
            "product_id": purchase.product_id,
            "product_name": purchase.product_name,
            "batch_id": purchase.batch_id,
            "batch_number": purchase.batch_number,
            "receipt_number": purchase.receipt_number,
            "category": purchase.category,
            "quantity": purchase.quantity,
            "dispensed_packs": purchase.dispensed_packs,
            "dispensed_blisters": purchase.dispensed_blisters,
            "dispensed_units": purchase.dispensed_units,
            "unit_price": purchase.unit_price,
            "total_amount": purchase.total_amount,
            "prescription_required": purchase.prescription_required,
            "purchased_at": purchase.purchased_at,
            "expiry_date": purchase.expiry_date,
        }
        for purchase in purchases
    ]
