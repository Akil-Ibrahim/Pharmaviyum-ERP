import json
from pathlib import Path


FIXTURE = Path(__file__).parent / "fixtures" / "halal_100_common_drugs.json"


def test_halal_benchmark_contains_100_examples() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert len(data["cases"]) == 100
    assert len({item["id"] for item in data["cases"]}) == 100
    assert {item["test_evidence"] for item in data["cases"]} == {"synthetic_only"}


def test_halal_benchmark_covers_multiple_atc_groups() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))

    groups = {item["atc_group"] for item in data["cases"]}

    assert len(groups) >= 10
