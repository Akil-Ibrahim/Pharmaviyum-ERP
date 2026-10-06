"""Static file serving for monolithic architecture."""

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


def get_static_path():
    """Locate the built frontend directory."""
    docker_path = Path("/app/static")
    if docker_path.exists():
        return docker_path
    local_path = (
        Path(__file__).parent.parent.parent.parent
        / "frontend"
        / "shadcn-admin"
        / "dist"
    )
    if local_path.exists():
        return local_path
    alt_path = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
    if alt_path.exists():
        return alt_path
    return None


def setup_static_files(app: FastAPI):
    """Serve built React frontend from FastAPI."""
    static_path = get_static_path()
    if not static_path:
        print("WARNING: Frontend build not found - API-only mode")
        return

    assets_path = static_path / "assets"
    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

    images_path = static_path / "images"
    if images_path.exists():
        app.mount("/images", StaticFiles(directory=str(images_path)), name="images")

    avatars_path = static_path / "avatars"
    if avatars_path.exists():
        app.mount("/avatars", StaticFiles(directory=str(avatars_path)), name="avatars")

    @app.get("/pharmaviyum-social-preview.png", include_in_schema=False)
    async def pharmaviyum_social_preview():
        preview_path = static_path / "images" / "pharmaviyum.png"
        if preview_path.exists():
            return FileResponse(str(preview_path), media_type="image/png")
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        favicon_path = static_path / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(str(favicon_path))
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        for prefix in EXCLUDED_PREFIXES:
            if full_path.startswith(prefix):
                return JSONResponse(status_code=404, content={"detail": "Not found"})
        index_path = static_path / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return JSONResponse(status_code=404, content={"detail": "Frontend not built"})
