"""Operator contracts for inspecting and replaying Edge outbox events."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

ReplayReasonCode = Literal[
    "credential_rotated",
    "central_endpoint_fixed",
    "schema_compatibility_restored",
    "central_conflict_resolved",
    "operator_verified",
]


class OutboxDeadLetterItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: UUID
    pharmacy_id: int
    event_type: str
    aggregate_type: str
    aggregate_id: str
    aggregate_version: int
    attempts: int
    dead_lettered_at: datetime
    dead_letter_reason: str
    last_error: str | None
    created_at: datetime


class OutboxDeadLetterPage(BaseModel):
    items: list[OutboxDeadLetterItem]
    total: int
    limit: int
    offset: int


class OutboxReplayRequest(BaseModel):
    reason_code: ReplayReasonCode


class OutboxReplayResponse(BaseModel):
    event_id: UUID
    status: Literal["scheduled"]
    available_at: datetime
    audit_id: int
