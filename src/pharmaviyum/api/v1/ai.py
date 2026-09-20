"""AI API Endpoints — Query, Streaming, and Tool Management."""

from __future__ import annotations

import json
import uuid
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select

from src.pharmaviyum.ai.dependencies import get_agent_harness
from src.pharmaviyum.ai.harness import AgentResponse
from src.pharmaviyum.ai.mcp import tool_registry
from src.pharmaviyum.ai.mcp.context import (
    MCPAuthorizationContext,
    reset_mcp_context,
    set_mcp_context,
)
from src.pharmaviyum.ai.mcp.registry import UserRole
from src.pharmaviyum.core.logging import logger
from src.pharmaviyum.models.patients import Patient
from src.pharmaviyum.modules.auth.deps import CurrentUser, SessionDep
from src.pharmaviyum.modules.auth.models import PharmacyMembership
from src.pharmaviyum.modules.auth.tenant import require_pharmacy_tenant

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])


class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's question",
    )
    session_id: str | None = Field(default=None, description="Conversation session ID")
    patient_id: int | None = Field(
        default=None, description="Patient ID for history lookup"
    )
    pharmacy_id: int = Field(..., gt=0, description="Authorized pharmacy tenant")
    country: str = Field(default="VN", description="Country code")
    language: str = Field(default="vi", description="Language code")
    halal_filter: bool = Field(
        default=False, description="Enable strict halal compliance check"
    )
    force_fresh: bool = Field(default=False, description="Bypass prompt cache")


async def _tenant_context(
    pharmacy_id: int, current_user: CurrentUser, session: SessionDep
):
    return await require_pharmacy_tenant(pharmacy_id, current_user, session)


async def _validate_patient_scope(
    patient_id: int | None, pharmacy_id: int, session: SessionDep
) -> None:
    """Reject AI requests that reference a patient outside the tenant."""
    if patient_id is None:
        return
    patient = await session.scalar(
        select(Patient.id).where(
            Patient.id == patient_id,
            Patient.pharmacy_id == pharmacy_id,
            Patient.is_active.is_(True),
        )
    )
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or not accessible",
        )


def _set_mcp_context(tenant, current_user: CurrentUser):
    return set_mcp_context(
        MCPAuthorizationContext(
            user_id=tenant.user_id,
            pharmacy_id=tenant.pharmacy_id,
            user_role=cast(UserRole, current_user.role),
        )
    )


def _scoped_session_id(session_id: str, tenant, current_user: CurrentUser) -> str:
    return f"pharmacy:{tenant.pharmacy_id}:user:{current_user.id}:session:{session_id}"


@router.get("/context")
async def ai_context(current_user: CurrentUser, session: SessionDep):
    """Return only pharmacy tenants the authenticated user may use with Mortarium."""
    if current_user.is_superuser:
        from src.pharmaviyum.models.pharmacy import Pharmacy

        result = await session.execute(
            select(Pharmacy.id, Pharmacy.name)
            .where(Pharmacy.is_active.is_(True))
            .order_by(Pharmacy.name)
        )
        return {
            "pharmacies": [
                {"id": pharmacy_id, "name": name} for pharmacy_id, name in result.all()
            ]
        }

    result = await session.execute(
        select(PharmacyMembership.pharmacy_id)
        .where(
            PharmacyMembership.user_id == current_user.id,
            PharmacyMembership.is_active.is_(True),
        )
        .order_by(PharmacyMembership.pharmacy_id)
    )
    pharmacy_ids = [pharmacy_id for pharmacy_id in result.scalars().all()]
    return {
        "pharmacies": [
            {"id": pharmacy_id, "name": f"Pharmacy #{pharmacy_id}"}
            for pharmacy_id in pharmacy_ids
        ]
    }


@router.post("/query", response_model=AgentResponse, status_code=status.HTTP_200_OK)
async def query_agent(
    request: QueryRequest,
    current_user: CurrentUser,
    session: SessionDep,
    harness=Depends(get_agent_harness),
):
    """Synchronous AI query bound to the authenticated pharmacy tenant."""
    tenant = await _tenant_context(request.pharmacy_id, current_user, session)
    await _validate_patient_scope(request.patient_id, tenant.pharmacy_id, session)
    raw_session_id = request.session_id or str(uuid.uuid4())
    session_id = _scoped_session_id(raw_session_id, tenant, current_user)
    context = {
        "user_id": tenant.user_id,
        "pharmacy_id": tenant.pharmacy_id,
        "patient_id": request.patient_id,
        "country": request.country,
        "language": request.language,
        "halal_filter": request.halal_filter,
        "force_fresh": request.force_fresh,
    }

    token = _set_mcp_context(tenant, current_user)
    try:
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

            return AgentResponse(
                session_id=raw_session_id,
                query=request.query,
                answer=result["answer"],
                sources=[
                    {
                        "source_id": f"tool:{item.get('tool', 'unknown')}:{index}",
                        "source_type": "tool_result",
                        "content": str(item.get("data", ""))[:500],
                        "metadata": {"tool": item.get("tool", "unknown")},
                        "relevance_score": 1.0,
                    }
                    for index, item in enumerate(result.get("tool_results", []))
                    if item.get("success")
                ],
                tool_calls=[
                    {
                        "tool_name": item.get("tool", "unknown"),
                        "input_data": item.get("input_data", {}),
                        "success": bool(item.get("success", False)),
                        "output_summary": (
                            str(item.get("data", ""))[:500]
                            if item.get("success")
                            else None
                        ),
                        "error": item.get("error"),
                    }
                    for item in result.get("tool_results", [])
                ],
                confidence=0.9 if not result.get("warnings") else 0.7,
                requires_human_review=(
                    "human_review_required" in result.get("warnings", [])
                ),
                safety_score=0.95 if not result.get("warnings") else 0.8,
                warnings=[
                    {"code": w, "severity": "warning", "message": w}
                    for w in result.get("warnings", [])
                ],
                model_used=result.get("model_used") or "configured-main",
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
    finally:
        reset_mcp_context(token)


@router.post("/query/stream")
async def query_agent_stream(
    request: QueryRequest,
    current_user: CurrentUser,
    session: SessionDep,
    harness=Depends(get_agent_harness),
):
    """Streaming AI query bound to the authenticated pharmacy tenant."""
    tenant = await _tenant_context(request.pharmacy_id, current_user, session)
    await _validate_patient_scope(request.patient_id, tenant.pharmacy_id, session)
    raw_session_id = request.session_id or str(uuid.uuid4())
    session_id = _scoped_session_id(raw_session_id, tenant, current_user)
    context = {
        "user_id": tenant.user_id,
        "pharmacy_id": tenant.pharmacy_id,
        "patient_id": request.patient_id,
        "country": request.country,
        "language": request.language,
        "halal_filter": request.halal_filter,
    }

    async def event_generator():
        token = _set_mcp_context(tenant, current_user)
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
            yield (
                "data: "
                + f"{json.dumps({'event': 'error', 'message': 'AI processing failed'})}"
                + "\n\n"
            )
        finally:
            reset_mcp_context(token)

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
    """List only MCP tools authorized for the authenticated user's role."""
    role = cast(UserRole, current_user.role)
    tools = []
    for meta in tool_registry.list_tools_for_role(role):
        tools.append(
            {
                "name": meta.name,
                "version": meta.version,
                "description": meta.description,
                "category": meta.category,
                "input_schema": meta.input_schema.model_json_schema(),
            }
        )
    return {"tools": tools, "authenticated_user_id": str(current_user.id)}
