"""Request and response contracts for Edge synchronization ingress."""

from datetime import datetime, timezone
import json
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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

    @model_validator(mode="after")
    def validate_initial_pos_payload(self) -> "SyncEventEnvelope":
        allowed_event_types = {
            "pos.sale.created",
            "pos.sale.cancelled",
            "pos.payment.succeeded",
            "pos.payment.failed",
        }
        if self.event_type not in allowed_event_types:
            raise ValueError("Unsupported event_type for synchronization contract v1")

        forbidden_keys = {
            "patient",
            "patientid",
            "patientname",
            "phone",
            "email",
            "address",
            "dob",
            "dateofbirth",
            "prescription",
            "medicalrecordnumber",
            "nationalid",
            "diagnosis",
            "allergy",
        }

        def inspect(value: Any) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    normalized = "".join(
                        character for character in str(key).lower()
                        if character.isalnum()
                    )
                    if normalized in forbidden_keys:
                        raise ValueError(
                            "Patient-identifying or clinical fields are not accepted"
                        )
                    inspect(child)
            elif isinstance(value, list):
                for child in value:
                    inspect(child)

        inspect(self.payload)
        if len(json.dumps(self.payload, separators=(",", ":"))) > 262144:
            raise ValueError("Event payload exceeds the 256 KiB limit")
        return self

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
