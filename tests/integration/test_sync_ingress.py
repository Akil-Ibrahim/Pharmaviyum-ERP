"""Integration tests for Edge enrollment and durable Central Inbox ingress."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select

from src.pharmaviyum.models.pharmacy import Pharmacy
from src.pharmaviyum.models.sync import CentralInboxEvent, PharmacyEdgeNode


@pytest.mark.integration
async def test_edge_enrollment_and_event_ingress_are_durable_and_idempotent(
    authenticated_client, test_db
):
    pharmacy = Pharmacy(name="Sync Test Pharmacy", code="SYNC-TEST")
    test_db.add(pharmacy)
    await test_db.flush()

    enrollment = await authenticated_client.post(
        "/api/v1/sync/edge-nodes",
        json={"pharmacy_id": pharmacy.id, "display_name": "Sync Test Edge"},
    )
    assert enrollment.status_code == 201, enrollment.text
    enrolled = enrollment.json()
    credential = enrolled["credential"]
    assert len(credential) >= 32

    node = await test_db.scalar(
        select(PharmacyEdgeNode).where(
            PharmacyEdgeNode.node_id == enrolled["node_id"]
        )
    )
    assert node is not None
    assert node.credential_hash != credential
    assert credential not in node.credential_hash

    event = {
        "event_id": str(uuid4()),
        "edge_node_id": enrolled["node_id"],
        "pharmacy_id": pharmacy.id,
        "event_type": "pos.sale.created",
        "schema_version": 1,
        "aggregate_type": "sale",
        "aggregate_id": "sale-1001",
        "aggregate_version": 1,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "payload": {"sale_id": 1001, "inventory_effect": "decrement"},
    }
    headers = {"X-Edge-Token": credential}
    first = await authenticated_client.post(
        "/api/v1/sync/events", json=event, headers=headers
    )
    assert first.status_code == 202, first.text
    assert first.json() == {
        "event_id": event["event_id"],
        "status": "accepted",
        "duplicate": False,
    }

    stored = await test_db.scalar(
        select(CentralInboxEvent).where(
            CentralInboxEvent.event_id == event["event_id"]
        )
    )
    assert stored is not None
    assert stored.pharmacy_id == pharmacy.id
    assert stored.edge_node_id == node.id
    assert stored.processing_status == "accepted"

    replay = await authenticated_client.post(
        "/api/v1/sync/events", json=event, headers=headers
    )
    assert replay.status_code == 202, replay.text
    assert replay.json()["duplicate"] is True

    altered = {**event, "payload": {"sale_id": 1001, "inventory_effect": "credit"}}
    conflict = await authenticated_client.post(
        "/api/v1/sync/events", json=altered, headers=headers
    )
    assert conflict.status_code == 409

    count = len(
        (
            await test_db.scalars(
                select(CentralInboxEvent).where(
                    CentralInboxEvent.event_id == event["event_id"]
                )
            )
        ).all()
    )
    assert count == 1


@pytest.mark.integration
async def test_edge_identity_cannot_submit_for_another_pharmacy(
    authenticated_client, test_db
):
    pharmacy_a = Pharmacy(name="Sync Pharmacy A", code="SYNC-A")
    pharmacy_b = Pharmacy(name="Sync Pharmacy B", code="SYNC-B")
    test_db.add_all([pharmacy_a, pharmacy_b])
    await test_db.flush()

    enrollment = await authenticated_client.post(
        "/api/v1/sync/edge-nodes",
        json={"pharmacy_id": pharmacy_a.id, "display_name": "Edge A"},
    )
    assert enrollment.status_code == 201, enrollment.text
    node = enrollment.json()

    event = {
        "event_id": str(uuid4()),
        "edge_node_id": node["node_id"],
        "pharmacy_id": pharmacy_b.id,
        "event_type": "pos.sale.created",
        "schema_version": 1,
        "aggregate_type": "sale",
        "aggregate_id": "sale-forged",
        "aggregate_version": 1,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "payload": {"sale_id": 7},
    }
    response = await authenticated_client.post(
        "/api/v1/sync/events",
        json=event,
        headers={"X-Edge-Token": node["credential"]},
    )
    assert response.status_code == 403
    assert (
        await test_db.scalar(
            select(CentralInboxEvent).where(
                CentralInboxEvent.event_id == event["event_id"]
            )
        )
        is None
    )


@pytest.mark.integration
async def test_revoked_edge_credential_is_rejected(
    authenticated_client, test_db
):
    pharmacy = Pharmacy(name="Revocation Test Pharmacy", code="SYNC-REVOKE")
    test_db.add(pharmacy)
    await test_db.flush()

    enrollment = await authenticated_client.post(
        "/api/v1/sync/edge-nodes",
        json={"pharmacy_id": pharmacy.id, "display_name": "Revocation Edge"},
    )
    assert enrollment.status_code == 201, enrollment.text
    node = enrollment.json()

    revoked = await authenticated_client.delete(
        f"/api/v1/sync/edge-nodes/{node['node_id']}"
    )
    assert revoked.status_code == 204

    event = {
        "event_id": str(uuid4()),
        "edge_node_id": node["node_id"],
        "pharmacy_id": pharmacy.id,
        "event_type": "pos.sale.created",
        "schema_version": 1,
        "aggregate_type": "sale",
        "aggregate_id": "sale-after-revoke",
        "aggregate_version": 1,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "payload": {"sale_id": 8},
    }
    response = await authenticated_client.post(
        "/api/v1/sync/events",
        json=event,
        headers={"X-Edge-Token": node["credential"]},
    )
    assert response.status_code == 401


@pytest.mark.integration
async def test_ingress_rejects_patient_data_and_unregistered_event_types(
    authenticated_client, test_db
):
    pharmacy = Pharmacy(name="Payload Safety Pharmacy", code="SYNC-SAFETY")
    test_db.add(pharmacy)
    await test_db.flush()

    enrollment = await authenticated_client.post(
        "/api/v1/sync/edge-nodes",
        json={"pharmacy_id": pharmacy.id, "display_name": "Safety Edge"},
    )
    assert enrollment.status_code == 201, enrollment.text
    node = enrollment.json()
    base_event = {
        "event_id": str(uuid4()),
        "edge_node_id": node["node_id"],
        "pharmacy_id": pharmacy.id,
        "event_type": "pos.sale.created",
        "schema_version": 1,
        "aggregate_type": "sale",
        "aggregate_id": "sale-sensitive",
        "aggregate_version": 1,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "payload": {"sale_id": 1002},
    }
    headers = {"X-Edge-Token": node["credential"]}

    patient_data = {
        **base_event,
        "payload": {"sale_id": 1002, "patient_name": "Not Allowed"},
    }
    rejected_patient_data = await authenticated_client.post(
        "/api/v1/sync/events", json=patient_data, headers=headers
    )
    assert rejected_patient_data.status_code == 422

    unsupported = {**base_event, "event_type": "patient.record.updated"}
    rejected_event = await authenticated_client.post(
        "/api/v1/sync/events", json=unsupported, headers=headers
    )
    assert rejected_event.status_code == 422

    assert (
        await test_db.scalar(
            select(CentralInboxEvent).where(
                CentralInboxEvent.aggregate_id == "sale-sensitive"
            )
        )
        is None
    )
