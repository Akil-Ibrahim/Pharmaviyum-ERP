"""End-to-end tests for POS checkout, FEFO allocation, and payment settlement."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timedelta

import pytest
from sqlalchemy import func, select

from src.pharmaviyum.models.drug_catalog import DrugReference, MedicinalProduct
from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.pharmacy import Pharmacy
from src.pharmaviyum.models.pos import Payment, Sale, SaleItemAllocation
from src.pharmaviyum.models.outbox import OutboxEvent
from src.pharmaviyum.models.product import Product


async def _create_pharmacy_product_and_stock(test_db):
    pharmacy = Pharmacy(name="POS Test Pharmacy", code="POS-TEST")
    product = Product(
        name="Omeprazole 20 mg",
        sku="POS-OMEP-20",
        price=10.50,
        stock=0,
        is_active=True,
    )
    test_db.add_all([pharmacy, product])
    await test_db.flush()
    now = datetime.utcnow()
    first = Inventory(
        product_id=product.id,
        pharmacy_id=pharmacy.id,
        quantity=2,
        reserved_quantity=0,
        lot_number="EARLY-LOT",
        expires_at=now + timedelta(days=30),
    )
    second = Inventory(
        product_id=product.id,
        pharmacy_id=pharmacy.id,
        quantity=5,
        reserved_quantity=0,
        lot_number="LATE-LOT",
        expires_at=now + timedelta(days=90),
    )
    test_db.add_all([first, second])
    await test_db.flush()
    return pharmacy, product, first, second


@pytest.mark.integration
async def test_pos_search_and_checkout_block_teva_and_israeli_medicines(
    authenticated_client, test_db
):
    pharmacy = Pharmacy(name="POS Exclusion Test Pharmacy", code="POS-EXCLUSION")
    reference = DrugReference(inn_name="omeprazole")
    test_db.add_all([pharmacy, reference])
    await test_db.flush()

    israeli_authorized = MedicinalProduct(
        drug_reference_id=reference.id,
        brand_name="ExampleAuthorized",
        product_type="branded",
        manufacturer="Example Pharma",
        authorization_country="Israel",
        manufacturer_country="Germany",
    )
    test_db.add(israeli_authorized)
    await test_db.flush()

    teva_product = Product(
        name="Teva Omeprazole 20 mg",
        sku="POS-EXCLUDED-TEVA",
        price=10.50,
        stock=0,
        is_active=True,
        manufacturer="Teva Pharmaceutical Industries",
    )
    israeli_origin_product = Product(
        name="ExampleOrigin Omeprazole 20 mg",
        sku="POS-EXCLUDED-ORIGIN",
        price=10.50,
        stock=0,
        is_active=True,
        manufacturer="Example Pharma",
        manufacturer_country="IL",
    )
    israeli_authorized_product = Product(
        name="ExampleAuthorized Omeprazole 20 mg",
        sku="POS-EXCLUDED-AUTH",
        price=10.50,
        stock=0,
        is_active=True,
        manufacturer="Example Pharma",
        manufacturer_country="Germany",
        medicinal_product_id=israeli_authorized.id,
    )
    products = [teva_product, israeli_origin_product, israeli_authorized_product]
    test_db.add_all(products)
    await test_db.flush()

    now = datetime.utcnow()
    lots = [
        Inventory(
            product_id=product.id,
            pharmacy_id=pharmacy.id,
            quantity=5,
            reserved_quantity=0,
            lot_number=f"EXCLUDED-{index}",
            expires_at=now + timedelta(days=30),
        )
        for index, product in enumerate(products, start=1)
    ]
    test_db.add_all(lots)
    await test_db.flush()

    search = await authenticated_client.get(
        "/api/v1/pos/products/search",
        params={"q": "omeprazole", "pharmacy_id": pharmacy.id},
    )
    assert search.status_code == 200, search.text
    assert search.json() == []

    for product, key in zip(
        products,
        (
            "pos-excluded-teva-0001",
            "pos-excluded-origin-0001",
            "pos-excluded-auth-0001",
        ),
    ):
        response = await authenticated_client.post(
            "/api/v1/pos/checkout",
            json={
                "pharmacy_id": pharmacy.id,
                "idempotency_key": key,
                "items": [{"product_id": product.id, "quantity": 1}],
                "payment_method": "cash",
                "cash_received": "20.00",
            },
        )
        assert response.status_code == 404
        assert (
            await test_db.scalar(select(Sale).where(Sale.idempotency_key == key))
            is None
        )

    for lot in lots:
        await test_db.refresh(lot)
        assert lot.quantity == 5
        assert lot.reserved_quantity == 0


@pytest.mark.integration
async def test_pos_product_search_returns_regulatory_identifier(
    authenticated_client, test_db
):
    pharmacy, product, _, _ = await _create_pharmacy_product_and_stock(test_db)
    product.regulatory_id = "REG-OMEP-2026"
    await test_db.flush()

    response = await authenticated_client.get(
        "/api/v1/pos/products/search",
        params={"q": "REG-OMEP-2026", "pharmacy_id": pharmacy.id},
    )

    assert response.status_code == 200, response.text
    assert len(response.json()) == 1
    assert response.json()[0]["regulatory_id"] == "REG-OMEP-2026"


@pytest.mark.integration
async def test_cash_checkout_records_receipt_and_allocates_fefo(
    authenticated_client, test_db
):
    pharmacy, product, first, second = await _create_pharmacy_product_and_stock(test_db)

    response = await authenticated_client.post(
        "/api/v1/pos/checkout",
        json={
            "pharmacy_id": pharmacy.id,
            "idempotency_key": "pos-cash-checkout-0001",
            "items": [{"product_id": product.id, "quantity": 3}],
            "payment_method": "cash",
            "cash_received": "40.00",
        },
    )

    assert response.status_code == 201, response.text
    receipt = response.json()
    assert receipt["status"] == "completed"
    assert receipt["total"] == "31.50"
    assert receipt["cash_change"] == "8.50"
    assert receipt["payments"][0]["status"] == "succeeded"
    assert receipt["payments"][0]["cash_received"] == "40.00"
    outbox_events = list(
        (
            await test_db.scalars(
                select(OutboxEvent).where(
                    OutboxEvent.aggregate_type == "sale",
                    OutboxEvent.aggregate_id == str(receipt["id"]),
                )
            )
        ).all()
    )
    assert len(outbox_events) == 1
    assert outbox_events[0].event_type == "pos.sale.created"
    assert outbox_events[0].payload["event_id"] == outbox_events[0].event_id
    assert outbox_events[0].payload["items"][0]["allocations"][0]["lot_number"] == "EARLY-LOT"
    allocations = receipt["items"][0]["allocations"]
    assert [(row["lot_number"], row["quantity"]) for row in allocations] == [
        ("EARLY-LOT", 2),
        ("LATE-LOT", 1),
    ]

    duplicate = await authenticated_client.post(
        "/api/v1/pos/checkout",
        json={
            "pharmacy_id": pharmacy.id,
            "idempotency_key": "pos-cash-checkout-0001",
            "items": [{"product_id": product.id, "quantity": 3}],
            "payment_method": "cash",
            "cash_received": "40.00",
        },
    )
    assert duplicate.status_code == 201
    assert duplicate.json()["id"] == receipt["id"]
    event_count = await test_db.scalar(
        select(func.count())
        .select_from(OutboxEvent)
        .where(OutboxEvent.aggregate_id == str(receipt["id"]))
    )
    assert event_count == 1

    await test_db.refresh(first)
    await test_db.refresh(second)
    assert first.quantity == 0
    assert second.quantity == 4
    assert first.reserved_quantity == 0
    assert second.reserved_quantity == 0


@pytest.mark.integration
async def test_fefo_skips_expired_lots_and_uses_undated_lots_last(
    authenticated_client, test_db
):
    pharmacy = Pharmacy(name="POS FEFO Edge Pharmacy", code="POS-FEFO-EDGE")
    product = Product(
        name="Cetirizine 10 mg",
        sku="POS-CET-10",
        price=4.25,
        stock=0,
        is_active=True,
    )
    test_db.add_all([pharmacy, product])
    await test_db.flush()

    now = datetime.utcnow()
    expired = Inventory(
        product_id=product.id,
        pharmacy_id=pharmacy.id,
        quantity=10,
        reserved_quantity=0,
        lot_number="EXPIRED-LOT",
        expires_at=now - timedelta(days=1),
    )
    undated = Inventory(
        product_id=product.id,
        pharmacy_id=pharmacy.id,
        quantity=2,
        reserved_quantity=0,
        lot_number="UNDATED-LOT",
        expires_at=None,
    )
    valid = Inventory(
        product_id=product.id,
        pharmacy_id=pharmacy.id,
        quantity=1,
        reserved_quantity=0,
        lot_number="VALID-LOT",
        expires_at=now + timedelta(days=30),
    )
    test_db.add_all([expired, undated, valid])
    await test_db.flush()

    response = await authenticated_client.post(
        "/api/v1/pos/checkout",
        json={
            "pharmacy_id": pharmacy.id,
            "idempotency_key": "pos-fefo-expiry-edge-0001",
            "items": [{"product_id": product.id, "quantity": 3}],
            "payment_method": "cash",
            "cash_received": "20.00",
        },
    )

    assert response.status_code == 201, response.text
    allocation_result = await test_db.execute(
        select(SaleItemAllocation)
        .where(SaleItemAllocation.sale_item.has(sale_id=response.json()["id"]))
        .order_by(SaleItemAllocation.id.asc())
    )
    allocations = list(allocation_result.scalars().all())
    assert [(row.lot_number, row.quantity) for row in allocations] == [
        ("VALID-LOT", 1),
        ("UNDATED-LOT", 2),
    ]

    await test_db.refresh(expired)
    await test_db.refresh(valid)
    await test_db.refresh(undated)
    assert expired.quantity == 10
    assert valid.quantity == 0
    assert undated.quantity == 0


@pytest.mark.integration
async def test_card_payment_reserves_stock_until_signed_webhook(
    authenticated_client, test_db, monkeypatch
):
    pharmacy, product, first, second = await _create_pharmacy_product_and_stock(test_db)
    secret = "test-webhook-secret"
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", secret)

    response = await authenticated_client.post(
        "/api/v1/pos/checkout",
        json={
            "pharmacy_id": pharmacy.id,
            "idempotency_key": "pos-card-checkout-0001",
            "items": [{"product_id": product.id, "quantity": 3}],
            "payment_method": "card_terminal",
        },
    )
    assert response.status_code == 201, response.text
    receipt = response.json()
    assert receipt["status"] == "awaiting_payment"
    payment_id = receipt["payments"][0]["id"]

    await test_db.refresh(first)
    await test_db.refresh(second)
    assert first.quantity == 2
    assert first.reserved_quantity == 2
    assert second.quantity == 5
    assert second.reserved_quantity == 1

    event = {
        "payment_id": payment_id,
        "provider_name": "test_terminal",
        "provider_payment_id": "terminal-tx-001",
        "status": "succeeded",
        "amount": "31.50",
    }
    body = json.dumps(event, separators=(",", ":")).encode()
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    webhook = await authenticated_client.post(
        "/api/v1/pos/payments/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Pharmaviyum-Signature": signature,
        },
    )
    assert webhook.status_code == 200, webhook.text
    assert webhook.json()["status"] == "processed"
    sale_events = list(
        (
            await test_db.scalars(
                select(OutboxEvent)
                .where(OutboxEvent.aggregate_id == str(receipt["id"]))
                .order_by(OutboxEvent.aggregate_version.asc())
            )
        ).all()
    )
    assert [event.aggregate_version for event in sale_events] == [1, 2]
    assert [event.event_type for event in sale_events] == [
        "pos.sale.created",
        "pos.payment.succeeded",
    ]

    await test_db.refresh(first)
    await test_db.refresh(second)
    assert first.quantity == 0
    assert first.reserved_quantity == 0
    assert second.quantity == 4
    assert second.reserved_quantity == 0

    sale = await test_db.scalar(select(Sale).where(Sale.id == receipt["id"]))
    payment = await test_db.scalar(select(Payment).where(Payment.id == payment_id))
    assert sale is not None and sale.status == "completed"
    assert payment is not None and payment.status == "succeeded"

    replay = await authenticated_client.post(
        "/api/v1/pos/payments/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Pharmaviyum-Signature": signature,
        },
    )
    assert replay.status_code == 200
    assert replay.json()["status"] == "already_processed"


@pytest.mark.integration
async def test_checkout_rejects_insufficient_stock_without_partial_decrement(
    authenticated_client, test_db
):
    pharmacy, product, first, second = await _create_pharmacy_product_and_stock(test_db)
    pharmacy_id = pharmacy.id
    product_id = product.id
    # The endpoint rolls back its transaction on insufficient stock; commit fixture
    # rows first so they remain persistent and can be reloaded after that rollback.
    await test_db.commit()

    response = await authenticated_client.post(
        "/api/v1/pos/checkout",
        json={
            "pharmacy_id": pharmacy_id,
            "idempotency_key": "pos-stock-fail-0001",
            "items": [{"product_id": product_id, "quantity": 8}],
            "payment_method": "cash",
            "cash_received": "100.00",
        },
    )

    assert response.status_code == 409
    await test_db.refresh(first)
    await test_db.refresh(second)
    assert first.quantity == 2
    assert second.quantity == 5
    assert first.reserved_quantity == 0
    assert second.reserved_quantity == 0
    assert (
        await test_db.scalar(
            select(Sale).where(Sale.idempotency_key == "pos-stock-fail-0001")
        )
        is None
    )
    assert (
        await test_db.scalar(
            select(OutboxEvent).where(
                OutboxEvent.event_type == "pos.sale.created"
            )
        )
        is None
    )


@pytest.mark.integration
async def test_cancel_pending_sale_releases_reserved_inventory(
    authenticated_client, test_db
):
    pharmacy, product, first, second = await _create_pharmacy_product_and_stock(test_db)
    response = await authenticated_client.post(
        "/api/v1/pos/checkout",
        json={
            "pharmacy_id": pharmacy.id,
            "idempotency_key": "pos-cancel-checkout-0001",
            "items": [{"product_id": product.id, "quantity": 3}],
            "payment_method": "online",
        },
    )
    assert response.status_code == 201, response.text
    receipt = response.json()
    assert receipt["status"] == "awaiting_payment"

    cancelled = await authenticated_client.post(
        f"/api/v1/pos/sales/{receipt['id']}/cancel"
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["payments"][0]["status"] == "failed"
    cancel_event = await test_db.scalar(
        select(OutboxEvent).where(
            OutboxEvent.aggregate_id == str(receipt["id"]),
            OutboxEvent.event_type == "pos.sale.cancelled",
        )
    )
    assert cancel_event is not None
    assert cancel_event.aggregate_version == 2

    await test_db.refresh(first)
    await test_db.refresh(second)
    assert first.quantity == 2
    assert first.reserved_quantity == 0
    assert second.quantity == 5
    assert second.reserved_quantity == 0
