"""Request and response contracts for Edge synchronization ingress."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EdgeNodeProvisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    pharmacy_id: int = Field(gt=0)
    display_name: str = Field(min_length=2, max_length=120)


class EdgeNodeProvisionResponse(BaseModel):
    node_id: UUID
    pharmacy_id: int
    display_name: str
    credential: str
    credential_notice: str = "Store this credential securely; it is shown only once."


class SyncEventEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    edge_node_id: UUID
    pharmacy_id: int = Field(gt=0)
    event_type: str = Field(min_length=3, max_length=120)
    schema_version: int = Field(ge=1)
    aggregate_type: str = Field(min_length=1, max_length=80)
    aggregate_id: str = Field(min_length=1, max_length=100)
    aggregate_version: int = Field(ge=1)
    occurred_at: datetime
    payload: dict[str, Any]

    @field_validator("occurred_at")
    @classmethod
    def require_timezone_aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone offset")
        return value.astimezone(timezone.utc)


class SyncEventAcknowledgement(BaseModel):
    event_id: UUID
    status: str
    duplicate: bool = False
