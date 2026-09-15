"""Presence handler for websocket connections.

Tracks simple join/leave events via websocket messages. This is a
lightweight example; production should use a shared backing store
for presence tracking (Redis, DB, etc.).
"""

from fastapi import FastAPI, WebSocket

from src.pharmaviyum.api.websocket.logger import get_ws_logger

log = get_ws_logger()


def register_presence(app: FastAPI, prefix: str = "/ws"):
    @app.websocket(f"{prefix}/presence")
    async def _presence(ws: WebSocket):
        await ws.accept()
        try:
            while True:
                msg = await ws.receive_text()
                log.info("presence_event", event=msg)
                await ws.send_text(f"ok: {msg}")
        except Exception:
            await ws.close()


__all__ = ["register_presence"]
