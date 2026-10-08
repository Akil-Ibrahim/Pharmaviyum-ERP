from pydantic import BaseModel, ConfigDict


class DrugCatalogResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    medicinal_product_id: int
    drug_reference_id: int
    inn_name: str
    atc_code: str | None
    ingredient_names: list[str]
    brand_name: str | None
    product_type: str
    manufacturer: str | None
    strength: str | None
    dosage_form: str | None
    route: str | None
    package_description: str | None
    gtin: str | None
    regulatory_id: str | None
