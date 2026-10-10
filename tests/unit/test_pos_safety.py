import pytest
from pydantic import ValidationError

from src.pharmaviyum.api.v1.pos import CheckoutRequest
from src.pharmaviyum.models.inventory_transaction import InventoryTransaction
from src.pharmaviyum.schemas.product_schema import ProductCreate


@pytest.mark.unit
def test_unclassified_product_defaults_to_prescription_required() -> None:
    product = ProductCreate(name="Unknown medicine", sku="RX-UNKNOWN")
    assert product.prescription_required is True


@pytest.mark.unit
def test_confirmed_otc_product_can_be_explicitly_classified() -> None:
    product = ProductCreate(
        name="Confirmed OTC product",
        sku="OTC-001",
        prescription_required=False,
    )
    assert product.prescription_required is False

@pytest.mark.unit
def test_inventory_transaction_ledger_rejects_zero_quantity_delta() -> None:
    constraint_names = {
        constraint.name
        for constraint in InventoryTransaction.__table__.constraints
        if constraint.name
    }
    assert "ck_inventory_transactions_nonzero_delta" in constraint_names

@pytest.mark.unit
def test_checkout_requires_idempotency_key() -> None:
    with pytest.raises(ValidationError):
        CheckoutRequest(
            pharmacy_id=1,
            patient_id=1,
            payment_method="cash",
            items=[{"product_id": 1, "quantity": 1}],
        )


@pytest.mark.unit
def test_checkout_accepts_a_stable_idempotency_key() -> None:
    request = CheckoutRequest(
        pharmacy_id=1,
        patient_id=1,
        payment_method="cash",
        idempotency_key="pos-checkout-test-key-0001",
        items=[{"product_id": 1, "quantity": 1}],
    )
    assert request.idempotency_key == "pos-checkout-test-key-0001"
