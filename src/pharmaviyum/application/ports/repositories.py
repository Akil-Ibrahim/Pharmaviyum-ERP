"""Application-layer repository contracts.

Repositories are infrastructure details; application services depend on these
ports rather than on SQLAlchemy implementations.
"""

from typing import Protocol, TypeVar

from src.pharmaviyum.models.patients import Patient

EntityT = TypeVar("EntityT")


class Repository(Protocol[EntityT]):
    """Minimal repository contract used by application services."""

    async def get_by_id(self, id: int) -> EntityT | None: ...

    async def create(self, entity: EntityT) -> EntityT: ...


class PatientRepositoryPort(Repository[Patient], Protocol):
    """Patient persistence contract exposed to the application layer."""

    async def get_by_phone(self, phone: str) -> Patient | None: ...

    async def get_by_email(self, email: str) -> Patient | None: ...
