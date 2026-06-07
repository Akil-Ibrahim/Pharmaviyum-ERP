def test_create_and_get_order(client):
    # create client (reuse user model as client if client endpoints absent)
    user_payload = {"username": "orderuser", "email": "ord@example.com", "password": "pwd"}
    uresp = client.post("/api/v1/users/", json=user_payload)
    assert uresp.status_code == 201
    user_id = uresp.json()["id"]

    # create order
    order_payload = {"client_id": user_id, "total_amount": 12.5}
    oresp = client.post("/api/v1/orders/", json=order_payload)
    assert oresp.status_code == 201
    order = oresp.json()
    assert order["client_id"] == user_id
    order_id = order["id"]

    # get order
    gresp = client.get(f"/api/v1/orders/{order_id}")
    assert gresp.status_code == 200
    assert gresp.json()["id"] == order_id
