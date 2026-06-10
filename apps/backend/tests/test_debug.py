import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_debug_login(client, seed_superadmin):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "TestPassword123!"}
    )
    print(f"\nStatus: {resp.status_code}")
    print(f"Body: {resp.json()}")
    assert resp.status_code == 200
    assert "access_token" in resp.json()
