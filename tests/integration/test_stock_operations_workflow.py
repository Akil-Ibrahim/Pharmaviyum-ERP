"""End-to-end pharmacy stock workflow integration tests.

These tests use the PostgreSQL service configured by CI and exercise the real
procurement, FEFO POS, inventory ledger, and inter-pharmacy transfer paths.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date, timedelta

import pytest
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
from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.inventory_transaction import InventoryTransaction
from src.pharmaviyum.models.order_item import OrderItem
from src.pharmaviyum.models.patients.patient_purchase import PatientPurchase
from src.pharmaviyum.models.patients.patient import Patient
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
