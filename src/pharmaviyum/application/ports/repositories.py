"""Application-layer repository contracts."""

from typing import Protocol, TypeVar

from src.pharmaviyum.models.patients import Patient

EntityT = TypeVar("EntityT")


class Repository(Protocol[EntityT]):
    """Minimal persistence contract used by application services."""

    async def get_by_id(self, id: int) -> EntityT | None: ...

    async def create(self, entity: EntityT) -> EntityT: ...

    async def update(self, entity: EntityT) -> EntityT: ...

    async def delete(self, id: int) -> bool: ...


class PatientRepositoryPort(Repository[Patient], Protocol):
    """Patient persistence contract exposed to the application layer."""

    async def get_by_external_id(
        self, external_id: str, pos_system: str, pharmacy_id: int | None = None
    ) -> Patient | None: ...

    async def get_by_phone(
        self, phone: str, pharmacy_id: int | None = None
    ) -> Patient | None: ...

    async def get_by_email(
        self, email: str, pharmacy_id: int | None = None
    ) -> Patient | None: ...

    async def get_by_id_with_relations(
        self, id: int, pharmacy_id: int | None = None
    ) -> Patient | None: ...

    async def search(self, **filters: object) -> tuple[list[Patient], int]: ...

    async def soft_delete(self, id: int, pharmacy_id: int | None = None) -> bool: ...

    async def get_ai_profile(
        self, id: int, pharmacy_id: int | None = None
    ) -> dict | None: ...

    async def count(self, **filters: object) -> int: ...

    async def get_loyalty_tiers_stats(self, pharmacy_id: int | None = None) -> dict: ...

    async def get_country_stats(self, pharmacy_id: int | None = None) -> dict: ...
    async def get_total_purchase_value(
        self, pharmacy_id: int | None = None
    ) -> float: ...

    async def get_total_loyalty_points(self, pharmacy_id: int | None = None) -> int: ...

    async def record_visit(
        self, id: int, pharmacy_id: int | None = None
    ) -> Patient | None: ...
