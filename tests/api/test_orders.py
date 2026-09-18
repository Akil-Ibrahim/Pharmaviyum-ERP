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
