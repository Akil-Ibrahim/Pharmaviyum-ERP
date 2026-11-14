from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.pharmaviyum.core.static_files import get_static_path, setup_static_files

pytestmark = pytest.mark.unit


def test_static_path_uses_fastapi_cloud_working_directory(
    tmp_path: Path, monkeypatch
) -> None:
    frontend_dist = tmp_path / "frontend" / "shadcn-admin" / "dist"
    frontend_dist.mkdir(parents=True)
    (frontend_dist / "index.html").write_text("<!doctype html><html></html>")

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PHARMAVIYUM_STATIC_DIR", raising=False)

    assert get_static_path() == frontend_dist.resolve()


def test_static_path_uses_staged_static_directory(tmp_path: Path, monkeypatch) -> None:
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<!doctype html><html></html>")

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PHARMAVIYUM_STATIC_DIR", raising=False)

    assert get_static_path() == static_dir.resolve()


def test_static_path_prefers_explicit_configuration(
    tmp_path: Path, monkeypatch
) -> None:
    configured_dist = tmp_path / "configured-dist"
    configured_dist.mkdir()
    (configured_dist / "index.html").write_text("<!doctype html>")

    working_dist = tmp_path / "frontend" / "shadcn-admin" / "dist"
    working_dist.mkdir(parents=True)
    (working_dist / "index.html").write_text("<!doctype html>")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PHARMAVIYUM_STATIC_DIR", str(configured_dist))

    assert get_static_path() == configured_dist.resolve()


def test_static_path_rejects_directory_without_spa_entrypoint(
    tmp_path: Path, monkeypatch
) -> None:
    incomplete_dist = tmp_path / "frontend" / "shadcn-admin" / "dist"
    incomplete_dist.mkdir(parents=True)

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PHARMAVIYUM_STATIC_DIR", raising=False)

    assert get_static_path() is None


def test_spa_fallback_serves_system_status_route(tmp_path: Path, monkeypatch) -> None:
    """Deep links must return the SPA entrypoint instead of a backend 404."""
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text(
        "<!doctype html><html><body>Pharmaviyum</body></html>"
    )

    monkeypatch.setenv("PHARMAVIYUM_STATIC_DIR", str(static_dir))
    app = FastAPI()
    setup_static_files(app)

    response = TestClient(app).get("/system-status")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Pharmaviyum" in response.text


def test_required_frontend_fails_fast_when_build_is_missing(monkeypatch) -> None:
    """Production must not silently start without its required React frontend."""
    monkeypatch.setattr(
        "src.pharmaviyum.core.static_files.get_static_path", lambda: None
    )

    with pytest.raises(RuntimeError, match="Frontend build not found"):
        setup_static_files(FastAPI(), required=True)
