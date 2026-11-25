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

def test_product_search_matches_strength_and_dosage_form(client):
    payload = {
        "name": "Example Medicine",
        "sku": "MED-SEARCH-001",
        "dosage_strength": "20 mg",
        "dosage_form": "capsule",
        "price": 1.0,
    }
    created = client.post("/api/v1/products/", json=payload)
    assert created.status_code == 201, created.text

    strength_result = client.get("/api/v1/products/search", params={"q": "20 mg"})
    assert strength_result.status_code == 200, strength_result.text
    assert any(item["sku"] == "MED-SEARCH-001" for item in strength_result.json())

    form_result = client.get("/api/v1/products/search", params={"q": "capsule"})
    assert form_result.status_code == 200, form_result.text
    assert any(item["sku"] == "MED-SEARCH-001" for item in form_result.json())
