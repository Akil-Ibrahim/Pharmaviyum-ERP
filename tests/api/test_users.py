def test_create_and_get_user(client):
    # create user
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "secret",
    }
    resp = client.post("/api/v1/users/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    user_id = data["id"]

    # get user
    resp2 = client.get(f"/api/v1/users/{user_id}")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["id"] == user_id
    assert data2["username"] == "testuser"
