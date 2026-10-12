"""Tenant-aware operational metrics for the pharmacy dashboard."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import case, func, select

from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.order import Order
from src.pharmaviyum.models.patients import Patient, PatientPurchase
from src.pharmaviyum.models.patients.patient_condition import PatientCondition
from src.pharmaviyum.models.prescription import Prescription
from src.pharmaviyum.models.product import Product
from src.pharmaviyum.models.product_batch import ProductBatch
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
        .group_by(sales_category_expression)
    )

    inventory_stock_query = select(
        Inventory.product_id,
        func.coalesce(
            func.sum(Inventory.quantity - Inventory.reserved_quantity), 0
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
        .outerjoin(
            inventory_stock_subquery,
            inventory_stock_subquery.c.product_id == Product.id,
        )
        .group_by(Product.id, Product.name, inventory_stock_subquery.c.stock)
        .order_by(func.sum(PatientPurchase.dispensed_packs).desc())
        .limit(10)
    )

    patient_purchase_query = (
        select(
            Patient.id,
            Patient.full_name,
            func.count(PatientPurchase.id).label("lines"),
            func.coalesce(func.sum(PatientPurchase.dispensed_packs), 0).label("packs"),
            func.coalesce(
                func.sum(PatientPurchase.quantity * PatientPurchase.unit_price), 0
            ).label("revenue"),
        )
        .join(PatientPurchase, PatientPurchase.patient_id == Patient.id)
        .group_by(Patient.id, Patient.full_name)
        .order_by(Patient.id)
        .limit(20)
    )

    expiry_query = select(
        func.count(Inventory.id)
        .filter(Inventory.expires_at.is_not(None))
        .label("tracked"),
        func.coalesce(
            func.sum(
                case(
                    (
                        Inventory.expires_at.is_not(None)
                        & (
                            func.date_trunc("month", Inventory.expires_at)
                            < current_month_start
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("expired"),
        func.coalesce(
            func.sum(
                case(
                    (
                        Inventory.expires_at.is_not(None)
                        & (
                            func.date_trunc("month", Inventory.expires_at)
                            >= current_month_start
                        )
                        & (
                            func.date_trunc("month", Inventory.expires_at)
                            <= red_cutoff_month
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("critical"),
        func.coalesce(
            func.sum(
                case(
                    (
                        Inventory.expires_at.is_not(None)
                        & (
                            func.date_trunc("month", Inventory.expires_at)
                            > red_cutoff_month
                        )
                        & (
                            func.date_trunc("month", Inventory.expires_at)
                            <= yellow_cutoff_month
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("warning"),
        func.coalesce(
            func.sum(
                case(
                    (
                        Inventory.expires_at.is_not(None)
                        & (
                            func.date_trunc("month", Inventory.expires_at)
                            > yellow_cutoff_month
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("extended_warning"),
    )

    if scope is not None:
        sales_category_query = sales_category_query.where(Patient.pharmacy_id == scope)
        top_products_query = top_products_query.where(Patient.pharmacy_id == scope)
        patient_purchase_query = patient_purchase_query.where(
            Patient.pharmacy_id == scope
        )
        expiry_query = expiry_query.where(Inventory.pharmacy_id == scope)

    sales_kpi = (await session.execute(sales_kpi_query)).one()
    order_kpi = (await session.execute(order_kpi_query)).one()
    prescription_kpi = (await session.execute(prescription_kpi_query)).one()
    patient_kpi = (await session.execute(patient_kpi_query)).one()

    sales_category = (await session.execute(sales_category_query)).all()
    top_products = (await session.execute(top_products_query)).all()
    patient_purchases = (await session.execute(patient_purchase_query)).all()

    latest_condition_subquery = select(
        PatientCondition.patient_id,
        PatientCondition.condition_name,
        func.row_number()
        .over(
            partition_by=PatientCondition.patient_id,
            order_by=(
                case(
                    (PatientCondition.status == "active", 0),
                    else_=1,
                ),
                PatientCondition.updated_at.desc(),
                PatientCondition.id.desc(),
            ),
        )
        .label("condition_rank"),
    ).subquery()

    dashboard_patient_ids = (
        select(Patient.id)
        .join(PatientPurchase, PatientPurchase.patient_id == Patient.id)
        .group_by(Patient.id)
        .order_by(Patient.id)
        .limit(20)
    )
    if scope is not None:
        dashboard_patient_ids = dashboard_patient_ids.where(
            Patient.pharmacy_id == scope
        )

    patient_medication_query = (
        select(
            Patient.id.label("patient_id"),
            Patient.full_name.label("patient_name"),
            PatientPurchase.id.label("purchase_id"),
            latest_condition_subquery.c.condition_name.label("condition"),
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            Product.dosage_strength,
            Product.dosage_form,
            Product.units_per_pack,
            PatientPurchase.dispensed_packs,
            PatientPurchase.unit_price,
            PatientPurchase.quantity,
            PatientPurchase.prescription_required,
            ProductBatch.expiry_date,
            case(
                (
                    func.lower(func.coalesce(Product.description, "")).like(
                        "%generic%"
                    ),
                    "Generic",
                ),
                (
                    func.lower(func.coalesce(Product.description, "")).like(
                        "%reference%"
                    ),
                    "Original",
                ),
                (
                    func.lower(func.coalesce(Product.description, "")).like(
                        "%original%"
                    ),
                    "Original",
                ),
                else_="Unclassified",
            ).label("product_type"),
        )
        .join(PatientPurchase, PatientPurchase.patient_id == Patient.id)
        .join(Product, Product.id == PatientPurchase.product_id)
        .outerjoin(ProductBatch, ProductBatch.id == PatientPurchase.batch_id)
        .outerjoin(
            latest_condition_subquery,
            (latest_condition_subquery.c.patient_id == Patient.id)
            & (latest_condition_subquery.c.condition_rank == 1),
        )
        .order_by(Patient.id, PatientPurchase.id)
    )
    patient_medication_query = patient_medication_query.where(
        Patient.id.in_(dashboard_patient_ids)
    )
    medication_rows = (await session.execute(patient_medication_query)).all()
    patient_medications: dict[int, dict] = {}
    for row in medication_rows:
        patient = patient_medications.setdefault(
            row.patient_id,
            {
                "patient_id": row.patient_id,
                "patient_name": row.patient_name,
                "condition": row.condition,
                "medications": [],
            },
        )
        if patient["condition"] is None and row.condition:
            patient["condition"] = row.condition
        patient["medications"].append(
            {
                "purchase_id": row.purchase_id,
                "product_id": row.product_id,
                "name": row.product_name,
                "dosage": row.dosage_strength,
                "form": row.dosage_form,
                "pack_size": int(row.units_per_pack or 0),
                "packs": int(row.dispensed_packs or 0),
                "amount": round(float((row.quantity or 0) * (row.unit_price or 0)), 2),
                "prescription_required": bool(row.prescription_required),
                "type": row.product_type,
                "expiry_date": row.expiry_date.isoformat() if row.expiry_date else None,
            }
        )

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
    available_packs_query = (
        select(
            func.coalesce(
                func.sum(
                    (Inventory.quantity - Inventory.reserved_quantity)
                    / func.nullif(Product.units_per_pack, 0)
                ),
                0,
            )
        )
        .select_from(Inventory)
        .join(Product, Product.id == Inventory.product_id)
    )
    if scope is not None:
        available_packs_query = available_packs_query.where(
            Inventory.pharmacy_id == scope
        )
    available_packs = float(
        (await session.execute(available_packs_query)).scalar_one() or 0
    )
    daily_packs = float(demand_30d) / 30.0
    days_on_hand = round(available_packs / daily_packs, 1) if daily_packs > 0 else None

    attention_query = (
        select(
            func.count(func.distinct(Inventory.product_id))
            .filter((Inventory.quantity - Inventory.reserved_quantity) <= 0)
            .label("stockout_items"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            Inventory.expires_at.is_not(None)
                            & (Inventory.expires_at >= today_start)
                            & (
                                func.date_trunc("month", Inventory.expires_at)
                                <= yellow_cutoff_month
                            ),
                            (Inventory.quantity - Inventory.reserved_quantity)
                            * Product.price,
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
                func.sum(Inventory.quantity - Inventory.reserved_quantity), 0
            ).label("available_units"),
            func.coalesce(product_demand_30d.c.packs_30d, 0).label("packs_30d"),
            func.coalesce(
                func.sum(
                    (Inventory.quantity - Inventory.reserved_quantity) * Product.price
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

    slow_moving_query = (
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
        .order_by(
            func.sum(
                (Inventory.quantity - Inventory.reserved_quantity) * Product.price
            ).desc()
        )
        .limit(5)
    )
    if scope is not None:
        slow_moving_query = slow_moving_query.where(Inventory.pharmacy_id == scope)

    attention = (await session.execute(attention_query)).one()
    slow_moving = (await session.execute(slow_moving_query)).all()

    return {
        "as_of": now.isoformat(),
        "patients": {
            "active": int(patient_kpi.active_patients or 0),
        },
        "sales": {
            "today": round(float(sales_kpi.today_sales or 0), 2),
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
        "patient_purchases": [
            {
                "patient_id": row.id,
                "patient_name": row.full_name,
                "lines": int(row.lines or 0),
                "packs": int(row.packs or 0),
                "revenue": round(float(row.revenue or 0), 2),
            }
            for row in patient_purchases
        ],
        "patient_medications": list(patient_medications.values())[:20],
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
                "reorder_level": int(row.reorder_level or 0),
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
            "stockout_items": int(attention.stockout_items or 0),
            "near_expiry_value": round(float(attention.near_expiry_value or 0), 2),
            "slow_moving_items": len(slow_moving),
            "slow_moving_stock_value": round(
                sum(float(row.stock_value or 0) for row in slow_moving), 2
            ),
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
