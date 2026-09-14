"""
DOCX Document Loader for Word documents.

Best practice 2026:
- python-docx for .docx parsing
- Table extraction for structured data
- Paragraph-level metadata
"""
from __future__ import annotations
from typing import AsyncIterator, Any
from pathlib import Path
from .base import LoaderConfig
from src.pharmaviyum.ai.rag.schemas import Document
from src.pharmaviyum.core.logging import logger


class DOCXLoader:
    """Load Microsoft Word .docx documents."""
    
    async def load(self, source: str, config: LoaderConfig) -> AsyncIterator[Document]:
        """Load DOCX document."""
        try:
            from docx import Document as DocxDocument
            
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"DOCX not found: {source}")
            
            doc = DocxDocument(str(path))
            logger.info(f"Loading DOCX: {path.name}")
            
            # Extract core properties
            props = doc.core_properties
            base_metadata = {
                "source": str(path),
                "filename": path.name,
                "title": props.title or "",
                "author": props.author or "",
                "created": str(props.created) if props.created else "",
                "modified": str(props.modified) if props.modified else "",
                "paragraph_count": len(doc.paragraphs),
                "table_count": len(doc.tables),
            }
            
            # Extract paragraphs as content
            paragraphs = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    paragraphs.append(text)
            
            # Extract tables if enabled
            if config.extract_tables and doc.tables:
                for i, table in enumerate(doc.tables):
                    table_text = self._table_to_text(table)
                    paragraphs.append(f"\n[TABLE {i+1}]\n{table_text}")
            
            # Yield as single document (DOCX is usually one logical unit)
            content = "\n\n".join(paragraphs)
            if content:
                yield Document(
                    content=content,
                    source=str(path),
                    doc_type="drug_info",
                    metadata=base_metadata,
                    country=config.metadata_filters.get("country", "VN"),
                    language=config.metadata_filters.get("language", "en"),
                )
        
        except ImportError:
            raise ImportError("Install python-docx: pip install python-docx")
    
    def _table_to_text(self, table) -> str:
        """Convert DOCX table to readable text."""
        rows = []
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            rows.append(" | ".join(cells))
        return "\n".join(rows)
    
    async def validate_source(self, source: str) -> bool:
        path = Path(source)
        return path.exists() and path.suffix.lower() == ".docx"
    
    def get_loader_info(self) -> dict[str, Any]:
        return {"name": "docx_loader", "version": "1.0", "formats": ["docx"]}
