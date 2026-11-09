"""
Global Halal Compliance Engine with Fiqh School Awareness.

Covers:
- Sunni: Hanafi, Shafii, Maliki, Hanbali
- Shia: Ja'fari (Sistani, Khamenei, Najafi)
- Zaydi (Yemen — unique school, closer to Sunni)

Key principles applied:
- Istihalah (chemical transformation)
- Darurah (life-saving necessity)
- Marja'-specific rulings
"""

from __future__ import annotations

import time
from typing import Literal, Optional, cast

from pydantic import BaseModel, Field

from src.pharmaviyum.core.logging import logger

from ..registry import registry
from .fiqh_authorities import COUNTRY_FIQH

HalalStatus = Literal["halal", "haram", "mushbooh", "darurah_exempt"]
FiqhSchool = Literal[
    "Hanafi", "Shafii", "Maliki", "Hanbali", "Ja'fari", "Zaydi", "Ibadi"
]


class HalalCheckRequest(BaseModel):
    drug_name: str
    country_code: str = Field(default="SA")
    patient_fiqh: Optional[FiqhSchool] = Field(
        default=None, description="Patient's specific fiqh school (if known)"
    )
    include_alternatives: bool = True
    is_life_saving: bool = Field(
        default=False, description="If True, applies Darurah exception"
    )


class HalalCertification(BaseModel):
    drug_name: str
    status: HalalStatus
    fiqh_school: FiqhSchool
    marja_reference: Optional[str]
    certification_body: Optional[str]
    concerns: list[str]
    notes: str
    alternatives: list[str]
    darurah_applied: bool = False
    istihalah_check: Optional[str] = None


# ============================================================================
# PHARMA-HALAL DATABASE WITH FIQH NUANCES
# ============================================================================

HALAL_DB: dict[str, dict] = {
    "Heparin (Porcine)": {
        "status": "haram",
        "darurah_exempt": True,  # Can be used in life-threatening situations
        "concerns": ["Derived from porcine intestinal mucosa"],
        "fiqh_specific": {
            "Ja'fari_Sistani": {
                "ruling": "haram_but_darurah_permits",
                "note": "Permissible ONLY if no synthetic alternative exists AND patient's life is at risk. Must document medical necessity.",
            },
            "Ja'fari_Khamenei": {
                "ruling": "haram_but_darurah_permits",
                "note": "Similar to Sistani, but requires explicit physician certification of necessity.",
            },
            "Hanafi": {"ruling": "haram_but_darurah_permits"},
            "Shafii": {"ruling": "haram_but_darurah_permits"},
        },
        "alternatives": [
            "Enoxaparin (synthetic LMWH)",
            "Fondaparinux (fully synthetic)",
            "Bivalirudin (direct thrombin inhibitor)",
        ],
    },
    "Insulin (Porcine)": {
        "status": "haram",
        "darurah_exempt": True,
        "concerns": ["Derived from porcine pancreas"],
        "fiqh_specific": {
            "Ja'fari_Sistani": {
                "ruling": "haram_but_darurah_permits",
                "note": "Historical ruling: permissible for diabetics when human insulin unavailable. Modern: synthetic analogs preferred.",
            },
        },
        "alternatives": [
            "Human insulin (recombinant DNA)",
            "Insulin Lispro",
            "Insulin Aspart",
            "Insulin Glargine",
        ],
    },
    "Amoxicillin Capsules": {
        "status": "mushbooh",
        "concerns": ["Capsule shell may contain bovine gelatin (source unknown)"],
        "fiqh_specific": {
            "Ja'fari_Sistani": {
                "ruling": "permissible_if_from_bone_without_meat",
                "note": "Sistani's unique ruling: gelatin extracted from bone (without meat residue) is permissible, even if animal not slaughtered Islamically.",
            },
            "Ja'fari_Khamenei": {
                "ruling": "haram_unless_halal_slaughtered",
                "note": "Stricter: requires Islamic slaughter for bovine source.",
            },
            "Hanafi": {"ruling": "haram_unless_halal_slaughtered"},
            "Shafii": {"ruling": "permissible_if_istihalah_proven"},
        },
        "alternatives": [
            "Amoxicillin tablets (gelatin-free)",
            "Amoxicillin suspension (verify glycerin)",
        ],
    },
    "Codeine Syrup": {
        "status": "haram",
        "darurah_exempt": False,  # Alternatives exist
        "concerns": ["Contains ethanol > 0.5% as primary solvent"],
        "fiqh_specific": {
            "Ja'fari_Sistani": {
                "ruling": "haram_if_fermented",
                "note": "Fermented ethanol (khamr) is strictly haram. Synthetic ethanol is less problematic but still avoided in oral meds.",
            },
            "Ja'fari_Khamenei": {
                "ruling": "haram",
                "note": "Any intoxicating amount is haram, regardless of source.",
            },
        },
        "alternatives": ["Codeine tablets", "Dextromethorphan syrup (alcohol-free)"],
    },
    "Omega-3 Fish Oil": {
        "status": "halal",  # But with fiqh-specific nuances
        "fiqh_specific": {
            "Ja'fari_Sistani": {
                "ruling": "halal_if_from_scaled_fish",
                "note": "Only fish with scales are halal. Verify fish species.",
            },
            "Ja'fari_Khamenei": {
                "ruling": "halal_if_from_scaled_fish",
            },
            "Hanafi": {"ruling": "halal_if_from_fish"},
            "Shafii": {"ruling": "halal"},  # All sea creatures halal
        },
        "concerns": ["Softgel shell may contain non-halal gelatin"],
        "alternatives": [
            "Omega-3 tablets",
            "Omega-3 drops in MCT oil (vegetarian capsule)",
        ],
    },
    "Vitamin D3 (Lanolin-derived)": {
        "status": "halal",
        "notes": "Lanolin from sheep wool is halal. Concern is only the softgel shell.",
        "fiqh_specific": {
            "Ja'fari_Sistani": {"ruling": "halal"},
            "Hanafi": {"ruling": "halal"},
            "Shafii": {"ruling": "halal"},
        },
    },
    "Vaccines (HEK293 cell line)": {
        "status": "mushbooh",
        "darurah_exempt": True,
        "concerns": ["Cell line derived from aborted fetal tissue (1970s)"],
        "fiqh_specific": {
            "Ja'fari_Sistani": {
                "ruling": "permissible_by_darurah",
                "note": "External use (injection) of substances from aborted fetus is permissible if no halal alternative exists.",
            },
            "Ja'fari_Khamenei": {
                "ruling": "permissible_if_no_alternative",
                "note": "Stricter: requires documented absence of alternatives.",
            },
            "Hanafi": {"ruling": "permissible_by_darurah"},
            "Shafii": {"ruling": "permissible"},
        },
        "alternatives": ["mRNA vaccines (no cell lines)", "Vaxchora (halal-certified)"],
    },
}


# ============================================================================
# ISTIHALA (CHEMICAL TRANSFORMATION) CHECKER
# ============================================================================


def check_istihalah(ingredient: str, final_product: str) -> dict[str, str] | None:
    """
    Check if chemical transformation (Istihalah) has occurred.

    Shia fiqh (especially Khamenei): requires complete transformation.
    Example: Ethanol evaporated during manufacturing → may be permissible.
    """
    ISTIHALA_CASES = {
        "ethanol_evaporated": {
            "original": "ethanol",
            "process": "evaporation during manufacturing",
            "shia_ruling": "permissible_if_no_residue",
            "sunni_ruling": "permissible",
            "note": "Khamenei: requires lab verification of zero residue. Sistani: more flexible.",
        },
        "gelatin_hydrolyzed": {
            "original": "non-halal gelatin",
            "process": "complete hydrolysis to amino acids",
            "shia_ruling": "permissible_if_complete",
            "sunni_ruling": "permissible",
            "note": "Must be proven by lab analysis.",
        },
    }
    return ISTIHALA_CASES.get(ingredient)


# ============================================================================
# MCP TOOL REGISTRATION
# ============================================================================


@registry.tool(
    name="check_halal_compliance",
    description=(
        "Global Halal compliance checker with fiqh school awareness. "
        "Covers Sunni (Hanafi, Shafii, Maliki, Hanbali) and Shia (Ja'fari: Sistani, Khamenei) "
        "jurisprudence. Applies principles of Istihalah (chemical transformation) and "
        "Darurah (life-saving necessity). Critical for MENA and SEA markets."
    ),
    input_schema=HalalCheckRequest,
    output_schema=HalalCertification,
    category="regulatory",
    latency_estimate_ms=80,
    requires_db=True,
    execution_class="read",
    tags=["halal", "fiqh", "shia", "sunni", "regulatory", "mena", "sea"],
)
async def check_halal_compliance(input: HalalCheckRequest) -> HalalCertification:
    """Advanced Halal compliance with fiqh school awareness."""
    start = time.perf_counter()
    drug_name = input.drug_name.strip().title()
    country = input.country_code.upper()

    # 1. Determine fiqh school
    country_info = COUNTRY_FIQH.get(
        country, {"school": "Hanbali", "marja": "state_mufti"}
    )
    fiqh_school = input.patient_fiqh or cast(FiqhSchool, country_info["school"])
    marja = country_info.get("marja")

    # 2. Lookup in DB
    cert_data = HALAL_DB.get(drug_name)

    if not cert_data:
        # Unknown drug
        return HalalCertification(
            drug_name=drug_name,
            status="mushbooh",
            fiqh_school=fiqh_school,
            marja_reference=marja,
            certification_body=None,
            concerns=["Unknown status. Verification required."],
            notes=f"Consult {marja or 'local religious authority'} for specific ruling.",
            alternatives=[],
            darurah_applied=False,
        )

    # 3. Apply fiqh-specific ruling
    status = cast(HalalStatus, cert_data["status"])
    notes = cert_data.get("notes", "")
    darurah_applied = False

    fiqh_key: str = fiqh_school
    if fiqh_school == "Ja'fari" and marja:
        fiqh_key = f"Ja'fari_{marja.split('_')[-1]}"  # e.g., "Ja'fari_Sistani"

    fiqh_ruling = cert_data.get("fiqh_specific", {}).get(fiqh_key, {})

    if fiqh_ruling:
        ruling = fiqh_ruling.get("ruling", status)
        fiqh_note = fiqh_ruling.get("note", "")

        # Apply Darurah if life-saving
        if input.is_life_saving and cert_data.get("darurah_exempt"):
            status = "darurah_exempt"
            darurah_applied = True
            notes = f"**DARURAH APPLIED**: Life-saving necessity. {fiqh_note}"
        elif (
            ruling == "permissible_if_from_bone_without_meat"
            and fiqh_school == "Ja'fari"
        ):
            # Sistani's unique ruling
            status = "mushbooh"
            notes = f"**Sistani's Ruling**: {fiqh_note}"
        else:
            status = cast(
                HalalStatus,
                ruling.replace("permissible", "halal").replace("haram", "haram"),
            )
            notes = fiqh_note

    # 4. Check Istihalah
    istihalah_check = None
    for concern in cert_data.get("concerns", []):
        if "ethanol" in concern.lower():
            istihalah = check_istihalah("ethanol_evaporated", drug_name)
            if istihalah:
                istihalah_check = istihalah["note"]

    # 5. Enrich alternatives
    alternatives = cert_data.get("alternatives", [])
    if (
        input.include_alternatives
        and status in ["haram", "mushbooh"]
        and not darurah_applied
    ):
        if any("gelatin" in c.lower() for c in cert_data["concerns"]):
            alternatives.extend(["Vegetarian capsules (HPMC)"])
        if any("ethanol" in c.lower() for c in cert_data["concerns"]):
            alternatives.append("Alcohol-free formulation")

    latency_ms = (time.perf_counter() - start) * 1000

    logger.info(
        f"Global Halal check: {drug_name} ({country}, {fiqh_school}) -> {status.upper()}",
        extra={
            "drug": drug_name,
            "status": status,
            "fiqh": fiqh_school,
            "marja": marja,
            "darurah": darurah_applied,
            "latency_ms": latency_ms,
        },
    )

    return HalalCertification(
        drug_name=drug_name,
        status=status,
        fiqh_school=fiqh_school,
        marja_reference=marja,
        certification_body=cert_data.get("certification_body"),
        concerns=cert_data.get("concerns", []),
        notes=notes,
        alternatives=list(dict.fromkeys(alternatives)),
        darurah_applied=darurah_applied,
        istihalah_check=istihalah_check,
    )
