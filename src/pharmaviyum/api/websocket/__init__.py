"""Websocket package exports for the API.

Keep top-level package minimal and re-export the mounting helper.
"""

from .router import mount_websocket_routes

__all__ = ["mount_websocket_routes"]
