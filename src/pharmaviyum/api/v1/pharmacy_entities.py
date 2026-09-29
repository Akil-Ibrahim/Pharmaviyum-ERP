"""Authenticated API for the pharmacy domain entities."""

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.models.erp_sync import ERPIntegration, ERPSyncEvent
from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.pharmacy import Pharmacy
from src.pharmaviyum.models.prescription import Prescription
from src.pharmaviyum.models.product import Product
from src.pharmaviyum.models.product_batch import ProductBatch
from src.pharmaviyum.models.supplier import Supplier
from src.pharmaviyum.modules.auth.deps import CurrentSuperuser, CurrentUser, SessionDep
from src.pharmaviyum.modules.auth.models import PharmacyMembership

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
    product_id: int = Field(gt=0)
    pharmacy_id: int = Field(gt=0)
    quantity: int = Field(default=0, ge=0)
    reserved_quantity: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=0, ge=0)
    lot_number: str | None = Field(default=None, max_length=100)
    expires_at: datetime | None = None


class InventoryUpdate(BaseModel):
    quantity: int | None = Field(default=None, ge=0)
    reserved_quantity: int | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    lot_number: str | None = Field(default=None, max_length=100)
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


class EntityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BatchOut(EntityOut):
    id: int
    product_id: int
    batch_number: str
    expiry_date: date
    received_quantity: int
    available_quantity: int
    barcode: str | None
    days_to_expiry: int
    expiry_status: str


EXPIRY_HOT_DAYS = 7
EXPIRY_WARNING_DAYS = 30


def _batch_expiry_status(expiry_date: date, today: date | None = None) -> tuple[int, str]:
    current_date = today or date.today()
    days_to_expiry = (expiry_date - current_date).days
    if days_to_expiry <= EXPIRY_HOT_DAYS:
        return days_to_expiry, "red"
    if days_to_expiry <= EXPIRY_WARNING_DAYS:
        return days_to_expiry, "yellow"
    return days_to_expiry, "green"


async def _list(session: AsyncSession, model: type[Any]) -> list[Any]:
    result = await session.execute(select(model).order_by(model.id.desc()))
    return list(result.scalars().all())


async def _require_inventory_dependencies(
    session: AsyncSession, product_id: int, pharmacy_id: int
) -> None:
    product = await session.get(Product, product_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=404, detail="Active product not found")
    pharmacy = await session.get(Pharmacy, pharmacy_id)
    if pharmacy is None or not pharmacy.is_active:
        raise HTTPException(status_code=404, detail="Active pharmacy not found")


def _validate_inventory_levels(quantity: int, reserved_quantity: int) -> None:
    if reserved_quantity > quantity:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="reserved_quantity cannot exceed quantity",
        )


@router.get("/pharmacies", response_model=None)
async def list_pharmacies(
    current_user: CurrentUser, session: SessionDep
) -> list[Pharmacy]:
    if current_user.is_superuser:
        return await _list(session, Pharmacy)
    result = await session.execute(
        select(Pharmacy)
        .join(PharmacyMembership, PharmacyMembership.pharmacy_id == Pharmacy.id)
        .where(
            PharmacyMembership.user_id == current_user.id,
            PharmacyMembership.is_active.is_(True),
        )
        .order_by(Pharmacy.id.desc())
    )
    return list(result.scalars().unique().all())


@router.post("/pharmacies", response_model=None, status_code=status.HTTP_201_CREATED)
async def create_pharmacy(
    data: PharmacyIn, _: CurrentSuperuser, session: SessionDep
) -> Pharmacy:
    pharmacy = Pharmacy(**data.model_dump())
    session.add(pharmacy)
    await session.commit()
    await session.refresh(pharmacy)
    return pharmacy


@router.get("/suppliers", response_model=None)
async def list_suppliers(_: CurrentSuperuser, session: SessionDep) -> list[Supplier]:
    return await _list(session, Supplier)


@router.post("/suppliers", response_model=None, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    data: SupplierIn, _: CurrentSuperuser, session: SessionDep
) -> Supplier:
    supplier = Supplier(**data.model_dump())
    session.add(supplier)
    await session.commit()
    await session.refresh(supplier)
    return supplier


@router.get("/inventory", response_model=None)
async def list_inventory(
    current_user: CurrentUser,
    session: SessionDep,
    product_id: int | None = Query(default=None, gt=0),
    pharmacy_id: int | None = Query(default=None, gt=0),
    low_stock: bool = False,
) -> list[Inventory]:
    query = select(Inventory)
    if not current_user.is_superuser:
        authorized_pharmacies = select(PharmacyMembership.pharmacy_id).where(
            PharmacyMembership.user_id == current_user.id,
            PharmacyMembership.is_active.is_(True),
        )
        query = query.where(Inventory.pharmacy_id.in_(authorized_pharmacies))
    if product_id is not None:
        query = query.where(Inventory.product_id == product_id)
    if pharmacy_id is not None:
        query = query.where(Inventory.pharmacy_id == pharmacy_id)
    if low_stock:
        query = query.where(
            Inventory.quantity - Inventory.reserved_quantity <= Inventory.reorder_level
        )
    query = query.order_by(Inventory.id.desc())
    result = await session.execute(query)
    return list(result.scalars().all())


@router.post("/inventory", response_model=None, status_code=status.HTTP_201_CREATED)
async def create_inventory(
    data: InventoryIn, _: CurrentSuperuser, session: SessionDep
) -> Inventory:
    _validate_inventory_levels(data.quantity, data.reserved_quantity)
    await _require_inventory_dependencies(session, data.product_id, data.pharmacy_id)

    existing = await session.scalar(
        select(Inventory).where(
            Inventory.product_id == data.product_id,
            Inventory.pharmacy_id == data.pharmacy_id,
            Inventory.lot_number == data.lot_number,
        )
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="Inventory lot already exists")

    inventory = Inventory(**data.model_dump())
    session.add(inventory)
    await session.commit()
    await session.refresh(inventory)
    return inventory


@router.patch("/inventory/{inventory_id}", response_model=None)
async def update_inventory(
    inventory_id: int,
    data: InventoryUpdate,
    _: CurrentSuperuser,
    session: SessionDep,
) -> Inventory:
    inventory = await session.get(Inventory, inventory_id)
    if inventory is None:
        raise HTTPException(status_code=404, detail="Inventory record not found")

    values = data.model_dump(exclude_unset=True)
    quantity = values.get("quantity", inventory.quantity)
    reserved_quantity = values.get("reserved_quantity", inventory.reserved_quantity)
    _validate_inventory_levels(quantity, reserved_quantity)

    if "lot_number" in values and values["lot_number"] != inventory.lot_number:
        duplicate = await session.scalar(
            select(Inventory).where(
                Inventory.product_id == inventory.product_id,
                Inventory.pharmacy_id == inventory.pharmacy_id,
                Inventory.lot_number == values["lot_number"],
                Inventory.id != inventory.id,
            )
        )
        if duplicate is not None:
            raise HTTPException(status_code=409, detail="Inventory lot already exists")

    for key, value in values.items():
        setattr(inventory, key, value)
    await session.commit()
    await session.refresh(inventory)
    return inventory


@router.delete("/inventory/{inventory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory(
    inventory_id: int, _: CurrentSuperuser, session: SessionDep
) -> None:
    inventory = await session.get(Inventory, inventory_id)
    if inventory is None:
        raise HTTPException(status_code=404, detail="Inventory record not found")
    await session.delete(inventory)
    await session.commit()


@router.get("/batches", response_model=None)
async def list_batches(
    _: CurrentSuperuser,
    session: SessionDep,
    product_id: int | None = Query(default=None, gt=0),
    expiry_status: str | None = Query(default=None, pattern="^(red|yellow|green)$"),
) -> list[BatchOut]:
    # ProductBatch currently has no pharmacy_id. Keep operational batch quantities
    # fail-closed until batch ownership is modeled explicitly.
    query = select(ProductBatch)
    if product_id is not None:
        query = query.where(ProductBatch.product_id == product_id)
    result = await session.execute(query.order_by(ProductBatch.id.desc()))
    batches = list(result.scalars().all())

    response: list[BatchOut] = []
    for batch in batches:
        days_to_expiry, status = _batch_expiry_status(batch.expiry_date)
        if expiry_status is not None and status != expiry_status:
            continue
        response.append(
            BatchOut(
                id=batch.id,
                product_id=batch.product_id,
                batch_number=batch.batch_number,
                expiry_date=batch.expiry_date,
                received_quantity=batch.received_quantity,
                available_quantity=batch.available_quantity,
                barcode=batch.barcode,
                days_to_expiry=days_to_expiry,
                expiry_status=status,
            )
        )
    return response


@router.get("/prescriptions", response_model=None)
async def list_prescriptions(
    _: CurrentSuperuser, session: SessionDep
) -> list[Prescription]:
    """List prescriptions; medical records are restricted to privileged operators."""
    return await _list(session, Prescription)


@router.post("/prescriptions", response_model=None, status_code=status.HTTP_201_CREATED)
async def create_prescription(
    data: PrescriptionIn, _: CurrentSuperuser, session: SessionDep
) -> Prescription:
    prescription = Prescription(**data.model_dump())
    session.add(prescription)
    await session.commit()
    await session.refresh(prescription)
    return prescription


@router.get("/erp/integrations", response_model=None)
async def list_erp_integrations(
    _: CurrentSuperuser, session: SessionDep
) -> list[ERPIntegration]:
    return await _list(session, ERPIntegration)


@router.post(
    "/erp/integrations", response_model=None, status_code=status.HTTP_201_CREATED
)
async def create_erp_integration(
    data: ERPIntegrationIn, _: CurrentSuperuser, session: SessionDep
) -> ERPIntegration:
    integration = ERPIntegration(**data.model_dump())
    session.add(integration)
    await session.commit()
    await session.refresh(integration)
    return integration


@router.post(
    "/erp/integrations/{integration_id}/events", status_code=status.HTTP_202_ACCEPTED
)
async def ingest_erp_event(
    integration_id: int,
    data: ERPEventIn,
    _: CurrentSuperuser,
    session: SessionDep,
) -> dict[str, str]:
    integration = await session.get(ERPIntegration, integration_id)
    if integration is None or not integration.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ERP integration not found"
        )

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


@router.get("/sync-events", response_model=None)
async def list_sync_events(
    _: CurrentSuperuser,
    session: SessionDep,
    integration_id: int | None = Query(default=None, gt=0),
) -> list[ERPSyncEvent]:
    query = select(ERPSyncEvent)
    if integration_id is not None:
        query = query.where(ERPSyncEvent.integration_id == integration_id)
    result = await session.execute(query.order_by(ERPSyncEvent.id.desc()).limit(100))
    return list(result.scalars().all())


@router.get("/erp/integrations/{integration_id}/events", response_model=None)
async def list_erp_events(
    integration_id: int, _: CurrentSuperuser, session: SessionDep
) -> list[ERPSyncEvent]:
    result = await session.execute(
        select(ERPSyncEvent)
        .where(ERPSyncEvent.integration_id == integration_id)
        .order_by(ERPSyncEvent.id.desc())
        .limit(100)
    )
    return list(result.scalars().all())
