"""Tenant boundary primitives.

The tenant is resolved at the API boundary and propagated through application
code via a request-scoped context. Infrastructure code can require the
context before executing tenant-owned operations.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator

from fastapi import Request


_tenant_id: ContextVar[str | None] = ContextVar("pharmaviyum_tenant_id", default=None)


def get_current_tenant() -> str:
    """Return the current tenant or fail closed when none is established."""
    tenant_id = _tenant_id.get()
    if not tenant_id:
        raise RuntimeError("Tenant context is not established")
    return tenant_id


def get_optional_tenant() -> str | None:
    """Return the current tenant without raising."""
    return _tenant_id.get()


def set_current_tenant(tenant_id: str) -> Token[str | None]:
    """Set a tenant for the current async context."""
    normalized = tenant_id.strip()
    if not normalized:
        raise ValueError("tenant_id must not be empty")
    return _tenant_id.set(normalized)


def reset_current_tenant(token: Token[str | None]) -> None:
    """Restore the previous tenant context."""
    _tenant_id.reset(token)


@contextmanager
def tenant_context(tenant_id: str) -> Iterator[str]:
    """Temporarily establish a tenant boundary."""
    token = set_current_tenant(tenant_id)
    try:
        yield tenant_id.strip()
    finally:
        reset_current_tenant(token)


def get_tenant_from_request(request: Request) -> str | None:
    """Extract tenant identity at the HTTP boundary."""
    value = request.headers.get("X-Tenant-ID")
    if value is None:
        return None
    value = value.strip()
    return value or None
