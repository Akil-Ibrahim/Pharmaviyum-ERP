import pytest

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
