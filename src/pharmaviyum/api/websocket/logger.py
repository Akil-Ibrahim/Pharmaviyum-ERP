"""Lightweight logger helpers for websocket components.

Websocket handlers should use this to obtain a logger rather than
configuring logging themselves.
"""

from structlog import get_logger


def get_ws_logger(name: str = "pharmaviyum.websocket"):
	"""Return a namespaced logger for websocket code.

	Keeps logging usage consistent across websocket handlers.
	"""
	return get_logger(name)


__all__ = ["get_ws_logger"]
