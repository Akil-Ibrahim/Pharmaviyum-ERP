"""WebSocket router helpers.

Provide small utilities to mount websocket endpoints on the FastAPI app.
Handlers live under `api.websocket.handlers` and should be minimal.
"""

from fastapi import FastAPI


def mount_websocket_routes(app: FastAPI, prefix: str = "/ws") -> None:
	"""Mount websocket-related routes on the application.

	This is intentionally simple — real apps may register multiple
	websocket endpoints and middleware here.
	"""
	# Import handlers lazily to avoid heavy imports at app startup
	from src.pharmaviyum.api.websocket.handlers.chat import register_chat

	# register_chat should attach routes to the app under `prefix`
	try:
		register_chat(app, prefix=prefix)
	except Exception:
		# If handlers are not implemented yet, silently skip to avoid
		# breaking the app during initial development.
		pass


__all__ = ["mount_websocket_routes"]
