"""Tests for Clients API endpoints - Phase 2."""
import pytest


def _token(client, seed_superadmin):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "TestPassword123!"}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


CLIENT = {
    "company_name": "Acme Logistics",
    "phone": "9876543210",
    "email": "acme@gmail.com",
    "client_type": "company",
    "gst_no": "27AAPFU0939F1ZV",
    "credit_limit": 100000.0,
    "payment_terms_days": 30,
}


class TestClientEndpoints:
    def test_create_client_success(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        resp = client.post("/api/v1/clients/", json=CLIENT, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["company_name"] == "Acme Logistics"

    def test_create_client_duplicate_email(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        client.post("/api/v1/clients/", json=CLIENT, headers=headers)
        dup = {**CLIENT, "company_name": "Acme 2", "phone": "9999999999"}
        resp = client.post("/api/v1/clients/", json=dup, headers=headers)
        assert resp.status_code == 409

    def test_list_clients(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        client.post("/api/v1/clients/", json=CLIENT, headers=headers)
        resp = client.get("/api/v1/clients/", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_clients(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        client.post("/api/v1/clients/", json=CLIENT, headers=headers)
        resp = client.get("/api/v1/clients/?search=Acme", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_get_client_by_id(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        create = client.post("/api/v1/clients/", json=CLIENT, headers=headers)
        client_id = create.json()["id"]
        resp = client.get(f"/api/v1/clients/{client_id}", headers=headers)
        assert resp.status_code == 200

    def test_update_client(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        create = client.post("/api/v1/clients/", json=CLIENT, headers=headers)
        client_id = create.json()["id"]
        resp = client.patch(
            f"/api/v1/clients/{client_id}",
            json={"phone": "9999999999"},
            headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["phone"] == "9999999999"

    def test_soft_delete_client(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        create = client.post("/api/v1/clients/", json=CLIENT, headers=headers)
        client_id = create.json()["id"]
        resp = client.delete(f"/api/v1/clients/{client_id}", headers=headers)
        assert resp.status_code == 204
        list_resp = client.get("/api/v1/clients/", headers=headers)
        assert list_resp.json()["total"] == 0

    def test_invalid_gst_number(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        bad = {**CLIENT, "email": "bad@gmail.com", "phone": "8888888888", "gst_no": "BADGST"}
        resp = client.post("/api/v1/clients/", json=bad, headers=headers)
        assert resp.status_code == 422

    def test_get_nonexistent_client(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        resp = client.get(
            "/api/v1/clients/00000000-0000-0000-0000-000000000000", headers=headers
        )
        assert resp.status_code == 404
