"""
PDF Document Loader for medical/pharmaceutical documents.

Best practice 2026:
- PyMuPDF (fitz) for fast extraction
- OCR fallback for scanned documents
- Table extraction for dosage charts
- Multi-page metadata tracking
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, AsyncIterator

from src.pharmaviyum.ai.rag.schemas import Document
from src.pharmaviyum.core.logging import logger

from .base import LoaderConfig


class PDFLoader:
    """Load and parse PDF documents with OCR and table support."""

    def __init__(self):
        self._fitz = None

    def _get_fitz(self):
        if self._fitz is None:
            try:
                import fitz  # PyMuPDF

                self._fitz = fitz
            except ImportError:
                raise ImportError("Install PyMuPDF: pip install pymupdf")
        return self._fitz

    async def load(self, source: str, config: LoaderConfig) -> AsyncIterator[Document]:
        """Load PDF document page by page."""
        fitz = self._get_fitz()
        path = Path(source)

        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {source}")

        doc = fitz.open(str(path))
        logger.info(f"Loading PDF: {path.name} ({len(doc)} pages)")

        try:
            # Extract document-level metadata
            meta = doc.metadata or {}
            base_metadata = {
                "source": str(path),
                "filename": path.name,
                "page_count": len(doc),
                "title": meta.get("title", ""),
                "author": meta.get("author", ""),
                "subject": meta.get("subject", ""),
                "created": meta.get("creationDate", ""),
                "modified": meta.get("modDate", ""),
            }

            # Process each page
            for page_num, page in enumerate(doc, 1):
                text = page.get_text("text").strip()

                # OCR fallback if text is empty (scanned PDF)
                if not text and config.ocr_enabled:
                    text = await self._ocr_page(page, config.languages)

                if not text:
                    continue

                # Extract tables if enabled
                tables = []
                if config.extract_tables:
                    tables = await self._extract_tables(page)

                # Build page content
                content = text
                if tables:
                    content += "\n\n[TABLES]\n" + "\n---\n".join(tables)

                page_metadata = {
                    **base_metadata,
                    "page_number": page_num,
                    "has_tables": len(tables) > 0,
                    "table_count": len(tables),
                    "ocr_used": not page.get_text("text").strip()
                    and config.ocr_enabled,
                }

                yield Document(
                    content=content,
                    source=str(path),
                    doc_type="drug_info",  # Can be overridden
                    metadata=page_metadata,
                    country=config.metadata_filters.get("country", "VN"),
                    language=self._detect_language(text, config.languages),
                )
        finally:
            doc.close()

    async def _ocr_page(self, page, languages: list[str]) -> str:
        """OCR fallback for scanned pages."""
        try:
            import pytesseract
            from PIL import Image

            # Convert page to image
            pix = page.get_pixmap(dpi=300)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))

            # Map our language codes to Tesseract
            lang_map = {
                "vi": "vie",
                "en": "eng",
                "ar": "ara",
                "th": "tha",
                "id": "ind",
            }
            tess_langs = "+".join([lang_map.get(lang, "eng") for lang in languages])

            text = pytesseract.image_to_string(img, lang=tess_langs)
            logger.debug(f"OCR extracted {len(text)} chars from page")
            return text
        except Exception as e:
            logger.warning(f"OCR failed: {e}")
            return ""

    async def _extract_tables(self, page) -> list[str]:
        """Extract tables from page as formatted text."""
        tables = []
        try:
            tab_finder = page.find_tables()
            for table in tab_finder.tables:
                df = table.to_pandas()
                # Convert DataFrame to readable text
                table_text = df.to_markdown(index=False)
                tables.append(table_text)
        except Exception as e:
            logger.debug(f"Table extraction failed: {e}")
        return tables

    def _detect_language(self, text: str, languages: list[str]) -> str:
        """Simple language detection based on character patterns."""
        try:
            from langdetect import detect

            return detect(text[:500])
        except Exception:
            return languages[0] if languages else "en"

    async def validate_source(self, source: str) -> bool:
        path = Path(source)
        return path.exists() and path.suffix.lower() == ".pdf"

    def get_loader_info(self) -> dict[str, Any]:
        return {"name": "pdf_loader", "version": "1.0", "formats": ["pdf"]}
