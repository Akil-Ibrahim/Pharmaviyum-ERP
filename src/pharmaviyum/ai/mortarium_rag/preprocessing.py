"""
Document Preprocessing Pipeline.

Best practice 2026:
- Text normalization for multi-language SEA/MENA content (vi, ar, th, id, en)
- Domain-specific metadata extraction (drug names, regulatory bodies)
- Pre-ingestion PII redaction for healthcare compliance (HIPAA/GDPR)
- Content hashing for deduplication
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

from src.pharmaviyum.ai.mortarium_rag.schemas import Document
from src.pharmaviyum.core.logging import logger


class TextNormalizer:
    """Normalizes text for consistent chunking and embedding."""

    WHITESPACE_PATTERN = re.compile(r"[\s\u200b\u200c\u200d\u2060]+")

    @classmethod
    def normalize(cls, text: str) -> str:
        """Normalize text for consistent chunking and embedding."""
        if not text:
            return ""
        text = unicodedata.normalize("NFKC", text)
        text = cls.WHITESPACE_PATTERN.sub(" ", text)
        text = text.replace("- \n", "")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


class MetadataExtractor:
    """Extracts domain-specific metadata for optimized vector search filtering."""

    REGULATORY_BODIES = {
        "MUI", "JAKIM", "BPOM", "SFDA", "ESMA", "GSO", "IFDA", "IQS",
        "YSMO", "Ministry of Health", "FDA Thailand", "Al-Azhar", "Diyanet",
    }
    DRUG_CATEGORIES = {
        "antibiotic", "analgesic", "antihypertensive", "antidiabetic",
        "anticoagulant", "psychotropic", "narcotic", "vitamin", "vaccine",
    }

    @classmethod
    def extract(cls, content: str, existing_metadata: dict[str, Any]) -> dict[str, Any]:
        """Extract and enrich metadata from document content."""
        content_lower = content.lower()
        extracted = existing_metadata.copy()
        found_regulators = [
            body for body in cls.REGULATORY_BODIES
            if body.lower() in content_lower or body in content
        ]
        if found_regulators:
            extracted["regulatory_bodies"] = found_regulators
        found_categories = [cat for cat in cls.DRUG_CATEGORIES if cat in content_lower]
        if found_categories:
            extracted["drug_categories"] = list(set(found_categories))
        word_count = len(content.split())
        extracted["word_count"] = word_count
        extracted["is_long_form"] = word_count > 2000
        if "language" not in extracted or extracted["language"] == "unknown":
            extracted["language"] = cls._detect_language_simple(content)
        return extracted

    @classmethod
    def _detect_language_simple(cls, text: str) -> str:
        """Fast heuristic language detection."""
        text_sample = text[:500].lower()
        if re.search(r"[\u0600-\u06FF]", text):
            return "ar"
        if re.search(r"[\u0E00-\u0E7F]", text):
            return "th"
        if re.search(r"[đơưăếầậổ]", text):
            return "vi"
        if re.search(r"\b(dengan|untuk|yang|dan)\b", text_sample):
            return "id"
        return "en"


class PIIRedactor:
    """Redacts Personally Identifiable Information before ingestion."""

    PATTERNS = {
        "phone": re.compile(r"\+?\d[\d\s\-]{7,15}\d"),
        "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
        "national_id_vn": re.compile(r"\b\d{9,12}\b"),
        "national_id_id": re.compile(r"\b\d{16}\b"),
        "patient_name": re.compile(r"\bPatient Name:\s*[A-Za-z\s]+\b", re.IGNORECASE),
    }

    @classmethod
    def redact(cls, content: str) -> tuple[str, list[str]]:
        """Redact PII from content."""
        redacted_types = []
        redacted_content = content
        for pii_type, pattern in cls.PATTERNS.items():
            if pattern.search(redacted_content):
                redacted_content = pattern.sub(
                    f"[REDACTED_{pii_type.upper()}]", redacted_content
                )
                redacted_types.append(pii_type)
        if redacted_types:
            logger.info(f"Redacted PII types: {redacted_types}")
        return redacted_content, redacted_types


class DocumentPreprocessor:
    """Main orchestrator for document preprocessing."""

    def __init__(self, enable_pii_redaction: bool = True):
        self.enable_pii_redaction = enable_pii_redaction

    def process(self, document: Document) -> Document:
        """Apply full preprocessing pipeline to a document."""
        clean_content = TextNormalizer.normalize(document.content)
        redacted_content = clean_content
        redacted_types = []
        if self.enable_pii_redaction:
            redacted_content, redacted_types = PIIRedactor.redact(clean_content)
        enriched_metadata = MetadataExtractor.extract(
            redacted_content, document.metadata
        )
        if redacted_types:
            enriched_metadata["pii_redacted"] = redacted_types
        content_hash = hashlib.sha256(redacted_content.encode("utf-8")).hexdigest()
        enriched_metadata["content_hash"] = content_hash
        return Document(
            id=document.id,
            content=redacted_content,
            source=document.source,
            doc_type=document.doc_type,
            metadata=enriched_metadata,
            country=document.country,
            language=enriched_metadata.get("language", document.language),
            created_at=document.created_at,
        )
