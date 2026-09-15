"""AI API Endpoints — Query, Streaming, and Tool Management."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.pharmaviyum.ai.dependencies import get_agent_harness
from src.pharmaviyum.ai.harness import AgentResponse
from src.pharmaviyum.ai.mcp import tool_registry
from src.pharmaviyum.core.logging import logger
from src.pharmaviyum.modules.auth.deps import CurrentUser, SessionDep
from src.pharmaviyum.modules.auth.tenant import require_pharmacy_tenant

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="User's question")
    session_id: str | None = Field(default=None, description="Conversation session ID")
    patient_id: int | None = Field(default=None, description="Patient ID for history lookup")
    pharmacy_id: int = Field(..., gt=0, description="Authorized pharmacy tenant")
    country: str = Field(default="VN", description="Country code")
    language: str = Field(default="vi", description="Language code")
    halal_filter: bool = Field(default=False, description="Enable strict halal compliance check")
    force_fresh: bool = Field(default=False, description="Bypass prompt cache")


async def _tenant_context(
    pharmacy_id: int,
    current_user: CurrentUser,
    session: SessionDep,
):
    return await require_pharmacy_tenant(pharmacy_id, current_user, session)


@router.post("/query", response_model=AgentResponse, status_code=status.HTTP_200_OK)
async def query_agent(
    request: QueryRequest,
    harness=Depends(get_agent_harness),
    current_user: CurrentUser = None,
    session: SessionDep = None,
):
    """Synchronous AI query bound to the authenticated pharmacy tenant."""
    tenant = await _tenant_context(request.pharmacy_id, current_user, session)
    session_id = request.session_id or str(uuid.uuid4())
    context = {
        "user_id": tenant.user_id,
        "pharmacy_id": tenant.pharmacy_id,
        "patient_id": request.patient_id,
        "country": request.country,
        "language": request.language,
        "halal_filter": request.halal_filter,
        "force_fresh": request.force_fresh,
    }

    logger.info(
        "AI Query: user=%s pharmacy=%s session=%s query=%s...",
        tenant.user_id,
        tenant.pharmacy_id,
        session_id,
        request.query[:50],
    )

    try:
        result = await harness.run(session_id=session_id, query=request.query, context=context)
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Agent execution failed"),
            )

        return AgentResponse(
            session_id=session_id,
            query=request.query,
            answer=result["answer"],
            sources=[],
            tool_calls=[],
            confidence=0.9 if not result.get("warnings") else 0.7,
            requires_human_review="human_review_required" in result.get("warnings", []),
            safety_score=0.95 if not result.get("warnings") else 0.8,
            warnings=[
                {"code": w, "severity": "warning", "message": w}
                for w in result.get("warnings", [])
            ],
            model_used="qwen2.5:7b",
            total_latency_ms=result.get("latency_ms", 0.0),
            trace_id=result.get("trace_id", ""),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Query endpoint failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during AI processing",
        ) from e


@router.post("/query/stream")
async def query_agent_stream(
    request: QueryRequest,
    harness=Depends(get_agent_harness),
    current_user: CurrentUser = None,
    session: SessionDep = None,
):
    """Streaming AI query bound to the authenticated pharmacy tenant."""
    tenant = await _tenant_context(request.pharmacy_id, current_user, session)
    session_id = request.session_id or str(uuid.uuid4())
    context = {
        "user_id": tenant.user_id,
        "pharmacy_id": tenant.pharmacy_id,
        "patient_id": request.patient_id,
        "country": request.country,
        "language": request.language,
        "halal_filter": request.halal_filter,
    }

    async def event_generator():
        try:
            async for event in harness.astream(
                session_id=session_id,
                query=request.query,
                context=context,
            ):
                yield f"data: {json.dumps(event)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error("Stream endpoint failed: %s", e, exc_info=True)
            yield f"data: {json.dumps({'event': 'error', 'message': 'AI processing failed'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/tools")
async def list_tools(current_user: CurrentUser):
    """List MCP tools only after authentication."""
    tools = []
    for meta in tool_registry.list_tools():
        tools.append(
            {
                "name": meta.name,
                "version": meta.version,
                "description": meta.description,
                "category": meta.category,
                "input_schema": meta.input_schema.model_json_schema(),
                "required_roles": meta.required_roles,
            }
        )
    return {"tools": tools, "authenticated_user_id": str(current_user.id)}
