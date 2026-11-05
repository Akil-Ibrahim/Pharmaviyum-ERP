"""End-to-end tests for POS checkout, FEFO allocation, and payment settlement."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.pharmacy import Pharmacy
from src.pharmaviyum.models.pos import Payment, Sale
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

    await test_db.refresh(first)
    await test_db.refresh(second)
    assert first.quantity == 0
    assert second.quantity == 4
    assert first.reserved_quantity == 0
    assert second.reserved_quantity == 0


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
        "currency": "UAH",
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

    response = await authenticated_client.post(
        "/api/v1/pos/checkout",
        json={
            "pharmacy_id": pharmacy.id,
            "idempotency_key": "pos-stock-fail-0001",
            "items": [{"product_id": product.id, "quantity": 8}],
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

    await test_db.refresh(first)
    await test_db.refresh(second)
    assert first.quantity == 2
    assert first.reserved_quantity == 0
    assert second.quantity == 5
    assert second.reserved_quantity == 0
