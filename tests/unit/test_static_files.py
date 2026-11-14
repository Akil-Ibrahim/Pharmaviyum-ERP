from pathlib import Path

from src.pharmaviyum.core.static_files import get_static_path


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


def test_system_status_deep_link_serves_spa_entrypoint(monkeypatch, tmp_path) -> None:
    """React client-side routes must return index.html on direct navigation."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from src.pharmaviyum.core import static_files

    (tmp_path / "index.html").write_text(
        "<!doctype html><html><body>Pharmaviyum</body></html>",
        encoding="utf-8",
    )
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("/* bundle */", encoding="utf-8")
    monkeypatch.setattr(static_files, "get_static_path", lambda: tmp_path)

    app = FastAPI()
    static_files.setup_static_files(app)

    response = TestClient(app).get("/system-status")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Pharmaviyum" in response.text


def test_production_fails_startup_when_spa_build_is_missing(monkeypatch) -> None:
    """Do not deploy an API-only production instance while the SPA is absent."""
    import pytest
    from fastapi import FastAPI

    from src.pharmaviyum.core import static_files

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setattr(static_files, "get_static_path", lambda: None)

    with pytest.raises(RuntimeError, match="Production frontend build is missing"):
        static_files.setup_static_files(FastAPI())


def test_development_can_run_without_frontend_build(monkeypatch) -> None:
    """API-only development/test processes remain supported."""
    from fastapi import FastAPI

    from src.pharmaviyum.core import static_files

    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setattr(static_files, "get_static_path", lambda: None)

    app = FastAPI()
    static_files.setup_static_files(app)

    assert not any(route.path == "/{full_path:path}" for route in app.routes)
