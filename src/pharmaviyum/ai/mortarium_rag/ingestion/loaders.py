from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator
from uuid import uuid4

import aiofiles
from bs4 import BeautifulSoup

from src.pharmaviyum.core.logging import logger


@dataclass
class LoadedDocument:
    id: str
    content: str
    source: str
    doc_type: str
    metadata: dict[str, Any]
    language: str = "auto"
    loaded_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.loaded_at is None:
            self.loaded_at = datetime.utcnow()


class DocumentLoader:
    """Multi-format document loader with async support."""

    async def load_file(
        self,
        file_path: str | Path,
        doc_type: str = "drug_info",
        language: str = "auto",
    ) -> LoadedDocument:
        """Load a single file and extract content + metadata."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        extension = file_path.suffix.lower()
        try:
            if extension == ".pdf":
                return await self._load_pdf(file_path, doc_type, language)
            if extension == ".docx":
                return await self._load_docx(file_path, doc_type, language)
            if extension in [".html", ".htm"]:
                return await self._load_html(file_path, doc_type, language)
            if extension in [".txt", ".md"]:
                return await self._load_text(file_path, doc_type, language)
            raise ValueError(f"Unsupported file format: {extension}")
        except Exception as e:
            logger.error(
                "Failed to load ingestion document",
                extra={"error_type": type(e).__name__},
            )
            raise

    async def load_directory(
        self,
        directory: str | Path,
        doc_type: str = "drug_info",
        language: str = "auto",
        extensions: list[str] | None = None,
    ) -> AsyncIterator[LoadedDocument]:
        """Load all supported files from a directory."""
        directory = Path(directory)
        if not directory.is_dir():
            raise NotADirectoryError(f"Directory not found: {directory}")
        supported_extensions = extensions or [
            ".pdf",
            ".docx",
            ".html",
            ".htm",
            ".txt",
            ".md",
        ]
        for file_path in sorted(directory.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                yield await self.load_file(file_path, doc_type, language)

    async def _load_pdf(
        self,
        file_path: Path,
        doc_type: str,
        language: str,
    ) -> LoadedDocument:
        try:
            import pypdf

            pdf_reader = pypdf.PdfReader(file_path)
            text_parts: list[str] = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            content = "\n\n".join(text_parts)
            metadata: dict[str, Any] = {
                "file_name": file_path.name,
                "file_size_bytes": file_path.stat().st_size,
                "page_count": len(pdf_reader.pages),
                "pdf_info": pdf_reader.metadata,
            }
            logger.info(
                f"Loaded PDF ({len(content)} chars, "
                f"{metadata['page_count']} pages)"
            )
            return LoadedDocument(
                str(uuid4()), content, str(file_path), doc_type, metadata, language
            )
        except ImportError:
            raise ImportError("Install pypdf: pip install pypdf")

    async def _load_docx(
        self,
        file_path: Path,
        doc_type: str,
        language: str,
    ) -> LoadedDocument:
        try:
            from docx import Document as DocxDocument

            doc = DocxDocument(str(file_path))
            text_parts: list[str] = [
                para.text for para in doc.paragraphs if para.text.strip()
            ]
            content = "\n\n".join(text_parts)
            metadata: dict[str, Any] = {
                "file_name": file_path.name,
                "file_size_bytes": file_path.stat().st_size,
                "paragraph_count": len(doc.paragraphs),
            }
            logger.info("Loaded DOCX document", extra={"character_count": len(content)})
            return LoadedDocument(
                str(uuid4()), content, str(file_path), doc_type, metadata, language
            )
        except ImportError:
            raise ImportError("Install python-docx: pip install python-docx")

    async def _load_html(
        self,
        file_path: Path,
        doc_type: str,
        language: str,
    ) -> LoadedDocument:
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                html_content = await f.read()
            soup = BeautifulSoup(html_content, "html.parser")
            for script in soup(["script", "style"]):
                script.decompose()
            content = soup.get_text(separator="\n", strip=True)
            title = soup.title.string if soup.title else None
            metadata: dict[str, Any] = {
                "file_name": file_path.name,
                "file_size_bytes": file_path.stat().st_size,
                "title": title,
            }
            logger.info("Loaded HTML document", extra={"character_count": len(content)})
            return LoadedDocument(
                str(uuid4()), content, str(file_path), doc_type, metadata, language
            )
        except ImportError:
            raise ImportError("Install beautifulsoup4: pip install beautifulsoup4")

    async def _load_text(
        self,
        file_path: Path,
        doc_type: str,
        language: str,
    ) -> LoadedDocument:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()
        metadata: dict[str, Any] = {
            "file_name": file_path.name,
            "file_size_bytes": file_path.stat().st_size,
        }
        logger.info("Loaded text document", extra={"character_count": len(content)})
        return LoadedDocument(
            str(uuid4()), content, str(file_path), doc_type, metadata, language
        )
