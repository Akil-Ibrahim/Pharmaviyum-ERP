"""Top-level API package for the application.

Expose a helper to mount API routers into a FastAPI app. Keep this
module minimal to avoid side effects at import time.
"""

from fastapi import FastAPI
from src.pharmaviyum.api.v1 import api_router


def mount_api(app: FastAPI, prefix: str = "/api/v1") -> None:
	"""Mount the versioned API router on the given FastAPI app.

	Args:
		app: FastAPI application instance to mount routes on.
		prefix: URL prefix for API routes (default: /api/v1).
	"""
	app.include_router(api_router, prefix=prefix)


__all__ = ["mount_api"]
