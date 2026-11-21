"""
Document Preprocessing for RAG Pipeline.

Best practice 2026:
- Text cleaning and normalization
- Language detection
- Metadata enrichment
- Deduplication checking
"""

from __future__ import annotations

import hashlib
import re

from src.pharmaviyum.core.logging import logger

from .loaders import LoadedDocument


class DocumentPreprocessor:
    """
    Preprocesses loaded documents before chunking.
    """

    def __init__(self):
        self._seen_hashes: set[str] = set()  # For deduplication

    def preprocess(
        self,
        doc: LoadedDocument,
        clean_text: bool = True,
        detect_language: bool = True,
        check_duplicates: bool = True,
    ) -> LoadedDocument | None:
        """
        Preprocess a document: clean, detect language, check duplicates.

        Returns:
            Preprocessed document, or None if duplicate
        """
        content = doc.content

        # 1. Clean text
        if clean_text:
            content = self._clean_text(content)

        # 2. Detect language
        if detect_language and doc.language == "auto":
            detected_lang = self._detect_language(content)
            doc.language = detected_lang
            doc.metadata["detected_language"] = detected_lang

        # 3. Check for duplicates
        if check_duplicates:
            content_hash = self._compute_hash(content)

            if content_hash in self._seen_hashes:
                logger.warning(f"Duplicate document detected: {doc.source}")
                return None

            self._seen_hashes.add(content_hash)
            doc.metadata["content_hash"] = content_hash

        # 4. Enrich metadata
        doc.metadata["char_count"] = len(content)
        doc.metadata["word_count"] = len(content.split())

        doc.content = content

        logger.info(
            f"Preprocessed document: {doc.source}",
            extra={
                "language": doc.language,
                "char_count": doc.metadata["char_count"],
                "word_count": doc.metadata["word_count"],
            },
        )

        return doc

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text.

        - Remove excessive whitespace
        - Normalize line breaks
        - Remove control characters
        """
        # Remove control characters (except newlines and tabs)
        text = re.sub(r"[\x00-\x09\x0b-\x1f\x7f-\x9f]", "", text)

        # Normalize line breaks
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove excessive whitespace (but preserve paragraph breaks)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def _detect_language(self, text: str) -> str:
        """
        Detect document language using heuristic patterns.

        For production, use langdetect or fasttext.
        """
        # Simple heuristic based on character patterns
        sample = text[:1000].lower()

        # Vietnamese indicators
        vi_patterns = [r"[àáạảãâầấậẩẫăằắặẳẵ]", r"[đ]", r"thuốc", r"bệnh nhân"]
        if any(re.search(p, sample) for p in vi_patterns):
            return "vi"

        # Thai indicators
        th_patterns = [r"[ก-๙]", r"ยา", r"ผู้ป่วย"]
        if any(re.search(p, sample) for p in th_patterns):
            return "th"

        # Arabic indicators
        ar_patterns = [r"[ء-ي]", r"دواء", r"مريض"]
        if any(re.search(p, sample) for p in ar_patterns):
            return "ar"

        # Indonesian/Malay indicators
        id_patterns = [r"obat", r"pasien", r"dokter"]
        if any(p in sample for p in id_patterns):
            return "id"

        # Default to English
        return "en"

    def _compute_hash(self, text: str) -> str:
        """Compute SHA256 hash of text for deduplication."""
        # Normalize before hashing
        normalized = re.sub(r"\s+", " ", text.strip().lower())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def reset_deduplication_cache(self):
        """Clear the deduplication cache (for new ingestion batches)."""
        self._seen_hashes.clear()
        logger.info("Deduplication cache reset")
