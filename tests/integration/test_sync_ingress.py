"""Integration tests for Edge enrollment and durable Central Inbox ingress."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select

from src.pharmaviyum.models.outbox import OutboxEvent, OutboxReplayAudit
from src.pharmaviyum.models.pharmacy import Pharmacy
from src.pharmaviyum.models.sync import CentralInboxEvent, PharmacyEdgeNode


def _sale_created_payload(sale_id: int) -> dict:
    """Return the allowlisted POS sale event payload shape."""
    return {
        "receipt_number": f"PV-TEST-{sale_id}",
        "status": "completed",
        "subtotal": "10.00",
        "discount_total": "0.00",
        "total": "10.00",
        "inventory_effect": "decrement",
        "items": [
            {
                "product_sku": "TEST-SKU-1",
                "product_name": "Test Medicine",
                "quantity": 1,
                "unit_price": "10.00",
                "line_total": "10.00",
                "allocations": [
                    {
                        "lot_number": "TEST-LOT-1",
                        "expires_at": None,
                        "quantity": 1,
                    }
                ],
            }
        ],
        "payment": {"method": "cash", "status": "succeeded", "amount": "10.00"},
    }


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
        select(PharmacyEdgeNode).where(PharmacyEdgeNode.node_id == enrolled["node_id"])
    )
    assert node is not None
    assert node.credential_hash != credential
    assert credential not in node.credential_hash

    event = {
        "event_id": str(uuid4()),
        "edge_node_id": enrolled["node_id"],
        "event_type": "pos.sale.created",
        "schema_version": 1,
        "aggregate_type": "sale",
        "aggregate_id": "PV-TEST-1001",
        "aggregate_version": 1,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "payload": _sale_created_payload(1001),
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
        select(CentralInboxEvent).where(CentralInboxEvent.event_id == event["event_id"])
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

    altered = {**event, "payload": {**_sale_created_payload(1001), "items": [{**_sale_created_payload(1001)["items"][0], "product_name": "Altered Test Medicine"}]}}
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
    enrollment_b = await authenticated_client.post(
        "/api/v1/sync/edge-nodes",
        json={"pharmacy_id": pharmacy_b.id, "display_name": "Edge B"},
    )
    assert enrollment_b.status_code == 201, enrollment_b.text
    node_b = enrollment_b.json()

    event = {
        "event_id": str(uuid4()),
        "edge_node_id": node_b["node_id"],
        "event_type": "pos.sale.created",
        "schema_version": 1,
        "aggregate_type": "sale",
        "aggregate_id": "PV-TEST-7",
        "aggregate_version": 1,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "payload": _sale_created_payload(7),
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
async def test_revoked_edge_credential_is_rejected(authenticated_client, test_db):
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
        "event_type": "pos.sale.created",
        "schema_version": 1,
        "aggregate_type": "sale",
        "aggregate_id": "PV-TEST-8",
        "aggregate_version": 1,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "payload": _sale_created_payload(8),
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
        "event_type": "pos.sale.created",
        "schema_version": 1,
        "aggregate_type": "sale",
        "aggregate_id": "PV-TEST-1002",
        "aggregate_version": 1,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "payload": _sale_created_payload(1002),
    }
    headers = {"X-Edge-Token": node["credential"]}

    forged_scope = {**base_event, "pharmacy_id": pharmacy.id}
    rejected_scope = await authenticated_client.post(
        "/api/v1/sync/events", json=forged_scope, headers=headers
    )
    assert rejected_scope.status_code == 422

    patient_data = {
        **base_event,
        "payload": {**_sale_created_payload(1002), "patient_name": "Not Allowed"},
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
                CentralInboxEvent.aggregate_id == "PV-TEST-1002"
            )
        )
        is None
    )


@pytest.mark.integration
async def test_superuser_can_inspect_and_audit_replay_of_dead_lettered_outbox_event(
    authenticated_client, test_db
):
    pharmacy = Pharmacy(name="Outbox Replay Pharmacy", code="SYNC-REPLAY")
    test_db.add(pharmacy)
    await test_db.flush()
    event = OutboxEvent(
        event_id=str(uuid4()),
        pharmacy_id=pharmacy.id,
        event_type="pos.sale.created",
        schema_version=1,
        aggregate_type="sale",
        aggregate_id="PV-REPLAY-1",
        aggregate_version=1,
        payload={"synthetic": True},
        dead_lettered_at=datetime.now(timezone.utc),
        dead_letter_reason="http_422",
        last_error="Central permanently rejected event: HTTP 422",
    )
    test_db.add(event)
    await test_db.commit()
    event_id = event.event_id

    listing = await authenticated_client.get(
        "/api/v1/sync/outbox/dead-lettered"
    )
    assert listing.status_code == 200, listing.text
    body = listing.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["event_id"] == event_id
    assert body["items"][0]["dead_letter_reason"] == "http_422"
    assert "payload" not in body["items"][0]

    replay = await authenticated_client.post(
        f"/api/v1/sync/outbox/{event_id}/replay",
        json={"reason_code": "central_conflict_resolved"},
    )
    assert replay.status_code == 200, replay.text
    replay_body = replay.json()
    assert replay_body["event_id"] == event_id
    assert replay_body["status"] == "scheduled"

    await test_db.refresh(event)
    assert event.dead_lettered_at is None
    assert event.dead_letter_reason is None
    assert event.available_at <= datetime.now(timezone.utc)

    audit = await test_db.scalar(
        select(OutboxReplayAudit).where(OutboxReplayAudit.event_id == event_id)
    )
    assert audit is not None
    assert audit.actor_user_id > 0
    assert audit.reason_code == "central_conflict_resolved"
    assert audit.previous_dead_letter_reason == "http_422"
    assert audit.attempts_at_replay == 0


@pytest.mark.integration
async def test_outbox_replay_rejects_events_that_are_not_quarantined(
    authenticated_client, test_db
):
    pharmacy = Pharmacy(name="Outbox Replay Guard Pharmacy", code="SYNC-REPLAY-GUARD")
    test_db.add(pharmacy)
    await test_db.flush()
    event = OutboxEvent(
        event_id=str(uuid4()),
        pharmacy_id=pharmacy.id,
        event_type="pos.sale.created",
        schema_version=1,
        aggregate_type="sale",
        aggregate_id="PV-REPLAY-2",
        aggregate_version=1,
        payload={"synthetic": True},
    )
    test_db.add(event)
    await test_db.commit()

    response = await authenticated_client.post(
        f"/api/v1/sync/outbox/{event.event_id}/replay",
        json={"reason_code": "operator_verified"},
    )
    assert response.status_code == 409
