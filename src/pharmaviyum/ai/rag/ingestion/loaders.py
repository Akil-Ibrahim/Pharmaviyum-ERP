"""
Document Loaders for RAG Ingestion Pipeline.

Best practice 2026:
- Multi-format support (PDF, DOCX, HTML, plain text)
- Metadata extraction (source, author, date, language)
- Async loading for non-blocking I/O
- Error handling with graceful degradation
"""
from __future__ import annotations
import asyncio
from pathlib import Path
from typing import AsyncIterator, Literal
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4
import aiofiles
from src.pharmaviyum.core.logging import logger


@dataclass
class LoadedDocument:
    """Document loaded from a source with metadata."""
    id: str
    content: str
    source: str
    doc_type: str
    metadata: dict
    language: str = "auto"
    loaded_at: datetime = None
    
    def __post_init__(self):
        if self.loaded_at is None:
            self.loaded_at = datetime.utcnow()


class DocumentLoader:
    """
    Multi-format document loader with async support.
    """
    
    async def load_file(
        self,
        file_path: str | Path,
        doc_type: str = "drug_info",
        language: str = "auto",
    ) -> LoadedDocument:
        """
        Load a single file and extract content + metadata.
        
        Supports: PDF, DOCX, HTML, TXT, MD
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        extension = file_path.suffix.lower()
        
        try:
            if extension == ".pdf":
                return await self._load_pdf(file_path, doc_type, language)
            elif extension == ".docx":
                return await self._load_docx(file_path, doc_type, language)
            elif extension in [".html", ".htm"]:
                return await self._load_html(file_path, doc_type, language)
            elif extension in [".txt", ".md"]:
                return await self._load_text(file_path, doc_type, language)
            else:
                raise ValueError(f"Unsupported file format: {extension}")
        
        except Exception as e:
            logger.error(f"Failed to load file {file_path}: {e}", exc_info=True)
            raise
    
    async def load_directory(
        self,
        directory: str | Path,
        doc_type: str = "drug_info",
        language: str = "auto",
        extensions: list[str] | None = None,
    ) -> AsyncIterator[LoadedDocument]:
        """
        Load all supported files from a directory.
        
        Yields documents one by one for memory efficiency.
        """
        directory = Path(directory)
        
        if not directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")
        
        if extensions is None:
            extensions = [".pdf", ".docx", ".html", ".htm", ".txt", ".md"]
        
        for file_path in directory.rglob("*"):
            if file_path.suffix.lower() in extensions:
                try:
                    doc = await self.load_file(file_path, doc_type, language)
                    yield doc
                except Exception as e:
                    logger.warning(f"Skipping file {file_path}: {e}")
                    continue
    
    async def _load_pdf(
        self,
        file_path: Path,
        doc_type: str,
        language: str,
    ) -> LoadedDocument:
        """Load PDF with text extraction."""
        try:
            import pypdf
            
            async with aiofiles.open(file_path, "rb") as f:
                content_bytes = await f.read()
            
            # Extract text from PDF
            pdf_reader = pypdf.PdfReader(file_path)
            text_parts = []
            
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            content = "\n\n".join(text_parts)
            
            # Extract metadata
            metadata = {
                "file_name": file_path.name,
                "file_size_bytes": file_path.stat().st_size,
                "page_count": len(pdf_reader.pages),
                "pdf_info": pdf_reader.metadata,
            }
            
            logger.info(f"Loaded PDF: {file_path.name} ({len(content)} chars, {metadata['page_count']} pages)")
            
            return LoadedDocument(
                id=str(uuid4()),
                content=content,
                source=str(file_path),
                doc_type=doc_type,
                metadata=metadata,
                language=language,
            )
        
        except ImportError:
            raise ImportError("Install pypdf: pip install pypdf")
    
    async def _load_docx(
        self,
        file_path: Path,
        doc_type: str,
        language: str,
    ) -> LoadedDocument:
        """Load DOCX with text extraction."""
        try:
            from docx import Document as DocxDocument
            
            doc = DocxDocument(file_path)
            
            # Extract paragraphs
            text_parts = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            
            content = "\n\n".join(text_parts)
            
            # Extract metadata
            metadata = {
                "file_name": file_path.name,
                "file_size_bytes": file_path.stat().st_size,
                "paragraph_count": len(doc.paragraphs),
                "core_properties": {
                    "author": doc.core_properties.author,
                    "title": doc.core_properties.title,
                    "created": doc.core_properties.created.isoformat() if doc.core_properties.created else None,
                },
            }
            
            logger.info(f"Loaded DOCX: {file_path.name} ({len(content)} chars)")
            
            return LoadedDocument(
                id=str(uuid4()),
                content=content,
                source=str(file_path),
                doc_type=doc_type,
                metadata=metadata,
                language=language,
            )
        
        except ImportError:
            raise ImportError("Install python-docx: pip install python-docx")
    
    async def _load_html(
        self,
        file_path: Path,
        doc_type: str,
        language: str,
    ) -> LoadedDocument:
        """Load HTML with tag stripping."""
        try:
            from bs4 import BeautifulSoup
            
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                html_content = await f.read()
            
            # Parse HTML and extract text
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            content = soup.get_text(separator="\n", strip=True)
            
            # Extract metadata
            metadata = {
                "file_name": file_path.name,
                "file_size_bytes": file_path.stat().st_size,
                "title": soup.title.string if soup.title else None,
            }
            
            logger.info(f"Loaded HTML: {file_path.name} ({len(content)} chars)")
            
            return LoadedDocument(
                id=str(uuid4()),
                content=content,
                source=str(file_path),
                doc_type=doc_type,
                metadata=metadata,
                language=language,
            )
        
        except ImportError:
            raise ImportError("Install beautifulsoup4: pip install beautifulsoup4")
    
    async def _load_text(
        self,
        file_path: Path,
        doc_type: str,
        language: str,
    ) -> LoadedDocument:
        """Load plain text or markdown file."""
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()
        
        metadata = {
            "file_name": file_path.name,
            "file_size_bytes": file_path.stat().st_size,
        }
        
        logger.info(f"Loaded text: {file_path.name} ({len(content)} chars)")
        
        return LoadedDocument(
            id=str(uuid4()),
            content=content,
            source=str(file_path),
            doc_type=doc_type,
            metadata=metadata,
            language=language,
        )
