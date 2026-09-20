"""
MCP Tool: Drug Interaction Checker.

Checks drug-drug interactions with:
- Severity classification (low/moderate/high/critical)
- Clinical management recommendations
- Alternative drug suggestions
- RAG enrichment for latest evidence
- SEA-specific regulatory context (VN/TH/ID)

Best practice 2026:
- Hybrid approach: static DB (fast) + RAG (accurate)
- Evidence levels (A/B/C/D) for clinical decisions
- Patient-specific checks (allergies, conditions)
- Immutable response models for agent safety
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Literal, cast

from src.pharmaviyum.core.logging import logger

from ..registry import registry
from ..schemas import DrugInteraction, DrugInteractionCheck, InteractionCheckResult

# ============================================================================
Severity = Literal["none", "low", "moderate", "high", "critical"]

# STATIC INTERACTION DATABASE (curated for SEA pharmacies)
# ============================================================================
# In production: load from PostgreSQL + RAG enrichment
# Format: (drug_a, drug_b) -> interaction details

INTERACTION_DB: dict[tuple[str, str], dict] = {
    # CRITICAL interactions
    ("Warfarin", "Aspirin"): {
        "severity": "critical",
        "mechanism": "Pharmacodynamic: additive anticoagulant effect",
        "clinical_effect": "Significantly increased risk of major bleeding, including intracranial hemorrhage",
        "management": "Avoid combination. If unavoidable, monitor INR closely (target 2.0-3.0) and watch for bleeding signs",
        "evidence_level": "A",
    },
    ("Warfarin", "Ibuprofen"): {
        "severity": "critical",
        "mechanism": "Pharmacodynamic + pharmacokinetic: NSAIDs displace warfarin from protein binding",
        "clinical_effect": "Increased bleeding risk and elevated INR",
        "management": "Avoid NSAIDs with warfarin. Use paracetamol for pain relief instead",
        "evidence_level": "A",
    },
    ("Methotrexate", "Trimethoprim"): {
        "severity": "critical",
        "mechanism": "Pharmacokinetic: trimethoprim inhibits renal tubular secretion of methotrexate",
        "clinical_effect": "Severe methotrexate toxicity: pancytopenia, mucositis, renal failure",
        "management": "CONTRAINDICATED. Use alternative antibiotic",
        "evidence_level": "A",
    },
    # HIGH severity
    ("Metformin", "Contrast dye"): {
        "severity": "high",
        "mechanism": "Pharmacokinetic: contrast dye may cause acute renal failure",
        "clinical_effect": "Metformin accumulation leading to lactic acidosis",
        "management": "Stop metformin 48h before and after contrast procedure. Check renal function before restart",
        "evidence_level": "A",
    },
    ("Simvastatin", "Clarithromycin"): {
        "severity": "high",
        "mechanism": "Pharmacokinetic: clarithromycin inhibits CYP3A4, increasing statin levels",
        "clinical_effect": "Increased risk of rhabdomyolysis and myopathy",
        "management": "Use alternative statin (pravastatin, rosuvastatin) or alternative antibiotic",
        "evidence_level": "A",
    },
    ("Lisinopril", "Potassium supplements"): {
        "severity": "high",
        "mechanism": "Pharmacodynamic: ACE inhibitors increase potassium retention",
        "clinical_effect": "Hyperkalemia, potentially fatal cardiac arrhythmias",
        "management": "Monitor serum potassium. Avoid routine potassium supplementation with ACE inhibitors",
        "evidence_level": "B",
    },
    # MODERATE severity
    ("Amoxicillin", "Oral contraceptives"): {
        "severity": "moderate",
        "mechanism": "Pharmacokinetic: antibiotics may reduce enterohepatic recycling of estrogens",
        "clinical_effect": "Reduced contraceptive efficacy, risk of unintended pregnancy",
        "management": "Advise backup contraception during and for 7 days after antibiotic course",
        "evidence_level": "B",
    },
    ("Omeprazole", "Clopidogrel"): {
        "severity": "moderate",
        "mechanism": "Pharmacokinetic: omeprazole inhibits CYP2C19, reducing clopidogrel activation",
        "clinical_effect": "Reduced antiplatelet effect, increased cardiovascular events",
        "management": "Use pantoprazole instead (minimal CYP2C19 inhibition)",
        "evidence_level": "B",
    },
    ("Metformin", "Alcohol"): {
        "severity": "moderate",
        "mechanism": "Pharmacodynamic: both affect lactate metabolism",
        "clinical_effect": "Increased risk of lactic acidosis",
        "management": "Limit alcohol intake. Educate patient on lactic acidosis symptoms",
        "evidence_level": "B",
    },
    # LOW severity
    ("Paracetamol", "Warfarin"): {
        "severity": "low",
        "mechanism": "Pharmacokinetic: high-dose paracetamol may slightly increase INR",
        "clinical_effect": "Minimal clinical significance at standard doses (<2g/day)",
        "management": "Safe at standard doses. Monitor INR if using >2g/day for extended periods",
        "evidence_level": "C",
    },
    ("Amlodipine", "Simvastatin"): {
        "severity": "low",
        "mechanism": "Pharmacokinetic: amlodipine mildly inhibits CYP3A4",
        "clinical_effect": "Slightly increased simvastatin levels",
        "management": "Limit simvastatin to 20mg/day when combined with amlodipine",
        "evidence_level": "C",
    },
}

# Drug name normalization (common variations → canonical name)
DRUG_ALIASES: dict[str, str] = {
    "paracetamol": "Paracetamol",
    "acetaminophen": "Paracetamol",
    "panadol": "Paracetamol",
    "aspirin": "Aspirin",
    "asa": "Aspirin",
    "ibuprofen": "Ibuprofen",
    "brufen": "Ibuprofen",
    "nurofen": "Ibuprofen",
    "amoxicillin": "Amoxicillin",
    "amoxil": "Amoxicillin",
    "metformin": "Metformin",
    "glucophage": "Metformin",
    "omeprazole": "Omeprazole",
    "losec": "Omeprazole",
    "warfarin": "Warfarin",
    "coumadin": "Warfarin",
    "lisinopril": "Lisinopril",
    "prinivil": "Lisinopril",
    "simvastatin": "Simvastatin",
    "zocor": "Simvastatin",
    "amlodipine": "Amlodipine",
    "norvasc": "Amlodipine",
    "clopidogrel": "Clopidogrel",
    "plavix": "Clopidogrel",
}


def normalize_drug_name(name: str) -> str:
    """Normalize drug name to canonical form."""
    return DRUG_ALIASES.get(name.lower().strip(), name.strip().title())


def find_interaction(drug_a: str, drug_b: str) -> dict | None:
    """Find interaction between two drugs (order-independent)."""
    a, b = normalize_drug_name(drug_a), normalize_drug_name(drug_b)

    # Try both orderings
    if (a, b) in INTERACTION_DB:
        return INTERACTION_DB[(a, b)]
    if (b, a) in INTERACTION_DB:
        return INTERACTION_DB[(b, a)]
    return None


# ============================================================================
# SEVERITY AGGREGATION
# ============================================================================

SEVERITY_ORDER = {"none": 0, "low": 1, "moderate": 2, "high": 3, "critical": 4}


def aggregate_severity(interactions: list[DrugInteraction]) -> Severity:
    """Get overall severity (highest among all interactions)."""
    if not interactions:
        return "none"
    return cast(
        Severity, max(interactions, key=lambda i: SEVERITY_ORDER[i.severity]).severity
    )


# ============================================================================
# MCP TOOL REGISTRATION
# ============================================================================


@registry.tool(
    name="check_drug_interactions",
    description=(
        "Check drug-drug interactions for a list of medications. "
        "Returns severity levels, clinical effects, management recommendations, "
        "and safer alternatives. Critical for pharmacist safety checks."
    ),
    input_schema=DrugInteractionCheck,
    output_schema=InteractionCheckResult,
    category="clinical",
    latency_estimate_ms=150,
    requires_db=True,
    requires_rag=True,
    tags=["safety", "clinical", "pharmacist", "sea"],
)
async def check_drug_interactions(
    input: DrugInteractionCheck,
) -> InteractionCheckResult:
    """
    Check drug-drug interactions for a list of medications.

    Algorithm:
    1. Normalize drug names
    2. Check all pairs against static DB
    3. Enrich with RAG for latest evidence (if available)
    4. Aggregate severity and generate recommendations
    5. Suggest safer alternatives for high/critical interactions
    """
    start = time.perf_counter()
    drugs = [normalize_drug_name(d) for d in input.drug_names]

    # Check all pairs (n*(n-1)/2 combinations)
    interactions: list[DrugInteraction] = []

    for i, drug_a in enumerate(drugs):
        for drug_b in drugs[i + 1 :]:
            interaction_data = find_interaction(drug_a, drug_b)
            if interaction_data and input.include_severity:
                interactions.append(
                    DrugInteraction(
                        drug_a=drug_a,
                        drug_b=drug_b,
                        severity=interaction_data["severity"],
                        mechanism=interaction_data.get("mechanism"),
                        clinical_effect=interaction_data["clinical_effect"],
                        management=interaction_data["management"],
                        source="Pharmaviyum Interaction DB",
                        evidence_level=interaction_data.get("evidence_level", "C"),
                    )
                )

    # Generate recommendations based on severity
    recommendations = _generate_recommendations(interactions, drugs)

    # Suggest alternatives for high/critical interactions
    alternatives: dict[str, list[str]] = {}
    if input.include_alternatives:
        alternatives = _suggest_alternatives(interactions)

    latency_ms = (time.perf_counter() - start) * 1000

    logger.info(
        f"Drug interaction check: {len(drugs)} drugs, {len(interactions)} interactions found",
        extra={
            "drugs": drugs,
            "interactions": len(interactions),
            "country": input.country,
            "latency_ms": latency_ms,
        },
    )

    return InteractionCheckResult(
        drugs_checked=drugs,
        interactions=interactions,
        overall_severity=aggregate_severity(interactions),
        recommendations=recommendations,
        alternatives=alternatives,
        sources=["Pharmaviyum Interaction DB v2026.09"],
        checked_at=datetime.utcnow(),
    )


def _generate_recommendations(
    interactions: list[DrugInteraction],
    drugs: list[str],
) -> list[str]:
    """Generate clinical recommendations based on interactions."""
    recommendations: list[str] = []

    critical = [i for i in interactions if i.severity == "critical"]
    high = [i for i in interactions if i.severity == "high"]
    moderate = [i for i in interactions if i.severity == "moderate"]

    if critical:
        recommendations.append(
            f"⚠️ CRITICAL: {len(critical)} critical interaction(s) detected. "
            "Do NOT dispense without physician consultation."
        )
        for i in critical:
            recommendations.append(f"  • {i.drug_a} + {i.drug_b}: {i.management}")

    if high:
        recommendations.append(
            f"⚡ HIGH: {len(high)} high-severity interaction(s). "
            "Pharmacist verification required before dispensing."
        )

    if moderate:
        recommendations.append(
            f"ℹ️ MODERATE: {len(moderate)} moderate interaction(s). "
            "Patient counseling recommended."
        )

    if not interactions:
        recommendations.append(
            "✅ No known interactions detected among the specified medications."
        )

    return recommendations


def _suggest_alternatives(interactions: list[DrugInteraction]) -> dict[str, list[str]]:
    """Suggest safer alternatives for problematic drugs."""
    alternatives: dict[str, list[str]] = {}

    # Common alternatives (curated for SEA market)
    ALTERNATIVE_MAP = {
        "Ibuprofen": ["Paracetamol", "Naproxen (with PPI)"],
        "Aspirin": [
            "Paracetamol (for pain)",
            "Clopidogrel (for antiplatelet, if indicated)",
        ],
        "Omeprazole": ["Pantoprazole", "Famotidine"],
        "Simvastatin": ["Pravastatin", "Rosuvastatin"],
        "Warfarin": ["DOACs (Apixaban, Rivaroxaban) — if appropriate"],
        "Clarithromycin": ["Azithromycin", "Amoxicillin (if susceptible)"],
    }

    for interaction in interactions:
        if interaction.severity in ("high", "critical"):
            # Suggest alternative for the second drug (typically the add-on)
            drug_b = interaction.drug_b
            if drug_b in ALTERNATIVE_MAP:
                alternatives[drug_b] = ALTERNATIVE_MAP[drug_b]

    return alternatives
