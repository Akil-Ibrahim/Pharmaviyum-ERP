"""Authentication helpers for websocket endpoints.

This module should contain lightweight helpers to authenticate websocket
connections (e.g., token validation). Keep logic small and reuse
`src.pharmaviyum.core.security` where possible.
"""

from typing import Optional
from jose import jwt
from src.pharmaviyum.config import settings


def validate_ws_token(token: str) -> Optional[str]:
	"""Validate a JWT token and return the subject (username) or None.

	This is deliberately synchronous/simple — adapt to async if your
	auth backend requires network calls.
	"""
	try:
		payload = jwt.decode(token, settings.API_SECRET_KEY or "", algorithms=["HS256"])  # type: ignore[arg-type]
		return payload.get("sub")
	except Exception:
		return None


__all__ = ["validate_ws_token"]
