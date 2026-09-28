"""Validate the real-world halal evidence source registry."""

from __future__ import annotations

import json
from pathlib import Path


FIXTURE = (
    Path(__file__).parent / "fixtures" / "halal_real_world_sources.json"
)

EXPECTED_SOURCE_IDS = {
    "us_dailymed",
    "eu_ema",
    "id_bpom_bpjph",
    "ir_ttac",
    "iq_gudea",
    "my_npra_jakim",
    "eg_eda",
}


def test_real_world_source_registry_is_complete() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    sources = payload["sources"]

    assert {source["id"] for source in sources} == EXPECTED_SOURCE_IDS
    assert len(sources) == 7
    assert all(source["country"] for source in sources)
    assert all(source["authority"] for source in sources)
    assert all(source["role"] for source in sources)


def test_real_world_registry_keeps_evidence_separate_from_halal_status() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert "status_policy" in payload
    assert "halal_status" not in payload
    assert "expected_halal_status" not in payload
