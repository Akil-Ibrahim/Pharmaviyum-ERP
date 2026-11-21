"""Pharmacy-scoped product search response for POS."""

from pydantic import BaseModel


class POSProductResponse(BaseModel):
    id: int
    name: str
    sku: str
    dosage_strength: str | None = None
    dosage_form: str | None = None
    units_per_pack: int
    manufacturer: str | None = None
    inn_name: str | None = None
    gtin: str | None = None
    barcode: str | None = None
    regulatory_id: str | None = None
    price: float
    stock: int
    medicinal_product_id: int | None = None
