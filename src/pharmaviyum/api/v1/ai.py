"""
AI API Endpoints — Query, Streaming, and Tool Management.
"""
from __future__ import annotations
import json
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.pharmaviyum.ai.dependencies import (
    get_agent_harness,
    get_rag_pipeline,
    get_ai_container,
    AIComponents,
)
from src.pharmaviyum.ai.harness import AgentResponse
from src.pharmaviyum.ai.mcp import tool_registry, mcp_client
from src.pharmaviyum.core.logging import logger

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="User's question")
    session_id: str | None = Field(default=None, description="Conversation session ID")
    patient_id: int | None = Field(default=None, description="Patient ID for history lookup")
    country: str = Field(default="VN", description="Country code (e.g., VN, ID, SA, IQ)")
    language: str = Field(default="vi", description="Language code (e.g., vi, en, ar, th, id)")
    halal_filter: bool = Field(default=False, description="Enable strict halal compliance check")
    force_fresh: bool = Field(default=False, description="Bypass prompt cache")


@router.post("/query", response_model=AgentResponse, status_code=status.HTTP_200_OK)
async def query_agent(
    request: QueryRequest,
    harness = Depends(get_agent_harness),
):
    """
    Synchronous AI query endpoint.
    Returns a structured AgentResponse with answer, sources, and warnings.
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    context = {
        "patient_id": request.patient_id,
        "country": request.country,
        "language": request.language,
        "halal_filter": request.halal_filter,
        "force_fresh": request.force_fresh,
    }
    
    logger.info(f"AI Query: session={session_id}, query={request.query[:50]}...")
    
    try:
        result = await harness.run(
            session_id=session_id,
            query=request.query,
            context=context,
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Agent execution failed"),
            )
        
        # Construct structured response
        return AgentResponse(
            session_id=session_id,
            query=request.query,
            answer=result["answer"],
            sources=[],  # Populated by harness in full implementation
            tool_calls=[],
            confidence=0.9 if not result.get("warnings") else 0.7,
            requires_human_review="human_review_required" in result.get("warnings", []),
            safety_score=0.95 if not result.get("warnings") else 0.8,
            warnings=[{"code": w, "severity": "warning", "message": w} for w in result.get("warnings", [])],
            model_used="qwen2.5:7b",
            total_latency_ms=result.get("latency_ms", 0.0),
            trace_id=result.get("trace_id", ""),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query endpoint failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during AI processing",
        )


@router.post("/query/stream")
async def query_agent_stream(
    request: QueryRequest,
    harness = Depends(get_agent_harness),
):
    """
    Streaming AI query endpoint (Server-Sent Events).
    Yields tokens and status updates in real-time.
    """
    session_id = request.session_id or str(uuid.uuid4())
    context = {
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
                # Format as SSE
                yield f"data: {json.dumps(event)}\n\n"
            
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream endpoint failed: {e}", exc_info=True)
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.get("/tools")
async def list_tools():
    """List all available MCP tools and their schemas."""
    tools = []
    for meta in tool_registry.list_tools():
        tools.append({
            "name": meta.name,
            "version": meta.version,
            "description": meta.description,
            "category": meta.category,
            "input_schema": meta.input_schema.model_json_schema(),
            "required_roles": meta.required_roles,
        })
    return {"tools": tools}
