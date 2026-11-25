def test_create_and_list_product(client):
    payload = {"name": "Test Product", "description": "Sample", "price": 9.99}
    resp = client.post("/api/v1/products/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Product"
    product_id = data["id"]

    # get product
    resp2 = client.get(f"/api/v1/products/{product_id}")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == product_id

    # list products
    resp3 = client.get("/api/v1/products/")
    assert resp3.status_code == 200
    assert isinstance(resp3.json(), list)
    assert any(p["id"] == product_id for p in resp3.json())
