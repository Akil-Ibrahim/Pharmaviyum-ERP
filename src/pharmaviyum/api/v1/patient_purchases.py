"""Patient purchase history endpoints with distinct admin and pharmacist policies."""

from datetime import datetime, timedelta
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


def _request_id(request: Request) -> str | None:
    """Keep correlation metadata bounded; it is never used as an auth input."""
    value = request.headers.get("x-request-id")
    return value[:128] if value else None


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
    skip: int = Query(0, ge=0, le=10000),
    limit: int = Query(50, ge=1, le=100),
    purchased_from: datetime | None = Query(None),
    purchased_to: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return a minimum-field purchase history after explicit tenant authorization.

    This route is for non-superuser pharmacist principals only. Platform support
    access must use a separate governed workflow. Only the legacy PatientPurchase
    ledger is returned; POS Sale history is not represented until P0.2 links it.
    """
    if current_user.is_superuser:
        db.add(
            PHIAccessAudit(
                actor_id=current_user.id, pharmacy_id=pharmacy_id,
                patient_id=patient_id, action="read_patient_history",
                decision="denied", purpose=purpose, request_id=_request_id(request),
            )
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform support access requires a separately governed workflow",
        )

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
                actor_id=current_user.id, pharmacy_id=pharmacy_id,
                patient_id=patient_id, action="read_patient_history",
                decision="denied", purpose=purpose, request_id=_request_id(request),
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
                actor_id=current_user.id, pharmacy_id=pharmacy_id,
                patient_id=patient_id, action="read_patient_history",
                decision="denied", purpose=purpose, request_id=_request_id(request),
            )
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found"
        )

    if (purchased_from is None) != (purchased_to is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Both purchased_from and purchased_to are required together",
        )
    if purchased_from is not None and purchased_to is not None:
        if purchased_from > purchased_to:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="purchased_from must not exceed purchased_to",
            )
        if purchased_to - purchased_from > timedelta(days=365):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Date range must not exceed 365 days",
            )

    purchase_query = (
        select(PatientPurchase)
        .join(Patient, Patient.id == PatientPurchase.patient_id)
        .where(
            Patient.id == patient_id,
            Patient.pharmacy_id == pharmacy_id,
            Patient.is_active.is_(True),
        )
        .options(selectinload(PatientPurchase.product))
    )
    if purchased_from is not None and purchased_to is not None:
        purchase_query = purchase_query.where(
            PatientPurchase.purchased_at >= purchased_from,
            PatientPurchase.purchased_at <= purchased_to,
        )
    result = await db.execute(
        purchase_query.order_by(
            PatientPurchase.purchased_at.desc(), PatientPurchase.id.desc()
        ).offset(skip).limit(limit)
    )
    purchases = result.scalars().all()
    db.add(
        PHIAccessAudit(
            actor_id=current_user.id, pharmacy_id=pharmacy_id,
            patient_id=patient_id, action="read_patient_history",
            decision="allowed", purpose=purpose, request_id=_request_id(request),
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