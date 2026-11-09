"""Read-only pharmacy operations tools for Mortarium.

All identity and tenant scope comes from the authenticated MCP context.
These tools expose operational facts; they never mutate pharmacy records.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, or_, select

from src.pharmaviyum.ai.mcp.context import require_mcp_context
from src.pharmaviyum.ai.mcp.registry import registry
from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.pos import Sale
from src.pharmaviyum.models.product import Product
from src.pharmaviyum.services.catalog_exclusions import allowed_pharmacy_product_conditions


class ProductSearchRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    query: str = Field(min_length=2, max_length=100)
    limit: int = Field(default=10, ge=1, le=25)


class ProductSearchItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    product_id: int
    name: str
    sku: str
    inn_name: str | None = None
    dosage_strength: str | None = None
    dosage_form: str | None = None
    manufacturer: str | None = None
    barcode: str | None = None
    available_stock: int


class ProductSearchResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    query: str
    count: int
    products: list[ProductSearchItem]


class InventoryOverviewRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    low_stock_only: bool = False
    limit: int = Field(default=25, ge=1, le=100)


class InventoryOverviewItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    product_id: int
    product_name: str
    sku: str
    lot_number: str | None = None
    expiry_date: date | None = None
    quantity: int
    reserved_quantity: int
    available_quantity: int
    reorder_level: int
    below_reorder_level: bool


class InventoryOverviewResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    pharmacy_id: int
    count: int
    low_stock_count: int
    items: list[InventoryOverviewItem]


class ExpiringInventoryRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    days_ahead: int = Field(default=90, ge=1, le=365)
    limit: int = Field(default=50, ge=1, le=100)


class ExpiringInventoryItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    product_id: int
    product_name: str
    sku: str
    lot_number: str | None = None
    expiry_date: date
    days_until_expiry: int
    available_quantity: int
    status: Literal["expired", "expiring"]


class ExpiringInventoryResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    pharmacy_id: int
    days_ahead: int
    count: int
    items: list[ExpiringInventoryItem]


class SalesSummaryRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    start_date: date
    end_date: date

    @classmethod
    def model_validate(cls, obj, **kwargs):
        result = super().model_validate(obj, **kwargs)
        if result.end_date < result.start_date:
            raise ValueError("end_date must be on or after start_date")
        if (result.end_date - result.start_date).days > 366:
            raise ValueError("date range must not exceed 367 calendar days")
        return result


class SalesSummaryResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    pharmacy_id: int
    start_date: date
    end_date: date
    completed_sales: int
    revenue: Decimal
    pending_sales: int
    cancelled_sales: int
    refunded_sales: int


@registry.tool(
    name="search_pharmacy_products",
    description=(
        "Search active sellable medicine products in the authenticated pharmacy by "
        "brand name, INN, SKU, barcode, manufacturer, strength or dosage form. "
        "Returns current available stock; read-only."
    ),
    input_schema=ProductSearchRequest,
    output_schema=ProductSearchResult,
    category="pharmacy_catalog",
    requires_db=True,
    tags=["pharmacy", "catalog", "medicine", "search", "read"],
)
async def search_pharmacy_products(input: ProductSearchRequest) -> ProductSearchResult:
    auth = require_mcp_context()
    from src.pharmaviyum.shared.core.database import async_session_factory

    term = f"%{input.query.strip()}%"
    inventory_join = (
        (Inventory.product_id == Product.id)
        & (Inventory.pharmacy_id == auth.pharmacy_id)
        & (Inventory.expires_at.is_(None) | (Inventory.expires_at > datetime.utcnow()))
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
                Product.inn_name.ilike(term),
                Product.sku.ilike(term),
                Product.barcode.ilike(term),
                Product.gtin.ilike(term),
                Product.regulatory_id.ilike(term),
                Product.manufacturer.ilike(term),
                Product.dosage_strength.ilike(term),
                Product.dosage_form.ilike(term),
            ),
        )
        .group_by(Product.id)
        .order_by(Product.name.asc(), Product.id.asc())
        .limit(input.limit)
    )
    async with async_session_factory() as session:
        rows = (await session.execute(statement)).all()

    items = [
        ProductSearchItem(
            product_id=product.id,
            name=product.name,
            sku=product.sku,
            inn_name=product.inn_name,
            dosage_strength=product.dosage_strength,
            dosage_form=product.dosage_form,
            manufacturer=product.manufacturer,
            barcode=product.barcode or product.gtin,
            available_stock=max(0, int(available_stock or 0)),
        )
        for product, available_stock in rows
    ]
    return ProductSearchResult(query=input.query, count=len(items), products=items)


@registry.tool(
    name="get_inventory_overview",
    description=(
        "Read the authenticated pharmacy's product and lot inventory, including "
        "on-hand, reserved and available quantities, reorder levels and expiry dates. "
        "Can return only below-reorder-level rows. Read-only."
    ),
    input_schema=InventoryOverviewRequest,
    output_schema=InventoryOverviewResult,
    category="pharmacy_inventory",
    requires_db=True,
    tags=["pharmacy", "inventory", "stock", "reorder", "read"],
)
async def get_inventory_overview(input: InventoryOverviewRequest) -> InventoryOverviewResult:
    auth = require_mcp_context()
    from src.pharmaviyum.shared.core.database import async_session_factory

    statement = (
        select(Inventory, Product)
        .join(Product, Product.id == Inventory.product_id)
        .where(
            Inventory.pharmacy_id == auth.pharmacy_id,
            Product.is_active.is_(True),
            *allowed_pharmacy_product_conditions(),
        )
    )
    if input.low_stock_only:
        statement = statement.where(
            (Inventory.quantity - Inventory.reserved_quantity)
            <= Inventory.reorder_level
        )
    statement = statement.order_by(
        Inventory.expires_at.asc().nullslast(), Product.name.asc()
    ).limit(input.limit)

    async with async_session_factory() as session:
        rows = (await session.execute(statement)).all()

    items = [
        InventoryOverviewItem(
            product_id=product.id,
            product_name=product.name,
            sku=product.sku,
            lot_number=lot.lot_number,
            expiry_date=lot.expires_at.date() if lot.expires_at else None,
            quantity=lot.quantity,
            reserved_quantity=lot.reserved_quantity,
            available_quantity=max(0, lot.quantity - lot.reserved_quantity),
            reorder_level=lot.reorder_level,
            below_reorder_level=(lot.quantity - lot.reserved_quantity) <= lot.reorder_level,
        )
        for lot, product in rows
    ]
    return InventoryOverviewResult(
        pharmacy_id=auth.pharmacy_id,
        count=len(items),
        low_stock_count=sum(item.below_reorder_level for item in items),
        items=items,
    )


@registry.tool(
    name="get_expiring_inventory",
    description=(
        "Find available pharmacy inventory lots that are already expired or expire "
        "within the requested number of days. Includes product, lot, expiry and "
        "available quantity. Does not block, write off or change stock."
    ),
    input_schema=ExpiringInventoryRequest,
    output_schema=ExpiringInventoryResult,
    category="pharmacy_inventory",
    requires_db=True,
    tags=["pharmacy", "inventory", "batch", "expiry", "fefo", "read"],
)
async def get_expiring_inventory(input: ExpiringInventoryRequest) -> ExpiringInventoryResult:
    auth = require_mcp_context()
    from src.pharmaviyum.shared.core.database import async_session_factory

    today = date.today()
    cutoff = datetime.combine(today + timedelta(days=input.days_ahead), time.max)
    statement = (
        select(Inventory, Product)
        .join(Product, Product.id == Inventory.product_id)
        .where(
            Inventory.pharmacy_id == auth.pharmacy_id,
            Inventory.expires_at.is_not(None),
            Inventory.expires_at <= cutoff,
            Inventory.quantity > Inventory.reserved_quantity,
            Product.is_active.is_(True),
            *allowed_pharmacy_product_conditions(),
        )
        .order_by(Inventory.expires_at.asc(), Product.name.asc())
        .limit(input.limit)
    )
    async with async_session_factory() as session:
        rows = (await session.execute(statement)).all()

    items = []
    for lot, product in rows:
        expiry = lot.expires_at.date()
        days_left = (expiry - today).days
        items.append(
            ExpiringInventoryItem(
                product_id=product.id,
                product_name=product.name,
                sku=product.sku,
                lot_number=lot.lot_number,
                expiry_date=expiry,
                days_until_expiry=days_left,
                available_quantity=max(0, lot.quantity - lot.reserved_quantity),
                status="expired" if days_left < 0 else "expiring",
            )
        )
    return ExpiringInventoryResult(
        pharmacy_id=auth.pharmacy_id,
        days_ahead=input.days_ahead,
        count=len(items),
        items=items,
    )


@registry.tool(
    name="get_sales_summary",
    description=(
        "Read a summary of sales for the authenticated pharmacy and inclusive date "
        "range. Reports completed revenue separately from pending, cancelled and "
        "refunded transaction counts. Does not initiate refunds or alter payments."
    ),
    input_schema=SalesSummaryRequest,
    output_schema=SalesSummaryResult,
    category="pharmacy_sales",
    requires_db=True,
    tags=["pharmacy", "sales", "pos", "revenue", "read"],
)
async def get_sales_summary(input: SalesSummaryRequest) -> SalesSummaryResult:
    auth = require_mcp_context()
    from src.pharmaviyum.shared.core.database import async_session_factory

    start = datetime.combine(input.start_date, time.min)
    end_exclusive = datetime.combine(input.end_date + timedelta(days=1), time.min)
    statement = (
        select(
            Sale.status,
            func.count(Sale.id),
            func.coalesce(func.sum(Sale.total), 0),
        )
        .where(
            Sale.pharmacy_id == auth.pharmacy_id,
            Sale.created_at >= start,
            Sale.created_at < end_exclusive,
        )
        .group_by(Sale.status)
    )
    async with async_session_factory() as session:
        rows = (await session.execute(statement)).all()

    counts = {str(status): int(count) for status, count, _ in rows}
    completed_revenue = sum(
        (Decimal(str(total or 0)) for status, _, total in rows if status == "completed"),
        Decimal("0.00"),
    )
    return SalesSummaryResult(
        pharmacy_id=auth.pharmacy_id,
        start_date=input.start_date,
        end_date=input.end_date,
        completed_sales=counts.get("completed", 0),
        revenue=completed_revenue,
        pending_sales=counts.get("awaiting_payment", 0),
        cancelled_sales=counts.get("cancelled", 0),
        refunded_sales=counts.get("refunded", 0),
    )
