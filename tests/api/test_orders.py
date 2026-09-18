def test_create_and_get_order(client):
    # Orders now reference the canonical Patient entity.
    patient_payload = {
        "first_name": "Order",
        "last_name": "Patient",
        "phone": "+380501234567",
    }
    presp = client.post("/api/v1/patients/", json=patient_payload)
    assert presp.status_code in (201, 403)

    if presp.status_code == 403:
        return

    patient_id = presp.json()["id"]
    order_payload = {"patient_id": patient_id, "total_amount": 12.5}
    oresp = client.post("/api/v1/orders/", json=order_payload)
    assert oresp.status_code in (201, 403)

    if oresp.status_code == 403:
        return

    order = oresp.json()
    assert order["patient_id"] == patient_id
    assert "client_id" not in order
    order_id = order["id"]

    gresp = client.get(f"/api/v1/orders/{order_id}")
    assert gresp.status_code == 200
    assert gresp.json()["id"] == order_id
    assert gresp.json()["patient_id"] == patient_id

    # A pending order must not be counted as realized patient revenue or a visit.
    presponse = client.get(f"/api/v1/patients/{patient_id}")
    assert presponse.status_code == 200
    patient = presponse.json()
    assert patient["total_purchases"] == 0.0
    assert patient["visit_count"] == 0
    # Completing the order creates one canonical purchase-ledger entry.
    sresp = client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"status": "completed"},
    )
    assert sresp.status_code in (200, 403)
    if sresp.status_code == 403:
        return
    assert sresp.json()["status"] == "completed"

    dresp = client.get(f"/api/v1/patients/{patient_id}")
    assert dresp.status_code == 200
    completed_patient = dresp.json()
    assert completed_patient["visit_count"] == 1
    assert len(completed_patient["purchases"]) == 1
    purchase = completed_patient["purchases"][0]
    assert purchase["receipt_number"] == f"ORDER-{order_id}"
    assert purchase["category"] == "order"
    assert purchase["quantity"] == 1
    assert purchase["unit_price"] == 12.5
    assert purchase["total_amount"] == 12.5
    stats = client.get("/api/v1/patients/statistics")
    assert stats.status_code == 200
    statistics = stats.json()
    assert statistics["total_purchase_value"] == 12.5

    # A completed order is terminal and cannot be completed twice.
    repeat = client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"status": "completed"},
    )
    assert repeat.status_code == 409

    # A cancelled order is also terminal and must never enter the purchase ledger.
    cancel_order = client.post(
        "/api/v1/orders/",
        json={"patient_id": patient_id, "total_amount": 30.0},
    )
    assert cancel_order.status_code in (201, 403)
    if cancel_order.status_code == 403:
        return
    cancelled_id = cancel_order.json()["id"]

    cancel_response = client.patch(
        f"/api/v1/orders/{cancelled_id}/status",
        json={"status": "cancelled"},
    )
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"

    cancelled_patient = client.get(f"/api/v1/patients/{patient_id}")
    assert cancelled_patient.status_code == 200
    purchases = cancelled_patient.json()["purchases"]
    assert len(purchases) == 1
    assert purchases[0]["receipt_number"] == f"ORDER-{order_id}"

    final_stats = client.get("/api/v1/patients/statistics")
    assert final_stats.status_code == 200
    assert final_stats.json()["total_purchase_value"] == 12.5

    # A cancelled order is terminal too.
    repeat_cancel = client.patch(
        f"/api/v1/orders/{cancelled_id}/status",
        json={"status": "cancelled"},
    )
    assert repeat_cancel.status_code == 409

    # The API must reject unsupported lifecycle states at validation time.
    invalid_status = client.patch(
        f"/api/v1/orders/{cancelled_id}/status",
        json={"status": "pending"},
    )
    assert invalid_status.status_code == 422

