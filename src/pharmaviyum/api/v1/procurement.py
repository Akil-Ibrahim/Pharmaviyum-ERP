"""Procurement, receiving, transfers and storage-control APIs."""

# mypy: disable-error-code="assignment,arg-type,call-overload,union-attr"

from datetime import date, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.models.audit_log import AuditLog
from src.pharmaviyum.models.goods_receipt import GoodsReceipt
from src.pharmaviyum.models.goods_receipt_item import GoodsReceiptItem
from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.inventory_transaction import InventoryTransaction
from src.pharmaviyum.models.pharmacy import Pharmacy
from src.pharmaviyum.models.product import Product
from src.pharmaviyum.models.product_batch import ProductBatch
from src.pharmaviyum.models.purchase_order import PurchaseOrder
from src.pharmaviyum.models.purchase_order_item import PurchaseOrderItem
from src.pharmaviyum.models.stock_transfer import StockTransfer
from src.pharmaviyum.models.stock_transfer_item import StockTransferItem
from src.pharmaviyum.models.supplier import Supplier
from src.pharmaviyum.models.supplier_product import SupplierProduct
from src.pharmaviyum.models.temperature_log import TemperatureLog
from src.pharmaviyum.modules.auth.deps import CurrentUser, SessionDep
from src.pharmaviyum.modules.auth.tenant import require_pharmacy_tenant

router = APIRouter(prefix="/procurement", tags=["Procurement & Stock"])


class SupplierProductCreate(BaseModel):
    supplier_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    supplier_sku: str | None = Field(default=None, max_length=64)
    purchase_price: float = Field(default=0, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    min_order_quantity: int = Field(default=1, gt=0)
    lead_time_days: int = Field(default=1, ge=0)


class PurchaseOrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    supplier_product_id: int | None = Field(default=None, gt=0)
    unit_price: float | None = Field(default=None, ge=0)


class PurchaseOrderCreate(BaseModel):
    pharmacy_id: int = Field(gt=0)
    supplier_id: int = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    expected_delivery_at: datetime | None = None
    items: list[PurchaseOrderItemCreate] = Field(min_length=1, max_length=100)


class GoodsReceiptItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    batch_number: str = Field(min_length=1, max_length=64)
    expiry_date: date
    quantity: int = Field(gt=0)
    purchase_price: float = Field(default=0, ge=0)
    storage_location: str = Field(
        default="shelf", pattern="^(shelf|refrigerator|special_storage|quarantine)$"
    )
    inspection_status: str = Field(
        default="accepted", pattern="^(accepted|quarantine|rejected)$"
    )
    rejection_reason: str | None = Field(default=None, max_length=500)


class GoodsReceiptCreate(BaseModel):
    pharmacy_id: int = Field(gt=0)
    supplier_id: int | None = Field(default=None, gt=0)
    purchase_order_id: int | None = Field(default=None, gt=0)
    source_type: str = Field(
        default="supplier", pattern="^(supplier|central_warehouse|pharmacy_transfer)$"
    )
    notes: str | None = Field(default=None, max_length=1000)
    items: list[GoodsReceiptItemCreate] = Field(min_length=1, max_length=100)


class StockTransferItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    batch_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class StockTransferCreate(BaseModel):
    source_pharmacy_id: int = Field(gt=0)
    destination_pharmacy_id: int = Field(gt=0)
    items: list[StockTransferItemCreate] = Field(min_length=1, max_length=100)


class TemperatureLogCreate(BaseModel):
    pharmacy_id: int = Field(gt=0)
    storage_location: str = Field(
        pattern="^(shelf|refrigerator|special_storage|quarantine)$"
    )
    temperature_c: float
    recorded_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=500)


def _storage_status(product: Product, temperature: float) -> str:
    if (
        product.storage_temperature_min is None
        or product.storage_temperature_max is None
    ):
        return "range_not_configured"
    return (
        "within_range"
        if (
            product.storage_temperature_min
            <= temperature
            <= product.storage_temperature_max
        )
        else "out_of_range"
    )


async def _inventory_for_batch(
    db: AsyncSession, pharmacy_id: int, product_id: int, batch_id: int
) -> Inventory | None:
    return await db.scalar(
        select(Inventory)
        .where(
            Inventory.pharmacy_id == pharmacy_id,
            Inventory.product_id == product_id,
            Inventory.batch_id == batch_id,
        )
        .with_for_update()
    )


@router.get("/suppliers")
async def list_procurement_suppliers(
    current_user: CurrentUser, db: SessionDep, pharmacy_id: int = Query(gt=0)
) -> list[dict[str, object]]:
    await require_pharmacy_tenant(pharmacy_id, current_user, db)
    result = await db.execute(
        select(Supplier).where(Supplier.is_active.is_(True)).order_by(Supplier.name)
    )
    return [
        {"id": s.id, "name": s.name, "code": s.code} for s in result.scalars().all()
    ]


@router.post("/supplier-products", status_code=201)
async def create_supplier_product(
    data: SupplierProductCreate,
    current_user: CurrentUser,
    db: SessionDep,
    pharmacy_id: int = Query(gt=0),
) -> SupplierProduct:
    await require_pharmacy_tenant(pharmacy_id, current_user, db)
    supplier = await db.get(Supplier, data.supplier_id)
    product = await db.get(Product, data.product_id)
    if supplier is None or not supplier.is_active:
        raise HTTPException(404, "Active supplier not found")
    if product is None or not product.is_active:
        raise HTTPException(404, "Active product not found")
    existing = await db.scalar(
        select(SupplierProduct).where(
            SupplierProduct.supplier_id == data.supplier_id,
            SupplierProduct.product_id == data.product_id,
        )
    )
    if existing:
        raise HTTPException(409, "Supplier-product mapping already exists")
    mapping = SupplierProduct(**data.model_dump())
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)
    return mapping


@router.get("/defectura")
async def get_defectura(
    current_user: CurrentUser,
    db: SessionDep,
    pharmacy_id: int = Query(gt=0),
) -> list[dict[str, object]]:
    tenant = await require_pharmacy_tenant(pharmacy_id, current_user, db)
    inventory_rows = await db.execute(
        select(Inventory, Product)
        .join(Product, Product.id == Inventory.product_id)
        .where(Inventory.pharmacy_id == tenant.pharmacy_id, Product.is_active.is_(True))
        .order_by(Product.name)
    )
    result: list[dict[str, object]] = []
    for inventory, product in inventory_rows.all():
        available = max(inventory.quantity - inventory.reserved_quantity, 0)
        if available > inventory.reorder_level:
            continue
        incoming = await db.scalar(
            select(func.coalesce(func.sum(PurchaseOrderItem.quantity), 0))
            .join(
                PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.purchase_order_id
            )
            .where(
                PurchaseOrder.pharmacy_id == tenant.pharmacy_id,
                PurchaseOrderItem.product_id == product.id,
                PurchaseOrder.status.in_(
                    ["draft", "approved", "ordered", "partially_received"]
                ),
            )
        )
        incoming = int(incoming or 0)
        recommended = max(inventory.reorder_level - available - incoming, 0)
        supplier_result = await db.execute(
            select(SupplierProduct, Supplier)
            .join(Supplier, Supplier.id == SupplierProduct.supplier_id)
            .where(
                SupplierProduct.product_id == product.id,
                SupplierProduct.is_active.is_(True),
                Supplier.is_active.is_(True),
            )
            .order_by(SupplierProduct.purchase_price, SupplierProduct.lead_time_days)
        )
        supplier_row = supplier_result.first()
        supplier = supplier_row[1] if supplier_row else None
        result.append(
            {
                "product_id": product.id,
                "product_name": product.name,
                "current_quantity": available,
                "reserved_quantity": inventory.reserved_quantity,
                "reorder_level": inventory.reorder_level,
                "incoming_quantity": incoming,
                "recommended_quantity": recommended,
                "supplier": (
                    {
                        "id": supplier.id,
                        "name": supplier.name,
                        "purchase_price": supplier_row[0].purchase_price,
                        "currency": supplier_row[0].currency,
                        "min_order_quantity": supplier_row[0].min_order_quantity,
                        "lead_time_days": supplier_row[0].lead_time_days,
                    }
                    if supplier_row
                    else None
                ),
            }
        )
    return result


@router.post("/purchase-orders", status_code=201)
async def create_purchase_order(
    data: PurchaseOrderCreate, current_user: CurrentUser, db: SessionDep
) -> PurchaseOrder:
    tenant = await require_pharmacy_tenant(data.pharmacy_id, current_user, db)
    supplier = await db.get(Supplier, data.supplier_id)
    if supplier is None or not supplier.is_active:
        raise HTTPException(404, "Active supplier not found")

    order = PurchaseOrder(
        order_number=f"PO-{datetime.utcnow():%Y%m%d}-{uuid4().hex[:8].upper()}",
        supplier_id=supplier.id,
        pharmacy_id=tenant.pharmacy_id,
        status="ordered",
        expected_delivery_at=data.expected_delivery_at,
        currency=data.currency.upper(),
        created_by=current_user.id,
        approved_by=current_user.id,
    )
    db.add(order)
    await db.flush()

    total = 0.0
    for item_data in data.items:
        mapping = None
        if item_data.supplier_product_id:
            mapping = await db.scalar(
                select(SupplierProduct).where(
                    SupplierProduct.id == item_data.supplier_product_id,
                    SupplierProduct.supplier_id == supplier.id,
                    SupplierProduct.product_id == item_data.product_id,
                    SupplierProduct.is_active.is_(True),
                )
            )
            if mapping is None:
                raise HTTPException(404, "Supplier-product mapping not found")
        elif item_data.unit_price is None:
            mapping = await db.scalar(
                select(SupplierProduct).where(
                    SupplierProduct.supplier_id == supplier.id,
                    SupplierProduct.product_id == item_data.product_id,
                    SupplierProduct.is_active.is_(True),
                )
            )
        unit_price = (
            item_data.unit_price
            if item_data.unit_price is not None
            else (mapping.purchase_price if mapping else None)
        )
        if unit_price is None:
            raise HTTPException(
                422, f"No purchase price for product {item_data.product_id}"
            )
        if mapping and item_data.quantity < mapping.min_order_quantity:
            raise HTTPException(
                422,
                f"Quantity for product {item_data.product_id} is below supplier "
                "minimum",
            )
        product = await db.get(Product, item_data.product_id)
        if product is None or not product.is_active:
            raise HTTPException(404, f"Product {item_data.product_id} not found")
        line_total = round(unit_price * item_data.quantity, 2)
        total += line_total
        db.add(
            PurchaseOrderItem(
                purchase_order_id=order.id,
                product_id=product.id,
                supplier_product_id=mapping.id if mapping else None,
                quantity=item_data.quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
        )
    order.total_amount = round(total, 2)
    db.add(
        AuditLog(
            actor_id=current_user.id,
            actor_type="user",
            action="purchase_order_created",
            entity="purchase_order",
            entity_id=order.id,
            changes={"supplier_id": supplier.id, "pharmacy_id": tenant.pharmacy_id},
        )
    )
    await db.commit()
    await db.refresh(order)
    return order


@router.post("/goods-receipts", status_code=201)
async def receive_goods(
    data: GoodsReceiptCreate, current_user: CurrentUser, db: SessionDep
) -> GoodsReceipt:
    tenant = await require_pharmacy_tenant(data.pharmacy_id, current_user, db)
    if data.source_type == "supplier" and data.supplier_id is None:
        raise HTTPException(422, "supplier_id is required for supplier receipts")
    receipt = GoodsReceipt(
        receipt_number=f"GR-{datetime.utcnow():%Y%m%d}-{uuid4().hex[:8].upper()}",
        supplier_id=data.supplier_id,
        pharmacy_id=tenant.pharmacy_id,
        purchase_order_id=data.purchase_order_id,
        source_type=data.source_type,
        status="accepted",
        received_by=current_user.id,
        notes=data.notes,
    )
    db.add(receipt)
    await db.flush()

    for item_data in data.items:
        product = await db.get(Product, item_data.product_id)
        if product is None or not product.is_active:
            raise HTTPException(404, f"Product {item_data.product_id} not found")
        if item_data.expiry_date <= date.today():
            raise HTTPException(422, "Received batch must have a future expiry date")
        if item_data.inspection_status == "accepted":
            required_location = product.storage_location_type
            if item_data.storage_location != required_location:
                raise HTTPException(
                    422,
                    f"Product requires storage location '{required_location}'",
                )
        batch = await db.scalar(
            select(ProductBatch)
            .where(
                ProductBatch.product_id == product.id,
                ProductBatch.batch_number == item_data.batch_number,
            )
            .with_for_update()
        )
        if batch is None:
            batch = ProductBatch(
                product_id=product.id,
                batch_number=item_data.batch_number,
                expiry_date=item_data.expiry_date,
                received_quantity=item_data.quantity,
                available_quantity=(
                    item_data.quantity
                    if item_data.inspection_status == "accepted"
                    else 0
                ),
            )
            db.add(batch)
            await db.flush()
        else:
            if batch.expiry_date != item_data.expiry_date:
                raise HTTPException(409, "Existing batch has a different expiry date")
            batch.received_quantity += item_data.quantity
            if item_data.inspection_status == "accepted":
                batch.available_quantity += item_data.quantity

        db.add(
            GoodsReceiptItem(
                goods_receipt_id=receipt.id,
                product_id=product.id,
                batch_id=batch.id,
                batch_number=batch.batch_number,
                expiry_date=batch.expiry_date,
                quantity=item_data.quantity,
                purchase_price=item_data.purchase_price,
                storage_location=item_data.storage_location,
                inspection_status=item_data.inspection_status,
                rejection_reason=item_data.rejection_reason,
            )
        )
        if item_data.inspection_status == "accepted":
            inventory = await db.scalar(
                select(Inventory)
                .where(
                    Inventory.product_id == product.id,
                    Inventory.pharmacy_id == tenant.pharmacy_id,
                    Inventory.batch_id == batch.id,
                )
                .with_for_update()
            )
            if inventory is None:
                inventory = Inventory(
                    product_id=product.id,
                    pharmacy_id=tenant.pharmacy_id,
                    quantity=0,
                    reserved_quantity=0,
                    reorder_level=0,
                    batch_id=batch.id,
                    lot_number=batch.batch_number,
                    expires_at=datetime.combine(batch.expiry_date, datetime.min.time()),
                )
                db.add(inventory)
                await db.flush()
            inventory.quantity += item_data.quantity
            inventory.expires_at = datetime.combine(
                batch.expiry_date, datetime.min.time()
            )
            db.add(
                InventoryTransaction(
                    pharmacy_id=tenant.pharmacy_id,
                    inventory_id=inventory.id,
                    product_id=product.id,
                    batch_id=batch.id,
                    transaction_type="receipt",
                    quantity_delta=item_data.quantity,
                    quantity_after=inventory.quantity,
                    actor_id=current_user.id,
                )
            )
    db.add(
        AuditLog(
            actor_id=current_user.id,
            actor_type="user",
            action="goods_received",
            entity="goods_receipt",
            entity_id=receipt.id,
            changes={
                "source_type": data.source_type,
                "pharmacy_id": tenant.pharmacy_id,
            },
        )
    )
    await db.commit()
    await db.refresh(receipt)
    return receipt


@router.post("/transfers", status_code=201)
async def create_stock_transfer(
    data: StockTransferCreate, current_user: CurrentUser, db: SessionDep
) -> StockTransfer:
    if data.source_pharmacy_id == data.destination_pharmacy_id:
        raise HTTPException(422, "Source and destination pharmacies must differ")
    source = await require_pharmacy_tenant(data.source_pharmacy_id, current_user, db)
    destination = await db.get(Pharmacy, data.destination_pharmacy_id)
    if destination is None or not destination.is_active:
        raise HTTPException(404, "Destination pharmacy not found")
    if not current_user.is_superuser:
        await require_pharmacy_tenant(data.destination_pharmacy_id, current_user, db)
    transfer = StockTransfer(
        transfer_number=f"TR-{datetime.utcnow():%Y%m%d}-{uuid4().hex[:8].upper()}",
        source_pharmacy_id=source.pharmacy_id,
        destination_pharmacy_id=destination.id,
        status="in_transit",
        created_by=current_user.id,
        approved_by=current_user.id,
        shipped_at=datetime.utcnow(),
    )
    db.add(transfer)
    await db.flush()

    for item_data in data.items:
        batch = await db.get(ProductBatch, item_data.batch_id)
        if batch is None or batch.product_id != item_data.product_id:
            raise HTTPException(404, "Product batch not found")
        inventory = await _inventory_for_batch(
            db, source.pharmacy_id, item_data.product_id, item_data.batch_id
        )
        if inventory is None or inventory.quantity < item_data.quantity:
            raise HTTPException(409, "Insufficient source inventory for transfer")
        inventory.quantity -= item_data.quantity
        if inventory.reserved_quantity > inventory.quantity:
            inventory.reserved_quantity = inventory.quantity
        db.add(
            StockTransferItem(
                stock_transfer_id=transfer.id,
                product_id=item_data.product_id,
                batch_id=item_data.batch_id,
                quantity=item_data.quantity,
            )
        )
        db.add(
            InventoryTransaction(
                pharmacy_id=source.pharmacy_id,
                inventory_id=inventory.id,
                product_id=item_data.product_id,
                batch_id=item_data.batch_id,
                transaction_type="transfer_out",
                quantity_delta=-item_data.quantity,
                quantity_after=inventory.quantity,
                actor_id=current_user.id,
            )
        )
    db.add(
        AuditLog(
            actor_id=current_user.id,
            actor_type="user",
            action="stock_transfer_created",
            entity="stock_transfer",
            entity_id=transfer.id,
            changes={"source": source.pharmacy_id, "destination": destination.id},
        )
    )
    await db.commit()
    await db.refresh(transfer)
    return transfer


@router.post("/transfers/{transfer_id}/receive")
async def receive_stock_transfer(
    transfer_id: int, current_user: CurrentUser, db: SessionDep
) -> StockTransfer:
    transfer = await db.get(StockTransfer, transfer_id)
    if transfer is None:
        raise HTTPException(404, "Stock transfer not found")
    await require_pharmacy_tenant(transfer.destination_pharmacy_id, current_user, db)
    if transfer.status != "in_transit":
        raise HTTPException(409, "Transfer is not awaiting receipt")

    result = await db.execute(
        select(StockTransferItem).where(
            StockTransferItem.stock_transfer_id == transfer.id
        )
    )
    for item in result.scalars().all():
        batch = await db.get(ProductBatch, item.batch_id)
        if batch is None:
            raise HTTPException(409, "Transfer batch no longer exists")
        inventory = await _inventory_for_batch(
            db, transfer.destination_pharmacy_id, item.product_id, item.batch_id
        )
        if inventory is None:
            inventory = Inventory(
                product_id=item.product_id,
                pharmacy_id=transfer.destination_pharmacy_id,
                quantity=0,
                reserved_quantity=0,
                reorder_level=0,
                batch_id=item.batch_id,
                lot_number=batch.batch_number,
                expires_at=datetime.combine(batch.expiry_date, datetime.min.time()),
            )
            db.add(inventory)
            await db.flush()
        inventory.quantity += item.quantity
        db.add(
            InventoryTransaction(
                pharmacy_id=transfer.destination_pharmacy_id,
                inventory_id=inventory.id,
                product_id=item.product_id,
                batch_id=item.batch_id,
                transaction_type="transfer_in",
                quantity_delta=item.quantity,
                quantity_after=inventory.quantity,
                actor_id=current_user.id,
            )
        )
    transfer.status = "received"
    transfer.received_at = datetime.utcnow()
    db.add(
        AuditLog(
            actor_id=current_user.id,
            actor_type="user",
            action="stock_transfer_received",
            entity="stock_transfer",
            entity_id=transfer.id,
            changes={"destination": transfer.destination_pharmacy_id},
        )
    )
    await db.commit()
    await db.refresh(transfer)
    return transfer


@router.post("/temperature", status_code=201)
async def record_temperature(
    data: TemperatureLogCreate, current_user: CurrentUser, db: SessionDep
) -> TemperatureLog:
    tenant = await require_pharmacy_tenant(data.pharmacy_id, current_user, db)
    products = await db.execute(
        select(Product).where(
            Product.is_active.is_(True),
            Product.storage_location_type == data.storage_location,
        )
    )
    statuses = [
        _storage_status(product, data.temperature_c)
        for product in products.scalars().all()
        if product.storage_temperature_min is not None
        or product.storage_temperature_max is not None
    ]
    status = (
        "out_of_range"
        if "out_of_range" in statuses
        else ("within_range" if statuses else "range_not_configured")
    )
    log = TemperatureLog(
        pharmacy_id=tenant.pharmacy_id,
        storage_location=data.storage_location,
        temperature_c=data.temperature_c,
        recorded_at=data.recorded_at or datetime.utcnow(),
        recorded_by=current_user.id,
        status=status,
        notes=data.notes,
    )
    db.add(log)
    if status == "out_of_range":
        db.add(
            AuditLog(
                actor_id=current_user.id,
                actor_type="user",
                action="temperature_excursion",
                entity="temperature_log",
                entity_id=None,
                changes={
                    "pharmacy_id": tenant.pharmacy_id,
                    "storage_location": data.storage_location,
                    "temperature_c": data.temperature_c,
                },
            )
        )
    await db.commit()
    await db.refresh(log)
    return log


@router.get("/temperature")
async def list_temperature_logs(
    current_user: CurrentUser,
    db: SessionDep,
    pharmacy_id: int = Query(gt=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[TemperatureLog]:
    tenant = await require_pharmacy_tenant(pharmacy_id, current_user, db)
    result = await db.execute(
        select(TemperatureLog)
        .where(TemperatureLog.pharmacy_id == tenant.pharmacy_id)
        .order_by(TemperatureLog.recorded_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
