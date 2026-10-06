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
        func.count(Order.id).filter(Order.created_at >= month_start).label("month_orders"),
        func.count(Order.id).filter(
            (Order.created_at >= month_start) & (Order.status == "completed")
        ).label("month_completed_orders"),
    )

    prescription_kpi_query = prescription_base.with_only_columns(
        func.count(Prescription.id).filter(
            Prescription.created_at >= month_start
        ).label("month_prescriptions")
    )

    patient_kpi_query = select(
        func.count(Patient.id).filter(Patient.is_active.is_(True)).label("active_patients")
    ).where(Patient.id.in_(patient_scope))


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

    inventory_stock_query = (
        select(
            Inventory.product_id,
            func.coalesce(
                func.sum(Inventory.quantity - Inventory.reserved_quantity), 0
            ).label("stock"),
        )
        .group_by(Inventory.product_id)
    )
    if scope is not None:
        inventory_stock_query = inventory_stock_query.where(Inventory.pharmacy_id == scope)

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

    dashboard_patient_ids = (
        select(Patient.id)
        .join(PatientPurchase, PatientPurchase.patient_id == Patient.id)
        .group_by(Patient.id)
        .order_by(Patient.id)
        .limit(20)
    )
    if scope is not None:
        dashboard_patient_ids = dashboard_patient_ids.where(Patient.pharmacy_id == scope)

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
        "inventory": {
            "retail_value": round(float(inventory_kpi.retail_value or 0), 2),
            "items": int(inventory_kpi.items or 0),
            "low_stock": int(inventory_kpi.low_stock or 0),
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
