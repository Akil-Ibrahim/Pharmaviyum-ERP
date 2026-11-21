"""ERP integration port.

The application layer knows only this contract. Concrete ERP clients belong
in infrastructure adapters and can be replaced without changing CRM logic.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ERPPatient:
    """Minimal patient representation exchanged with an ERP."""

    external_id: str
    full_name: str
    phone: str
    email: str | None = None


class ERPAdapter(Protocol):
    """Port implemented by a concrete ERP integration adapter."""

    async def upsert_patient(self, patient: ERPPatient) -> str: ...

    async def get_patient(self, external_id: str) -> ERPPatient | None: ...
