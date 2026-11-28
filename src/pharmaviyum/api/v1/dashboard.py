"""Tenant-aware operational metrics for the pharmacy dashboard."""

from datetime import datetime, timedelta
from statistics import median

from fastapi import APIRouter, Query
from sqlalchemy import case, func, select

from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.order import Order
from src.pharmaviyum.models.patients import Patient, PatientPurchase
from src.pharmaviyum.models.prescription import Prescription
from src.pharmaviyum.models.product import Product
from src.pharmaviyum.modules.auth.deps import CurrentUser, SessionDep
from src.pharmaviyum.modules.auth.tenant import resolve_pharmacy_scope

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get("/summary")
async def get_dashboard_summary(
    current_user: CurrentUser,
    session: SessionDep,
    pharmacy_id: int | None = Query(default=None, gt=0),
) -> dict:
    """Return the minimum real operational metrics needed by the dashboard.

    Revenue is sourced from PatientPurchase, the canonical realized-sales
    ledger. Pending orders are deliberately excluded from revenue.
    """

    scope = await resolve_pharmacy_scope(pharmacy_id, current_user, session)
    now = datetime.utcnow()
    today = now.date()
    today_start = datetime.combine(today, datetime.min.time())
    tomorrow_start = today_start + timedelta(days=1)
    month_start = today_start.replace(day=1)
    # Expiry policy is month-based in the dashboard UI:
    # <= 3 months = red, 4-12 months = yellow, > 12 months = green.
    current_month_start = today_start.replace(day=1)

    def month_start_after(months: int) -> datetime:
        total = current_month_start.year * 12 + current_month_start.month - 1 + months
        year, month_index = divmod(total, 12)
        return current_month_start.replace(year=year, month=month_index + 1)

    red_cutoff_month = month_start_after(3)
    yellow_cutoff_month = month_start_after(12)
    slow_moving_cutoff = now - timedelta(days=90)

    patient_scope = select(Patient.id)
    if scope is not None:
        patient_scope = patient_scope.where(Patient.pharmacy_id == scope)

    purchase_base = select(PatientPurchase).join(
        Patient, Patient.id == PatientPurchase.patient_id
    )
    order_base = select(Order).join(Patient, Patient.id == Order.patient_id)
    prescription_base = select(Prescription).join(
        Patient, Patient.id == Prescription.patient_id
    )

    if scope is not None:
        purchase_base = purchase_base.where(Patient.pharmacy_id == scope)
        order_base = order_base.where(Patient.pharmacy_id == scope)
        prescription_base = prescription_base.where(Patient.pharmacy_id == scope)

    # A rolling 30-day comparison avoids partial-month bias. Receipts are
    # counted distinctly because PatientPurchase stores one row per receipt line.
    period_30d_start = now - timedelta(days=30)
    previous_30d_start = now - timedelta(days=60)
    sales_period_query = purchase_base.with_only_columns(
        func.coalesce(
            func.sum(
                case(
                    (
                        PatientPurchase.purchased_at >= period_30d_start,
                        PatientPurchase.quantity * PatientPurchase.unit_price,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("revenue_30d"),
        func.coalesce(
            func.sum(
                case(
                    (
                        (PatientPurchase.purchased_at >= previous_30d_start)
                        & (PatientPurchase.purchased_at < period_30d_start),
                        PatientPurchase.quantity * PatientPurchase.unit_price,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("previous_revenue_30d"),
        func.count(
            func.distinct(
                case(
                    (
                        PatientPurchase.purchased_at >= period_30d_start,
                        PatientPurchase.receipt_number,
                    ),
                    else_=None,
                )
            )
        ).label("orders_30d"),
    )

    daily_revenue_query = (
        select(
            func.date_trunc("day", PatientPurchase.purchased_at).label("day"),
            func.coalesce(
                func.sum(PatientPurchase.quantity * PatientPurchase.unit_price), 0
            ).label("revenue"),
        )
        .join(Patient, Patient.id == PatientPurchase.patient_id)
        .where(PatientPurchase.purchased_at >= period_30d_start)
        .group_by(func.date_trunc("day", PatientPurchase.purchased_at))
        .order_by(func.date_trunc("day", PatientPurchase.purchased_at))
    )

    sales_kpi_query = purchase_base.with_only_columns(
        func.coalesce(
            func.sum(
                case(
                    (
                        (PatientPurchase.purchased_at >= today_start)
                        & (PatientPurchase.purchased_at < tomorrow_start),
                        PatientPurchase.quantity * PatientPurchase.unit_price,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("today_sales"),
        func.coalesce(
            func.sum(
                case(
                    (
                        PatientPurchase.purchased_at >= month_start,
                        PatientPurchase.quantity * PatientPurchase.unit_price,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("month_revenue"),
    )

    order_kpi_query = order_base.with_only_columns(
        func.count(Order.id)
        .filter(Order.created_at >= month_start)
        .label("month_orders"),
        func.count(Order.id)
        .filter((Order.created_at >= month_start) & (Order.status == "completed"))
        .label("month_completed_orders"),
    )

    prescription_kpi_query = prescription_base.with_only_columns(
        func.count(Prescription.id)
        .filter(Prescription.created_at >= month_start)
        .label("month_prescriptions")
    )

    patient_kpi_query = select(
        func.count(Patient.id)
        .filter(Patient.is_active.is_(True))
        .label("active_patients")
    ).where(Patient.id.in_(patient_scope))

    sales_category_expression = case(
        (PatientPurchase.prescription_required.is_(True), "Rx"), else_="OTC"
    )
    sales_category_query = (
        select(
            sales_category_expression.label("category"),
            func.count(PatientPurchase.id).label("lines"),
            func.coalesce(func.sum(PatientPurchase.dispensed_packs), 0).label("packs"),
            func.coalesce(
                func.sum(PatientPurchase.quantity * PatientPurchase.unit_price), 0
            ).label("revenue"),
        )
        .join(Patient, Patient.id == PatientPurchase.patient_id)
        .where(PatientPurchase.purchased_at >= month_start)
        .group_by(sales_category_expression)
    )

    inventory_stock_query = select(
        Inventory.product_id,
        func.coalesce(
            func.sum(
                case(
                    (
                        Inventory.expires_at.is_(None)
                        | (Inventory.expires_at >= today_start),
                        Inventory.quantity - Inventory.reserved_quantity,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("stock"),
    ).group_by(Inventory.product_id)
    if scope is not None:
        inventory_stock_query = inventory_stock_query.where(
            Inventory.pharmacy_id == scope
        )

    inventory_stock_subquery = inventory_stock_query.subquery()

    top_products_query = (
        select(
            Product.id,
            Product.name,
            func.coalesce(func.sum(PatientPurchase.dispensed_packs), 0).label("packs"),
            func.coalesce(
                func.sum(PatientPurchase.quantity * PatientPurchase.unit_price), 0
            ).label("revenue"),
            func.coalesce(inventory_stock_subquery.c.stock, 0).label("stock"),
        )
        .join(PatientPurchase, PatientPurchase.product_id == Product.id)
        .join(Patient, Patient.id == PatientPurchase.patient_id)
        .where(PatientPurchase.purchased_at >= month_start)
        .outerjoin(
            inventory_stock_subquery,
            inventory_stock_subquery.c.product_id == Product.id,
        )
        .group_by(Product.id, Product.name, inventory_stock_subquery.c.stock)
        .order_by(func.sum(PatientPurchase.dispensed_packs).desc())
        .limit(10)
    )

    available_units = Inventory.quantity - Inventory.reserved_quantity
    has_available_stock = available_units > 0
    expiry_query = select(
        func.count(Inventory.id)
        .filter(Inventory.expires_at.is_not(None) & has_available_stock)
        .label("tracked"),
        func.count(Inventory.id)
        .filter(
            Inventory.expires_at.is_not(None)
            & (Inventory.expires_at < today_start)
            & has_available_stock
        )
        .label("expired"),
        func.count(Inventory.id)
        .filter(
            Inventory.expires_at.is_not(None)
            & (Inventory.expires_at >= today_start)
            & (Inventory.expires_at <= red_cutoff_month)
            & has_available_stock
        )
        .label("critical"),
        func.count(Inventory.id)
        .filter(
            Inventory.expires_at.is_not(None)
            & (Inventory.expires_at > red_cutoff_month)
            & (Inventory.expires_at <= yellow_cutoff_month)
            & has_available_stock
        )
        .label("warning"),
        func.count(Inventory.id)
        .filter(
            Inventory.expires_at.is_not(None)
            & (Inventory.expires_at > yellow_cutoff_month)
            & has_available_stock
        )
        .label("extended_warning"),
    )

    if scope is not None:
        sales_category_query = sales_category_query.where(Patient.pharmacy_id == scope)
        top_products_query = top_products_query.where(Patient.pharmacy_id == scope)
        expiry_query = expiry_query.where(Inventory.pharmacy_id == scope)

    if scope is not None:
        daily_revenue_query = daily_revenue_query.where(Patient.pharmacy_id == scope)

    sales_kpi = (await session.execute(sales_kpi_query)).one()
    sales_period = (await session.execute(sales_period_query)).one()
    daily_revenue = (await session.execute(daily_revenue_query)).all()
    order_kpi = (await session.execute(order_kpi_query)).one()
    prescription_kpi = (await session.execute(prescription_kpi_query)).one()
    patient_kpi = (await session.execute(patient_kpi_query)).one()

    sales_category = (await session.execute(sales_category_query)).all()
    top_products = (await session.execute(top_products_query)).all()

    inventory_kpi_query = (
        select(
            func.coalesce(
                func.sum(
                    (Inventory.quantity - Inventory.reserved_quantity) * Product.price
                ),
                0,
            ).label("retail_value"),
            func.count(Inventory.id).label("items"),
            func.count(Inventory.id)
            .filter(
                Inventory.quantity - Inventory.reserved_quantity
                <= Inventory.reorder_level
            )
            .label("low_stock"),
        )
        .select_from(Inventory)
        .join(Product, Product.id == Inventory.product_id)
    )
    if scope is not None:
        inventory_kpi_query = inventory_kpi_query.where(Inventory.pharmacy_id == scope)

    inventory_kpi = (await session.execute(inventory_kpi_query)).one()
    expiry = (await session.execute(expiry_query)).one()

    # Inventory runway: compare current available stock with the last 30 days
    # of realized dispensing. We intentionally do not calculate inventory
    # turnover here because Product has no cost-of-goods field yet.
    demand_30d_query = (
        select(
            func.coalesce(func.sum(PatientPurchase.dispensed_packs), 0).label(
                "packs_30d"
            )
        )
        .join(Patient, Patient.id == PatientPurchase.patient_id)
        .where(PatientPurchase.purchased_at >= now - timedelta(days=30))
    )
    if scope is not None:
        demand_30d_query = demand_30d_query.where(Patient.pharmacy_id == scope)

    demand_30d = (await session.execute(demand_30d_query)).scalar_one() or 0
    expired_value_query = (
        select(
            func.coalesce(
                func.sum(
                    (Inventory.quantity - Inventory.reserved_quantity) * Product.price
                ),
                0,
            )
        )
        .select_from(Inventory)
        .join(Product, Product.id == Inventory.product_id)
        .where(
            Inventory.expires_at.is_not(None),
            Inventory.expires_at < today_start,
            (Inventory.quantity - Inventory.reserved_quantity) > 0,
        )
    )
    if scope is not None:
        expired_value_query = expired_value_query.where(Inventory.pharmacy_id == scope)
    expired_value = (await session.execute(expired_value_query)).scalar_one() or 0

    # Aggregate packs rather than raw units so runway is comparable with
    # dispensed_packs. Products without a valid pack size are ignored.
    # Determine stockout at product level across all lots. An empty lot must
    # not mark a medicine out of stock when another unexpired lot is available.
    stockout_stock_expression = case(
        (
            Inventory.expires_at.is_(None) | (Inventory.expires_at >= today_start),
            available_units,
        ),
        else_=0,
    )
    stockout_products_query = (
        select(Inventory.product_id)
        .group_by(Inventory.product_id)
        .having(func.sum(stockout_stock_expression) <= 0)
    )
    if scope is not None:
        stockout_products_query = stockout_products_query.where(
            Inventory.pharmacy_id == scope
        )
    stockout_products = stockout_products_query.subquery()
    stockout_count_query = select(func.count()).select_from(stockout_products)

    attention_query = (
        select(
            func.coalesce(
                func.sum(
                    case(
                        (
                            Inventory.expires_at.is_not(None)
                            & (Inventory.expires_at >= today_start)
                            & (Inventory.expires_at <= yellow_cutoff_month)
                            & has_available_stock,
                            available_units * Product.price,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("near_expiry_value"),
        )
        .select_from(Inventory)
        .join(Product, Product.id == Inventory.product_id)
    )
    if scope is not None:
        attention_query = attention_query.where(Inventory.pharmacy_id == scope)

    recent_sales_query = (
        select(
            PatientPurchase.product_id.label("product_id"),
            func.coalesce(func.sum(PatientPurchase.dispensed_packs), 0).label(
                "recent_packs"
            ),
        )
        .join(Patient, Patient.id == PatientPurchase.patient_id)
        .where(PatientPurchase.purchased_at >= slow_moving_cutoff)
        .group_by(PatientPurchase.product_id)
    )
    if scope is not None:
        recent_sales_query = recent_sales_query.where(Patient.pharmacy_id == scope)
    recent_sales = recent_sales_query.subquery()

    # Procurement attention: products approaching their configured reorder level.
    # We use realized 30-day dispensing to estimate runway, without inventing supplier lead times.
    product_demand_30d_query = (
        select(
            PatientPurchase.product_id.label("product_id"),
            func.coalesce(func.sum(PatientPurchase.dispensed_packs), 0).label(
                "packs_30d"
            ),
        )
        .join(Patient, Patient.id == PatientPurchase.patient_id)
        .where(PatientPurchase.purchased_at >= now - timedelta(days=30))
        .group_by(PatientPurchase.product_id)
    )
    if scope is not None:
        product_demand_30d_query = product_demand_30d_query.where(
            Patient.pharmacy_id == scope
        )
    product_demand_30d = product_demand_30d_query.subquery()

    reorder_attention_query = (
        select(
            Product.id,
            Product.name,
            Product.units_per_pack,
            func.max(Inventory.reorder_level).label("reorder_level"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            Inventory.expires_at.is_(None)
                            | (Inventory.expires_at >= today_start),
                            Inventory.quantity - Inventory.reserved_quantity,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("available_units"),
            func.coalesce(product_demand_30d.c.packs_30d, 0).label("packs_30d"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            Inventory.expires_at.is_(None)
                            | (Inventory.expires_at >= today_start),
                            (Inventory.quantity - Inventory.reserved_quantity)
                            * Product.price,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("stock_value"),
        )
        .select_from(Product)
        .join(Inventory, Inventory.product_id == Product.id)
        .outerjoin(product_demand_30d, product_demand_30d.c.product_id == Product.id)
        .group_by(
            Product.id,
            Product.name,
            Product.units_per_pack,
            product_demand_30d.c.packs_30d,
        )
        .having(
            func.sum(Inventory.quantity - Inventory.reserved_quantity)
            <= func.max(Inventory.reorder_level)
        )
        .order_by(
            func.sum(Inventory.quantity - Inventory.reserved_quantity).asc(),
            product_demand_30d.c.packs_30d.desc(),
        )
        .limit(5)
    )
    if scope is not None:
        reorder_attention_query = reorder_attention_query.where(
            Inventory.pharmacy_id == scope
        )

    slow_moving_base_query = (
        select(
            Product.id,
            Product.name,
            func.coalesce(recent_sales.c.recent_packs, 0).label("recent_packs"),
            func.coalesce(
                func.sum(Inventory.quantity - Inventory.reserved_quantity), 0
            ).label("stock"),
            func.coalesce(
                func.sum(
                    (Inventory.quantity - Inventory.reserved_quantity) * Product.price
                ),
                0,
            ).label("stock_value"),
        )
        .select_from(Product)
        .join(Inventory, Inventory.product_id == Product.id)
        .outerjoin(recent_sales, recent_sales.c.product_id == Product.id)
        .group_by(Product.id, Product.name, recent_sales.c.recent_packs)
        .having(func.coalesce(recent_sales.c.recent_packs, 0) == 0)
    )
    if scope is not None:
        slow_moving_base_query = slow_moving_base_query.where(
            Inventory.pharmacy_id == scope
        )
    slow_moving_subquery = slow_moving_base_query.subquery()
    slow_moving_summary_query = select(
        func.count(slow_moving_subquery.c.id).label("item_count"),
        func.coalesce(func.sum(slow_moving_subquery.c.stock_value), 0).label(
            "stock_value"
        ),
    )
    slow_moving_query = (
        select(slow_moving_subquery)
        .order_by(slow_moving_subquery.c.stock_value.desc())
        .limit(5)
    )

    # Days of stock is calculated per SKU first, then summarized as the median.
    # Summing packs across unrelated medicines would produce a misleading KPI.
    sku_coverage_query = (
        select(
            Product.units_per_pack.label("units_per_pack"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            Inventory.expires_at.is_(None)
                            | (Inventory.expires_at >= today_start),
                            available_units,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("available_units"),
            func.coalesce(product_demand_30d.c.packs_30d, 0).label("packs_30d"),
        )
        .select_from(Product)
        .join(Inventory, Inventory.product_id == Product.id)
        .outerjoin(
            product_demand_30d,
            product_demand_30d.c.product_id == Product.id,
        )
        .group_by(
            Product.id,
            Product.units_per_pack,
            product_demand_30d.c.packs_30d,
        )
        .having(func.coalesce(product_demand_30d.c.packs_30d, 0) > 0)
    )
    if scope is not None:
        sku_coverage_query = sku_coverage_query.where(
            Inventory.pharmacy_id == scope
        )
    coverage_rows = (await session.execute(sku_coverage_query)).all()
    sku_days_on_hand = [
        (float(row.available_units or 0) / float(row.units_per_pack))
        / (float(row.packs_30d) / 30.0)
        for row in coverage_rows
        if row.units_per_pack and row.packs_30d and row.available_units > 0
    ]
    days_on_hand = round(median(sku_days_on_hand), 1) if sku_days_on_hand else None

    attention = (await session.execute(attention_query)).one()
    stockout_items = (await session.execute(stockout_count_query)).scalar_one()
    slow_moving_summary = (await session.execute(slow_moving_summary_query)).one()
    slow_moving = (await session.execute(slow_moving_query)).all()

    return {
        "as_of": f"{now.isoformat()}Z",
        "patients": {
            "active": int(patient_kpi.active_patients or 0),
        },
        "sales": {
            "today": round(float(sales_kpi.today_sales or 0), 2),
            "revenue_30d": round(float(sales_period.revenue_30d or 0), 2),
            "previous_revenue_30d": round(
                float(sales_period.previous_revenue_30d or 0), 2
            ),
            "revenue_growth_30d": (
                round(
                    (
                        float(sales_period.revenue_30d or 0)
                        - float(sales_period.previous_revenue_30d or 0)
                    )
                    / float(sales_period.previous_revenue_30d)
                    * 100,
                    1,
                )
                if float(sales_period.previous_revenue_30d or 0) > 0
                else None
            ),
            "average_order_value_30d": (
                round(
                    float(sales_period.revenue_30d or 0)
                    / int(sales_period.orders_30d or 0),
                    2,
                )
                if int(sales_period.orders_30d or 0) > 0
                else 0
            ),
            "orders_30d": int(sales_period.orders_30d or 0),
            "daily_revenue": [
                {
                    "day": row.day.isoformat(),
                    "revenue": round(float(row.revenue or 0), 2),
                }
                for row in daily_revenue
            ],
            "by_category": [
                {
                    "category": row.category,
                    "lines": int(row.lines or 0),
                    "packs": int(row.packs or 0),
                    "revenue": round(float(row.revenue or 0), 2),
                }
                for row in sales_category
            ],
        },
        "top_products": [
            {
                "id": row.id,
                "name": row.name,
                "packs": int(row.packs or 0),
                "revenue": round(float(row.revenue or 0), 2),
                "stock": int(row.stock or 0),
            }
            for row in top_products
        ],
        "revenue": {
            "month": round(float(sales_kpi.month_revenue or 0), 2),
        },
        "orders": {
            "month": int(order_kpi.month_orders or 0),
            "completed_month": int(order_kpi.month_completed_orders or 0),
        },
        "prescriptions": {
            "month": int(prescription_kpi.month_prescriptions or 0),
        },
        "reorder_attention": [
            {
                "id": row.id,
                "name": row.name,
                "available_packs": round(
                    float(row.available_units or 0) / float(row.units_per_pack or 1), 1
                ),
                "reorder_level": round(
                    float(row.reorder_level or 0) / float(row.units_per_pack or 1), 1
                ),
                "packs_30d": int(row.packs_30d or 0),
                "days_on_hand": (
                    round(
                        (
                            float(row.available_units or 0)
                            / float(row.units_per_pack or 1)
                        )
                        / (float(row.packs_30d or 0) / 30.0),
                        1,
                    )
                    if row.packs_30d
                    else None
                ),
                "stock_value": round(float(row.stock_value or 0), 2),
            }
            for row in (await session.execute(reorder_attention_query)).all()
        ],
        "attention": {
            "stockout_items": int(stockout_items or 0),
            "near_expiry_value": round(float(attention.near_expiry_value or 0), 2),
            "slow_moving_items": int(slow_moving_summary.item_count or 0),
            "slow_moving_stock_value": round(
                float(slow_moving_summary.stock_value or 0), 2
            ),
            # Details are intentionally capped; headline count/value cover all matches.
            "slow_moving": [
                {
                    "id": row.id,
                    "name": row.name,
                    "packs_90d": int(row.recent_packs or 0),
                    "stock": int(row.stock or 0),
                    "stock_value": round(float(row.stock_value or 0), 2),
                }
                for row in slow_moving
            ],
        },
        "inventory": {
            "retail_value": round(float(inventory_kpi.retail_value or 0), 2),
            "items": int(inventory_kpi.items or 0),
            "low_stock": int(inventory_kpi.low_stock or 0),
            "days_on_hand": days_on_hand,
            "demand_30d_packs": int(demand_30d),
            "expired_value": round(float(expired_value), 2),
            "expiry_tracked": int(expiry.tracked or 0),
            "expired": int(expiry.expired or 0),
            "critical_expiry": int(expiry.critical or 0),
            "warning_expiry": int(expiry.warning or 0),
            "extended_expiry": int(expiry.extended_warning or 0),
            "expiry_red": int((expiry.expired or 0) + (expiry.critical or 0)),
            # The UI has exactly three mutually exclusive buckets:
            # red = expired/<=3 months, yellow = >3-12 months,
            # green = >12 months.
            "expiry_yellow": int(expiry.warning or 0),
            "expiry_green": int(expiry.extended_warning or 0),
        },
    }
