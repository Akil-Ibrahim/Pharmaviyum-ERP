"""Request-scoped tenant context for multi-pharmacy isolation.

The context is intentionally small and framework-agnostic. API/authentication
code sets it at the request boundary; application services and repositories
consume it without depending on FastAPI or JWT details.
"""

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True, slots=True)
class TenantContext:
    """Identity of the tenant used to scope application data access."""

    pharmacy_id: int

    def __post_init__(self) -> None:
        if self.pharmacy_id <= 0:
            raise ValueError("pharmacy_id must be a positive integer")


_current_tenant: ContextVar[TenantContext | None] = ContextVar(
    "pharmaviyum_tenant_context",
    default=None,
)


def get_tenant() -> TenantContext | None:
    """Return the current tenant, or ``None`` outside a tenant scope."""

    return _current_tenant.get()


def require_tenant() -> TenantContext:
    """Return the current tenant or fail closed when none is configured."""

    tenant = _current_tenant.get()
    if tenant is None:
        raise RuntimeError("Tenant context is required for this operation")
    return tenant


@contextmanager
def tenant_scope(pharmacy_id: int) -> Iterator[TenantContext]:
    """Temporarily bind a pharmacy tenant to the current async context."""

    context = TenantContext(pharmacy_id=pharmacy_id)
    token: Token[TenantContext | None] = _current_tenant.set(context)
    try:
        yield context
    finally:
        _current_tenant.reset(token)
