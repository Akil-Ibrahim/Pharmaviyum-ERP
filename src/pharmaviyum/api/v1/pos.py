import hashlib
import json
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from src.pharmaviyum.models.audit_log import AuditLog
from src.pharmaviyum.services.fefo import allocate_fefo
from src.pharmaviyum.services.pos_state import confirm_payment
from src.pharmaviyum.services.expired_inventory import (
    list_expired_inventory,
    quarantine_expired_inventory,
)
from src.pharmaviyum.models.dispensing import Dispensing
from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.inventory_transaction import InventoryTransaction
from src.pharmaviyum.models.order import Order
from src.pharmaviyum.models.order_item import OrderItem
from src.pharmaviyum.models.patients.patient import Patient
from src.pharmaviyum.models.patients.patient_purchase import PatientPurchase
from src.pharmaviyum.models.prescription import Prescription
from src.pharmaviyum.models.product import Product
from src.pharmaviyum.models.product_batch import ProductBatch
from src.pharmaviyum.modules.auth.deps import CurrentUser, SessionDep
from src.pharmaviyum.modules.auth.tenant import require_pharmacy_tenant
from src.pharmaviyum.schemas.pos_schema import (
    POSTransactionCreate,
    POSTransactionResponse,
)

router = APIRouter(prefix="/pos", tags=["POS"])


def _pos_request_hash(data: POSTransactionCreate) -> str:
    payload = json.dumps(
        data.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def _idempotent_pos_response(
    db,
    order: Order,
    request_hash: str,
) -> POSTransactionResponse:
    if order.idempotency_request_hash != request_hash:
        raise HTTPException(
            status_code=409,
            detail="Idempotency key was already used with a different transaction payload",
        )
    if order.status != "completed":
        raise HTTPException(
            status_code=409,
            detail="Idempotency key is associated with an incomplete POS transaction",
        )
    item_count = await db.scalar(
        select(func.count(OrderItem.id)).where(OrderItem.order_id == order.id)
    )
    return POSTransactionResponse(
        order_id=order.id,
        receipt_number=order.receipt_number or "",
        status=order.status,
        payment_method=order.payment_method or "",
        payment_status=order.payment_status,
        total_amount=float(order.total_amount),
        item_count=int(item_count or 0),
        inventory_updated=True,
        patient_history_updated=True,
        audit_created=True,
    )


@router.get("/products/search")
async def search_pos_products(
    db: SessionDep,
    _: CurrentUser,
    q: str = Query(min_length=1, max_length=100),
    pharmacy_id: int = Query(gt=0),
    limit: int = Query(default=20, ge=1, le=50),
) -> list[dict[str, object]]:
    """Search the pharmacy product catalog by name, INN, SKU, GTIN or barcode."""
    await require_pharmacy_tenant(pharmacy_id, _, db)
    term = f"%{q.strip()}%"
    result = await db.execute(
        select(Product)
        .where(
            Product.is_active.is_(True),
            or_(
                Product.name.ilike(term),
                Product.inn_name.ilike(term),
                Product.sku.ilike(term),
                Product.gtin.ilike(term),
                Product.barcode.ilike(term),
            ),
        )
        .order_by(Product.name)
        .limit(limit)
    )
    return [
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "inn_name": p.inn_name,
            "gtin": p.gtin,
            "barcode": p.barcode,
            "price": p.price,
            "units_per_pack": p.units_per_pack,
            "blisters_per_pack": p.blisters_per_pack,
            "units_per_blister": p.units_per_blister,
            "halal_status": p.halal_status,
        }
        for p in result.scalars().all()
    ]


@router.post("/inventory/expire")
async def quarantine_expired_pos_inventory(
    db: SessionDep,
    current_user: CurrentUser,
    pharmacy_id: int = Query(gt=0),
) -> dict[str, int | str]:
    """Remove expired stock from usable inventory and record it separately."""
    tenant = await require_pharmacy_tenant(pharmacy_id, current_user, db)
    count = await quarantine_expired_inventory(
        db, pharmacy_id=tenant.pharmacy_id, actor_id=current_user.id
    )
    await db.commit()
    return {
        "status": "ok",
        "quarantined_inventory_rows": count,
    }


@router.get("/inventory/expired")
async def get_expired_pos_inventory(
    db: SessionDep,
    current_user: CurrentUser,
    pharmacy_id: int = Query(gt=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, object]]:
    """List stock that has been removed from usable inventory because it expired."""
    tenant = await require_pharmacy_tenant(pharmacy_id, current_user, db)
    return await list_expired_inventory(db, pharmacy_id=tenant.pharmacy_id, limit=limit)


@router.post("/transactions", response_model=POSTransactionResponse, status_code=201)
async def confirm_pos_transaction(
    data: POSTransactionCreate,
    db: SessionDep,
    current_user: CurrentUser,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> POSTransactionResponse:
    """Atomically confirm a pharmacist POS sale/dispensing transaction."""
    if idempotency_key is not None:
        idempotency_key = idempotency_key.strip()
        if not idempotency_key or len(idempotency_key) > 255:
            raise HTTPException(
                status_code=400,
                detail="Idempotency-Key must contain 1-255 non-whitespace characters",
            )

    tenant = await require_pharmacy_tenant(data.pharmacy_id, current_user, db)
    request_hash = _pos_request_hash(data) if idempotency_key else None

    if idempotency_key is not None:
        existing_order = await db.scalar(
            select(Order).where(
                Order.pharmacy_id == tenant.pharmacy_id,
                Order.idempotency_key == idempotency_key,
            )
        )
        if existing_order is not None:
            return await _idempotent_pos_response(
                db, existing_order, request_hash or ""
            )

    # Expired stock is quarantined before any dispensing transaction is processed.
    await quarantine_expired_inventory(
        db, pharmacy_id=tenant.pharmacy_id, actor_id=current_user.id
    )

    patient = await db.scalar(
        select(Patient).where(
            Patient.id == data.patient_id,
            Patient.pharmacy_id == tenant.pharmacy_id,
            Patient.is_active.is_(True),
        )
    )
    if patient is None:
        raise HTTPException(
            status_code=404, detail="Patient not found in pharmacy tenant"
        )

    if not data.items:
        raise HTTPException(status_code=400, detail="At least one product is required")

    order = Order(
        patient_id=patient.id,
        pharmacy_id=tenant.pharmacy_id,
        pharmacist_id=current_user.id,
        status="pending",
        payment_method=data.payment_method,
        payment_status="unpaid",
        idempotency_key=idempotency_key,
        idempotency_request_hash=request_hash,
    )
    db.add(order)
    try:
        await db.flush()
    except IntegrityError:
        if idempotency_key is None:
            raise
        await db.rollback()
        existing_order = await db.scalar(
            select(Order).where(
                Order.pharmacy_id == tenant.pharmacy_id,
                Order.idempotency_key == idempotency_key,
            )
        )
        if existing_order is None:
            raise
        return await _idempotent_pos_response(
            db, existing_order, request_hash or ""
        )

    total = 0.0
    now = datetime.utcnow()
    purchase_entries: list[PatientPurchase] = []
    for item in data.items:
        product = await db.scalar(
            select(Product).where(
                Product.id == item.product_id, Product.is_active.is_(True)
            )
        )
        if product is None:
            raise HTTPException(
                status_code=404, detail=f"Product {item.product_id} not found"
            )

        quantity_units = (
            item.packs * product.units_per_pack
            + item.blisters * product.units_per_blister
            + item.units
        )
        if quantity_units <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"Quantity for product {product.id} must be greater than zero",
            )

        batch = None
        if item.batch_id is not None:
            batch = await db.scalar(
                select(ProductBatch).where(
                    ProductBatch.id == item.batch_id,
                    ProductBatch.product_id == product.id,
                )
            )
            if batch is None:
                raise HTTPException(status_code=404, detail="Product batch not found")
            if batch.expiry_date < now.date():
                raise HTTPException(
                    status_code=409, detail="Cannot dispense an expired batch"
                )

        # Allocate usable inventory deterministically by FEFO; one sale may
        # consume multiple batches when the earliest batch is insufficient.
        inventory_rows = (
            await db.execute(
                select(Inventory)
                .join(ProductBatch, ProductBatch.id == Inventory.batch_id, isouter=True)
                .where(
                    Inventory.product_id == product.id,
                    Inventory.pharmacy_id == tenant.pharmacy_id,
                    Inventory.quantity > 0,
                    (Inventory.expires_at.is_(None)) | (Inventory.expires_at >= now),
                )
                .order_by(
                    ProductBatch.expiry_date.asc().nulls_last(),
                    Inventory.expires_at.asc().nulls_last(),
                    Inventory.id.asc(),
                )
                .with_for_update()
            )
        ).scalars().all()

        if batch is not None:
            inventory_rows = [row for row in inventory_rows if row.batch_id == batch.id]

        allocations = allocate_fefo(
            [
                {
                    "id": row.batch_id or row.id,
                    "expiry_date": row.expires_at.date() if row.expires_at is not None else None,
                    "quantity": row.quantity,
                }
                for row in inventory_rows
            ],
            quantity_units,
            today=now.date(),
        )
        inventory_by_batch = {row.batch_id or row.id: row for row in inventory_rows}

        if item.prescription_id is not None:
            prescription = await db.scalar(
                select(Prescription).where(
                    Prescription.id == item.prescription_id,
                    Prescription.patient_id == patient.id,
                    Prescription.status == "active",
                )
            )
            if prescription is None:
                raise HTTPException(
                    status_code=409,
                    detail="Prescription is not active for this patient",
                )
            if (
                prescription.product_id is not None
                and prescription.product_id != product.id
            ):
                raise HTTPException(
                    status_code=409, detail="Prescription does not match product"
                )
            if prescription.expires_at is not None and prescription.expires_at < now:
                raise HTTPException(status_code=409, detail="Prescription has expired")

        unit_price = product.price if item.unit_price is None else item.unit_price
        line_total = round(unit_price * quantity_units, 2)
        total = round(total + line_total, 2)

        for allocation_index, allocation in enumerate(allocations):
            allocation_quantity = allocation["quantity"]
            inventory = inventory_by_batch[allocation["batch_id"]]
            allocation_batch = (
                await db.get(ProductBatch, inventory.batch_id)
                if inventory.batch_id is not None
                else None
            )

            allocation_line_total = round(unit_price * allocation_quantity, 2)
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                batch_id=allocation_batch.id if allocation_batch else None,
                quantity_units=allocation_quantity,
                dispensed_packs=item.packs if allocation_index == 0 else 0,
                dispensed_blisters=item.blisters if allocation_index == 0 else 0,
                dispensed_units=item.units if allocation_index == 0 else 0,
                unit_price=unit_price,
                line_total=allocation_line_total,
            )
            db.add(order_item)
            await db.flush()

            inventory.quantity -= allocation_quantity
            if allocation_batch is not None:
                allocation_batch.available_quantity = max(
                    allocation_batch.available_quantity - allocation_quantity, 0
                )

            dispensing = Dispensing(
                pharmacy_id=tenant.pharmacy_id,
                patient_id=patient.id,
                order_id=order.id,
                prescription_id=item.prescription_id,
                product_id=product.id,
                inventory_id=inventory.id,
                batch_id=allocation_batch.id if allocation_batch else None,
                quantity_units=allocation_quantity,
                pharmacist_id=current_user.id,
                status="completed",
                dispensed_at=now,
            )
            db.add(dispensing)
            await db.flush()

            db.add(
                InventoryTransaction(
                    pharmacy_id=tenant.pharmacy_id,
                    inventory_id=inventory.id,
                    product_id=product.id,
                    batch_id=allocation_batch.id if allocation_batch else None,
                    order_id=order.id,
                    dispensing_id=dispensing.id,
                    transaction_type="dispense",
                    quantity_delta=-allocation_quantity,
                    quantity_after=inventory.quantity,
                    actor_id=current_user.id,
                    created_at=now,
                )
            )
            purchase = PatientPurchase(
                patient_id=patient.id,
                batch_id=allocation_batch.id if allocation_batch else None,
                product_id=product.id,
                receipt_number="PENDING",
                category="pos",
                quantity=allocation_quantity,
                dispensed_packs=item.packs if allocation_index == 0 else 0,
                dispensed_blisters=item.blisters if allocation_index == 0 else 0,
                dispensed_units=item.units if allocation_index == 0 else 0,
                unit_price=unit_price,
                prescription_required=item.prescription_id is not None,
                purchased_at=now,
            )
            db.add(purchase)
            purchase_entries.append(purchase)

    receipt_number = f"PV-{now:%Y%m%d%H%M%S}-{uuid4().hex[:8].upper()}"
    order.total_amount = total
    order.receipt_number = receipt_number
    confirm_payment(order, now)
    order.confirmed_at = now
    patient.visit_count += 1
    patient.last_visit_date = now

    await db.flush()
    for purchase in purchase_entries:
        purchase.receipt_number = receipt_number

    db.add(
        AuditLog(
            actor_id=current_user.id,
            actor_type="user",
            action="dispense",
            entity="order",
            entity_id=order.id,
            changes={
                "pharmacy_id": tenant.pharmacy_id,
                "patient_id": patient.id,
                "total_amount": total,
                "payment_method": data.payment_method,
                "item_count": len(data.items),
            },
        )
    )
    await db.commit()

    return POSTransactionResponse(
        order_id=order.id,
        receipt_number=receipt_number,
        status=order.status,
        payment_method=data.payment_method,
        payment_status=order.payment_status,
        total_amount=total,
        item_count=len(data.items),
        inventory_updated=True,
        patient_history_updated=True,
        audit_created=True,
    )
