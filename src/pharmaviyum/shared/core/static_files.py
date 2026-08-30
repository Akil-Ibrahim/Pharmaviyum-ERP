"""Static file serving for monolithic architecture."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse


EXCLUDED_PREFIXES = (
    "api/", "docs", "redoc", "openapi",
    "metrics", "health", "ready",
    "favicon.ico", "assets/",
)


def get_static_path():
    """Locate the built frontend directory."""
    docker_path = Path("/app/static")
    if docker_path.exists():
        return docker_path
    local_path = Path(__file__).parent.parent.parent.parent.parent / "frontend" / "dist"
    if local_path.exists():
        return local_path
    return None


def setup_static_files(app: FastAPI):
    """Serve built React frontend from FastAPI."""
    static_path = get_static_path()
    if not static_path:
        return
    
    assets_path = static_path / "assets"
    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")
    
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
        return JSONResponse(
            status_code=404,
            content={"detail": "Frontend not built. Run 'bun run build' first"}
        )
