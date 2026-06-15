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


class TestTruckTenantFilter:
    def test_superadmin_filters_trucks_by_tenant(self, client, seed_superadmin, seed_tenant, second_tenant):
        su_headers = _auth(client, seed_superadmin)

        own = client.post("/api/v1/trucks/", json=TRUCK, headers=su_headers)
        assert own.status_code == 201, own.text

        other_headers = second_tenant["headers"]
        other_tenant_id = second_tenant["tenant_id"]
        other_truck = {**TRUCK, "registration_no": "DL01ZZ9999"}
        other = client.post("/api/v1/trucks/", json=other_truck, headers=other_headers)
        assert other.status_code == 201, other.text

        unfiltered = client.get("/api/v1/trucks/", headers=su_headers)
        assert unfiltered.status_code == 200, unfiltered.text
        tenant_ids = {t["tenant_id"] for t in unfiltered.json()["items"]}
        assert str(seed_tenant.id) in tenant_ids
        assert other_tenant_id in tenant_ids

        filtered = client.get("/api/v1/trucks/", params={"tenant_id": other_tenant_id}, headers=su_headers)
        assert filtered.status_code == 200, filtered.text
        filtered_data = filtered.json()
        assert filtered_data["total"] >= 1
        assert all(t["tenant_id"] == other_tenant_id for t in filtered_data["items"])


class TestTruckAvatar:
    def test_upload_get_and_remove_avatar(self, client, seed_superadmin, tiny_png_bytes):
        headers = _auth(client, seed_superadmin)
        create = client.post("/api/v1/trucks/", json=TRUCK, headers=headers)
        assert create.status_code == 201, create.text
        truck_id = create.json()["id"]
        assert create.json()["has_avatar"] is False

        upload = client.post(
            f"/api/v1/trucks/{truck_id}/avatar",
            files={"file": ("avatar.png", tiny_png_bytes, "image/png")},
            headers=headers,
        )
        assert upload.status_code == 200, upload.text
        assert upload.json()["has_avatar"] is True

        get_resp = client.get(f"/api/v1/trucks/{truck_id}/avatar", headers=headers)
        assert get_resp.status_code == 200, get_resp.text
        assert get_resp.headers["content-type"] == "image/png"
        assert get_resp.content == tiny_png_bytes

        remove = client.delete(f"/api/v1/trucks/{truck_id}/avatar", headers=headers)
        assert remove.status_code == 200, remove.text
        assert remove.json()["has_avatar"] is False

        missing = client.get(f"/api/v1/trucks/{truck_id}/avatar", headers=headers)
        assert missing.status_code == 404

    def test_upload_rejects_non_image(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        create = client.post("/api/v1/trucks/", json=TRUCK, headers=headers)
        truck_id = create.json()["id"]

        resp = client.post(
            f"/api/v1/trucks/{truck_id}/avatar",
            files={"file": ("notes.txt", b"not an image", "text/plain")},
            headers=headers,
        )
        assert resp.status_code == 400

    def test_cannot_access_avatar_of_truck_in_another_tenant(self, client, seed_superadmin, second_tenant, tiny_png_bytes):
        su_headers = _auth(client, seed_superadmin)
        create = client.post("/api/v1/trucks/", json=TRUCK, headers=su_headers)
        truck_id = create.json()["id"]

        other_headers = second_tenant["headers"]
        upload = client.post(
            f"/api/v1/trucks/{truck_id}/avatar",
            files={"file": ("avatar.png", tiny_png_bytes, "image/png")},
            headers=other_headers,
        )
        assert upload.status_code in (403, 404)


class TestTruckPhotos:
    def test_upload_list_get_and_remove_photos(self, client, seed_superadmin, tiny_png_bytes):
        headers = _auth(client, seed_superadmin)
        create = client.post("/api/v1/trucks/", json=TRUCK, headers=headers)
        assert create.status_code == 201, create.text
        truck_id = create.json()["id"]

        # Upload 6 photos (the max) and assert position increments 0..5
        photo_ids = []
        for i in range(6):
            resp = client.post(
                f"/api/v1/trucks/{truck_id}/photos",
                files={"file": (f"photo{i}.png", tiny_png_bytes, "image/png")},
                headers=headers,
            )
            assert resp.status_code == 201, resp.text
            data = resp.json()
            assert data["position"] == i
            assert data["truck_id"] == truck_id
            photo_ids.append(data["id"])

        # 7th photo is rejected
        seventh = client.post(
            f"/api/v1/trucks/{truck_id}/photos",
            files={"file": ("photo7.png", tiny_png_bytes, "image/png")},
            headers=headers,
        )
        assert seventh.status_code == 400, seventh.text

        # List returns all 6, ordered by position
        listing = client.get(f"/api/v1/trucks/{truck_id}/photos", headers=headers)
        assert listing.status_code == 200, listing.text
        items = listing.json()
        assert len(items) == 6
        assert [p["position"] for p in items] == [0, 1, 2, 3, 4, 5]

        # Fetching a photo returns the correct bytes/content-type
        first_id = items[0]["id"]
        get_resp = client.get(f"/api/v1/trucks/{truck_id}/photos/{first_id}", headers=headers)
        assert get_resp.status_code == 200, get_resp.text
        assert get_resp.headers["content-type"] == "image/png"
        assert get_resp.content == tiny_png_bytes

        # Removing a photo drops the count back to 5 and the file is gone
        remove = client.delete(f"/api/v1/trucks/{truck_id}/photos/{first_id}", headers=headers)
        assert remove.status_code == 204, remove.text

        listing_after = client.get(f"/api/v1/trucks/{truck_id}/photos", headers=headers)
        assert len(listing_after.json()) == 5

        missing = client.get(f"/api/v1/trucks/{truck_id}/photos/{first_id}", headers=headers)
        assert missing.status_code == 404

    def test_upload_rejects_non_image(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        create = client.post("/api/v1/trucks/", json=TRUCK, headers=headers)
        truck_id = create.json()["id"]

        resp = client.post(
            f"/api/v1/trucks/{truck_id}/photos",
            files={"file": ("notes.txt", b"not an image", "text/plain")},
            headers=headers,
        )
        assert resp.status_code == 400

    def test_cannot_access_photos_of_truck_in_another_tenant(self, client, seed_superadmin, second_tenant, tiny_png_bytes):
        su_headers = _auth(client, seed_superadmin)
        create = client.post("/api/v1/trucks/", json=TRUCK, headers=su_headers)
        truck_id = create.json()["id"]
        client.post(
            f"/api/v1/trucks/{truck_id}/photos",
            files={"file": ("photo.png", tiny_png_bytes, "image/png")},
            headers=su_headers,
        )

        other_headers = second_tenant["headers"]
        listing = client.get(f"/api/v1/trucks/{truck_id}/photos", headers=other_headers)
        assert listing.status_code in (403, 404)

        upload = client.post(
            f"/api/v1/trucks/{truck_id}/photos",
            files={"file": ("photo.png", tiny_png_bytes, "image/png")},
            headers=other_headers,
        )
        assert upload.status_code in (403, 404)


class TestTruckDocumentsDriverAccess:
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
                "phone": "9000000098",
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

    def test_driver_can_list_documents_for_assigned_truck(self, client, seed_superadmin, seed_roles, seed_tenant):
        sa_headers = _auth(client, seed_superadmin)
        ta_headers = self._create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.truckdoc1@example.com")
        truck_id = client.post("/api/v1/trucks/", json={**TRUCK, "registration_no": "MH12TD0001"}, headers=ta_headers).json()["id"]
        driver_headers, driver_id = self._create_driver_user(client, ta_headers, seed_roles, "truckdoc.driver1@example.com", "TDOC1111111")

        assign = client.patch(f"/api/v1/trucks/{truck_id}", json={"assigned_driver_id": driver_id}, headers=ta_headers)
        assert assign.status_code == 200, assign.text

        resp = client.get(f"/api/v1/trucks/{truck_id}/documents", headers=driver_headers)
        assert resp.status_code == 200, resp.text

    def test_driver_cannot_list_documents_for_unassigned_truck(self, client, seed_superadmin, seed_roles, seed_tenant):
        sa_headers = _auth(client, seed_superadmin)
        ta_headers = self._create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.truckdoc2@example.com")
        truck_id = client.post("/api/v1/trucks/", json={**TRUCK, "registration_no": "MH12TD0002"}, headers=ta_headers).json()["id"]
        driver_headers, _ = self._create_driver_user(client, ta_headers, seed_roles, "truckdoc.driver2@example.com", "TDOC2222222")

        resp = client.get(f"/api/v1/trucks/{truck_id}/documents", headers=driver_headers)
        assert resp.status_code == 403
