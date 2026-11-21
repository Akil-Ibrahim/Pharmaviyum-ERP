from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.pharmaviyum.db.session import get_db
from src.pharmaviyum.models.pharmacy_membership import PharmacyMembership
from src.pharmaviyum.models.patients import Patient, PatientPurchase
from src.pharmaviyum.models.phi_access_audit import PHIAccessAudit
from src.pharmaviyum.modules.auth.deps import CurrentSuperuser, CurrentUser

router = APIRouter(prefix="/patient-purchases", tags=["Patient Purchases"])


@router.get("/")
async def list_patient_purchases(
    _: CurrentSuperuser,
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    pharmacy_id: int = Query(..., gt=0),
) -> list[dict[str, Any]]:
    """Retain the legacy administrative listing behind superuser auth."""
    result = await db.execute(
        select(PatientPurchase)
        .join(Patient, Patient.id == PatientPurchase.patient_id)
        .where(Patient.pharmacy_id == pharmacy_id)
        .options(
            selectinload(PatientPurchase.product), selectinload(PatientPurchase.batch)
        )
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


@router.get("/{patient_id}/history")
async def get_pharmacist_patient_history(
    patient_id: int,
    current_user: CurrentUser,
    request: Request,
    pharmacy_id: int = Query(..., gt=0),
    purpose: Literal[
        "dispensing_review", "medication_reconciliation", "patient_request"
    ] = Query(...),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return a minimal purchase history after explicit tenant authorization.

    A superuser is not implicitly granted global PHI access by this route:
    an active pharmacy membership is required for every principal.
    """
    membership = await db.scalar(
        select(PharmacyMembership.id).where(
            PharmacyMembership.user_id == current_user.id,
            PharmacyMembership.pharmacy_id == pharmacy_id,
            PharmacyMembership.is_active.is_(True),
        )
    )
    if membership is None:
        db.add(
            PHIAccessAudit(
                actor_id=current_user.id,
                pharmacy_id=pharmacy_id,
                patient_id=patient_id,
                action="read_patient_history",
                decision="denied",
                purpose=purpose,
                request_id=request.headers.get("x-request-id"),
            )
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active pharmacy membership is required",
        )

    patient_exists = await db.scalar(
        select(Patient.id).where(
            Patient.id == patient_id,
            Patient.pharmacy_id == pharmacy_id,
            Patient.is_active.is_(True),
        )
    )
    if patient_exists is None:
        db.add(
            PHIAccessAudit(
                actor_id=current_user.id,
                pharmacy_id=pharmacy_id,
                patient_id=patient_id,
                action="read_patient_history",
                decision="denied",
                purpose=purpose,
                request_id=request.headers.get("x-request-id"),
            )
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    result = await db.execute(
        select(PatientPurchase)
        .join(Patient, Patient.id == PatientPurchase.patient_id)
        .where(
            Patient.id == patient_id,
            Patient.pharmacy_id == pharmacy_id,
            Patient.is_active.is_(True),
        )
        .options(selectinload(PatientPurchase.product))
        .order_by(PatientPurchase.purchased_at.desc(), PatientPurchase.id.desc())
        .limit(100)
    )
    purchases = result.scalars().all()
    db.add(
        PHIAccessAudit(
            actor_id=current_user.id,
            pharmacy_id=pharmacy_id,
            patient_id=patient_id,
            action="read_patient_history",
            decision="allowed",
            purpose=purpose,
            request_id=request.headers.get("x-request-id"),
        )
    )
    return [
        {
            "id": purchase.id,
            "product_name": purchase.product_name,
            "category": purchase.category,
            "quantity": purchase.quantity,
            "purchased_at": purchase.purchased_at,
        }
        for purchase in purchases
    ]
