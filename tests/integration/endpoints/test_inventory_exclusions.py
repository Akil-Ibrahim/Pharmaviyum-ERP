"""Integration tests for origin-neutral inventory operations."""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.pharmacy import Pharmacy
from src.pharmaviyum.models.product import Product

pytestmark = pytest.mark.integration


async def _create_origin_neutral_inventory_fixture(test_db: AsyncSession):
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


async def test_origin_neutral_tevaproduct_can_be_received_into_inventory(
    authenticated_client: AsyncClient,
    test_db: AsyncSession,
):
    pharmacy = Pharmacy(name="Origin Neutral Receipt Pharmacy", code="ORIGIN-RECEIPT")
    product = Product(
        name="Omeprazole 20 mg",
        sku="ORIGIN-TEVA-RECEIPT",
        price=10.50,
        stock=0,
        is_active=True,
        manufacturer="Teva Pharmaceutical Industries",
    )
    test_db.add_all([pharmacy, product])
    await test_db.flush()

    expiry = datetime.utcnow() + timedelta(days=90)
    lot_response = await authenticated_client.post(
        "/api/v1/inventory",
        json={
            "product_id": product.id,
            "pharmacy_id": pharmacy.id,
            "quantity": 0,
            "reserved_quantity": 0,
            "lot_number": "TEVA-RECEIPT-LOT",
            "expires_at": expiry.isoformat(),
        },
    )
    assert lot_response.status_code == 201, lot_response.text
    inventory_id = lot_response.json()["id"]

    receipt = await authenticated_client.post(
        "/api/v1/pos/inventory/receive",
        json={
            "product_id": product.id,
            "pharmacy_id": pharmacy.id,
            "quantity": 5,
            "lot_number": "TEVA-RECEIPT-LOT",
            "expiry_date": expiry.isoformat(),
            "idempotency_key": "teva-origin-receipt-0001",
        },
    )
    assert receipt.status_code == 201, receipt.text
    assert receipt.json()["inventory_id"] == inventory_id
    assert receipt.json()["received_quantity"] == 5
    assert receipt.json()["lot_quantity"] == 5

    inventory = await test_db.get(Inventory, inventory_id)
    assert inventory is not None
    await test_db.refresh(inventory)
    assert inventory.quantity == 5
    assert inventory.reserved_quantity == 0

async def test_inventory_adjustment_allows_origin_neutral_products(
    authenticated_client: AsyncClient,
    test_db: AsyncSession,
):
    _, product, inventory = await _create_origin_neutral_inventory_fixture(test_db)
    assert product.manufacturer == "Teva Pharmaceutical Industries"

    increase = await authenticated_client.post(
        f"/api/v1/inventory/{inventory.id}/adjustments",
        json={
            "quantity_delta": 1,
            "reason": "Manual stock reconciliation",
            "idempotency_key": "origin-neutral-increase-001",
        },
    )

    assert increase.status_code == 200, increase.text
    await test_db.refresh(inventory)
    assert inventory.quantity == 6

    reduction = await authenticated_client.post(
        f"/api/v1/inventory/{inventory.id}/adjustments",
        json={
            "quantity_delta": -1,
            "reason": "Damaged stock reconciliation",
            "idempotency_key": "origin-neutral-reduction-001",
        },
    )

    assert reduction.status_code == 200, reduction.text
    await test_db.refresh(inventory)
    assert inventory.quantity == 5

    metadata_change = await authenticated_client.patch(
        f"/api/v1/inventory/{inventory.id}",
        json={"lot_number": "RENAMED-LOT"},
    )
    assert metadata_change.status_code == 409, metadata_change.text
    await test_db.refresh(inventory)
    assert inventory.lot_number == "TEVA-LOT-001"

async def test_inventory_patch_cannot_change_pos_owned_reservations(
    authenticated_client: AsyncClient,
    test_db: AsyncSession,
):
    _, _, inventory = await _create_origin_neutral_inventory_fixture(test_db)

    response = await authenticated_client.patch(
        f"/api/v1/inventory/{inventory.id}",
        json={"reserved_quantity": 1},
    )
    quantity_response = await authenticated_client.patch(
        f"/api/v1/inventory/{inventory.id}",
        json={"quantity": 4},
    )

    assert response.status_code == 422
    assert quantity_response.status_code == 422
    await test_db.refresh(inventory)
    assert inventory.quantity == 5
    assert inventory.reserved_quantity == 0


async def test_inventory_lot_with_stock_cannot_be_deleted(
    authenticated_client: AsyncClient,
    test_db: AsyncSession,
):
    _, _, inventory = await _create_origin_neutral_inventory_fixture(test_db)

    response = await authenticated_client.delete(
        f"/api/v1/inventory/{inventory.id}"
    )

    assert response.status_code == 409
    await test_db.refresh(inventory)
    assert inventory.quantity == 5
    assert inventory.reserved_quantity == 0
