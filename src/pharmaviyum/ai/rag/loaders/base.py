"""
Base Document Loader Protocol.

Best practice 2026:
- Protocol-based design for pluggable loaders
- Async-first for non-blocking I/O
- Structured metadata extraction
- Error handling with retry hints
"""
from __future__ import annotations
from typing import Protocol, AsyncIterator, Any, Literal
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from src.pharmaviyum.ai.rag.schemas import Document


@dataclass
class LoaderConfig:
    """Configuration for document loading."""
    source_type: Literal["pdf", "html", "docx", "database", "web", "file"]
    batch_size: int = 10
    max_file_size_mb: int = 50
    extract_tables: bool = True
    extract_images: bool = False
    ocr_enabled: bool = True
    languages: list[str] = field(default_factory=lambda: ["vi", "en", "ar", "th", "id"])
    metadata_filters: dict[str, Any] = field(default_factory=dict)


class DocumentLoader(Protocol):
    """Protocol for all document loaders."""
    
    async def load(self, source: str, config: LoaderConfig) -> AsyncIterator[Document]:
        """Load documents from source asynchronously."""
        ...
    
    async def validate_source(self, source: str) -> bool:
        """Check if source is accessible and valid."""
        ...
    
    def get_loader_info(self) -> dict[str, Any]:
        """Return loader metadata."""
        ...


@dataclass
class LoadResult:
    """Result of a document load operation."""
    loader_name: str
    source: str
    documents_loaded: int
    documents_failed: int
    total_tokens: int
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
