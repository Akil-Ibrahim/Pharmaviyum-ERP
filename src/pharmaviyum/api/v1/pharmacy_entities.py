"""Authenticated API for the pharmacy domain entities."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.models.erp_sync import ERPIntegration, ERPSyncEvent
from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.mortarium_ai import MortariumAISession
from src.pharmaviyum.models.pharmacy import Pharmacy
from src.pharmaviyum.models.prescription import Prescription
from src.pharmaviyum.models.supplier import Supplier
from src.pharmaviyum.modules.auth.deps import CurrentSuperuser, CurrentUser, SessionDep

router = APIRouter(prefix="/api/v1", tags=["Pharmacy Domain"])


class PharmacyIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=64)
    address: str | None = None
    timezone: str = "UTC"


class SupplierIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=64)
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None


class InventoryIn(BaseModel):
    product_id: int
    pharmacy_id: int
    quantity: int = Field(default=0, ge=0)
    reserved_quantity: int = Field(default=0, ge=0)
    lot_number: str | None = None
    expires_at: datetime | None = None


class PrescriptionIn(BaseModel):
    patient_id: int
    product_id: int | None = None
    prescription_number: str = Field(min_length=1, max_length=100)
    dosage: str | None = None
    instructions: str | None = None
    status: str = Field(default="active", max_length=32)
    issued_at: datetime | None = None
    expires_at: datetime | None = None


class ERPIntegrationIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    provider: str = Field(min_length=1, max_length=100)
    endpoint: str = Field(min_length=1, max_length=500)
    sync_mode: str = Field(default="realtime", max_length=32)


class ERPEventIn(BaseModel):
    event_id: str = Field(min_length=1, max_length=128)
    entity_type: str = Field(min_length=1, max_length=64)
    entity_id: str | None = None
    direction: str = Field(default="inbound", max_length=16)


class MortariumSessionIn(BaseModel):
    session_key: str = Field(min_length=1, max_length=128)
    patient_id: int | None = None


class EntityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)


async def _list(session: AsyncSession, model: type[Any]) -> list[Any]:
    result = await session.execute(select(model).order_by(model.id.desc()))
    return list(result.scalars().all())


@router.get("/pharmacies")
async def list_pharmacies(_: CurrentUser, session: SessionDep) -> list[Pharmacy]:
    return await _list(session, Pharmacy)


@router.post("/pharmacies", status_code=status.HTTP_201_CREATED)
async def create_pharmacy(data: PharmacyIn, _: CurrentSuperuser, session: SessionDep) -> Pharmacy:
    pharmacy = Pharmacy(**data.model_dump())
    session.add(pharmacy)
    await session.commit()
    await session.refresh(pharmacy)
    return pharmacy


@router.get("/suppliers")
async def list_suppliers(_: CurrentUser, session: SessionDep) -> list[Supplier]:
    return await _list(session, Supplier)


@router.post("/suppliers", status_code=status.HTTP_201_CREATED)
async def create_supplier(data: SupplierIn, _: CurrentSuperuser, session: SessionDep) -> Supplier:
    supplier = Supplier(**data.model_dump())
    session.add(supplier)
    await session.commit()
    await session.refresh(supplier)
    return supplier


@router.get("/inventory")
async def list_inventory(_: CurrentUser, session: SessionDep) -> list[Inventory]:
    return await _list(session, Inventory)


@router.post("/inventory", status_code=status.HTTP_201_CREATED)
async def create_inventory(data: InventoryIn, _: CurrentSuperuser, session: SessionDep) -> Inventory:
    inventory = Inventory(**data.model_dump())
    session.add(inventory)
    await session.commit()
    await session.refresh(inventory)
    return inventory


@router.get("/prescriptions")
async def list_prescriptions(_: CurrentUser, session: SessionDep) -> list[Prescription]:
    return await _list(session, Prescription)


@router.post("/prescriptions", status_code=status.HTTP_201_CREATED)
async def create_prescription(
    data: PrescriptionIn, _: CurrentSuperuser, session: SessionDep
) -> Prescription:
    prescription = Prescription(**data.model_dump())
    session.add(prescription)
    await session.commit()
    await session.refresh(prescription)
    return prescription


@router.get("/erp/integrations")
async def list_erp_integrations(_: CurrentUser, session: SessionDep) -> list[ERPIntegration]:
    return await _list(session, ERPIntegration)


@router.post("/erp/integrations", status_code=status.HTTP_201_CREATED)
async def create_erp_integration(
    data: ERPIntegrationIn, _: CurrentSuperuser, session: SessionDep
) -> ERPIntegration:
    integration = ERPIntegration(**data.model_dump())
    session.add(integration)
    await session.commit()
    await session.refresh(integration)
    return integration


@router.post("/erp/integrations/{integration_id}/events", status_code=status.HTTP_202_ACCEPTED)
async def ingest_erp_event(
    integration_id: int,
    data: ERPEventIn,
    _: CurrentSuperuser,
    session: SessionDep,
) -> dict[str, str]:
    integration = await session.get(ERPIntegration, integration_id)
    if integration is None or not integration.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ERP integration not found")

    existing = await session.scalar(
        select(ERPSyncEvent).where(ERPSyncEvent.event_id == data.event_id)
    )
    if existing is not None:
        return {"status": "duplicate", "event_id": data.event_id}

    event = ERPSyncEvent(integration_id=integration_id, **data.model_dump())
    integration.last_event_at = datetime.utcnow()
    session.add(event)
    await session.commit()
    return {"status": "accepted", "event_id": data.event_id}


@router.get("/erp/integrations/{integration_id}/events")
async def list_erp_events(
    integration_id: int, _: CurrentUser, session: SessionDep
) -> list[ERPSyncEvent]:
    result = await session.execute(
        select(ERPSyncEvent)
        .where(ERPSyncEvent.integration_id == integration_id)
        .order_by(ERPSyncEvent.id.desc())
        .limit(100)
    )
    return list(result.scalars().all())


@router.get("/mortarium-ai/sessions")
async def list_mortarium_sessions(_: CurrentUser, session: SessionDep) -> list[MortariumAISession]:
    return await _list(session, MortariumAISession)


@router.post("/mortarium-ai/sessions", status_code=status.HTTP_201_CREATED)
async def create_mortarium_session(
    data: MortariumSessionIn,
    current_user: CurrentUser,
    session: SessionDep,
) -> MortariumAISession:
    ai_session = MortariumAISession(
        user_id=str(current_user.id),
        **data.model_dump(),
    )
    session.add(ai_session)
    await session.commit()
    await session.refresh(ai_session)
    return ai_session
