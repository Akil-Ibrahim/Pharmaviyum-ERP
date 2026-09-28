from src.pharmaviyum.schemas.product_schema import ProductCreate, ProductResponse


def test_product_create_defaults_halal_to_unknown() -> None:
    product = ProductCreate(name="Test medicine", sku="TEST-HALAL-001")

    assert product.halal_status == "unknown"
    assert product.halal_standard is None
    assert product.halal_evidence == {}


def test_product_response_exposes_halal_evidence() -> None:
    assert ProductResponse.model_fields["halal_status"].default == "unknown"
    assert "halal_evidence" in ProductResponse.model_fields
