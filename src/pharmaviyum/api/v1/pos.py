import hashlib
import json
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from src.pharmaviyum.models.audit_log import AuditLog
from src.pharmaviyum.models.cash_shift import CashShift
from src.pharmaviyum.models.cash_transaction import CashTransaction
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
from src.pharmaviyum.models.pos_return import POSReturn, POSReturnItem
from src.pharmaviyum.modules.auth.deps import CurrentUser, SessionDep
from src.pharmaviyum.modules.auth.tenant import require_pharmacy_tenant
from src.pharmaviyum.schemas.pos_schema import (
    POSTransactionCreate,
    POSTransactionResponse,
    POSReturnCreate,
    POSReturnResponse,
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

    active_shift = await db.scalar(
        select(CashShift).where(
            CashShift.pharmacy_id == tenant.pharmacy_id,
            CashShift.status == "open",
        )
    )

    order = Order(
        patient_id=patient.id,
        pharmacy_id=tenant.pharmacy_id,
        pharmacist_id=current_user.id,
        cash_shift_id=active_shift.id if active_shift is not None else None,
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

        batch_ids = [row.batch_id for row in inventory_rows if row.batch_id is not None]
        batch_expiry_rows = (
            await db.execute(
                select(ProductBatch.id, ProductBatch.expiry_date).where(
                    ProductBatch.id.in_(batch_ids)
                )
            )
        ).all()
        batch_expiry_by_id = {int(row[0]): row[1] for row in batch_expiry_rows}

        allocations = allocate_fefo(
            [
                {
                    "id": row.batch_id or row.id,
                    "expiry_date": (
                        batch_expiry_by_id.get(row.batch_id)
                        if row.batch_id is not None
                        else row.expires_at.date() if row.expires_at is not None else None
                    ),
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
    if active_shift is not None:
        db.add(
            CashTransaction(
                cash_shift_id=active_shift.id,
                pharmacy_id=tenant.pharmacy_id,
                order_id=order.id,
                actor_id=current_user.id,
                transaction_type="sale",
                payment_method=order.payment_method or "unknown",
                amount=float(order.total_amount),
                idempotency_key=f"sale:{order.id}",
                created_at=now,
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



@router.post("/transactions/{order_id}/void", response_model=POSTransactionResponse)
async def void_pos_transaction(
    order_id: int,
    db: SessionDep,
    current_user: CurrentUser,
    reason: str = Query(min_length=3, max_length=500),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=255),
) -> POSTransactionResponse:
    """Void a completed POS sale and restore every dispensed batch exactly once."""
    idempotency_key = idempotency_key.strip()
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key is required")

    order = await db.scalar(select(Order).where(Order.id == order_id))
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    await require_pharmacy_tenant(order.pharmacy_id, current_user, db)

    existing_void = await db.scalar(
        select(Order).where(
            Order.pharmacy_id == order.pharmacy_id,
            Order.void_idempotency_key == idempotency_key,
        )
    )
    if existing_void is not None:
        if existing_void.id != order.id:
            raise HTTPException(
                status_code=409,
                detail="Idempotency key was already used for another void",
            )
        return POSTransactionResponse(
            order_id=order.id,
            receipt_number=order.receipt_number or "",
            status=order.status,
            payment_method=order.payment_method or "",
            payment_status=order.payment_status,
            total_amount=float(order.total_amount),
            item_count=await db.scalar(
                select(func.count(OrderItem.id)).where(OrderItem.order_id == order.id)
            )
            or 0,
            inventory_updated=True,
            patient_history_updated=True,
            audit_created=True,
        )

    if order.status != "completed" or order.payment_status != "paid":
        raise HTTPException(
            status_code=409,
            detail="Only a completed paid POS sale can be voided",
        )
    if order.voided_at is not None:
        raise HTTPException(status_code=409, detail="POS sale is already voided")

    now = datetime.utcnow()
    dispense_transactions = (
        await db.execute(
            select(InventoryTransaction)
            .where(
                InventoryTransaction.order_id == order.id,
                InventoryTransaction.transaction_type == "dispense",
            )
            .with_for_update()
        )
    ).scalars().all()
    if not dispense_transactions:
        raise HTTPException(
            status_code=409,
            detail="POS sale has no inventory dispense records to reverse",
        )

    receipt_number = f"{order.receipt_number or order.id}-VOID"
    for transaction in dispense_transactions:
        inventory = await db.get(Inventory, transaction.inventory_id, with_for_update=True)
        if inventory is None:
            raise HTTPException(status_code=409, detail="Inventory record no longer exists")
        batch = (
            await db.get(ProductBatch, transaction.batch_id, with_for_update=True)
            if transaction.batch_id is not None
            else None
        )
        inventory.quantity += -transaction.quantity_delta
        if batch is not None:
            batch.available_quantity += -transaction.quantity_delta

        db.add(
            InventoryTransaction(
                pharmacy_id=order.pharmacy_id,
                inventory_id=inventory.id,
                product_id=transaction.product_id,
                batch_id=transaction.batch_id,
                order_id=order.id,
                dispensing_id=transaction.dispensing_id,
                transaction_type="return",
                quantity_delta=-transaction.quantity_delta,
                quantity_after=inventory.quantity,
                actor_id=current_user.id,
                created_at=now,
            )
        )

        if transaction.dispensing_id is not None:
            dispensing = await db.get(Dispensing, transaction.dispensing_id)
            if dispensing is not None:
                dispensing.status = "voided"

        purchase = await db.scalar(
            select(PatientPurchase).where(
                PatientPurchase.receipt_number == order.receipt_number,
                PatientPurchase.patient_id == order.patient_id,
                PatientPurchase.batch_id == transaction.batch_id,
                PatientPurchase.product_id == transaction.product_id,
            )
        )
        if purchase is not None:
            db.add(
                PatientPurchase(
                    patient_id=order.patient_id,
                    batch_id=transaction.batch_id,
                    product_id=transaction.product_id,
                    receipt_number=receipt_number,
                    category="pos_void",
                    quantity=-abs(purchase.quantity),
                    dispensed_packs=-abs(purchase.dispensed_packs),
                    dispensed_blisters=-abs(purchase.dispensed_blisters),
                    dispensed_units=-abs(purchase.dispensed_units),
                    unit_price=purchase.unit_price,
                    prescription_required=purchase.prescription_required,
                    purchased_at=now,
                )
            )

    shift = await db.scalar(select(CashShift).where(CashShift.id == order.cash_shift_id)) if order.cash_shift_id else None
    if shift is not None:
        db.add(
            CashTransaction(
                cash_shift_id=shift.id,
                pharmacy_id=order.pharmacy_id,
                order_id=order.id,
                actor_id=current_user.id,
                transaction_type="refund",
                payment_method=order.payment_method or "unknown",
                amount=-float(order.total_amount),
                idempotency_key=f"void:{order.id}",
                created_at=now,
            )
        )

    order.status = "voided"
    order.payment_status = "refunded"
    order.void_idempotency_key = idempotency_key
    order.voided_at = now
    order.void_reason = reason
    await db.flush()

    db.add(
        AuditLog(
            actor_id=current_user.id,
            actor_type="user",
            action="void",
            entity="order",
            entity_id=order.id,
            changes={
                "pharmacy_id": order.pharmacy_id,
                "reason": reason,
                "restored_transactions": len(dispense_transactions),
                "original_receipt": order.receipt_number,
            },
        )
    )
    await db.commit()

    return POSTransactionResponse(
        order_id=order.id,
        receipt_number=order.receipt_number or "",
        status=order.status,
        payment_method=order.payment_method or "",
        payment_status=order.payment_status,
        total_amount=float(order.total_amount),
        item_count=len(dispense_transactions),
        inventory_updated=True,
        patient_history_updated=True,
        audit_created=True,
    )


@router.post(
    "/transactions/{order_id}/return",
    response_model=POSReturnResponse,
    status_code=201,
)
async def return_pos_transaction(
    order_id: int,
    data: POSReturnCreate,
    db: SessionDep,
    current_user: CurrentUser,
    idempotency_key: str = Header(
        ..., alias="Idempotency-Key", min_length=1, max_length=255
    ),
) -> POSReturnResponse:
    """Partially return sold units without mutating the original completed sale."""
    idempotency_key = idempotency_key.strip()
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key is required")

    request_hash = hashlib.sha256(
        json.dumps(
            data.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    order = await db.scalar(select(Order).where(Order.id == order_id))
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    tenant = await require_pharmacy_tenant(order.pharmacy_id, current_user, db)

    existing_return = await db.scalar(
        select(POSReturn).where(
            POSReturn.pharmacy_id == tenant.pharmacy_id,
            POSReturn.idempotency_key == idempotency_key,
        )
    )
    if existing_return is not None:
        if existing_return.request_hash != request_hash:
            raise HTTPException(
                status_code=409,
                detail="Idempotency key was already used with a different return payload",
            )
        return POSReturnResponse(
            return_id=existing_return.id,
            order_id=existing_return.order_id,
            status=existing_return.status,
            refund_method=existing_return.refund_method,
            total_amount=float(existing_return.total_amount),
            item_count=int(await db.scalar(select(func.count(POSReturnItem.id)).where(POSReturnItem.return_id == existing_return.id)) or 0),
        )

    if order.status != "completed" or order.payment_status != "paid":
        raise HTTPException(
            status_code=409,
            detail="Only a completed paid POS sale can be partially returned",
        )

    if data.refund_method != order.payment_method:
        raise HTTPException(
            status_code=409,
            detail="Refund method must match the original payment method",
        )

    requested_item_ids = [item.order_item_id for item in data.items]
    if len(requested_item_ids) != len(set(requested_item_ids)):
        raise HTTPException(status_code=400, detail="Each order item may appear only once")

    order_items = (
        await db.execute(
            select(OrderItem)
            .where(
                OrderItem.order_id == order.id,
                OrderItem.id.in_(requested_item_ids),
            )
            .with_for_update()
        )
    ).scalars().all()
    order_items_by_id = {item.id: item for item in order_items}
    if len(order_items_by_id) != len(requested_item_ids):
        raise HTTPException(status_code=404, detail="One or more order items were not found")

    returned_rows = (
        await db.execute(
            select(
                POSReturnItem.order_item_id,
                func.coalesce(func.sum(POSReturnItem.quantity_units), 0),
            )
            .join(POSReturn, POSReturn.id == POSReturnItem.return_id)
            .where(
                POSReturn.order_id == order.id,
                POSReturn.status == "completed",
                POSReturnItem.order_item_id.in_(requested_item_ids),
            )
            .group_by(POSReturnItem.order_item_id)
        )
    ).all()
    returned_by_item = {int(row[0]): int(row[1]) for row in returned_rows}

    for requested in data.items:
        order_item = order_items_by_id[requested.order_item_id]
        already_returned = returned_by_item.get(order_item.id, 0)
        remaining = order_item.quantity_units - already_returned
        if requested.quantity_units > remaining:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Return quantity for order item {order_item.id} exceeds "
                    f"remaining quantity ({remaining})"
                ),
            )

    now = datetime.utcnow()
    active_shift = None
    if order.cash_shift_id is not None:
        active_shift = await db.scalar(
            select(CashShift).where(CashShift.id == order.cash_shift_id)
        )

    return_record = POSReturn(
        pharmacy_id=tenant.pharmacy_id,
        order_id=order.id,
        patient_id=order.patient_id,
        cash_shift_id=order.cash_shift_id,
        actor_id=current_user.id,
        status="completed",
        reason=data.reason,
        refund_method=data.refund_method,
        total_amount=0.0,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        created_at=now,
        completed_at=now,
    )
    db.add(return_record)
    await db.flush()

    total_refund = 0.0
    for requested in data.items:
        order_item = order_items_by_id[requested.order_item_id]
        inventory = await db.scalar(
            select(Inventory)
            .where(
                Inventory.pharmacy_id == tenant.pharmacy_id,
                Inventory.product_id == order_item.product_id,
                Inventory.batch_id == order_item.batch_id,
            )
            .with_for_update()
        )
        if inventory is None:
            raise HTTPException(
                status_code=409,
                detail=f"Inventory record for returned order item {order_item.id} no longer exists",
            )

        batch = (
            await db.get(ProductBatch, order_item.batch_id, with_for_update=True)
            if order_item.batch_id is not None
            else None
        )
        inventory.quantity += requested.quantity_units
        if batch is not None:
            batch.available_quantity += requested.quantity_units

        amount = round(order_item.unit_price * requested.quantity_units, 2)
        total_refund = round(total_refund + amount, 2)
        db.add(
            POSReturnItem(
                return_id=return_record.id,
                order_item_id=order_item.id,
                product_id=order_item.product_id,
                batch_id=order_item.batch_id,
                quantity_units=requested.quantity_units,
                unit_price=order_item.unit_price,
                amount=amount,
            )
        )
        db.add(
            InventoryTransaction(
                pharmacy_id=tenant.pharmacy_id,
                inventory_id=inventory.id,
                product_id=order_item.product_id,
                batch_id=order_item.batch_id,
                order_id=order.id,
                transaction_type="return",
                quantity_delta=requested.quantity_units,
                quantity_after=inventory.quantity,
                actor_id=current_user.id,
                created_at=now,
            )
        )
        db.add(
            PatientPurchase(
                patient_id=order.patient_id,
                batch_id=order_item.batch_id,
                product_id=order_item.product_id,
                receipt_number=f"{order.receipt_number or order.id}-RET-{return_record.id}",
                category="pos_return",
                quantity=-requested.quantity_units,
                dispensed_packs=0,
                dispensed_blisters=0,
                dispensed_units=-requested.quantity_units,
                unit_price=order_item.unit_price,
                prescription_required=False,
                purchased_at=now,
            )
        )

    return_record.total_amount = total_refund
    if active_shift is not None:
        db.add(
            CashTransaction(
                cash_shift_id=active_shift.id,
                pharmacy_id=tenant.pharmacy_id,
                order_id=order.id,
                actor_id=current_user.id,
                transaction_type="refund",
                payment_method=data.refund_method,
                amount=-total_refund,
                idempotency_key=f"return:{return_record.id}",
                created_at=now,
            )
        )

    db.add(
        AuditLog(
            actor_id=current_user.id,
            actor_type="user",
            action="return",
            entity="order",
            entity_id=order.id,
            changes={
                "pharmacy_id": tenant.pharmacy_id,
                "return_id": return_record.id,
                "reason": data.reason,
                "total_refund": total_refund,
                "item_count": len(data.items),
            },
        )
    )

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        existing_return = await db.scalar(
            select(POSReturn).where(
                POSReturn.pharmacy_id == tenant.pharmacy_id,
                POSReturn.idempotency_key == idempotency_key,
            )
        )
        if existing_return is None:
            raise
        if existing_return.request_hash != request_hash:
            raise HTTPException(
                status_code=409,
                detail="Idempotency key was already used with a different return payload",
            )
        return POSReturnResponse(
            return_id=existing_return.id,
            order_id=existing_return.order_id,
            status=existing_return.status,
            refund_method=existing_return.refund_method,
            total_amount=float(existing_return.total_amount),
            item_count=int(await db.scalar(select(func.count(POSReturnItem.id)).where(POSReturnItem.return_id == existing_return.id)) or 0),
        )

    return POSReturnResponse(
        return_id=return_record.id,
        order_id=order.id,
        status=return_record.status,
        refund_method=return_record.refund_method,
        total_amount=total_refund,
        item_count=len(data.items),
    )
