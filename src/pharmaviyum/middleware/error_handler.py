"""Centralized error handlers for FastAPI application.

Register handlers for application-specific exceptions and fallbacks so the
API returns stable JSON structures for errors.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.pharmaviyum.core.exceptions import PharmaviyumException


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers on the FastAPI application.

    Handlers translate internal exceptions into JSON responses with a
    consistent shape: {"detail": ..., "code": ...}.
    """

    @app.exception_handler(APIException)
    async def _api_exception_handler(request: Request, exc: APIException):
        return JSONResponse(
            status_code=getattr(exc, "status_code", 500),
            content={"detail": exc.message},
        )

    @app.exception_handler(Exception)
    async def _generic_exception_handler(request: Request, exc: Exception):
        # In production attach correlation ids and avoid leaking internals
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )


__all__ = ["register_exception_handlers"]
