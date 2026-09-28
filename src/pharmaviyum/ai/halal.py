"""Evidence-based halal assessment for pharmaceutical products.

Phase 1 intentionally separates factual product evidence from future fiqh/fatwa
interpretation. It does not issue religious rulings.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class HalalStatus(StrEnum):
    HALAL = "halal"
    HARAM = "haram"
    UNKNOWN = "unknown"


class HalalComponentEvidence(BaseModel):
    """Evidence about one pharmaceutical ingredient/component."""

    name: str = Field(..., min_length=1)
    component_type: str = "ingredient"
    origin: str | None = None
    evidence: str | None = None
    status: HalalStatus = HalalStatus.UNKNOWN


class HalalAssessment(BaseModel):
    """Deterministic evidence assessment; not a religious ruling."""

    status: HalalStatus
    standard: str = "OIC/SMIIC 50-1:2022"
    manufacturer: str | None = None
    source_documents: list[str] = Field(default_factory=list)
    components: list[HalalComponentEvidence] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    fiqh_assessments: list[dict[str, str]] = Field(default_factory=list)


_PORCINE_TERMS = (
    "pork",
    "porcine",
    "swine",
    "pig",
    "lard",
    "свин",
    "свини",
    "свиной",
)

_BOVINE_TERMS = ("bovine", "beef", "cattle", "коров", "говяж", "крупного рогатого скота")


def assess_halal(
    *,
    manufacturer: str | None,
    source_documents: list[str] | None,
    components: list[HalalComponentEvidence],
    halal_certified: bool = False,
) -> HalalAssessment:
    """Assess halal status from explicit evidence only.

    Unknown is preferred whenever a material animal-derived component has an
    unresolved origin. No Sunni/Shia fiqh or fatwa is inferred here.
    """
    normalized = [
        (component.name.lower(), (component.origin or "").lower())
        for component in components
    ]
    reasons: list[str] = []

    for component, (name, origin) in zip(components, normalized):
        combined = f"{name} {origin}"
        if any(term in combined for term in _PORCINE_TERMS):
            component.status = HalalStatus.HARAM
            reasons.append(
                f"Confirmed porcine-derived component: {component.name}."
            )
        elif any(term in combined for term in _BOVINE_TERMS):
            if origin and any(
                marker in origin
                for marker in ("halal", "zabiha", "zabihah", "slaughter", "сертифиц")
            ):
                component.status = HalalStatus.HALAL
            else:
                component.status = HalalStatus.UNKNOWN
                reasons.append(
                    f"Bovine origin is present but halal-compliant origin/slaughter "
                    f"is not sufficiently evidenced: {component.name}."
                )
        elif any(
            marker in combined
            for marker in ("gelatin", "gelatine", "желатин", "glycerin", "глицерин")
        ):
            component.status = HalalStatus.UNKNOWN
            reasons.append(
                f"Potentially animal-derived component requires origin evidence: "
                f"{component.name}."
            )

    if any(c.status == HalalStatus.HARAM for c in components):
        status = HalalStatus.HARAM
    elif any(c.status == HalalStatus.UNKNOWN for c in components):
        status = HalalStatus.UNKNOWN
    elif halal_certified:
        status = HalalStatus.HALAL
        reasons.append("Halal certification is explicitly documented.")
    elif components:
        status = HalalStatus.HALAL
        reasons.append("No prohibited component was identified in the supplied evidence.")
    else:
        status = HalalStatus.UNKNOWN
        reasons.append("No component evidence was supplied.")

    return HalalAssessment(
        status=status,
        manufacturer=manufacturer,
        source_documents=source_documents or [],
        components=components,
        reasons=reasons,
    )
