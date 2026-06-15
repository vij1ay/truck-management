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


class TestDriverTenantFilter:
    def test_superadmin_filters_drivers_by_tenant(self, client, seed_superadmin, seed_tenant, second_tenant):
        su_headers = _auth(client, seed_superadmin)

        own = client.post("/api/v1/drivers/", json=DRIVER, headers=su_headers)
        assert own.status_code == 201, own.text

        other_headers = second_tenant["headers"]
        other_tenant_id = second_tenant["tenant_id"]
        other_driver = {**DRIVER, "license_no": "DL9876543210", "phone": "9123456789"}
        other = client.post("/api/v1/drivers/", json=other_driver, headers=other_headers)
        assert other.status_code == 201, other.text

        unfiltered = client.get("/api/v1/drivers/", headers=su_headers)
        assert unfiltered.status_code == 200, unfiltered.text
        tenant_ids = {d["tenant_id"] for d in unfiltered.json()["items"]}
        assert str(seed_tenant.id) in tenant_ids
        assert other_tenant_id in tenant_ids

        filtered = client.get("/api/v1/drivers/", params={"tenant_id": other_tenant_id}, headers=su_headers)
        assert filtered.status_code == 200, filtered.text
        filtered_data = filtered.json()
        assert filtered_data["total"] >= 1
        assert all(d["tenant_id"] == other_tenant_id for d in filtered_data["items"])


class TestDriverMe:
    def test_get_my_driver_profile_with_assigned_truck(self, client, seed_superadmin, seed_tenant):
        su_headers = _auth(client, seed_superadmin)

        # Create a login (Driver role) and link it to a Driver record
        user_resp = client.post(
            "/api/v1/users",
            json={
                "email": "mobile.driver@example.com",
                "password": "TestPass123",
                "first_name": "Mobile",
                "last_name": "Driver",
            },
            headers=su_headers,
        )
        assert user_resp.status_code == 201, user_resp.text
        user_id = user_resp.json()["id"]

        driver_resp = client.post(
            "/api/v1/drivers/",
            json={**DRIVER, "user_id": user_id, "license_no": "MM1234567890"},
            headers=su_headers,
        )
        assert driver_resp.status_code == 201, driver_resp.text
        driver_id = driver_resp.json()["id"]

        # Create a truck and assign it to this driver
        truck_resp = client.post(
            "/api/v1/trucks/",
            json={
                "registration_no": "MH14XY9999",
                "truck_type": "flatbed",
                "ownership_type": "owned",
                "capacity_tons": 10.0,
            },
            headers=su_headers,
        )
        assert truck_resp.status_code == 201, truck_resp.text
        truck_id = truck_resp.json()["id"]

        patch_resp = client.patch(
            f"/api/v1/trucks/{truck_id}",
            json={"assigned_driver_id": driver_id},
            headers=su_headers,
        )
        assert patch_resp.status_code == 200, patch_resp.text

        # Log in as the driver and call /drivers/me
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "mobile.driver@example.com", "password": "TestPass123"},
        )
        driver_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        me = client.get("/api/v1/drivers/me", headers=driver_headers)
        assert me.status_code == 200, me.text
        data = me.json()
        assert data["id"] == driver_id
        assert data["current_truck"] is not None
        assert data["current_truck"]["id"] == truck_id
        assert data["current_truck"]["registration_no"] == "MH14XY9999"

    def test_get_my_driver_profile_404_without_linked_driver(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        resp = client.get("/api/v1/drivers/me", headers=headers)
        assert resp.status_code == 404


class TestDriverDocumentsDriverAccess:
    def _create_tenant_admin(self, client, sa_headers, seed_roles, seed_tenant, email):
        resp = client.post(
            "/api/v1/users",
            json={
                "email": email,
                "password": "TestPass123",
                "first_name": "Tenant",
                "last_name": "Admin",
                "tenant_id": str(seed_tenant.id),
                "role_ids": [str(seed_roles["TenantAdmin"].id)],
            },
            headers=sa_headers,
        )
        assert resp.status_code == 201, resp.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass123"})
        assert login.status_code == 200, login.text
        return {"Authorization": f"Bearer {login.json()['access_token']}"}

    def _create_driver_user(self, client, headers, seed_roles, email, license_no):
        user_resp = client.post(
            "/api/v1/users",
            json={
                "email": email,
                "password": "TestPass123",
                "first_name": "Mobile",
                "last_name": "Driver",
                "role_ids": [str(seed_roles["Driver"].id)],
            },
            headers=headers,
        )
        assert user_resp.status_code == 201, user_resp.text
        user_id = user_resp.json()["id"]

        driver_resp = client.post(
            "/api/v1/drivers/",
            json={
                "first_name": "Mobile",
                "last_name": "Driver",
                "phone": "9000000097",
                "license_no": license_no,
                "license_class": "hmv",
                "license_expiry": "2030-01-01",
                "user_id": user_id,
            },
            headers=headers,
        )
        assert driver_resp.status_code == 201, driver_resp.text
        driver_id = driver_resp.json()["id"]

        login = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass123"})
        assert login.status_code == 200, login.text
        return {"Authorization": f"Bearer {login.json()['access_token']}"}, driver_id

    def test_driver_can_list_own_documents(self, client, seed_superadmin, seed_roles, seed_tenant):
        sa_headers = _auth(client, seed_superadmin)
        ta_headers = self._create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.driverdoc1@example.com")
        driver_headers, driver_id = self._create_driver_user(client, ta_headers, seed_roles, "driverdoc.driver1@example.com", "DDOC1111111")

        resp = client.get(f"/api/v1/drivers/{driver_id}/documents", headers=driver_headers)
        assert resp.status_code == 200, resp.text

    def test_driver_cannot_list_other_drivers_documents(self, client, seed_superadmin, seed_roles, seed_tenant):
        sa_headers = _auth(client, seed_superadmin)
        ta_headers = self._create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.driverdoc2@example.com")
        driver_headers_a, _ = self._create_driver_user(client, ta_headers, seed_roles, "driverdoc.driver2a@example.com", "DDOC2222221")
        _, driver_id_b = self._create_driver_user(client, ta_headers, seed_roles, "driverdoc.driver2b@example.com", "DDOC2222222")

        resp = client.get(f"/api/v1/drivers/{driver_id_b}/documents", headers=driver_headers_a)
        assert resp.status_code == 403
