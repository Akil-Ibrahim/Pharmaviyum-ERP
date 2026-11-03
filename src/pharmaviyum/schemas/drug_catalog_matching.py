from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DrugCatalogMatchCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_type: Literal["drug_reference", "medicinal_product"]
    drug_reference_id: int = Field(gt=0)
    medicinal_product_id: int | None = Field(default=None, gt=0)
    display_name: str
    confidence: float = Field(ge=0, le=1)
    reasons: list[str]
