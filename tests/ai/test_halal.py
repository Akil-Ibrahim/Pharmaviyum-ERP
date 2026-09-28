from src.pharmaviyum.ai.halal import (
    HalalComponentEvidence,
    HalalStatus,
    assess_halal,
)


def test_porcine_component_is_haram() -> None:
    result = assess_halal(
        manufacturer="Example Pharma",
        source_documents=["official SmPC"],
        components=[
            HalalComponentEvidence(
                name="gelatin",
                origin="porcine",
            )
        ],
    )

    assert result.status == HalalStatus.HARAM


def test_bovine_component_without_halal_origin_is_unknown() -> None:
    result = assess_halal(
        manufacturer="Example Pharma",
        source_documents=["official SmPC"],
        components=[
            HalalComponentEvidence(
                name="gelatin",
                origin="bovine",
            )
        ],
    )

    assert result.status == HalalStatus.UNKNOWN


def test_halal_certification_can_support_halal_status() -> None:
    result = assess_halal(
        manufacturer="Example Pharma",
        source_documents=["manufacturer halal certificate"],
        components=[
            HalalComponentEvidence(
                name="cellulose",
                origin="plant",
            )
        ],
        halal_certified=True,
    )

    assert result.status == HalalStatus.HALAL


def test_missing_evidence_is_unknown() -> None:
    result = assess_halal(
        manufacturer="Example Pharma",
        source_documents=[],
        components=[],
    )

    assert result.status == HalalStatus.UNKNOWN
