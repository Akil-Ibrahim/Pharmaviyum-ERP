"""Authenticated Central Inbox ingress for Pharmacy Edge events."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from src.pharmaviyum.models.outbox import OutboxEvent, OutboxReplayAudit
from src.pharmaviyum.models.sync import CentralInboxEvent
from src.pharmaviyum.modules.auth.deps import CurrentSuperuser, SessionDep
from src.pharmaviyum.schemas.outbox import (
    OutboxDeadLetterItem,
    OutboxDeadLetterPage,
    OutboxReplayRequest,
    OutboxReplayResponse,
)
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


@router.get(
    "/outbox/dead-lettered",
    response_model=OutboxDeadLetterPage,
)
async def list_dead_lettered_outbox_events(
    db: SessionDep,
    _: CurrentSuperuser,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> OutboxDeadLetterPage:
    """List quarantined Edge events without exposing their business payloads."""
    filters = (
        OutboxEvent.dead_lettered_at.is_not(None),
        OutboxEvent.published_at.is_(None),
    )
    total = await db.scalar(
        select(func.count()).select_from(OutboxEvent).where(*filters)
    )
    rows = await db.scalars(
        select(OutboxEvent)
        .where(*filters)
        .order_by(OutboxEvent.dead_lettered_at.asc(), OutboxEvent.id.asc())
        .limit(limit)
        .offset(offset)
    )
    return OutboxDeadLetterPage(
        items=[OutboxDeadLetterItem.model_validate(row) for row in rows.all()],
        total=total or 0,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/outbox/{event_id}/replay",
    response_model=OutboxReplayResponse,
)
async def replay_dead_lettered_outbox_event(
    event_id: UUID,
    payload: OutboxReplayRequest,
    db: SessionDep,
    actor: CurrentSuperuser,
) -> OutboxReplayResponse:
    """Schedule a quarantined immutable event for audited operator replay."""
    event = await db.scalar(
        select(OutboxEvent)
        .where(OutboxEvent.event_id == str(event_id))
        .with_for_update()
    )
    if event is None:
        raise HTTPException(status_code=404, detail="Outbox event not found")
    if event.published_at is not None:
        raise HTTPException(status_code=409, detail="Outbox event is already published")
    if event.dead_lettered_at is None or event.dead_letter_reason is None:
        raise HTTPException(status_code=409, detail="Outbox event is not quarantined")

    now = datetime.now(timezone.utc)
    previous_reason = event.dead_letter_reason
    audit = OutboxReplayAudit(
        outbox_event_id=event.id,
        event_id=event.event_id,
        actor_user_id=actor.id,
        reason_code=payload.reason_code,
        previous_dead_letter_reason=previous_reason,
        attempts_at_replay=event.attempts,
    )
    db.add(audit)
    event.dead_lettered_at = None
    event.dead_letter_reason = None
    event.available_at = now
    event.locked_until = None
    event.lease_token = None
    await db.flush()
    await db.commit()
    return OutboxReplayResponse(
        event_id=event_id,
        status="scheduled",
        available_at=now,
        audit_id=audit.id,
    )


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
