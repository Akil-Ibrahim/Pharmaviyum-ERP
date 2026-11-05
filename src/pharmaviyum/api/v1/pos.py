"""Pharmacy point-of-sale checkout and payment settlement endpoints."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.pos import Payment, Sale, SaleItem, SaleItemAllocation
from src.pharmaviyum.models.product import Product
from src.pharmaviyum.modules.auth.deps import CurrentUser, SessionDep
from src.pharmaviyum.modules.auth.tenant import require_pharmacy_tenant
from src.pharmaviyum.schemas.pos import (
    InventoryReceiptCreate,
    InventoryReceiptResponse,
    SaleCreate,
    SaleResponse,
)
from src.pharmaviyum.schemas.pos_product import POSProductResponse
from src.pharmaviyum.services.catalog_exclusions import (
    allowed_pharmacy_product_conditions,
)

router = APIRouter(prefix="/api/v1/pos", tags=["Point of Sale"])
CENT = Decimal("0.01")


def _money(value: Decimal | float | int) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


async def _load_sale(db: SessionDep, sale_id: int) -> Sale:
    result = await db.execute(
        select(Sale)
        .where(Sale.id == sale_id)
        .options(selectinload(Sale.items), selectinload(Sale.payments))
    )
    sale = result.scalar_one_or_none()
    if sale is None:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale


@router.get("/products/search", response_model=list[POSProductResponse])
async def search_pos_products(
    db: SessionDep,
    user: CurrentUser,
    q: str = Query(..., min_length=2, max_length=100),
    pharmacy_id: int = Query(..., gt=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[POSProductResponse]:
    """Search pharmacy sellable products with authoritative, non-expired tenant stock."""
    await require_pharmacy_tenant(pharmacy_id, user, db)
    term = f"%{q.strip()}%"
    now = datetime.utcnow()
    inventory_join = (
        (Inventory.product_id == Product.id)
        & (Inventory.pharmacy_id == pharmacy_id)
        & (Inventory.expires_at.is_(None) | (Inventory.expires_at > now))
    )
    statement = (
        select(
            Product,
            func.coalesce(
                func.sum(Inventory.quantity - Inventory.reserved_quantity), 0
            ).label("available_stock"),
        )
        .outerjoin(Inventory, inventory_join)
        .where(
            Product.is_active.is_(True),
            *allowed_pharmacy_product_conditions(),
            or_(
                Product.name.ilike(term),
                Product.sku.ilike(term),
                Product.inn_name.ilike(term),
                Product.manufacturer.ilike(term),
                Product.regulatory_id.ilike(term),
                Product.gtin.ilike(term),
                Product.barcode.ilike(term),
                Product.dosage_strength.ilike(term),
                Product.dosage_form.ilike(term),
            ),
        )
        .group_by(Product.id)
        .order_by(Product.name.asc(), Product.id.asc())
        .limit(limit)
    )
    rows = (await db.execute(statement)).all()
    return [
        POSProductResponse(
            id=product.id,
            name=product.name,
            sku=product.sku,
            dosage_strength=product.dosage_strength,
            dosage_form=product.dosage_form,
            units_per_pack=product.units_per_pack,
            manufacturer=product.manufacturer,
            inn_name=product.inn_name,
            gtin=product.gtin,
            barcode=product.barcode,
            price=product.price,
            stock=int(available_stock),
            medicinal_product_id=product.medicinal_product_id,
        )
        for product, available_stock in rows
    ]


@router.post(
    "/inventory/receive",
    response_model=InventoryReceiptResponse,
    status_code=status.HTTP_201_CREATED,
)
async def receive_inventory(
    payload: InventoryReceiptCreate,
    db: SessionDep,
    user: CurrentUser,
) -> InventoryReceiptResponse:
    """Receive a traceable medicine lot into one authorized pharmacy."""
    await require_pharmacy_tenant(payload.pharmacy_id, user, db)
    product_result = await db.execute(
        select(Product).where(
            Product.id == payload.product_id,
            Product.is_active.is_(True),
            *allowed_pharmacy_product_conditions(),
        )
    )
    product = product_result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Active sellable product not found")

    expiry = payload.expiry_date
    if expiry.tzinfo is not None:
        expiry = expiry.replace(tzinfo=None)
    expiry = expiry.replace(hour=0, minute=0, second=0, microsecond=0)
    if expiry.date() < datetime.utcnow().date():
        raise HTTPException(
            status_code=422, detail="Cannot receive an expired medicine lot"
        )

    lot_result = await db.execute(
        select(Inventory)
        .where(
            Inventory.product_id == payload.product_id,
            Inventory.pharmacy_id == payload.pharmacy_id,
            Inventory.lot_number == payload.lot_number.strip(),
        )
        .with_for_update()
    )
    lot = lot_result.scalar_one_or_none()
    if lot is not None:
        if lot.expires_at is not None and lot.expires_at.date() != expiry.date():
            raise HTTPException(
                status_code=409,
                detail="This lot number already exists with a different expiry date",
            )
        if lot.expires_at is None:
            lot.expires_at = expiry
        lot.quantity += payload.quantity
        lot.reorder_level = max(lot.reorder_level, 0)
    else:
        lot = Inventory(
            product_id=payload.product_id,
            pharmacy_id=payload.pharmacy_id,
            quantity=payload.quantity,
            reserved_quantity=0,
            reorder_level=0,
            lot_number=payload.lot_number.strip(),
            expires_at=expiry,
        )
        db.add(lot)

    try:
        await db.flush()
        response = InventoryReceiptResponse(
            inventory_id=lot.id,
            pharmacy_id=lot.pharmacy_id,
            product_id=lot.product_id,
            lot_number=lot.lot_number or "",
            expiry_date=lot.expires_at or expiry,
            received_quantity=payload.quantity,
            lot_quantity=lot.quantity,
            available_quantity=lot.quantity - lot.reserved_quantity,
            message="Stock receipt recorded",
        )
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Concurrent receipt conflict; refresh stock and retry",
        ) from exc
    return response


@router.get("/products/{product_id}/lots")
async def get_product_lots(
    product_id: int,
    db: SessionDep,
    user: CurrentUser,
    pharmacy_id: int = Query(..., gt=0),
) -> list[dict[str, object]]:
    """Return real, sellable stock lots for one product in the selected pharmacy."""
    await require_pharmacy_tenant(pharmacy_id, user, db)
    product_result = await db.execute(
        select(Product.id).where(
            Product.id == product_id,
            Product.is_active.is_(True),
            *allowed_pharmacy_product_conditions(),
        )
    )
    if product_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Active product not found")
    now = datetime.utcnow()
    result = await db.execute(
        select(Inventory)
        .where(
            Inventory.product_id == product_id,
            Inventory.pharmacy_id == pharmacy_id,
            Inventory.quantity > Inventory.reserved_quantity,
            (Inventory.expires_at.is_(None) | (Inventory.expires_at > now)),
        )
        .order_by(Inventory.expires_at.asc().nullslast(), Inventory.id.asc())
    )
    return [
        {
            "inventory_id": row.id,
            "lot_number": row.lot_number,
            "expiry_date": (
                row.expires_at.date().isoformat() if row.expires_at else None
            ),
            "quantity": row.quantity,
            "reserved_quantity": row.reserved_quantity,
            "available_quantity": row.quantity - row.reserved_quantity,
            "expiry_date_missing": row.expires_at is None,
        }
        for row in result.scalars().all()
    ]


@router.post(
    "/checkout", response_model=SaleResponse, status_code=status.HTTP_201_CREATED
)
async def checkout(
    payload: SaleCreate,
    db: SessionDep,
    cashier: CurrentUser,
) -> SaleResponse:
    """Create an idempotent sale, allocate FEFO stock, and record its payment state."""
    await require_pharmacy_tenant(payload.pharmacy_id, cashier, db)

    existing_result = await db.execute(
        select(Sale)
        .where(
            Sale.pharmacy_id == payload.pharmacy_id,
            Sale.idempotency_key == payload.idempotency_key,
        )
        .options(selectinload(Sale.items), selectinload(Sale.payments))
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        requested_items = sorted(
            (line.product_id, line.quantity) for line in payload.items
        )
        saved_items = sorted(
            (item.product_id, item.quantity) for item in existing.items
        )
        saved_payment = existing.payments[0] if existing.payments else None
        same_request = (
            requested_items == saved_items
            and existing.discount_total == _money(payload.discount_total)
            and saved_payment is not None
            and saved_payment.method == payload.payment_method
            and (
                payload.payment_method != "cash"
                or saved_payment.cash_received == _money(payload.cash_received or 0)
            )
        )
        if not same_request:
            raise HTTPException(
                status_code=409,
                detail="Idempotency key was already used for a different checkout request",
            )
        return SaleResponse.model_validate(
            {
                **{
                    k: getattr(existing, k)
                    for k in (
                        "id",
                        "receipt_number",
                        "pharmacy_id",
                        "subtotal",
                        "discount_total",
                        "total",
                        "status",
                        "created_at",
                        "completed_at",
                        "items",
                        "payments",
                    )
                },
                "cash_change": existing.cash_change,
            }
        )

    product_ids = [line.product_id for line in payload.items]
    products_result = await db.execute(
        select(Product).where(
            Product.id.in_(product_ids),
            Product.is_active.is_(True),
            *allowed_pharmacy_product_conditions(),
        )
    )
    products = {product.id: product for product in products_result.scalars().all()}
    if len(products) != len(product_ids):
        raise HTTPException(
            status_code=404, detail="One or more active products were not found"
        )

    subtotal = sum(
        (
            _money(products[line.product_id].price) * line.quantity
            for line in payload.items
        ),
        Decimal("0.00"),
    )
    discount = _money(payload.discount_total)
    total = _money(subtotal - discount)
    if discount > subtotal or total <= 0:
        raise HTTPException(
            status_code=422,
            detail="Discount must be less than the subtotal and total must be positive",
        )
    if payload.payment_method == "cash" and _money(payload.cash_received or 0) < total:
        raise HTTPException(
            status_code=422, detail="Cash received is less than the sale total"
        )

    now = datetime.utcnow()
    sale = Sale(
        receipt_number=f"PV-{now:%Y%m%d}-{uuid4().hex[:10].upper()}",
        pharmacy_id=payload.pharmacy_id,
        cashier_user_id=cashier.id,
        idempotency_key=payload.idempotency_key,
        subtotal=subtotal,
        discount_total=discount,
        total=total,
        status="completed" if payload.payment_method == "cash" else "awaiting_payment",
        completed_at=now if payload.payment_method == "cash" else None,
    )
    db.add(sale)
    await db.flush()

    for line in sorted(payload.items, key=lambda item: item.product_id):
        product = products[line.product_id]
        item = SaleItem(
            sale_id=sale.id,
            product_id=product.id,
            product_name=product.name,
            sku=product.sku,
            quantity=line.quantity,
            unit_price=_money(product.price),
            line_total=_money(_money(product.price) * line.quantity),
        )
        db.add(item)
        await db.flush()

        inventory_result = await db.execute(
            select(Inventory)
            .where(
                Inventory.product_id == product.id,
                Inventory.pharmacy_id == payload.pharmacy_id,
                Inventory.quantity > Inventory.reserved_quantity,
                (Inventory.expires_at.is_(None) | (Inventory.expires_at > now)),
            )
            .order_by(Inventory.expires_at.asc().nulls_last(), Inventory.id.asc())
            .with_for_update()
        )
        lots = list(inventory_result.scalars().all())
        remaining = line.quantity
        for lot in lots:
            available = lot.quantity - lot.reserved_quantity
            take = min(available, remaining)
            if take <= 0:
                continue
            if payload.payment_method == "cash":
                lot.quantity -= take
            else:
                lot.reserved_quantity += take
            db.add(
                SaleItemAllocation(
                    sale_item_id=item.id,
                    inventory_id=lot.id,
                    lot_number=lot.lot_number,
                    expires_at=lot.expires_at,
                    quantity=take,
                )
            )
            remaining -= take
            if remaining == 0:
                break
        if remaining:
            await db.rollback()
            raise HTTPException(
                status_code=409,
                detail=f"Insufficient non-expired stock for {product.name}; checkout was not completed",
            )

    payment = Payment(
        sale_id=sale.id,
        method=payload.payment_method,
        status="succeeded" if payload.payment_method == "cash" else "pending",
        amount=total,
        cash_received=(
            _money(payload.cash_received or 0)
            if payload.payment_method == "cash"
            else None
        ),
        change_due=(
            (_money(payload.cash_received or 0) - total)
            if payload.payment_method == "cash"
            else None
        ),
        provider_name="cash_register" if payload.payment_method == "cash" else None,
        idempotency_key=payload.idempotency_key,
        settled_at=now if payload.payment_method == "cash" else None,
    )
    db.add(payment)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        duplicate_result = await db.execute(
            select(Sale)
            .where(
                Sale.pharmacy_id == payload.pharmacy_id,
                Sale.idempotency_key == payload.idempotency_key,
            )
            .options(selectinload(Sale.items), selectinload(Sale.payments))
        )
        duplicate = duplicate_result.scalar_one_or_none()
        if duplicate is None:
            raise
        duplicate_items = sorted(
            (item.product_id, item.quantity) for item in duplicate.items
        )
        requested_items = sorted(
            (line.product_id, line.quantity) for line in payload.items
        )
        duplicate_payment = duplicate.payments[0] if duplicate.payments else None
        if (
            duplicate_items != requested_items
            or duplicate.discount_total != discount
            or duplicate_payment is None
            or duplicate_payment.method != payload.payment_method
            or (
                payload.payment_method == "cash"
                and duplicate_payment.cash_received
                != _money(payload.cash_received or 0)
            )
        ):
            raise HTTPException(
                status_code=409,
                detail="Idempotency key conflicts with another checkout",
            )
        return SaleResponse.model_validate(duplicate)

    saved = await _load_sale(db, sale.id)
    return SaleResponse.model_validate(
        {
            **{
                k: getattr(saved, k)
                for k in (
                    "id",
                    "receipt_number",
                    "pharmacy_id",
                    "subtotal",
                    "discount_total",
                    "total",
                    "status",
                    "created_at",
                    "completed_at",
                    "items",
                    "payments",
                )
            },
            "cash_change": saved.cash_change,
        }
    )


@router.post("/payments/webhook", status_code=status.HTTP_200_OK)
async def payment_webhook(
    request: Request,
    db: SessionDep,
    x_pharmaviyum_signature: str | None = Header(default=None),
) -> dict[str, str]:
    """Settle external payment notifications using a shared-secret HMAC-SHA256 signature.

    Configure PAYMENT_WEBHOOK_SECRET and have the payment adapter sign the exact
    raw request body. Provider-specific signature verification belongs in the
    provider adapter before this normalized event reaches this endpoint.
    """
    secret = os.getenv("PAYMENT_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(status_code=503, detail="Payment webhook is not configured")
    raw_body = await request.body()
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    if not x_pharmaviyum_signature or not hmac.compare_digest(
        expected, x_pharmaviyum_signature
    ):
        raise HTTPException(status_code=401, detail="Invalid payment webhook signature")
    try:
        event = json.loads(raw_body)
        payment_id = int(event["payment_id"])
        event_status = event["status"]
        provider_name = str(event["provider_name"])
        provider_payment_id = str(event["provider_payment_id"])
        event_amount = _money(Decimal(str(event["amount"])))
    except (
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
        InvalidOperation,
    ) as exc:
        raise HTTPException(
            status_code=400, detail="Invalid payment event payload"
        ) from exc
    if event_status not in {"succeeded", "failed"}:
        raise HTTPException(status_code=422, detail="Unsupported payment event status")

    payment_lookup = await db.get(Payment, payment_id)
    if payment_lookup is None or payment_lookup.method == "cash":
        raise HTTPException(status_code=404, detail="External payment not found")
    sale_result = await db.execute(
        select(Sale).where(Sale.id == payment_lookup.sale_id).with_for_update()
    )
    sale = sale_result.scalar_one()
    result = await db.execute(
        select(Payment).where(Payment.id == payment_id).with_for_update()
    )
    payment = result.scalar_one()
    if payment.status != "pending":
        # Webhook retries are intentionally idempotent.
        if (
            payment.status == event_status
            and payment.provider_payment_id == provider_payment_id
        ):
            return {"status": "already_processed"}
        raise HTTPException(
            status_code=409, detail="Payment has already been finalized"
        )
    if event_amount != payment.amount:
        raise HTTPException(
            status_code=409, detail="Payment amount does not match the sale"
        )
    allocations_result = await db.execute(
        select(SaleItemAllocation)
        .join(SaleItem, SaleItem.id == SaleItemAllocation.sale_item_id)
        .where(SaleItem.sale_id == sale.id)
    )
    allocations = list(allocations_result.scalars().all())
    inventory_ids = [allocation.inventory_id for allocation in allocations]
    inventory_result = await db.execute(
        select(Inventory)
        .where(Inventory.id.in_(inventory_ids))
        .order_by(Inventory.id.asc())
        .with_for_update()
    )
    inventory_by_id = {row.id: row for row in inventory_result.scalars().all()}

    for allocation in allocations:
        lot = inventory_by_id[allocation.inventory_id]
        lot.reserved_quantity -= allocation.quantity
        if event_status == "succeeded":
            lot.quantity -= allocation.quantity

    payment.status = event_status
    payment.provider_name = provider_name[:80]
    payment.provider_payment_id = provider_payment_id[:160]
    payment.settled_at = datetime.utcnow()
    sale.status = "completed" if event_status == "succeeded" else "cancelled"
    sale.completed_at = datetime.utcnow() if event_status == "succeeded" else None
    await db.commit()
    return {"status": "processed"}


@router.post("/sales/{sale_id}/cancel", response_model=SaleResponse)
async def cancel_pending_sale(
    sale_id: int,
    db: SessionDep,
    user: CurrentUser,
) -> SaleResponse:
    """Cancel an unpaid POS sale and release its reserved FEFO lots."""
    sale_result = await db.execute(
        select(Sale).where(Sale.id == sale_id).with_for_update()
    )
    sale = sale_result.scalar_one_or_none()
    if sale is None:
        raise HTTPException(status_code=404, detail="Sale not found")
    await require_pharmacy_tenant(sale.pharmacy_id, user, db)
    if sale.status != "awaiting_payment":
        raise HTTPException(
            status_code=409, detail="Only pending-payment sales can be cancelled"
        )

    payment_result = await db.execute(
        select(Payment).where(Payment.sale_id == sale.id).with_for_update()
    )
    payments = list(payment_result.scalars().all())
    if any(payment.status == "succeeded" for payment in payments):
        raise HTTPException(
            status_code=409, detail="A settled sale cannot be cancelled"
        )

    allocation_result = await db.execute(
        select(SaleItemAllocation)
        .join(SaleItem, SaleItem.id == SaleItemAllocation.sale_item_id)
        .where(SaleItem.sale_id == sale.id)
    )
    allocations = list(allocation_result.scalars().all())
    inventory_ids = [allocation.inventory_id for allocation in allocations]
    inventory_result = await db.execute(
        select(Inventory).where(Inventory.id.in_(inventory_ids)).with_for_update()
    )
    inventory_by_id = {lot.id: lot for lot in inventory_result.scalars().all()}
    for allocation in allocations:
        lot = inventory_by_id[allocation.inventory_id]
        lot.reserved_quantity -= allocation.quantity
    for payment in payments:
        if payment.status == "pending":
            payment.status = "failed"
            payment.settled_at = datetime.utcnow()
    sale.status = "cancelled"
    await db.commit()
    return SaleResponse.model_validate(await _load_sale(db, sale.id))


@router.get("/sales/{sale_id}", response_model=SaleResponse)
async def get_sale(sale_id: int, db: SessionDep, user: CurrentUser) -> SaleResponse:
    sale = await _load_sale(db, sale_id)
    await require_pharmacy_tenant(sale.pharmacy_id, user, db)
    return SaleResponse.model_validate(sale)
