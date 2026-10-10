"""Point-of-sale catalog and atomic checkout endpoints."""

from datetime import date, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select

from src.pharmaviyum.models.audit_log import AuditLog
from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.inventory_transaction import InventoryTransaction
from src.pharmaviyum.models.order import Order
from src.pharmaviyum.models.patients.patient import Patient
from src.pharmaviyum.models.patients.patient_purchase import PatientPurchase
from src.pharmaviyum.models.pharmacy import Pharmacy
from src.pharmaviyum.models.prescription import Prescription
from src.pharmaviyum.models.product import Product
from src.pharmaviyum.models.product_batch import ProductBatch
from src.pharmaviyum.modules.auth.deps import CurrentUser, SessionDep
from src.pharmaviyum.modules.auth.tenant import resolve_pharmacy_scope

router = APIRouter(prefix="/api/v1/pos", tags=["Point of Sale"])


class CheckoutLine(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=500)


class CheckoutRequest(BaseModel):
    pharmacy_id: int = Field(gt=0)
    patient_id: int = Field(gt=0)
    payment_method: str = Field(pattern="^(cash|card|mobile|other)$")
    items: list[CheckoutLine] = Field(min_length=1, max_length=100)


@router.get("/catalog")
async def catalog(
    current_user: CurrentUser,
    session: SessionDep,
    pharmacy_id: int = Query(gt=0),
    q: str = Query(default="", max_length=120),
) -> list[dict]:
    """Return active catalog products with pharmacy-scoped sellable stock."""
    scope = await resolve_pharmacy_scope(pharmacy_id, current_user, session)
    if scope is None:
        scope = pharmacy_id

    query = select(Product).where(Product.is_active.is_(True))
    if q.strip():
        term = f"%{q.strip()}%"
        query = query.where(
            or_(
                Product.name.ilike(term),
                Product.sku.ilike(term),
                Product.barcode.ilike(term),
                Product.gtin.ilike(term),
                Product.inn_name.ilike(term),
                Product.dosage_strength.ilike(term),
                Product.dosage_form.ilike(term),
                Product.manufacturer.ilike(term),
            )
        )

    products = list(
        (
            await session.execute(
                query.order_by(Product.name, Product.id).limit(100)
            )
        )
        .scalars()
        .all()
    )
    rows: list[dict] = []
    for product in products:
        stock_rows = list(
            (
                await session.execute(
                    select(Inventory).where(
                        Inventory.product_id == product.id,
                        Inventory.pharmacy_id == scope,
                        Inventory.quantity > Inventory.reserved_quantity,
                    )
                )
            )
            .scalars()
            .all()
        )
        available = 0
        expiry_dates = []
        for stock in stock_rows:
            if stock.expires_at and stock.expires_at.date() < date.today():
                continue
            quantity = max(0, stock.quantity - stock.reserved_quantity)
            available += quantity
            if quantity and stock.expires_at:
                expiry_dates.append(stock.expires_at.date())

        rows.append(
            {
                "id": product.id,
                "name": product.name,
                "sku": product.sku,
                "barcode": product.barcode,
                "gtin": product.gtin,
                "inn_name": product.inn_name,
                "strength": product.dosage_strength,
                "form": product.dosage_form,
                "manufacturer": product.manufacturer,
                "units_per_pack": product.units_per_pack,
                "price": product.price,
                "prescription_required": product.prescription_required,
                "available_quantity": available,
                "earliest_expiry": (
                    min(expiry_dates).isoformat() if expiry_dates else None
                ),
            }
        )
    return rows


@router.post("/checkout", status_code=status.HTTP_201_CREATED)
async def checkout(
    data: CheckoutRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> dict:
    """Record a sale, FEFO stock deductions, patient purchases, and audit event atomically."""
    scope = await resolve_pharmacy_scope(data.pharmacy_id, current_user, session)
    if scope is None:
        scope = data.pharmacy_id

    pharmacy = await session.get(Pharmacy, scope)
    if pharmacy is None or not pharmacy.is_active:
        raise HTTPException(status_code=404, detail="Active pharmacy not found")

    patient = await session.scalar(
        select(Patient)
        .where(
            Patient.id == data.patient_id,
            Patient.is_active.is_(True),
            Patient.pharmacy_id == scope,
        )
        .with_for_update()
    )
    if patient is None:
        raise HTTPException(
            status_code=404, detail="Active patient not found in this pharmacy"
        )

    requested: dict[int, int] = {}
    for line in data.items:
        requested[line.product_id] = (
            requested.get(line.product_id, 0) + line.quantity
        )

    receipt_number = f"POS-{datetime.utcnow():%Y%m%d}-{uuid4().hex[:10].upper()}"
    allocations: list[dict] = []
    total = 0.0

    try:
        # Consistent lock ordering reduces deadlocks between overlapping carts.
        for product_id, requested_quantity in sorted(requested.items()):
            product = await session.scalar(
                select(Product)
                .where(
                    Product.id == product_id,
                    Product.is_active.is_(True),
                )
                .with_for_update()
            )
            if product is None:
                raise HTTPException(
                    status_code=404, detail=f"Product {product_id} not found"
                )

            if product.prescription_required:
                now = datetime.utcnow()
                prescription = await session.scalar(
                    select(Prescription)
                    .where(
                        Prescription.patient_id == patient.id,
                        Prescription.product_id == product.id,
                        Prescription.status == "active",
                        or_(
                            Prescription.expires_at.is_(None),
                            Prescription.expires_at >= now,
                        ),
                        or_(
                            Prescription.issued_at.is_(None),
                            Prescription.issued_at <= now,
                        ),
                    )
                    .limit(1)
                )
                if prescription is None:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "A valid active prescription is required for "
                            f"{product.name}."
                        ),
                    )

            stock_rows = list(
                (
                    await session.execute(
                        select(Inventory)
                        .where(
                            Inventory.product_id == product_id,
                            Inventory.pharmacy_id == scope,
                            Inventory.quantity > Inventory.reserved_quantity,
                        )
                        .order_by(
                            Inventory.expires_at.asc().nulls_last(),
                            Inventory.id.asc(),
                        )
                        .with_for_update()
                    )
                )
                .scalars()
                .all()
            )

            remaining = requested_quantity
            for stock in stock_rows:
                if remaining <= 0:
                    break
                if stock.expires_at and stock.expires_at.date() < date.today():
                    continue

                available = max(0, stock.quantity - stock.reserved_quantity)
                if not available:
                    continue

                batch = None
                if stock.lot_number:
                    batch = await session.scalar(
                        select(ProductBatch)
                        .where(
                            ProductBatch.product_id == product_id,
                            ProductBatch.batch_number == stock.lot_number,
                        )
                        .with_for_update()
                    )
                    if batch is None:
                        raise HTTPException(
                            status_code=409,
                            detail=(
                                f"Lot {stock.lot_number} has no matching batch "
                                "record; reconcile stock before selling."
                            ),
                        )
                    if batch.expiry_date < date.today():
                        continue
                    available = min(available, batch.available_quantity)

                quantity = min(remaining, available)
                if quantity <= 0:
                    continue

                stock.quantity -= quantity
                if batch is not None:
                    batch.available_quantity -= quantity

                line_total = round(float(product.price) * quantity, 2)
                allocations.append(
                    {
                        "product": product,
                        "batch": batch,
                        "inventory": stock,
                        "quantity": quantity,
                        "unit_price": float(product.price),
                        "line_total": line_total,
                    }
                )
                total += line_total
                remaining -= quantity

            if remaining:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Insufficient non-expired stock for {product.name}; "
                        f"{remaining} unit(s) unavailable."
                    ),
                )

        order = Order(
            patient_id=patient.id,
            total_amount=round(total, 2),
            status="completed",
            receipt_number=receipt_number,
            payment_method=data.payment_method,
        )
        session.add(order)
        await session.flush()

        receipt_lines = []
        for allocation in allocations:
            product, batch = allocation["product"], allocation["batch"]
            inventory = allocation["inventory"]
            quantity = allocation["quantity"]
            session.add(
                PatientPurchase(
                    patient_id=patient.id,
                    product_id=product.id,
                    batch_id=batch.id if batch else None,
                    receipt_number=receipt_number,
                    category="pos_sale",
                    quantity=quantity,
                    dispensed_packs=quantity,
                    dispensed_blisters=0,
                    dispensed_units=0,
                    unit_price=allocation["unit_price"],
                    prescription_required=product.prescription_required,
                    purchased_at=datetime.utcnow(),
                )
            )
            session.add(
                InventoryTransaction(
                    pharmacy_id=scope,
                    product_id=product.id,
                    inventory_id=inventory.id,
                    batch_id=batch.id if batch else None,
                    transaction_type="sale",
                    quantity_delta=-quantity,
                    reference_type="order",
                    reference_id=order.id,
                    receipt_number=receipt_number,
                    created_by=current_user.id,
                )
            )
            receipt_lines.append(
                {
                    "product_id": product.id,
                    "product_name": product.name,
                    "batch_number": batch.batch_number if batch else None,
                    "expiry_date": (
                        batch.expiry_date.isoformat() if batch else None
                    ),
                    "quantity": quantity,
                    "unit_price": allocation["unit_price"],
                    "line_total": allocation["line_total"],
                }
            )

        patient.visit_count += 1
        patient.last_visit_date = datetime.utcnow()
        session.add(
            AuditLog(
                actor_id=current_user.id,
                actor_type="user",
                action="pos.checkout",
                entity="order",
                entity_id=order.id,
                changes={
                    "receipt_number": receipt_number,
                    "pharmacy_id": scope,
                    "patient_id": patient.id,
                    "payment_method": data.payment_method,
                    "total_amount": round(total, 2),
                    "items": receipt_lines,
                },
            )
        )
        await session.commit()
        return {
            "order_id": order.id,
            "receipt_number": receipt_number,
            "status": order.status,
            "patient_id": patient.id,
            "patient_name": patient.full_name,
            "payment_method": data.payment_method,
            "total_amount": round(total, 2),
            "items": receipt_lines,
            "created_at": (
                order.created_at.isoformat()
                if order.created_at
                else datetime.utcnow().isoformat()
            ),
        }
    except HTTPException:
        await session.rollback()
        raise
    except Exception:
        await session.rollback()
        raise
