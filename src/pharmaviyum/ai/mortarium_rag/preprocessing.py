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

    # Multi-language whitespace and control character cleanup
    WHITESPACE_PATTERN = re.compile(r"[\s\u200b\u200c\u200d\u2060]+")

    @classmethod
    def normalize(cls, text: str) -> str:
        """
        Normalize text:
        1. NFKC Unicode normalization (fixes weird encodings)
        2. Collapse multiple whitespaces/newlines
        3. Strip leading/trailing whitespace
        """
        if not text:
            return ""

        # Unicode normalization
        text = unicodedata.normalize("NFKC", text)

        # Collapse whitespace
        text = cls.WHITESPACE_PATTERN.sub(" ", text)

        # Clean up specific artifacts from PDF/OCR
        text = text.replace("- \n", "")  # Fix hyphenated line breaks
        text = re.sub(r"\n{3,}", "\n\n", text)  # Max 2 consecutive newlines

        return text.strip()


class MetadataExtractor:
    """Extracts domain-specific metadata for optimized vector search filtering."""

    # Regulatory bodies in SEA/MENA
    REGULATORY_BODIES = {
        "MUI",
        "JAKIM",
        "BPOM",
        "SFDA",
        "ESMA",
        "GSO",
        "IFDA",
        "IQS",
        "YSMO",
        "Ministry of Health",
        "FDA Thailand",
        "Al-Azhar",
        "Diyanet",
    }

    # Common drug categories (simplified for extraction)
    DRUG_CATEGORIES = {
        "antibiotic",
        "analgesic",
        "antihypertensive",
        "antidiabetic",
        "anticoagulant",
        "psychotropic",
        "narcotic",
        "vitamin",
        "vaccine",
    }

    @classmethod
    def extract(cls, content: str, existing_metadata: dict[str, Any]) -> dict[str, Any]:
        """Extract and enrich metadata from document content."""
        content_lower = content.lower()
        extracted = existing_metadata.copy()

        # 1. Detect regulatory bodies mentioned
        found_regulators = [
            body
            for body in cls.REGULATORY_BODIES
            if body.lower() in content_lower or body in content
        ]
        if found_regulators:
            extracted["regulatory_bodies"] = found_regulators

        # 2. Detect drug categories
        found_categories = [cat for cat in cls.DRUG_CATEGORIES if cat in content_lower]
        if found_categories:
            extracted["drug_categories"] = list(set(found_categories))

        # 3. Estimate document complexity (word count)
        word_count = len(content.split())
        extracted["word_count"] = word_count
        extracted["is_long_form"] = word_count > 2000

        # 4. Language confidence (if not already set)
        if "language" not in extracted or extracted["language"] == "unknown":
            extracted["language"] = cls._detect_language_simple(content)

        return extracted

    @classmethod
    def _detect_language_simple(cls, text: str) -> str:
        """Fast heuristic language detection."""
        text_sample = text[:500].lower()

        # Arabic script detection
        if re.search(r"[\u0600-\u06FF]", text):
            return "ar"
        # Thai script detection
        if re.search(r"[\u0E00-\u0E7F]", text):
            return "th"
        # Vietnamese specific characters
        if re.search(r"[đơưăếầậổ]", text):
            return "vi"
        # Indonesian/Malay specific patterns
        if re.search(r"\b(dengan|untuk|yang|dan)\b", text_sample):
            return "id"

        return "en"  # Default fallback


class PIIRedactor:
    """Redacts Personally Identifiable Information before ingestion."""

    # Patterns for common PII
    PATTERNS = {
        "phone": re.compile(r"\+?\d[\d\s\-]{7,15}\d"),
        "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
        "national_id_vn": re.compile(r"\b\d{9,12}\b"),  # Vietnamese ID
        "national_id_id": re.compile(r"\b\d{16}\b"),  # Indonesian NIK
        "patient_name": re.compile(r"\bPatient Name:\s*[A-Za-z\s]+\b", re.IGNORECASE),
    }

    @classmethod
    def redact(cls, content: str) -> tuple[str, list[str]]:
        """
        Redact PII from content.
        Returns: (redacted_content, list_of_redacted_types)
        """
        redacted_types: list[str] = []
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
    """
    Main orchestrator for document preprocessing.

    Pipeline:
    1. Normalize text
    2. Redact PII (security first)
    3. Extract metadata
    4. Generate content hash (for deduplication)
    """

    def __init__(self, enable_pii_redaction: bool = True):
        self.enable_pii_redaction = enable_pii_redaction

    def process(self, document: Document) -> Document:
        """Apply full preprocessing pipeline to a document."""

        # Step 1: Normalize
        clean_content = TextNormalizer.normalize(document.content)

        # Step 2: Redact PII
        redacted_content = clean_content
        redacted_types: list[str] = []
        if self.enable_pii_redaction:
            redacted_content, redacted_types = PIIRedactor.redact(clean_content)

        # Step 3: Extract Metadata
        enriched_metadata = MetadataExtractor.extract(
            redacted_content, document.metadata
        )
        if redacted_types:
            enriched_metadata["pii_redacted"] = redacted_types

        # Step 4: Generate Content Hash (for deduplication)
        content_hash = hashlib.sha256(redacted_content.encode("utf-8")).hexdigest()
        enriched_metadata["content_hash"] = content_hash

        # Return new immutable Document
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
