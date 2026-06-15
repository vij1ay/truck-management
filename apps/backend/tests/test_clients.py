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


def _login(client, email, password="TestPass123!"):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _create_tenant(client, sa_headers, name, admin_email):
    resp = client.post(
        "/api/v1/tenants",
        json={
            "name": name,
            "admin_email": admin_email,
            "admin_password": "TestPass123!",
            "admin_first_name": "Tenant",
            "admin_last_name": "Admin",
        },
        headers=sa_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestClientPortalLink:
    """Linking an existing portal (Client-role) account to a Client record by
    email — how a shipper gains a relationship with a SECOND tenant/carrier."""

    def test_link_unknown_email_404(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        c = client.post("/api/v1/clients/", json=CLIENT, headers=headers)
        client_id = c.json()["id"]

        resp = client.post(
            f"/api/v1/clients/{client_id}/link-portal-account",
            json={"email": "nobody@example.com"},
            headers=headers,
        )
        assert resp.status_code == 404

    def test_link_non_client_role_rejected(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        c = client.post("/api/v1/clients/", json=CLIENT, headers=headers)
        client_id = c.json()["id"]

        # admin@example.com is SuperAdmin, not Client
        resp = client.post(
            f"/api/v1/clients/{client_id}/link-portal-account",
            json={"email": "admin@example.com"},
            headers=headers,
        )
        assert resp.status_code == 400

    def test_link_relink_and_unlink(self, client, seed_superadmin, seed_tenant, seed_roles):
        sa_headers = _token(client, seed_superadmin)

        # Tenant B + its TenantAdmin
        _create_tenant(client, sa_headers, "Carrier B", "admin.b@example.com")
        b_headers = _login(client, "admin.b@example.com")

        # Two clients in Tenant B
        b1 = client.post("/api/v1/clients/", json={**CLIENT, "company_name": "B Client 1", "email": "b1@example.com"}, headers=b_headers)
        b1_id = b1.json()["id"]
        b2 = client.post("/api/v1/clients/", json={**CLIENT, "company_name": "B Client 2", "email": "b2@example.com"}, headers=b_headers)
        b2_id = b2.json()["id"]

        # Tenant A's TenantAdmin (SuperAdmin can only assign the TenantAdmin role)
        a_admin = client.post(
            "/api/v1/users",
            json={
                "email": "admin.a@example.com",
                "password": "TestPass123!",
                "first_name": "Tenant",
                "last_name": "Admin",
                "tenant_id": str(seed_tenant.id),
                "role_ids": [str(seed_roles["TenantAdmin"].id)],
            },
            headers=sa_headers,
        )
        assert a_admin.status_code == 201, a_admin.text
        a_headers = _login(client, "admin.a@example.com")

        # A shipper portal account, created (and linked to a client) in Tenant A
        a1 = client.post("/api/v1/clients/", json={**CLIENT, "company_name": "A Client", "email": "a1@example.com"}, headers=a_headers)
        a1_id = a1.json()["id"]
        shipper = client.post(
            "/api/v1/users",
            json={
                "email": "shipper@example.com",
                "password": "TestPass123!",
                "first_name": "Ship",
                "last_name": "Per",
                "role_ids": [str(seed_roles["Client"].id)],
                "client_id": a1_id,
            },
            headers=a_headers,
        )
        assert shipper.status_code == 201, shipper.text

        # Tenant B links B1 to the same shipper account
        link1 = client.post(
            f"/api/v1/clients/{b1_id}/link-portal-account",
            json={"email": "shipper@example.com"},
            headers=b_headers,
        )
        assert link1.status_code == 200, link1.text
        assert link1.json()["user_id"] is not None
        b1_user_id = link1.json()["user_id"]

        # A1 (Tenant A) remains linked — separate tenant, separate relationship
        a1_check = client.get(f"/api/v1/clients/{a1_id}", headers=sa_headers)
        assert a1_check.json()["user_id"] == b1_user_id

        # Re-link within Tenant B to B2 — B1 should be unlinked
        link2 = client.post(
            f"/api/v1/clients/{b2_id}/link-portal-account",
            json={"email": "shipper@example.com"},
            headers=b_headers,
        )
        assert link2.status_code == 200, link2.text
        assert link2.json()["user_id"] == b1_user_id

        b1_check = client.get(f"/api/v1/clients/{b1_id}", headers=b_headers)
        assert b1_check.json()["user_id"] is None

        # Unlink B2
        unlink = client.delete(f"/api/v1/clients/{b2_id}/link-portal-account", headers=b_headers)
        assert unlink.status_code == 200, unlink.text
        assert unlink.json()["user_id"] is None


class TestClientTenantFilter:
    def test_superadmin_filters_clients_by_tenant(self, client, seed_superadmin, seed_tenant, second_tenant):
        su_headers = _token(client, seed_superadmin)

        own = client.post("/api/v1/clients/", json={**CLIENT, "company_name": "Tenant A Client"}, headers=su_headers)
        assert own.status_code == 201, own.text

        other_headers = second_tenant["headers"]
        other_tenant_id = second_tenant["tenant_id"]
        other = client.post(
            "/api/v1/clients/",
            json={**CLIENT, "company_name": "Tenant B Client", "email": "tenantb@example.com"},
            headers=other_headers,
        )
        assert other.status_code == 201, other.text

        unfiltered = client.get("/api/v1/clients/", headers=su_headers)
        assert unfiltered.status_code == 200, unfiltered.text
        tenant_ids = {c["tenant_id"] for c in unfiltered.json()["items"]}
        assert str(seed_tenant.id) in tenant_ids
        assert other_tenant_id in tenant_ids

        filtered = client.get("/api/v1/clients/", params={"tenant_id": other_tenant_id}, headers=su_headers)
        assert filtered.status_code == 200, filtered.text
        filtered_data = filtered.json()
        assert filtered_data["total"] >= 1
        assert all(c["tenant_id"] == other_tenant_id for c in filtered_data["items"])


class TestClientAvatar:
    def test_upload_get_and_remove_avatar(self, client, seed_superadmin, tiny_png_bytes):
        headers = _token(client, seed_superadmin)
        create = client.post("/api/v1/clients/", json=CLIENT, headers=headers)
        assert create.status_code == 201, create.text
        client_id = create.json()["id"]
        assert create.json()["has_avatar"] is False

        upload = client.post(
            f"/api/v1/clients/{client_id}/avatar",
            files={"file": ("avatar.png", tiny_png_bytes, "image/png")},
            headers=headers,
        )
        assert upload.status_code == 200, upload.text
        assert upload.json()["has_avatar"] is True

        get_resp = client.get(f"/api/v1/clients/{client_id}/avatar", headers=headers)
        assert get_resp.status_code == 200, get_resp.text
        assert get_resp.headers["content-type"] == "image/png"
        assert get_resp.content == tiny_png_bytes

        remove = client.delete(f"/api/v1/clients/{client_id}/avatar", headers=headers)
        assert remove.status_code == 200, remove.text
        assert remove.json()["has_avatar"] is False

        missing = client.get(f"/api/v1/clients/{client_id}/avatar", headers=headers)
        assert missing.status_code == 404

    def test_upload_rejects_non_image(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        create = client.post("/api/v1/clients/", json=CLIENT, headers=headers)
        client_id = create.json()["id"]

        resp = client.post(
            f"/api/v1/clients/{client_id}/avatar",
            files={"file": ("notes.txt", b"not an image", "text/plain")},
            headers=headers,
        )
        assert resp.status_code == 400
