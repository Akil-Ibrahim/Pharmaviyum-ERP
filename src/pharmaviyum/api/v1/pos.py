# mypy: disable-error-code="assignment,arg-type,call-overload"
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import or_, select

from src.pharmaviyum.models.audit_log import AuditLog
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
from src.pharmaviyum.services.expired_inventory import (
    list_expired_inventory,
    quarantine_expired_inventory,
)

router = APIRouter(prefix="/pos", tags=["POS"])


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
) -> POSTransactionResponse:
    """Atomically confirm a pharmacist POS sale/dispensing transaction."""
    tenant = await require_pharmacy_tenant(data.pharmacy_id, current_user, db)

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
    )
    db.add(order)
    await db.flush()

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

        # FEFO: when the pharmacist does not explicitly choose a batch,
        # select the earliest-expiring usable batch automatically.
        inventory_query = (
            select(Inventory)
            .join(ProductBatch, ProductBatch.id == Inventory.batch_id, isouter=True)
            .where(
                Inventory.product_id == product.id,
                Inventory.pharmacy_id == tenant.pharmacy_id,
                Inventory.quantity >= quantity_units,
            )
        )
        if batch is not None:
            inventory_query = inventory_query.where(Inventory.batch_id == batch.id)
        else:
            inventory_query = inventory_query.where(
                (Inventory.expires_at.is_(None)) | (Inventory.expires_at >= now)
            ).order_by(
                ProductBatch.expiry_date.asc().nulls_last(),
                Inventory.expires_at.asc().nulls_last(),
                Inventory.id.asc(),
            )
        inventory = await db.scalar(inventory_query.with_for_update())
        if inventory is None:
            raise HTTPException(
                status_code=409, detail="Product is not stocked in this pharmacy"
            )
        if inventory.quantity < quantity_units:
            raise HTTPException(status_code=409, detail="Insufficient inventory")
        if inventory.expires_at is not None and inventory.expires_at < now:
            raise HTTPException(
                status_code=409, detail="Cannot dispense expired inventory"
            )

        # When FEFO selected the batch implicitly, keep that batch attached to
        # the order, dispensing record, patient history and stock ledger.
        if batch is None and inventory.batch_id is not None:
            batch = await db.get(ProductBatch, inventory.batch_id)
            if batch is None:
                raise HTTPException(
                    status_code=409, detail="Inventory batch no longer exists"
                )
            if batch.expiry_date < now.date():
                raise HTTPException(
                    status_code=409, detail="Cannot dispense an expired batch"
                )

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

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            batch_id=batch.id if batch else None,
            quantity_units=quantity_units,
            dispensed_packs=item.packs,
            dispensed_blisters=item.blisters,
            dispensed_units=item.units,
            unit_price=unit_price,
            line_total=line_total,
        )
        db.add(order_item)
        await db.flush()

        inventory.quantity -= quantity_units
        if batch is not None:
            batch.available_quantity = max(batch.available_quantity - quantity_units, 0)
        dispensing = Dispensing(
            pharmacy_id=tenant.pharmacy_id,
            patient_id=patient.id,
            order_id=order.id,
            prescription_id=item.prescription_id,
            product_id=product.id,
            inventory_id=inventory.id,
            batch_id=batch.id if batch else None,
            quantity_units=quantity_units,
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
                batch_id=batch.id if batch else None,
                order_id=order.id,
                dispensing_id=dispensing.id,
                transaction_type="dispense",
                quantity_delta=-quantity_units,
                quantity_after=inventory.quantity,
                actor_id=current_user.id,
                created_at=now,
            )
        )
        purchase = PatientPurchase(
            patient_id=patient.id,
            batch_id=batch.id if batch else None,
            product_id=product.id,
            receipt_number="PENDING",
            category="pos",
            quantity=quantity_units,
            dispensed_packs=item.packs,
            dispensed_blisters=item.blisters,
            dispensed_units=item.units,
            unit_price=unit_price,
            prescription_required=item.prescription_id is not None,
            purchased_at=now,
        )
        db.add(purchase)
        purchase_entries.append(purchase)

    receipt_number = f"PV-{now:%Y%m%d%H%M%S}-{uuid4().hex[:8].upper()}"
    order.total_amount = total
    order.receipt_number = receipt_number
    order.status = "completed"
    order.payment_status = "paid"
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
