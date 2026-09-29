"""POS cash shift lifecycle endpoints."""
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import func, select

from src.pharmaviyum.models.cash_shift import CashShift
from src.pharmaviyum.models.cash_transaction import CashTransaction
from src.pharmaviyum.models.order import Order
from src.pharmaviyum.modules.auth.deps import CurrentUser, SessionDep
from src.pharmaviyum.modules.auth.tenant import require_pharmacy_tenant

router = APIRouter(prefix="/pos/shifts", tags=["POS Cash Shifts"])


class CashShiftOpen(BaseModel):
    pharmacy_id: int = Field(gt=0)
    opening_cash: float = Field(ge=0)


class CashShiftClose(BaseModel):
    closing_cash: float = Field(ge=0)
    reason: str | None = Field(default=None, max_length=500)


def _response(shift: CashShift) -> dict:
    return {
        "id": shift.id,
        "pharmacy_id": shift.pharmacy_id,
        "pharmacist_id": shift.pharmacist_id,
        "status": shift.status,
        "opening_cash": shift.opening_cash,
        "closing_cash": shift.closing_cash,
        "expected_cash": shift.expected_cash,
        "difference": shift.difference,
        "opened_at": shift.opened_at,
        "closed_at": shift.closed_at,
    }


@router.post("/open")
async def open_cash_shift(
    data: CashShiftOpen,
    db: SessionDep,
    current_user: CurrentUser,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> dict:
    await require_pharmacy_tenant(data.pharmacy_id, current_user, db)
    key = idempotency_key.strip()
    if not key:
        raise HTTPException(status_code=400, detail="Idempotency-Key is required")

    existing = await db.scalar(
        select(CashShift).where(
            CashShift.pharmacy_id == data.pharmacy_id,
            CashShift.open_idempotency_key == key,
        )
    )
    if existing:
        return _response(existing)

    active = await db.scalar(
        select(CashShift).where(
            CashShift.pharmacy_id == data.pharmacy_id,
            CashShift.status == "open",
        )
    )
    if active:
        raise HTTPException(status_code=409, detail="A cash shift is already open")

    shift = CashShift(
        pharmacy_id=data.pharmacy_id,
        pharmacist_id=current_user.id,
        opening_cash=data.opening_cash,
        status="open",
        opened_at=datetime.utcnow(),
        open_idempotency_key=key,
    )
    db.add(shift)
    await db.commit()
    await db.refresh(shift)
    return _response(shift)


@router.post("/{shift_id}/close")
async def close_cash_shift(
    shift_id: int,
    data: CashShiftClose,
    db: SessionDep,
    current_user: CurrentUser,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> dict:
    shift = await db.scalar(select(CashShift).where(CashShift.id == shift_id))
    if not shift:
        raise HTTPException(status_code=404, detail="Cash shift not found")
    await require_pharmacy_tenant(shift.pharmacy_id, current_user, db)
    key = idempotency_key.strip()
    if not key:
        raise HTTPException(status_code=400, detail="Idempotency-Key is required")

    if shift.status == "closed":
        if shift.close_idempotency_key == key:
            return _response(shift)
        raise HTTPException(status_code=409, detail="Cash shift is already closed")

    cash_net = await db.scalar(
        select(func.coalesce(func.sum(CashTransaction.amount), 0.0)).where(
            CashTransaction.cash_shift_id == shift.id,
            CashTransaction.payment_method == "cash",
        )
    )
    expected = round(float(shift.opening_cash) + float(cash_net or 0.0), 2)
    now = datetime.utcnow()
    shift.expected_cash = expected
    shift.closing_cash = data.closing_cash
    shift.difference = round(data.closing_cash - expected, 2)
    shift.closed_at = now
    shift.close_reason = data.reason
    shift.close_idempotency_key = key
    shift.status = "closed"
    await db.commit()
    await db.refresh(shift)
    return _response(shift)
