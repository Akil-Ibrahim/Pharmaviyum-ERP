"""Tenant-aware operational metrics for the pharmacy dashboard."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import case, func, select

from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.order import Order
from src.pharmaviyum.models.patients import Patient, PatientPurchase
from src.pharmaviyum.models.prescription import Prescription
from src.pharmaviyum.models.product import Product
from src.pharmaviyum.models.product_batch import ProductBatch
from src.pharmaviyum.models.patients.patient_condition import PatientCondition
from src.pharmaviyum.modules.auth.deps import CurrentUser, SessionDep
from src.pharmaviyum.modules.auth.tenant import resolve_pharmacy_scope

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


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

    today_sales = await session.scalar(
        purchase_base.with_only_columns(
            func.coalesce(
                func.sum(PatientPurchase.quantity * PatientPurchase.unit_price),
                0,
            )
        ).where(
            PatientPurchase.purchased_at >= today_start,
            PatientPurchase.purchased_at < tomorrow_start,
        )
    )

    month_revenue = await session.scalar(
        purchase_base.with_only_columns(
            func.coalesce(
                func.sum(PatientPurchase.quantity * PatientPurchase.unit_price),
                0,
            )
        ).where(PatientPurchase.purchased_at >= month_start)
    )

    month_orders = await session.scalar(
        order_base.with_only_columns(func.count(Order.id)).where(
            Order.created_at >= month_start
        )
    )

    month_completed_orders = await session.scalar(
        order_base.with_only_columns(func.count(Order.id)).where(
            Order.created_at >= month_start,
            Order.status == "completed",
        )
    )

    month_prescriptions = await session.scalar(
        prescription_base.with_only_columns(func.count(Prescription.id)).where(
            Prescription.created_at >= month_start
        )
    )

    active_patients = await session.scalar(
        select(func.count(Patient.id)).where(
            Patient.is_active.is_(True),
            Patient.id.in_(patient_scope),
        )
    )

    sales_category_query = (
        select(
            case(
                (PatientPurchase.prescription_required.is_(True), "Rx"), else_="OTC"
            ).label("category"),
            func.count(PatientPurchase.id).label("lines"),
            func.coalesce(func.sum(PatientPurchase.dispensed_packs), 0).label("packs"),
            func.coalesce(
                func.sum(PatientPurchase.quantity * PatientPurchase.unit_price), 0
            ).label("revenue"),
        )
        .join(Patient, Patient.id == PatientPurchase.patient_id)
        .group_by(
            case((PatientPurchase.prescription_required.is_(True), "Rx"), else_="OTC")
        )
    )

    inventory_stock_subquery = (
        select(
            func.coalesce(func.sum(Inventory.quantity - Inventory.reserved_quantity), 0)
        )
        .where(Inventory.product_id == Product.id)
        .correlate(Product)
        .scalar_subquery()
    )

    if scope is not None:
        inventory_stock_subquery = inventory_stock_subquery.where(
            Inventory.pharmacy_id == scope
        )

    top_products_query = (
        select(
            Product.id,
            Product.name,
            func.coalesce(func.sum(PatientPurchase.dispensed_packs), 0).label("packs"),
            func.coalesce(
                func.sum(PatientPurchase.quantity * PatientPurchase.unit_price), 0
            ).label("revenue"),
            inventory_stock_subquery.label("stock"),
        )
        .join(PatientPurchase, PatientPurchase.product_id == Product.id)
        .join(Patient, Patient.id == PatientPurchase.patient_id)
        .group_by(Product.id, Product.name)
        .order_by(func.sum(PatientPurchase.dispensed_packs).desc())
        .limit(10)
    )

    original_generic_query = (
        select(
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
            ).label("type"),
            func.count(PatientPurchase.id).label("lines"),
            func.coalesce(
                func.sum(PatientPurchase.quantity * PatientPurchase.unit_price), 0
            ).label("revenue"),
        )
        .join(PatientPurchase, PatientPurchase.product_id == Product.id)
        .join(Patient, Patient.id == PatientPurchase.patient_id)
        .group_by(
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
            )
        )
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

    inventory_query = select(
        func.coalesce(
            func.sum(
                (Inventory.quantity - Inventory.reserved_quantity) * Product.price
            ),
            0,
        )
    ).join(Product, Product.id == Inventory.product_id)
    inventory_items_query = select(func.count(Inventory.id))
    low_stock_query = select(func.count(Inventory.id)).where(
        Inventory.quantity - Inventory.reserved_quantity <= Inventory.reorder_level
    )
    expiry_query = select(
        func.count(Inventory.id)
        .where(Inventory.expires_at.is_not(None))
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
        original_generic_query = original_generic_query.where(
            Patient.pharmacy_id == scope
        )
        patient_purchase_query = patient_purchase_query.where(
            Patient.pharmacy_id == scope
        )
        inventory_query = inventory_query.where(Inventory.pharmacy_id == scope)
        inventory_items_query = inventory_items_query.where(Inventory.pharmacy_id == scope)
        low_stock_query = low_stock_query.where(Inventory.pharmacy_id == scope)
        expiry_query = expiry_query.where(Inventory.pharmacy_id == scope)

    sales_category = (await session.execute(sales_category_query)).all()
    top_products = (await session.execute(top_products_query)).all()
    original_generic = (await session.execute(original_generic_query)).all()
    patient_purchases = (await session.execute(patient_purchase_query)).all()

    latest_condition_subquery = (
        select(
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
        )
        .subquery()
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
                    func.lower(func.coalesce(Product.description, "")).like("%generic%"),
                    "Generic",
                ),
                (
                    func.lower(func.coalesce(Product.description, "")).like("%reference%"),
                    "Original",
                ),
                (
                    func.lower(func.coalesce(Product.description, "")).like("%original%"),
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
    if scope is not None:
        patient_medication_query = patient_medication_query.where(
            Patient.pharmacy_id == scope
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

    inventory_value = await session.scalar(inventory_query)
    inventory_items = await session.scalar(inventory_items_query)
    low_stock = await session.scalar(low_stock_query)
    expiry = (await session.execute(expiry_query)).one()

    return {
        "as_of": now.isoformat(),
        "patients": {
            "active": int(active_patients or 0),
        },
        "sales": {
            "today": round(float(today_sales or 0), 2),
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
        "original_vs_generic": [
            {
                "type": row.type,
                "lines": int(row.lines or 0),
                "revenue": round(float(row.revenue or 0), 2),
            }
            for row in original_generic
        ],
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
            "month": round(float(month_revenue or 0), 2),
        },
        "orders": {
            "month": int(month_orders or 0),
            "completed_month": int(month_completed_orders or 0),
        },
        "prescriptions": {
            "month": int(month_prescriptions or 0),
        },
        "inventory": {
            "retail_value": round(float(inventory_value or 0), 2),
            "items": int(inventory_items or 0),
            "low_stock": int(low_stock or 0),
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
