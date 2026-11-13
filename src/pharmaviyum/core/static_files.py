"""Static file serving for monolithic architecture."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

EXCLUDED_PREFIXES = (
    "api/",
    "docs",
    "redoc",
    "openapi",
    "metrics",
    "health",
    "ready",
    "favicon.ico",
    "assets/",
    "images/",
    "avatars/",
)


def get_static_path() -> Path | None:
    """Locate a built frontend in Docker, FastAPI Cloud, or local development."""
    module_root = Path(__file__).resolve().parent.parent.parent.parent
    working_directory = Path.cwd()
    configured_path = os.getenv("PHARMAVIYUM_STATIC_DIR")

    candidates = [
        Path(configured_path).expanduser() if configured_path else None,
        Path("/app/static"),
        working_directory / "static",
        module_root / "static",
        working_directory / "frontend" / "shadcn-admin" / "dist",
        working_directory / "frontend" / "dist",
        module_root / "frontend" / "shadcn-admin" / "dist",
        module_root / "frontend" / "dist",
    ]

    for candidate in candidates:
        if candidate is not None and (candidate / "index.html").is_file():
            return candidate.resolve()
    return None


def setup_static_files(app: FastAPI):
    """Serve built React frontend from FastAPI."""
    static_path = get_static_path()
    if not static_path:
        print("WARNING: Frontend build not found - API-only mode")
        return

    assets_path = static_path / "assets"
    if assets_path.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

    images_path = static_path / "images"
    if images_path.is_dir():
        app.mount("/images", StaticFiles(directory=str(images_path)), name="images")

    avatars_path = static_path / "avatars"
    if avatars_path.is_dir():
        app.mount("/avatars", StaticFiles(directory=str(avatars_path)), name="avatars")

    @app.get("/pharmaviyum-social-preview-v3.png", include_in_schema=False)
    async def pharmaviyum_social_preview_v3():
        preview_path = static_path / "images" / "pharmaviyum.png"
        if preview_path.is_file():
            return FileResponse(
                str(preview_path),
                media_type="image/png",
                headers={"Cache-Control": "no-store, max-age=0"},
            )
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        favicon_path = static_path / "favicon.ico"
        if favicon_path.is_file():
            return FileResponse(str(favicon_path))
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        for prefix in EXCLUDED_PREFIXES:
            if full_path.startswith(prefix):
                return JSONResponse(status_code=404, content={"detail": "Not found"})
        index_path = static_path / "index.html"
        if index_path.is_file():
            return FileResponse(str(index_path))
        return JSONResponse(status_code=404, content={"detail": "Frontend not built"})
