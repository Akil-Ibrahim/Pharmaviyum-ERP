from datetime import date

import pytest
from pydantic import ValidationError

from src.pharmaviyum.api.v1.procurement import (
    GoodsReceiptItemCreate,
    PurchaseOrderCreate,
    StockTransferCreate,
    TemperatureLogCreate,
)
from src.pharmaviyum.schemas.product_schema import ProductCreate


def test_goods_receipt_requires_positive_quantity() -> None:
    with pytest.raises(ValidationError):
        GoodsReceiptItemCreate(
            product_id=1,
            batch_number="B1",
            expiry_date=date(2030, 1, 1),
            quantity=0,
        )


def test_goods_receipt_supports_refrigerator_storage() -> None:
    item = GoodsReceiptItemCreate(
        product_id=1,
        batch_number="B1",
        expiry_date=date(2030, 1, 1),
        quantity=10,
        storage_location="refrigerator",
    )
    assert item.storage_location == "refrigerator"


def test_purchase_order_requires_items() -> None:
    with pytest.raises(ValidationError):
        PurchaseOrderCreate(pharmacy_id=1, supplier_id=1, items=[])


def test_transfer_requires_batch_aware_item() -> None:
    transfer = StockTransferCreate(
        source_pharmacy_id=1,
        destination_pharmacy_id=2,
        items=[{"product_id": 1, "batch_id": 7, "quantity": 5}],
    )
    assert transfer.items[0].batch_id == 7


def test_temperature_log_rejects_unknown_storage_location() -> None:
    with pytest.raises(ValidationError):
        TemperatureLogCreate(
            pharmacy_id=1,
            storage_location="counter",
            temperature_c=22,
        )


def test_product_storage_requirements_are_validated() -> None:
    product = ProductCreate(
        name="Cold Chain Product",
        sku="COLD-001",
        storage_temperature_min=2,
        storage_temperature_max=8,
        storage_location_type="refrigerator",
    )
    assert product.storage_temperature_min == 2
    assert product.storage_temperature_max == 8
    assert product.storage_location_type == "refrigerator"
