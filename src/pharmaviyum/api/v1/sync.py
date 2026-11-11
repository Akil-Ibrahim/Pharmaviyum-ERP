"""Authenticated Central Inbox ingress for Pharmacy Edge events."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.pharmaviyum.models.sync import CentralInboxEvent
from src.pharmaviyum.modules.auth.deps import CurrentSuperuser, SessionDep
from src.pharmaviyum.schemas.sync import (
    EdgeNodeProvisionRequest,
    EdgeNodeProvisionResponse,
    SyncEventAcknowledgement,
    SyncEventEnvelope,
)
from src.pharmaviyum.services.edge_identity import (
    authenticate_edge_node,
    provision_edge_node,
    revoke_edge_node,
)

router = APIRouter(prefix="/api/v1/sync", tags=["Pharmacy Synchronization"])


@router.post(
    "/edge-nodes",
    response_model=EdgeNodeProvisionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_edge_node(
    payload: EdgeNodeProvisionRequest,
    db: SessionDep,
    _: CurrentSuperuser,
) -> EdgeNodeProvisionResponse:
    """Enroll an Edge node. The bearer credential is returned exactly once."""
    try:
        node, credential = await provision_edge_node(
            db, pharmacy_id=payload.pharmacy_id, display_name=payload.display_name
        )
        await db.commit()
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return EdgeNodeProvisionResponse(
        node_id=UUID(node.node_id),
        pharmacy_id=node.pharmacy_id,
        display_name=node.display_name,
        credential=credential,
    )


@router.delete("/edge-nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disable_edge_node(
    node_id: UUID,
    db: SessionDep,
    _: CurrentSuperuser,
) -> None:
    """Revoke an Edge node credential."""
    node = await revoke_edge_node(db, node_id=str(node_id))
    if node is None:
        raise HTTPException(status_code=404, detail="Edge node not found")
    await db.commit()


@router.post(
    "/events",
    response_model=SyncEventAcknowledgement,
    status_code=status.HTTP_202_ACCEPTED,
)
async def receive_sync_event(
    event: SyncEventEnvelope,
    db: SessionDep,
    x_edge_token: str = Header(..., alias="X-Edge-Token", min_length=32),
) -> SyncEventAcknowledgement:
    """Durably accept an event from its enrolled Edge node.

    The authenticated node registration, not the request body, is authoritative
    for pharmacy scope. This endpoint stores and acknowledges events only; it
    does not apply inventory, payment, dispensing or other domain side effects.
    """
    node = await authenticate_edge_node(db, x_edge_token)
    if node is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked Edge credential",
        )
    if event.edge_node_id != UUID(node.node_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Event scope does not match the authenticated Edge identity",
        )

    existing = await db.scalar(
        select(CentralInboxEvent).where(
            CentralInboxEvent.event_id == str(event.event_id)
        )
    )
    if existing is not None:
        same_event = (
            existing.pharmacy_id == node.pharmacy_id
            and existing.edge_node_id == node.id
            and existing.event_type == event.event_type
            and existing.schema_version == event.schema_version
            and existing.aggregate_type == event.aggregate_type
            and existing.aggregate_id == event.aggregate_id
            and existing.aggregate_version == event.aggregate_version
            and existing.occurred_at == event.occurred_at
            and existing.payload == event.payload
        )
        if not same_event:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="event_id was previously used with different event content",
            )
        node.last_seen_at = datetime.now(timezone.utc)
        await db.commit()
        return SyncEventAcknowledgement(
            event_id=event.event_id, status="accepted", duplicate=True
        )

    version_conflict = await db.scalar(
        select(CentralInboxEvent).where(
            CentralInboxEvent.pharmacy_id == node.pharmacy_id,
            CentralInboxEvent.aggregate_type == event.aggregate_type,
            CentralInboxEvent.aggregate_id == event.aggregate_id,
            CentralInboxEvent.aggregate_version == event.aggregate_version,
        )
    )
    if version_conflict is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Aggregate version already exists with a different event_id",
        )

    authenticated_node_id = node.id
    authenticated_pharmacy_id = node.pharmacy_id
    inbox_event = CentralInboxEvent(
        event_id=str(event.event_id),
        pharmacy_id=node.pharmacy_id,
        edge_node_id=node.id,
        event_type=event.event_type,
        schema_version=event.schema_version,
        aggregate_type=event.aggregate_type,
        aggregate_id=event.aggregate_id,
        aggregate_version=event.aggregate_version,
        occurred_at=event.occurred_at,
        payload=event.payload,
        processing_status="accepted",
    )
    db.add(inbox_event)
    node.last_seen_at = datetime.now(timezone.utc)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        duplicate = await db.scalar(
            select(CentralInboxEvent).where(
                CentralInboxEvent.event_id == str(event.event_id)
            )
        )
        if duplicate is not None:
            same_event = (
                duplicate.pharmacy_id == authenticated_pharmacy_id
                and duplicate.edge_node_id == authenticated_node_id
                and duplicate.event_type == event.event_type
                and duplicate.schema_version == event.schema_version
                and duplicate.aggregate_type == event.aggregate_type
                and duplicate.aggregate_id == event.aggregate_id
                and duplicate.aggregate_version == event.aggregate_version
                and duplicate.occurred_at == event.occurred_at
                and duplicate.payload == event.payload
            )
            if same_event:
                return SyncEventAcknowledgement(
                    event_id=event.event_id, status="accepted", duplicate=True
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="event_id was concurrently used with different event content",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Event conflicts with an existing aggregate version",
        ) from exc

    return SyncEventAcknowledgement(event_id=event.event_id, status="accepted")
