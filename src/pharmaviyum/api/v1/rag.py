"""RAG endpoints for AI-assisted features.

This module provides a small wrapper to call the local Mortarium AI
service. Keep calls short and add timeouts and error handling for
production readiness.
"""

import httpx
from fastapi import APIRouter, HTTPException

from src.pharmaviyum.config import settings

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/ask")
async def ask_rag(question: dict):
    """Forward a short question payload to the AI service and return answer.

    Expects JSON like {"question": "..."}. This is a thin proxy and
    should validate and sanitize input for production.
    """
    ai_url = settings.AI_SERVICE_URL.rstrip("/") + "/api/ask"
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            resp = await c.post(ai_url, json=question)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


__all__ = ["router"]
