from pydantic import BaseModel, ConfigDict, Field


class DrugCatalogIngredientResult(BaseModel):
    ingredient_name: str
    strength_value: str | None = None
    strength_unit: str | None = None
    source_identifier: str | None = None


class DrugCatalogResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    medicinal_product_id: int | None = None
    drug_reference_id: int | None = None
    inn_name: str
    atc_code: str | None = None
    ingredient_names: list[str] = Field(default_factory=list)
    ingredient_components: list[DrugCatalogIngredientResult] = Field(
        default_factory=list
    )
    brand_name: str | None = None
    product_type: str = "reference"
    manufacturer: str | None = None
    strength: str | None = None
    dosage_form: str | None = None
    route: str | None = None
    package_description: str | None = None
    gtin: str | None = None
    regulatory_id: str | None = None
    authorization_country: str | None = None
    manufacturer_country: str | None = None
    authorization_status: str | None = None
    product_class: str | None = None
    source_record_id: str | None = None
    source_name: str | None = None
    review_status: str = "approved"
