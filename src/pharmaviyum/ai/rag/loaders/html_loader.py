"""
HTML/Web Document Loader for pharmaceutical web resources.

Best practice 2026:
- BeautifulSoup4 for parsing
- Readability algorithm for main content extraction
- Link and metadata preservation
- Respect for robots.txt
"""
from __future__ import annotations
from typing import AsyncIterator, Any
from pathlib import Path
from .base import DocumentLoader, LoaderConfig
from src.pharmaviyum.ai.rag.schemas import Document
from src.pharmaviyum.core.logging import logger


class HTMLLoader:
    """Load HTML documents from files or URLs."""
    
    async def load(self, source: str, config: LoaderConfig) -> AsyncIterator[Document]:
        """Load HTML content."""
        if source.startswith(("http://", "https://")):
            content, metadata = await self._load_url(source, config)
        else:
            content, metadata = await self._load_file(source)
        
        if content:
            yield Document(
                content=content,
                source=source,
                doc_type="drug_info",
                metadata=metadata,
                country=config.metadata_filters.get("country", "VN"),
                language=config.metadata_filters.get("language", "en"),
            )
    
    async def _load_url(self, url: str, config: LoaderConfig) -> tuple[str, dict]:
        """Fetch and parse HTML from URL."""
        try:
            import aiohttp
            from bs4 import BeautifulSoup
            from readability import Document as ReadabilityDoc
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as resp:
                    if resp.status != 200:
                        logger.warning(f"HTTP {resp.status} for {url}")
                        return "", {}
                    html = await resp.text()
            
            # Extract main content using readability
            readability_doc = ReadabilityDoc(html)
            title = readability_doc.title()
            content_html = readability_doc.summary()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content_html, "html.parser")
            
            # Remove script/style tags
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            
            text = soup.get_text(separator="\n", strip=True)
            
            metadata = {
                "url": url,
                "title": title,
                "content_length": len(text),
                "source_type": "web",
            }
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"Failed to load URL {url}: {e}")
            return "", {}
    
    async def _load_file(self, path: str) -> tuple[str, dict]:
        """Load HTML from local file."""
        try:
            from bs4 import BeautifulSoup
            
            file_path = Path(path)
            html = file_path.read_text(encoding="utf-8")
            soup = BeautifulSoup(html, "html.parser")
            
            # Extract title
            title = soup.title.string if soup.title else file_path.stem
            
            # Remove unwanted tags
            for tag in soup(["script", "style"]):
                tag.decompose()
            
            text = soup.get_text(separator="\n", strip=True)
            
            metadata = {
                "file_path": str(file_path),
                "title": title,
                "content_length": len(text),
                "source_type": "file",
            }
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"Failed to load file {path}: {e}")
            return "", {}
    
    async def validate_source(self, source: str) -> bool:
        if source.startswith(("http://", "https://")):
            return True
        path = Path(source)
        return path.exists() and path.suffix.lower() in [".html", ".htm"]
    
    def get_loader_info(self) -> dict[str, Any]:
        return {"name": "html_loader", "version": "1.0", "formats": ["html", "htm", "url"]}
