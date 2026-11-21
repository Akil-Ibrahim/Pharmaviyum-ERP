"""Provision Edge identities and authenticate high-entropy node credentials."""

import hashlib
import secrets
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.models.pharmacy import Pharmacy
from src.pharmaviyum.models.sync import PharmacyEdgeNode


def _credential_digest(credential: str) -> str:
    """Hash a high-entropy, randomly generated Edge credential for storage."""
    return hashlib.sha256(credential.encode("utf-8")).hexdigest()


async def provision_edge_node(
    session: AsyncSession, *, pharmacy_id: int, display_name: str
) -> tuple[PharmacyEdgeNode, str]:
    """Create a node identity and return its one-time plaintext credential."""
    pharmacy = await session.get(Pharmacy, pharmacy_id)
    if pharmacy is None or not pharmacy.is_active:
        raise ValueError("An active pharmacy is required to enroll an Edge node")

    credential = secrets.token_urlsafe(32)
    node = PharmacyEdgeNode(
        node_id=str(uuid4()),
        pharmacy_id=pharmacy_id,
        display_name=display_name,
        credential_hash=_credential_digest(credential),
        is_active=True,
    )
    session.add(node)
    await session.flush()
    return node, credential


async def authenticate_edge_node(
    session: AsyncSession, credential: str
) -> PharmacyEdgeNode | None:
    """Resolve an active Edge node from its one-time-issued bearer credential."""
    digest = _credential_digest(credential)
    node = await session.scalar(
        select(PharmacyEdgeNode).where(
            PharmacyEdgeNode.credential_hash == digest,
            PharmacyEdgeNode.is_active.is_(True),
            PharmacyEdgeNode.revoked_at.is_(None),
        )
    )
    return node


async def revoke_edge_node(
    session: AsyncSession, *, node_id: str
) -> PharmacyEdgeNode | None:
    """Revoke one Edge identity; its credential becomes unusable immediately."""
    node = await session.scalar(
        select(PharmacyEdgeNode).where(PharmacyEdgeNode.node_id == node_id)
    )
    if node is None:
        return None
    node.is_active = False
    node.revoked_at = datetime.now(timezone.utc)
    await session.flush()
    return node
