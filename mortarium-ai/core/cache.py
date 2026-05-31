import hashlib, json
from typing import Any, Dict
from core.db import redis_client
from config import settings
import structlog

logger = structlog.get_logger()
CACHE_TTL_SECONDS = 300

def _build_cache_key(question: str, metadata: Dict[str, Any]) -> str:
    payload = f"{question.strip().lower()}|{json.dumps(metadata, sort_keys=True)}"
    return f"mortarium:rag:{hashlib.sha256(payload.encode()).hexdigest()[:16]}"

async def get_cached_response(key: str) -> Dict[str, Any] | None:
    try:
        data = await redis_client.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        logger.error("Cache read failed", error=str(e))
        return None

async def cache_response(key: str, data: Dict[str, Any]) -> None:
    try:
        await redis_client.setex(key, CACHE_TTL_SECONDS, json.dumps(data, ensure_ascii=False))
    except Exception as e:
        logger.warning("Cache write failed", error=str(e))
