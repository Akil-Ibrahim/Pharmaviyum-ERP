"""End-to-end pharmacy stock workflow integration tests.

These tests use the PostgreSQL service configured by CI and exercise the real
procurement, FEFO POS, inventory ledger, and inter-pharmacy transfer paths.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from src.pharmaviyum.api.v1.pos import confirm_pos_transaction
from src.pharmaviyum.api.v1.procurement import (
    GoodsReceiptCreate,
    GoodsReceiptItemCreate,
    StockTransferCreate,
    StockTransferItemCreate,
    create_stock_transfer,
    receive_goods,
    receive_stock_transfer,
)
from src.pharmaviyum.database import AsyncSessionLocal
from src.pharmaviyum.models.audit_log import AuditLog
from src.pharmaviyum.models.dispensing import Dispensing
from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.inventory_transaction import InventoryTransaction
from src.pharmaviyum.models.order import Order
from src.pharmaviyum.models.order_item import OrderItem
from src.pharmaviyum.models.patients.patient import Patient
from src.pharmaviyum.models.patients.patient_purchase import PatientPurchase
from src.pharmaviyum.models.pharmacy import Pharmacy
from src.pharmaviyum.models.product import Product
from src.pharmaviyum.models.product_batch import ProductBatch
from src.pharmaviyum.models.supplier import Supplier
from src.pharmaviyum.models.user import User
from src.pharmaviyum.schemas.pos_schema import POSItem, POSTransactionCreate

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session", autouse=True)
def apply_migrations() -> None:
    """Apply the current migration head to the CI PostgreSQL database."""
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for integration tests")
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        env=os.environ.copy(),
    )


@pytest.mark.asyncio
async def test_receiving_fefo_dispensing_and_pharmacy_transfer() -> None:
    """Verify receipt -> inventory -> FEFO -> dispensing -> A-to-B transfer."""
    async with AsyncSessionLocal() as db:
        suffix = os.urandom(6).hex()
        user = User(
            email=f"it-{suffix}@example.test",
            username=f"it-{suffix}",
            hashed_password="not-used-in-test",
            is_active=True,
            is_superuser=True,
        )
        pharmacy_a = Pharmacy(name=f"Integration A {suffix}", code=f"ITA-{suffix}")
        pharmacy_b = Pharmacy(name=f"Integration B {suffix}", code=f"ITB-{suffix}")
        supplier = Supplier(name=f"Supplier {suffix}", code=f"SUP-{suffix}")
        product = Product(
            name=f"FEFO Product {suffix}",
            sku=f"FEFO-{suffix}",
            units_per_pack=1,
            price=10.0,
            storage_location_type="shelf",
            is_active=True,
        )
        patient = Patient(
            pharmacy_id=None,
            first_name="Integration",
            last_name="Patient",
            full_name="Integration Patient",
            phone=f"+38099{suffix[:7]}",
            country="UA",
            is_active=True,
        )
        db.add_all([user, pharmacy_a, pharmacy_b, supplier, product, patient])
        await db.flush()
        patient.pharmacy_id = pharmacy_a.id
        await db.commit()

        today = date.today()
        early_expiry = today + timedelta(days=30)
        late_expiry = today + timedelta(days=120)

        receipt = await receive_goods(
            GoodsReceiptCreate(
                pharmacy_id=pharmacy_a.id,
                supplier_id=supplier.id,
                items=[
                    GoodsReceiptItemCreate(
                        product_id=product.id,
                        batch_number=f"EARLY-{suffix}",
                        expiry_date=early_expiry,
                        quantity=5,
                        storage_location="shelf",
                    ),
                    GoodsReceiptItemCreate(
                        product_id=product.id,
                        batch_number=f"LATE-{suffix}",
                        expiry_date=late_expiry,
                        quantity=10,
                        storage_location="shelf",
                    ),
                ],
            ),
            user,
            db,
        )
        assert receipt.status == "accepted"

        batches = (
            (
                await db.execute(
                    select(ProductBatch)
                    .where(ProductBatch.product_id == product.id)
                    .order_by(ProductBatch.expiry_date)
                )
            )
            .scalars()
            .all()
        )
        assert [batch.batch_number for batch in batches] == [
            f"EARLY-{suffix}",
            f"LATE-{suffix}",
        ]
        early_batch, late_batch = batches
        assert early_batch.available_quantity == 5
        assert late_batch.available_quantity == 10

        inventories = (
            (
                await db.execute(
                    select(Inventory).where(
                        Inventory.pharmacy_id == pharmacy_a.id,
                        Inventory.product_id == product.id,
                    )
                )
            )
            .scalars()
            .all()
        )
        assert sorted(row.quantity for row in inventories) == [5, 10]

        sale = await confirm_pos_transaction(
            POSTransactionCreate(
                pharmacy_id=pharmacy_a.id,
                patient_id=patient.id,
                payment_method="cash",
                items=[POSItem(product_id=product.id, units=4)],
            ),
            db,
            user,
        )
        assert sale.status == "completed"

        await db.refresh(early_batch)
        await db.refresh(late_batch)
        assert early_batch.available_quantity == 1
        assert late_batch.available_quantity == 10

        sale_item = await db.scalar(
            select(OrderItem).where(OrderItem.order_id == sale.order_id)
        )
        assert sale_item is not None
        assert sale_item.batch_id == early_batch.id

        purchase = await db.scalar(
            select(PatientPurchase).where(
                PatientPurchase.receipt_number == sale.receipt_number
            )
        )
        assert purchase is not None
        assert purchase.batch_id == early_batch.id

        dispense_tx = await db.scalar(
            select(InventoryTransaction).where(
                InventoryTransaction.order_id == sale.order_id,
                InventoryTransaction.transaction_type == "dispense",
            )
        )
        assert dispense_tx is not None
        assert dispense_tx.batch_id == early_batch.id
        assert dispense_tx.quantity_delta == -4
        assert dispense_tx.quantity_after == 1

        transfer = await create_stock_transfer(
            StockTransferCreate(
                source_pharmacy_id=pharmacy_a.id,
                destination_pharmacy_id=pharmacy_b.id,
                items=[
                    StockTransferItemCreate(
                        product_id=product.id,
                        batch_id=late_batch.id,
                        quantity=2,
                    )
                ],
            ),
            user,
            db,
        )
        assert transfer.status == "in_transit"

        source_inventory = await db.scalar(
            select(Inventory).where(
                Inventory.pharmacy_id == pharmacy_a.id,
                Inventory.product_id == product.id,
                Inventory.batch_id == late_batch.id,
            )
        )
        assert source_inventory is not None
        assert source_inventory.quantity == 8

        received_transfer = await receive_stock_transfer(transfer.id, user, db)
        assert received_transfer.status == "received"

        destination_inventory = await db.scalar(
            select(Inventory).where(
                Inventory.pharmacy_id == pharmacy_b.id,
                Inventory.product_id == product.id,
                Inventory.batch_id == late_batch.id,
            )
        )
        assert destination_inventory is not None
        assert destination_inventory.quantity == 2
        assert destination_inventory.lot_number == late_batch.batch_number

        transfer_in = await db.scalar(
            select(InventoryTransaction).where(
                InventoryTransaction.pharmacy_id == pharmacy_b.id,
                InventoryTransaction.batch_id == late_batch.id,
                InventoryTransaction.transaction_type == "transfer_in",
            )
        )
        assert transfer_in is not None
        assert transfer_in.quantity_delta == 2


@pytest.mark.asyncio
async def test_pos_transaction_persists_full_fefo_traceability() -> None:
    """Verify a real POS sale persists the complete batch-aware transaction chain."""
    async with AsyncSessionLocal() as db:
        suffix = os.urandom(6).hex()
        user = User(
            email=f"pos-{suffix}@example.test",
            username=f"pos-{suffix}",
            hashed_password="not-used-in-test",
            is_active=True,
            is_superuser=True,
        )
        pharmacy = Pharmacy(name=f"POS Pharmacy {suffix}", code=f"POS-{suffix}")
        supplier = Supplier(name=f"POS Supplier {suffix}", code=f"POSS-{suffix}")
        product = Product(
            name=f"POS Product {suffix}",
            sku=f"POS-{suffix}",
            units_per_pack=1,
            price=10.0,
            storage_location_type="shelf",
            is_active=True,
        )
        patient = Patient(
            pharmacy_id=None,
            first_name="POS",
            last_name="Patient",
            full_name="POS Patient",
            phone=f"+38067{suffix[:7]}",
            country="UA",
            is_active=True,
        )
        db.add_all([user, pharmacy, supplier, product, patient])
        await db.flush()
        patient.pharmacy_id = pharmacy.id
        await db.commit()

        today = date.today()
        await receive_goods(
            GoodsReceiptCreate(
                pharmacy_id=pharmacy.id,
                supplier_id=supplier.id,
                items=[
                    GoodsReceiptItemCreate(
                        product_id=product.id,
                        batch_number=f"EARLY-{suffix}",
                        expiry_date=today + timedelta(days=30),
                        quantity=4,
                        storage_location="shelf",
                    ),
                    GoodsReceiptItemCreate(
                        product_id=product.id,
                        batch_number=f"LATE-{suffix}",
                        expiry_date=today + timedelta(days=120),
                        quantity=12,
                        storage_location="shelf",
                    ),
                ],
            ),
            user,
            db,
        )
        await db.commit()

        batches = (
            (
                await db.execute(
                    select(ProductBatch)
                    .where(ProductBatch.product_id == product.id)
                    .order_by(ProductBatch.expiry_date)
                )
            )
            .scalars()
            .all()
        )
        assert len(batches) == 2
        early_batch, late_batch = batches

        sale = await confirm_pos_transaction(
            POSTransactionCreate(
                pharmacy_id=pharmacy.id,
                patient_id=patient.id,
                payment_method="card",
                items=[POSItem(product_id=product.id, units=10)],
            ),
            db,
            user,
        )
        assert sale.status == "completed"
        assert sale.receipt_number
        assert sale.total_amount == 100.0

        await db.refresh(early_batch)
        await db.refresh(late_batch)
        assert early_batch.available_quantity == 4
        assert late_batch.available_quantity == 2

        sale_item = await db.scalar(
            select(OrderItem).where(OrderItem.order_id == sale.order_id)
        )
        assert sale_item is not None
        assert sale_item.batch_id == late_batch.id
        assert sale_item.quantity_units == 10

        dispensing = await db.scalar(
            select(Dispensing).where(Dispensing.order_id == sale.order_id)
        )
        assert dispensing is not None
        assert dispensing.batch_id == late_batch.id
        assert dispensing.quantity_units == 10

        dispense_tx = await db.scalar(
            select(InventoryTransaction).where(
                InventoryTransaction.order_id == sale.order_id,
                InventoryTransaction.transaction_type == "dispense",
            )
        )
        assert dispense_tx is not None
        assert dispense_tx.batch_id == late_batch.id
        assert dispense_tx.dispensing_id == dispensing.id
        assert dispense_tx.quantity_delta == -10
        assert dispense_tx.quantity_after == 2

        purchase = await db.scalar(
            select(PatientPurchase).where(
                PatientPurchase.receipt_number == sale.receipt_number
            )
        )
        assert purchase is not None
        assert purchase.patient_id == patient.id
        assert purchase.product_id == product.id
        assert purchase.batch_id == late_batch.id
        assert purchase.quantity == 10

        order = await db.scalar(select(Order).where(Order.id == sale.order_id))
        assert order is not None
        assert order.receipt_number == sale.receipt_number
        assert order.status == "completed"
        assert order.payment_status == "paid"

        inventory = await db.scalar(
            select(Inventory).where(
                Inventory.pharmacy_id == pharmacy.id,
                Inventory.product_id == product.id,
                Inventory.batch_id == late_batch.id,
            )
        )
        assert inventory is not None
        assert inventory.quantity == 2

        audit = await db.scalar(
            select(AuditLog).where(
                AuditLog.entity == "order",
                AuditLog.entity_id == sale.order_id,
                AuditLog.action == "dispense",
            )
        )
        assert audit is not None
        assert audit.actor_id == user.id
        assert audit.changes is not None
        assert audit.changes["patient_id"] == patient.id
        assert audit.changes["item_count"] == 1


@pytest.mark.asyncio
async def test_pos_rejects_expired_batch_without_creating_sale() -> None:
    """An expired explicitly selected batch must never become a completed sale."""
    async with AsyncSessionLocal() as db:
        suffix = os.urandom(6).hex()
        user = User(
            email=f"expired-{suffix}@example.test",
            username=f"expired-{suffix}",
            hashed_password="not-used-in-test",
            is_active=True,
            is_superuser=True,
        )
        pharmacy = Pharmacy(
            name=f"Expired Pharmacy {suffix}",
            code=f"EXP-{suffix}",
        )
        product = Product(
            name=f"Expired Product {suffix}",
            sku=f"EXP-{suffix}",
            units_per_pack=1,
            price=10.0,
            is_active=True,
        )
        patient = Patient(
            pharmacy_id=None,
            first_name="Expired",
            last_name="Patient",
            full_name="Expired Patient",
            phone=f"+38068{suffix[:7]}",
            country="UA",
            is_active=True,
        )
        db.add_all([user, pharmacy, product, patient])
        await db.flush()
        patient.pharmacy_id = pharmacy.id

        batch = ProductBatch(
            product_id=product.id,
            batch_number=f"EXPIRED-{suffix}",
            expiry_date=date.today() - timedelta(days=1),
            received_quantity=5,
            available_quantity=5,
        )
        db.add(batch)
        await db.flush()
        inventory = Inventory(
            product_id=product.id,
            pharmacy_id=pharmacy.id,
            batch_id=batch.id,
            lot_number=batch.batch_number,
            quantity=5,
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        db.add(inventory)
        await db.commit()

        with pytest.raises(HTTPException) as exc_info:
            await confirm_pos_transaction(
                POSTransactionCreate(
                    pharmacy_id=pharmacy.id,
                    patient_id=patient.id,
                    payment_method="cash",
                    items=[
                        POSItem(
                            product_id=product.id,
                            batch_id=batch.id,
                            units=1,
                        )
                    ],
                ),
                db,
                user,
            )

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "Cannot dispense an expired batch"

        await db.rollback()
        assert (
            await db.scalar(select(Order).where(Order.patient_id == patient.id)) is None
        )
        assert (
            await db.scalar(
                select(Dispensing).where(Dispensing.patient_id == patient.id)
            )
            is None
        )
        assert (
            await db.scalar(
                select(PatientPurchase).where(PatientPurchase.patient_id == patient.id)
            )
            is None
        )


@pytest.mark.asyncio
async def test_pos_transaction_rolls_back_all_changes_on_late_failure() -> None:
    """A failure after an earlier line must not leave partial POS state committed."""
    async with AsyncSessionLocal() as db:
        suffix = os.urandom(6).hex()
        user = User(
            email=f"rollback-{suffix}@example.test",
            username=f"rollback-{suffix}",
            hashed_password="not-used-in-test",
            is_active=True,
            is_superuser=True,
        )
        pharmacy = Pharmacy(
            name=f"Rollback Pharmacy {suffix}",
            code=f"RB-{suffix}",
        )
        product = Product(
            name=f"Rollback Product {suffix}",
            sku=f"RB-{suffix}",
            units_per_pack=1,
            price=10.0,
            is_active=True,
        )
        patient = Patient(
            pharmacy_id=None,
            first_name="Rollback",
            last_name="Patient",
            full_name="Rollback Patient",
            phone=f"+38069{suffix[:7]}",
            country="UA",
            is_active=True,
        )
        db.add_all([user, pharmacy, product, patient])
        await db.flush()
        patient.pharmacy_id = pharmacy.id

        batch = ProductBatch(
            product_id=product.id,
            batch_number=f"RB-{suffix}",
            expiry_date=date.today() + timedelta(days=120),
            received_quantity=5,
            available_quantity=5,
        )
        db.add(batch)
        await db.flush()
        inventory = Inventory(
            product_id=product.id,
            pharmacy_id=pharmacy.id,
            batch_id=batch.id,
            lot_number=batch.batch_number,
            quantity=5,
            expires_at=datetime.utcnow() + timedelta(days=120),
        )
        db.add(inventory)
        await db.commit()

        with pytest.raises(HTTPException) as exc_info:
            await confirm_pos_transaction(
                POSTransactionCreate(
                    pharmacy_id=pharmacy.id,
                    patient_id=patient.id,
                    payment_method="cash",
                    items=[
                        POSItem(product_id=product.id, units=2),
                        POSItem(product_id=999999999, units=1),
                    ],
                ),
                db,
                user,
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Product 999999999 not found"

        await db.rollback()
        await db.refresh(inventory)
        await db.refresh(batch)

        assert inventory.quantity == 5
        assert batch.available_quantity == 5
        assert (
            await db.scalar(select(Order).where(Order.patient_id == patient.id)) is None
        )
        assert (
            await db.scalar(
                select(InventoryTransaction).where(
                    InventoryTransaction.inventory_id == inventory.id,
                    InventoryTransaction.transaction_type == "dispense",
                )
            )
            is None
        )
        assert (
            await db.scalar(
                select(Dispensing).where(Dispensing.patient_id == patient.id)
            )
            is None
        )
        assert (
            await db.scalar(
                select(PatientPurchase).where(PatientPurchase.patient_id == patient.id)
            )
            is None
        )
        assert (
            await db.scalar(
                select(AuditLog).where(
                    AuditLog.actor_id == user.id,
                    AuditLog.action == "dispense",
                )
            )
            is None
        )
