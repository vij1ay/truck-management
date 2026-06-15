"""Tests for user timezone preferences and backend-localized display timestamps."""
import re

import pytest


def _auth(client, seed_superadmin):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "TestPassword123!"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _create_client(client, headers, name="Linked Client Co"):
    resp = client.post(
        "/api/v1/clients/",
        json={"company_name": name, "phone": "9876540001", "client_type": "company"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


DISPLAY_RE = re.compile(r"^\d{2} \w{3} \d{4}, \d{2}:\d{2} (AM|PM) \w+$")


class TestUserTimezone:
    def test_create_user_with_timezone(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        resp = client.post(
            "/api/v1/users",
            json={
                "email": "ist.user@example.com",
                "password": "TestPass123",
                "first_name": "IST",
                "last_name": "User",
                "timezone": "Asia/Kolkata",
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["timezone"] == "Asia/Kolkata"
        assert DISPLAY_RE.match(data["created_at"]), data["created_at"]
        assert data["created_at"].endswith("IST")

    def test_create_user_without_timezone_defaults(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        resp = client.post(
            "/api/v1/users",
            json={
                "email": "default.tz@example.com",
                "password": "TestPass123",
                "first_name": "Default",
                "last_name": "TZ",
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["timezone"] == "Asia/Kolkata"  # settings.DEFAULT_TIMEZONE
        assert data["created_at"].endswith("IST")

    def test_create_user_invalid_timezone_rejected(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        resp = client.post(
            "/api/v1/users",
            json={
                "email": "bad.tz@example.com",
                "password": "TestPass123",
                "first_name": "Bad",
                "last_name": "TZ",
                "timezone": "Not/AZone",
            },
            headers=headers,
        )
        assert resp.status_code == 422

    def test_list_timezones(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        resp = client.get("/api/v1/users/timezones", headers=headers)
        assert resp.status_code == 200
        timezones = resp.json()["timezones"]
        assert "Asia/Kolkata" in timezones
        assert "America/New_York" in timezones

    def test_user_local_time_reflects_their_timezone(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        create = client.post(
            "/api/v1/users",
            json={
                "email": "ny.user@example.com",
                "password": "TestPass123",
                "first_name": "NY",
                "last_name": "User",
                "timezone": "America/New_York",
            },
            headers=headers,
        )
        assert create.status_code == 201, create.text

        # Log in as the new user and confirm their own profile is rendered in
        # America/New_York time, independent of the admin's (IST) request above.
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "ny.user@example.com", "password": "TestPass123"},
        )
        assert login.status_code == 200, login.text
        ny_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        me = client.get("/api/v1/users/me", headers=ny_headers)
        assert me.status_code == 200
        data = me.json()
        assert data["timezone"] == "America/New_York"
        assert DISPLAY_RE.match(data["created_at"]), data["created_at"]
        assert data["created_at"].endswith(("EST", "EDT"))

    def test_update_user_timezone(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        create = client.post(
            "/api/v1/users",
            json={
                "email": "update.tz@example.com",
                "password": "TestPass123",
                "first_name": "Update",
                "last_name": "TZ",
                "timezone": "Asia/Kolkata",
            },
            headers=headers,
        )
        assert create.status_code == 201, create.text
        user_id = create.json()["id"]

        update = client.patch(
            f"/api/v1/users/{user_id}",
            json={"timezone": "America/New_York"},
            headers=headers,
        )
        assert update.status_code == 200, update.text
        assert update.json()["timezone"] == "America/New_York"


class TestUserClientLink:
    def test_create_user_with_client_link(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "Acme Logistics")

        resp = client.post(
            "/api/v1/users",
            json={
                "email": "acme.portal@example.com",
                "password": "TestPass123",
                "first_name": "Acme",
                "last_name": "Portal",
                "client_id": client_id,
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["client_id"] == client_id

        # Reflected on get + list too
        user_id = resp.json()["id"]
        get_resp = client.get(f"/api/v1/users/{user_id}", headers=headers)
        assert get_resp.json()["client_id"] == client_id

    def test_link_client_already_linked_rejected(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "Single Login Co")

        first = client.post(
            "/api/v1/users",
            json={
                "email": "first.portal@example.com",
                "password": "TestPass123",
                "first_name": "First",
                "last_name": "User",
                "client_id": client_id,
            },
            headers=headers,
        )
        assert first.status_code == 201, first.text

        second = client.post(
            "/api/v1/users",
            json={
                "email": "second.portal@example.com",
                "password": "TestPass123",
                "first_name": "Second",
                "last_name": "User",
                "client_id": client_id,
            },
            headers=headers,
        )
        assert second.status_code == 409, second.text

    def test_update_user_relink_and_unlink_client(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_a = _create_client(client, headers, "Client A")
        client_b = _create_client(client, headers, "Client B")

        create = client.post(
            "/api/v1/users",
            json={
                "email": "relink.portal@example.com",
                "password": "TestPass123",
                "first_name": "Relink",
                "last_name": "User",
                "client_id": client_a,
            },
            headers=headers,
        )
        assert create.status_code == 201, create.text
        user_id = create.json()["id"]
        assert create.json()["client_id"] == client_a

        # Re-link to client B
        relink = client.patch(f"/api/v1/users/{user_id}", json={"client_id": client_b}, headers=headers)
        assert relink.status_code == 200, relink.text
        assert relink.json()["client_id"] == client_b

        # Unlink entirely
        unlink = client.patch(f"/api/v1/users/{user_id}", json={"client_id": None}, headers=headers)
        assert unlink.status_code == 200, unlink.text
        assert unlink.json()["client_id"] is None

        # client_a should now be free for a new user
        reuse = client.post(
            "/api/v1/users",
            json={
                "email": "reuse.portal@example.com",
                "password": "TestPass123",
                "first_name": "Reuse",
                "last_name": "User",
                "client_id": client_a,
            },
            headers=headers,
        )
        assert reuse.status_code == 201, reuse.text


class TestUserTenantFilter:
    def test_superadmin_filters_users_by_tenant(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)

        # SuperAdmin creates a second tenant (which provisions its own TenantAdmin user)
        create_tenant = client.post(
            "/api/v1/tenants",
            json={
                "name": "Other Logistics Co",
                "subscription_tier": "trial",
                "max_users": 10,
                "admin_email": "admin@other-logistics.example",
                "admin_password": "OtherPass123",
                "admin_first_name": "Other",
                "admin_last_name": "Admin",
            },
            headers=headers,
        )
        assert create_tenant.status_code == 201, create_tenant.text
        other_tenant_id = create_tenant.json()["id"]

        # Unfiltered list includes users from both tenants
        unfiltered = client.get("/api/v1/users", headers=headers)
        assert unfiltered.status_code == 200, unfiltered.text
        all_tenant_ids = {u["tenant_id"] for u in unfiltered.json()["items"]}
        assert str(seed_tenant.id) in all_tenant_ids
        assert other_tenant_id in all_tenant_ids

        # Filtering by the new tenant only returns its users
        filtered = client.get(
            "/api/v1/users", params={"tenant_id": other_tenant_id}, headers=headers
        )
        assert filtered.status_code == 200, filtered.text
        filtered_data = filtered.json()
        assert filtered_data["total"] >= 1
        assert all(u["tenant_id"] == other_tenant_id for u in filtered_data["items"])
        emails = {u["email"] for u in filtered_data["items"]}
        assert "admin@other-logistics.example" in emails

        # Filtering by the original tenant excludes the new tenant's users
        original_filtered = client.get(
            "/api/v1/users", params={"tenant_id": str(seed_tenant.id)}, headers=headers
        )
        assert original_filtered.status_code == 200, original_filtered.text
        assert all(
            u["tenant_id"] == str(seed_tenant.id) for u in original_filtered.json()["items"]
        )


class TestUserAvatar:
    def test_upload_get_and_remove_avatar(self, client, seed_superadmin, seed_tenant, tiny_png_bytes):
        headers = _auth(client, seed_superadmin)
        user_id = seed_superadmin.id

        upload = client.post(
            f"/api/v1/users/{user_id}/avatar",
            files={"file": ("avatar.png", tiny_png_bytes, "image/png")},
            headers=headers,
        )
        assert upload.status_code == 200, upload.text
        assert upload.json()["has_avatar"] is True

        get_resp = client.get(f"/api/v1/users/{user_id}/avatar", headers=headers)
        assert get_resp.status_code == 200, get_resp.text
        assert get_resp.headers["content-type"] == "image/png"
        assert get_resp.content == tiny_png_bytes

        remove = client.delete(f"/api/v1/users/{user_id}/avatar", headers=headers)
        assert remove.status_code == 200, remove.text
        assert remove.json()["has_avatar"] is False

        missing = client.get(f"/api/v1/users/{user_id}/avatar", headers=headers)
        assert missing.status_code == 404

    def test_upload_rejects_non_image(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        user_id = seed_superadmin.id

        resp = client.post(
            f"/api/v1/users/{user_id}/avatar",
            files={"file": ("notes.txt", b"not an image", "text/plain")},
            headers=headers,
        )
        assert resp.status_code == 400

    def test_user_can_upload_own_avatar_but_not_others(self, client, seed_superadmin, seed_tenant, tiny_png_bytes):
        su_headers = _auth(client, seed_superadmin)

        # Create a non-admin user in the same tenant
        create = client.post(
            "/api/v1/users",
            json={
                "email": "selfavatar@example.com",
                "password": "TestPass123",
                "first_name": "Self",
                "last_name": "Avatar",
            },
            headers=su_headers,
        )
        assert create.status_code == 201, create.text
        other_user_id = create.json()["id"]

        login = client.post(
            "/api/v1/auth/login",
            json={"email": "selfavatar@example.com", "password": "TestPass123"},
        )
        own_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Can upload their own avatar
        own_upload = client.post(
            f"/api/v1/users/{other_user_id}/avatar",
            files={"file": ("avatar.png", tiny_png_bytes, "image/png")},
            headers=own_headers,
        )
        assert own_upload.status_code == 200, own_upload.text

        # Cannot upload the SuperAdmin's avatar
        forbidden = client.post(
            f"/api/v1/users/{seed_superadmin.id}/avatar",
            files={"file": ("avatar.png", tiny_png_bytes, "image/png")},
            headers=own_headers,
        )
        assert forbidden.status_code == 403


class TestUserPreferredLanguage:
    def test_self_update_preferred_language(self, client, seed_superadmin, seed_tenant):
        su_headers = _auth(client, seed_superadmin)

        create = client.post(
            "/api/v1/users",
            json={
                "email": "lang.user@example.com",
                "password": "TestPass123",
                "first_name": "Lang",
                "last_name": "User",
            },
            headers=su_headers,
        )
        assert create.status_code == 201, create.text
        user_id = create.json()["id"]
        assert create.json()["preferred_language"] is None

        login = client.post(
            "/api/v1/auth/login",
            json={"email": "lang.user@example.com", "password": "TestPass123"},
        )
        own_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        for lang in ("hi", "ta", "en"):
            update = client.patch(
                f"/api/v1/users/{user_id}",
                json={"preferred_language": lang},
                headers=own_headers,
            )
            assert update.status_code == 200, update.text
            assert update.json()["preferred_language"] == lang

    def test_invalid_preferred_language_rejected(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        resp = client.patch(
            f"/api/v1/users/{seed_superadmin.id}",
            json={"preferred_language": "fr"},
            headers=headers,
        )
        assert resp.status_code == 422
