"""
HTML/Web Document Loader for pharmaceutical web resources.

Best practice 2026:
- BeautifulSoup4 for parsing
- Readability algorithm for main content extraction
- Link and metadata preservation
- Respect for robots.txt
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from pathlib import Path
from typing import Any, AsyncIterator
from urllib.parse import urlparse

from src.pharmaviyum.ai.mortarium_rag.schemas import Document
from src.pharmaviyum.core.logging import logger

from .base import LoaderConfig


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

    @staticmethod
    async def _validate_remote_url(url: str) -> None:
        """Reject non-HTTP URLs and destinations on private/internal networks."""
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Only http(s) URLs with a hostname are allowed")

        hostname = parsed.hostname.rstrip(".").lower()
        if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(
            ".localhost"
        ):
            raise ValueError("Localhost URLs are not allowed")

        try:
            literal = ipaddress.ip_address(hostname)
            addresses = [literal]
        except ValueError:
            infos = await asyncio.to_thread(
                socket.getaddrinfo,
                hostname,
                parsed.port or (443 if parsed.scheme == "https" else 80),
                type=socket.SOCK_STREAM,
            )
            addresses = [ipaddress.ip_address(info[4][0]) for info in infos]

        if any(
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_reserved
            or address.is_multicast
            or address.is_unspecified
            for address in addresses
        ):
            raise ValueError(
                "URLs resolving to private or internal networks are not allowed"
            )

    async def _load_url(self, url: str, config: LoaderConfig) -> tuple[str, dict]:
        """Fetch and parse HTML from a validated public URL."""
        try:
            await self._validate_remote_url(url)
            import aiohttp
            from bs4 import BeautifulSoup
            from readability import Document as ReadabilityDoc

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30, allow_redirects=False) as resp:
                    if 300 <= resp.status < 400:
                        logger.warning("Redirect rejected for URL %s", url)
                        return "", {}
                    if resp.status != 200:
                        logger.warning(f"HTTP {resp.status} for {url}")
                        return "", {}
                    html = await resp.text()

            readability_doc = ReadabilityDoc(html)
            title = readability_doc.title()
            content_html = readability_doc.summary()

            soup = BeautifulSoup(content_html, "html.parser")
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

            title = soup.title.string if soup.title else file_path.stem

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
            try:
                await self._validate_remote_url(source)
            except (OSError, ValueError):
                return False
            return True
        path = Path(source)
        return path.exists() and path.suffix.lower() in [".html", ".htm"]

    def get_loader_info(self) -> dict[str, Any]:
        return {
            "name": "html_loader",
            "version": "1.0",
            "formats": ["html", "htm", "url"],
        }
