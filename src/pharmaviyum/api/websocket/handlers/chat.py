"""Chat websocket handler example.

Provides a `register_chat` function which attaches a sample websocket
endpoint. In production this would integrate auth, rooms, and message
persistence.
"""

from fastapi import FastAPI, WebSocket
from src.pharmaviyum.api.websocket.logger import get_ws_logger

log = get_ws_logger()


def register_chat(app: FastAPI, prefix: str = "/ws"):
	"""Register a simple echo-based chat endpoint.

	This is intentionally minimal to serve as a template for real
	chat handlers.
	"""
	@app.websocket(f"{prefix}/chat")
	async def _chat(ws: WebSocket):
		await ws.accept()
		try:
			while True:
				msg = await ws.receive_text()
				log.info("chat_message", message=msg)
				await ws.send_text(f"echo: {msg}")
		except Exception:
			await ws.close()


__all__ = ["register_chat"]
