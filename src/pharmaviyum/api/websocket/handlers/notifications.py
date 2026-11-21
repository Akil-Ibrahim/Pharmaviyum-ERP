"""WebSocket notifications handler.

This module provides a tiny example registration function which can be
used by the websocket router to mount notification endpoints.
"""

from fastapi import FastAPI, WebSocket

from src.pharmaviyum.api.websocket.logger import get_ws_logger

log = get_ws_logger()


def register_notifications(app: FastAPI, prefix: str = "/ws"):
    """Register a simple notifications websocket route.

    For production, implement authentication and connection limits.
    """

    @app.websocket(f"{prefix}/notifications")
    async def _notifications(ws: WebSocket):
        await ws.accept()
        try:
            while True:
                data = await ws.receive_text()
                log.info("received_notification_message", message=data)
                await ws.send_text(f"ack: {data}")
        except Exception:
            await ws.close()


__all__ = ["register_notifications"]
