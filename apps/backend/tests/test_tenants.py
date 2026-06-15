"""Tests for Tenant logo (avatar) upload — profile picture feature."""
import pytest


def _auth(client, seed_superadmin):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "TestPassword123!"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


class TestTenantAvatar:
    def test_upload_get_and_remove_avatar(self, client, seed_superadmin, seed_tenant, tiny_png_bytes):
        headers = _auth(client, seed_superadmin)
        tenant_id = seed_tenant.id

        upload = client.post(
            f"/api/v1/tenants/{tenant_id}/avatar",
            files={"file": ("logo.png", tiny_png_bytes, "image/png")},
            headers=headers,
        )
        assert upload.status_code == 200, upload.text
        assert upload.json()["has_avatar"] is True

        get_resp = client.get(f"/api/v1/tenants/{tenant_id}/avatar", headers=headers)
        assert get_resp.status_code == 200, get_resp.text
        assert get_resp.headers["content-type"] == "image/png"
        assert get_resp.content == tiny_png_bytes

        remove = client.delete(f"/api/v1/tenants/{tenant_id}/avatar", headers=headers)
        assert remove.status_code == 200, remove.text
        assert remove.json()["has_avatar"] is False

        missing = client.get(f"/api/v1/tenants/{tenant_id}/avatar", headers=headers)
        assert missing.status_code == 404

    def test_upload_rejects_non_image(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)

        resp = client.post(
            f"/api/v1/tenants/{seed_tenant.id}/avatar",
            files={"file": ("notes.txt", b"not an image", "text/plain")},
            headers=headers,
        )
        assert resp.status_code == 400

    def test_non_superadmin_cannot_upload_tenant_avatar(self, client, seed_superadmin, second_tenant, tiny_png_bytes):
        other_headers = second_tenant["headers"]
        other_tenant_id = second_tenant["tenant_id"]

        resp = client.post(
            f"/api/v1/tenants/{other_tenant_id}/avatar",
            files={"file": ("logo.png", tiny_png_bytes, "image/png")},
            headers=other_headers,
        )
        assert resp.status_code == 403
