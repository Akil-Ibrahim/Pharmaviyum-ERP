"""Explainable candidate matching for imported drug-catalog source records.

Scores are suggestions only. This module never writes catalog entities or review
decisions and deliberately avoids treating a source record as local authorization.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any


def _normalize(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", str(value).casefold()).strip()


def _similarity(left: Any, right: Any) -> float:
    a, b = _normalize(left), _normalize(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def _best_similarity(value: Any, candidates: list[str]) -> float:
    return max((_similarity(value, candidate) for candidate in candidates), default=0.0)


def _score_candidate(payload: dict, reference, product=None) -> tuple[float, list[str]]:
    ingredient = payload.get("ingredient_name") or payload.get("ingredient")
    if not ingredient:
        return 0.0, []

    ingredient_names = [reference.inn_name] + [
        item.ingredient_name for item in (reference.ingredients or [])
    ]
    ingredient_score = _best_similarity(ingredient, ingredient_names)
    if ingredient_score < 0.72:
        return 0.0, []

    weighted = [(0.50, ingredient_score, "active ingredient")]
    if product is not None:
        comparisons = (
            ("brand_name", "brand_name", 0.15, "brand"),
            ("strength", "strength", 0.15, "strength"),
            ("dosage_form", "dosage_form", 0.10, "dosage form"),
            ("route", "route", 0.05, "route"),
            ("country", "authorization_country", 0.05, "country"),
        )
        for source_key, target_key, weight, label in comparisons:
            source_value = payload.get(source_key)
            if source_key == "brand_name":
                source_value = source_value or payload.get("product_name")
            target_value = getattr(product, target_key, None)
            if source_value and target_value:
                weighted.append(
                    (weight, _similarity(source_value, target_value), label)
                )

    denominator = sum(weight for weight, _, _ in weighted)
    score = sum(weight * value for weight, value, _ in weighted) / denominator
    reasons = [
        f"{label}: {round(value * 100)}%"
        for _, value, label in weighted
        if value >= 0.80
    ]
    return round(score, 4), reasons


def suggest_matches(payload: dict | None, references: list) -> list[dict]:
    """Return ranked existing reference/product candidates, never auto-approve."""
    source = payload or {}
    candidates: list[dict] = []
    for reference in references:
        ref_score, ref_reasons = _score_candidate(source, reference)
        if ref_score >= 0.50:
            candidates.append(
                {
                    "target_type": "drug_reference",
                    "drug_reference_id": reference.id,
                    "medicinal_product_id": None,
                    "display_name": reference.inn_name,
                    "confidence": ref_score,
                    "reasons": ref_reasons,
                }
            )

        for product in reference.medicinal_products or []:
            score, reasons = _score_candidate(source, reference, product)
            if score < 0.50:
                continue
            label = product.brand_name or reference.inn_name
            candidates.append(
                {
                    "target_type": "medicinal_product",
                    "drug_reference_id": reference.id,
                    "medicinal_product_id": product.id,
                    "display_name": label,
                    "confidence": score,
                    "reasons": reasons,
                }
            )

    candidates.sort(
        key=lambda item: (
            item["confidence"],
            item["target_type"] == "medicinal_product",
        ),
        reverse=True,
    )
    return candidates[:10]


def rank_reference_ids(
    payload: dict | None,
    reference_rows: list[tuple[int, str]],
    ingredient_rows: list[tuple[int, str]],
    limit: int = 250,
) -> list[int]:
    """Rank lightweight reference-name rows before loading full ORM graphs.

    The scan intentionally uses the same fuzzy similarity function as the
    explainable matcher. Only the best bounded set of reference IDs is hydrated.
    """
    source = payload or {}
    ingredient = source.get("ingredient_name") or source.get("ingredient")
    if not ingredient or limit < 1:
        return []

    names_by_reference: dict[int, list[str]] = {}
    for reference_id, name in ingredient_rows:
        names_by_reference.setdefault(reference_id, []).append(name)

    ranked: list[tuple[float, int]] = []
    for reference_id, inn_name in reference_rows:
        names = [inn_name, *names_by_reference.get(reference_id, [])]
        score = _best_similarity(ingredient, names)
        if score >= 0.72:
            ranked.append((score, reference_id))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [reference_id for _, reference_id in ranked[:limit]]
