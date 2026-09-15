from fastapi.testclient import TestClient

from src.pharmaviyum.main import app

client = TestClient(app)


def test_admin_fallback_login():
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "Admin123!@#"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert "access_token" in payload
    assert payload["token_type"] == "bearer"
