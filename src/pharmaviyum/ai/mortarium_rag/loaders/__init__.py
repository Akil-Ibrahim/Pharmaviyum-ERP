"""
Document Loaders Module.

Public API:
- PDFLoader: PDF documents with OCR and table extraction
- HTMLLoader: HTML files and web URLs
- DOCXLoader: Microsoft Word documents
- LoaderConfig: Configuration for loaders
- LoadResult: Result of load operations
"""

from .base import DocumentLoader, LoaderConfig, LoadResult
from .docx_loader import DOCXLoader
from .html_loader import HTMLLoader
from .pdf_loader import PDFLoader

__all__ = [
    "DocumentLoader",
    "LoaderConfig",
    "LoadResult",
    "PDFLoader",
    "HTMLLoader",
    "DOCXLoader",
]
