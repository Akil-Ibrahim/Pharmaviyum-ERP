import pytest

from src.pharmaviyum.ai.mortarium_rag.loaders.html_loader import HTMLLoader


@pytest.mark.asyncio
@pytest.mark.unit
async def test_html_loader_rejects_localhost_url():
    with pytest.raises(ValueError, match="Localhost"):
        await HTMLLoader._validate_remote_url("http://localhost:8000/health")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_html_loader_rejects_private_ip():
    with pytest.raises(ValueError, match="private or internal"):
        await HTMLLoader._validate_remote_url("http://127.0.0.1:8080/internal")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_html_loader_rejects_non_http_scheme():
    with pytest.raises(ValueError, match="Only http"):
        await HTMLLoader._validate_remote_url("file:///etc/passwd")
