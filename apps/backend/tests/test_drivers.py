"""Tests for Drivers API endpoints - Phase 2."""
import pytest
from datetime import date, timedelta


def _auth(client, seed_superadmin):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "TestPassword123!"}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _future_date(days=365):
    return (date.today() + timedelta(days=days)).isoformat()


def _past_date(days=10):
    return (date.today() - timedelta(days=days)).isoformat()


DRIVER = {
    "first_name": "Ravi",
    "last_name": "Kumar",
    "phone": "9876543210",
    "license_no": "MH1234567890",
    "license_class": "hmv",
    "license_expiry": _future_date(365),
}


class TestDriverEndpoints:
    def test_create_driver_success(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        resp = client.post("/api/v1/drivers/", json=DRIVER, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["first_name"] == "Ravi"
        assert data["license_no"] == "MH1234567890"

    def test_create_duplicate_license(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        client.post("/api/v1/drivers/", json=DRIVER, headers=headers)
        dup = {**DRIVER, "phone": "9999999999"}
        resp = client.post("/api/v1/drivers/", json=dup, headers=headers)
        assert resp.status_code == 409

    def test_list_drivers(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        client.post("/api/v1/drivers/", json=DRIVER, headers=headers)
        resp = client.get("/api/v1/drivers/", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_get_driver_by_id(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        create = client.post("/api/v1/drivers/", json=DRIVER, headers=headers)
        driver_id = create.json()["id"]
        resp = client.get(f"/api/v1/drivers/{driver_id}", headers=headers)
        assert resp.status_code == 200

    def test_get_nonexistent_driver(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        resp = client.get(
            "/api/v1/drivers/00000000-0000-0000-0000-000000000000", headers=headers
        )
        assert resp.status_code == 404

    def test_update_driver(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        create = client.post("/api/v1/drivers/", json=DRIVER, headers=headers)
        driver_id = create.json()["id"]
        resp = client.patch(
            f"/api/v1/drivers/{driver_id}",
            json={"phone": "9999999999"},
            headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["phone"] == "9999999999"

    def test_toggle_availability(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        create = client.post("/api/v1/drivers/", json=DRIVER, headers=headers)
        driver_id = create.json()["id"]
        # The endpoint expects a DriverAvailabilityUpdate schema (is_available, status)
        resp = client.post(
            f"/api/v1/drivers/{driver_id}/toggle-availability",
            json={"is_available": False, "status": "on_leave"},
            headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["is_available"] is False

    def test_toggle_availability_with_expired_license(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        # 1. Create with valid license
        valid_driver = {**DRIVER, "license_no": "EXP-UNIQUE-123"}
        create = client.post("/api/v1/drivers/", json=valid_driver, headers=headers)
        assert create.status_code == 201
        driver_id = create.json()["id"]
        
        # 2. Update to expired license (PATCH doesn't block expired dates)
        patch = client.patch(f"/api/v1/drivers/{driver_id}", json={"license_expiry": "2020-01-01"}, headers=headers)
        assert patch.status_code == 200
        
        # 3. Try to toggle availability to True (should fail)
        resp = client.post(
            f"/api/v1/drivers/{driver_id}/toggle-availability",
            json={"is_available": True},
            headers=headers
        )
        assert resp.status_code == 400

    def test_soft_delete_driver(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        create = client.post("/api/v1/drivers/", json=DRIVER, headers=headers)
        driver_id = create.json()["id"]
        resp = client.delete(f"/api/v1/drivers/{driver_id}", headers=headers)
        assert resp.status_code == 204
        list_resp = client.get("/api/v1/drivers/", headers=headers)
        assert list_resp.json()["total"] == 0
