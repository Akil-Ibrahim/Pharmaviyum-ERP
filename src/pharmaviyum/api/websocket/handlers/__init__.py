"""Websocket handlers package.

Individual handler modules should expose a `register_*` function that
attaches routes to the FastAPI app. This keeps registration explicit
and testable.
"""

from .chat import register_chat
from .notifications import register_notifications
from .presence import register_presence

__all__ = ["register_chat", "register_presence", "register_notifications"]
