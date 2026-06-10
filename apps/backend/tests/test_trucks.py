"""Tests for Trucks API endpoints - Phase 2."""
import pytest
from datetime import date


def _get_token(client, seed_superadmin):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "TestPassword123!"}
    )
    return resp.json()["access_token"]


def _auth(client, seed_superadmin):
    return {"Authorization": f"Bearer {_get_token(client, seed_superadmin)}"}


TRUCK = {
    "registration_no": "MH12AB1234",
    "truck_type": "flatbed",
    "ownership_type": "owned",
    "make": "Tata",
    "model": "LPT 2518",
    "year": 2022,
    "capacity_tons": 25.0,
}


class TestTruckEndpoints:
    def test_create_truck_success(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        resp = client.post("/api/v1/trucks/", json=TRUCK, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["registration_no"] == "MH12AB1234"
        assert data["truck_type"] == "flatbed"

    def test_create_duplicate_registration(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        client.post("/api/v1/trucks/", json=TRUCK, headers=headers)
        resp = client.post("/api/v1/trucks/", json=TRUCK, headers=headers)
        assert resp.status_code == 409

    def test_list_trucks_empty(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        resp = client.get("/api/v1/trucks/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    def test_list_trucks_with_data(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        client.post("/api/v1/trucks/", json=TRUCK, headers=headers)
        resp = client.get("/api/v1/trucks/", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_get_truck_by_id(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        create = client.post("/api/v1/trucks/", json=TRUCK, headers=headers)
        truck_id = create.json()["id"]
        resp = client.get(f"/api/v1/trucks/{truck_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == truck_id

    def test_get_nonexistent_truck(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        resp = client.get(
            "/api/v1/trucks/00000000-0000-0000-0000-000000000000", headers=headers
        )
        assert resp.status_code == 404

    def test_update_truck(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        create = client.post("/api/v1/trucks/", json=TRUCK, headers=headers)
        truck_id = create.json()["id"]
        resp = client.patch(
            f"/api/v1/trucks/{truck_id}",
            json={"make": "Ashok Leyland"},
            headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["make"] == "Ashok Leyland"

    def test_soft_delete_truck(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        create = client.post("/api/v1/trucks/", json=TRUCK, headers=headers)
        truck_id = create.json()["id"]
        resp = client.delete(f"/api/v1/trucks/{truck_id}", headers=headers)
        assert resp.status_code == 204
        # Should not appear in list
        list_resp = client.get("/api/v1/trucks/", headers=headers)
        assert list_resp.json()["total"] == 0

    def test_activate_deactivate_truck(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        create = client.post("/api/v1/trucks/", json=TRUCK, headers=headers)
        truck_id = create.json()["id"]

        deact = client.post(f"/api/v1/trucks/{truck_id}/deactivate", headers=headers)
        assert deact.status_code == 200
        assert deact.json()["status"] == "inactive"

        act = client.post(f"/api/v1/trucks/{truck_id}/activate", headers=headers)
        assert act.status_code == 200
        assert act.json()["status"] == "active"

    def test_invalid_year(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        bad = {**TRUCK, "registration_no": "MH12ZZ9999", "year": 1800}
        resp = client.post("/api/v1/trucks/", json=bad, headers=headers)
        assert resp.status_code == 422

    def test_filter_by_status(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        client.post("/api/v1/trucks/", json=TRUCK, headers=headers)
        resp = client.get("/api/v1/trucks/?status=active", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1
