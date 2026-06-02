"""
FastAPI application with LangGraph integration.
Includes caching, rate limiting, and OpenTelemetry tracing.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except ImportError:  # pragma: no cover
    FastAPIInstrumentor = None
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from core.graph import build_mortarium_graph
from core.cache import get_cached_response, cache_response, _build_cache_key
from core.db import engine, redis_client, init_db_extensions
from core.otel import setup_otel
from api.middleware import RequestIDMiddleware, setup_cors
from config import settings
import asyncio, structlog

logger = structlog.get_logger()
graph = build_mortarium_graph()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize infrastructure on startup."""
    setup_otel()
    await init_db_extensions()
    logger.info("Mortarium AI started successfully")
    yield
    await engine.dispose()
    await redis_client.aclose()
    logger.info("Mortarium AI shut down")

app = FastAPI(title="Mortarium AI API", version="2.2.0", lifespan=lifespan)
if FastAPIInstrumentor is not None:
    FastAPIInstrumentor.instrument_app(app)
app.add_middleware(RequestIDMiddleware)
setup_cors(app)
app.state.limiter = Limiter(key_func=get_remote_address)

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)
    user_id: str | None = None
    pharmacy_id: str | None = None

class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    cached: bool
    processing_ms: float
    request_id: str

@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.SERVICE_NAME}

@app.get("/ready")
async def readiness():
    try:
        await redis_client.ping()
        await engine.connect()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/api/ask", response_model=QueryResponse)
@app.state.limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def ask(req: QueryRequest, request: Request):
    metadata = {"user_id": req.user_id, "pharmacy_id": req.pharmacy_id}
    cache_key = _build_cache_key(req.question, metadata)
    
    # Check cache first
    cached = await get_cached_response(cache_key)
    if cached:
        return QueryResponse(**cached, cached=True, processing_ms=0.0, request_id=request.state.request_id)
    
    start = asyncio.get_event_loop().time()
    try:
        state = {
            "question": req.question,
            "documents": [],
            "db_context": None,
            "metadata": metadata,
            "retry_count": 0,
            "chat_history": []
        }
        # Execute LangGraph workflow in threadpool to avoid blocking event loop
        result = await run_in_threadpool(graph.invoke, state)
        
        response_data = {
            "answer": result["generation"],
            "sources": result["documents"][:3]
        }
        await cache_response(cache_key, response_data)
        
        elapsed_ms = (asyncio.get_event_loop().time() - start) * 1000
        return QueryResponse(**response_data, cached=False, processing_ms=round(elapsed_ms, 2), request_id=request.state.request_id)
    except Exception as e:
        logger.error("RAG pipeline failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Processing error")
