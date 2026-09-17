"""Top-level API package for the application.

Expose a helper to mount the versioned API router into a FastAPI app.
Keep this module minimal to avoid import-time side effects.
"""

from fastapi import FastAPI

from src.pharmaviyum.api.v1 import api_v1_router


def mount_api(app: FastAPI, prefix: str = "/api/v1") -> None:
    """Mount the versioned API router on the given FastAPI application."""
    app.include_router(api_v1_router, prefix=prefix)


__all__ = ["mount_api"]
