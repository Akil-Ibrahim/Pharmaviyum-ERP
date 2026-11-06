"""Integration tests for strict catalog exclusions in inventory operations."""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.pharmacy import Pharmacy
from src.pharmaviyum.models.product import Product

pytestmark = pytest.mark.integration


async def _create_excluded_inventory_fixture(test_db: AsyncSession):
    pharmacy = Pharmacy(name="Excluded Stock Pharmacy", code="EXCLUDED-STOCK")
    product = Product(
        name="Omeprazole 20 mg",
        sku="EXCLUDED-TEVA-001",
        price=10.50,
        stock=0,
        is_active=True,
        manufacturer="Teva Pharmaceutical Industries",
    )
    test_db.add_all([pharmacy, product])
    await test_db.flush()
    inventory = Inventory(
        product_id=product.id,
        pharmacy_id=pharmacy.id,
        quantity=5,
        reserved_quantity=0,
        lot_number="TEVA-LOT-001",
        expires_at=datetime.utcnow() + timedelta(days=90),
    )
    test_db.add(inventory)
    await test_db.flush()
    return pharmacy, product, inventory


async def test_generic_inventory_receipt_rejects_excluded_product(
    authenticated_client: AsyncClient,
    test_db: AsyncSession,
):
    pharmacy = Pharmacy(name="Excluded Receipt Pharmacy", code="EXCLUDED-RECEIPT")
    product = Product(
        name="Omeprazole 20 mg",
        sku="EXCLUDED-TEVA-RECEIPT",
        price=10.50,
        stock=0,
        is_active=True,
        manufacturer="Teva Pharmaceutical Industries",
    )
    test_db.add_all([pharmacy, product])
    await test_db.flush()

    response = await authenticated_client.post(
        "/api/v1/inventory",
        json={
            "product_id": product.id,
            "pharmacy_id": pharmacy.id,
            "quantity": 5,
            "reserved_quantity": 0,
            "lot_number": "TEVA-RECEIPT-LOT",
        },
    )

    assert response.status_code == 404
    assert (
        await test_db.scalar(
            select(Inventory.id).where(Inventory.product_id == product.id)
        )
        is None
    )


async def test_inventory_adjustment_cannot_increase_excluded_stock(
    authenticated_client: AsyncClient,
    test_db: AsyncSession,
):
    _, product, inventory = await _create_excluded_inventory_fixture(test_db)

    increase = await authenticated_client.patch(
        f"/api/v1/inventory/{inventory.id}",
        json={"quantity": 6},
    )

    assert increase.status_code == 404
    await test_db.refresh(inventory)
    assert inventory.quantity == 5

    reduction = await authenticated_client.patch(
        f"/api/v1/inventory/{inventory.id}",
        json={"quantity": 4},
    )

    assert reduction.status_code == 200, reduction.text
    await test_db.refresh(inventory)
    assert inventory.quantity == 4
