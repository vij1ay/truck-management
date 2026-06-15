"""Tests for the Audit Log viewer API — GET /audit-logs."""
from datetime import date, timedelta

import pytest


def _token(client, seed_superadmin):
    r = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "TestPassword123!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


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


class TestAuditLogs:
    def test_list_includes_login_event_with_user_email(self, client, seed_superadmin):
        # Logging in itself creates a LOGIN audit entry for this user
        headers = _token(client, seed_superadmin)

        resp = client.get("/api/v1/audit-logs?event_category=auth", headers=headers)
        assert resp.status_code == 200, resp.text
        items = resp.json()["items"]
        login_entries = [i for i in items if i["event_type"] == "LOGIN"]
        assert len(login_entries) >= 1
        assert login_entries[0]["user_email"] == "admin@example.com"

    def test_get_single_log_includes_user_email(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)

        listed = client.get("/api/v1/audit-logs?event_category=auth", headers=headers)
        log_id = next(i["id"] for i in listed.json()["items"] if i["event_type"] == "LOGIN")

        detail = client.get(f"/api/v1/audit-logs/{log_id}", headers=headers)
        assert detail.status_code == 200, detail.text
        assert detail.json()["user_email"] == "admin@example.com"

    def test_date_range_filter(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)

        # A start_date in the future should exclude everything that just happened
        future = (date.today() + timedelta(days=1)).isoformat()
        resp_future = client.get(f"/api/v1/audit-logs?start_date={future}T00:00:00", headers=headers)
        assert resp_future.status_code == 200, resp_future.text
        assert resp_future.json()["total"] == 0

        # A start_date in the past should include the login that just happened
        past = (date.today() - timedelta(days=1)).isoformat()
        resp_past = client.get(f"/api/v1/audit-logs?start_date={past}T00:00:00", headers=headers)
        assert resp_past.status_code == 200, resp_past.text
        assert resp_past.json()["total"] >= 1

        # An end_date in the past should exclude everything that just happened
        resp_end = client.get(f"/api/v1/audit-logs?end_date={past}T00:00:00", headers=headers)
        assert resp_end.status_code == 200, resp_end.text
        assert resp_end.json()["total"] == 0

    def test_tenant_admin_cannot_see_other_tenants_logs(self, client, seed_superadmin):
        sa_headers = _token(client, seed_superadmin)

        tenant_a = _create_tenant(client, sa_headers, "Audit Tenant A", "audit.a@example.com")
        tenant_b = _create_tenant(client, sa_headers, "Audit Tenant B", "audit.b@example.com")

        a_headers = _login(client, "audit.a@example.com")
        b_headers = _login(client, "audit.b@example.com")

        # Tenant A's login event should be visible to A's TenantAdmin...
        a_logs = client.get("/api/v1/audit-logs?event_category=auth", headers=a_headers)
        assert a_logs.status_code == 200, a_logs.text
        a_user_ids = {i["user_id"] for i in a_logs.json()["items"]}

        # ...but Tenant B's TenantAdmin should not see A's user_id in their logs
        b_logs = client.get("/api/v1/audit-logs?event_category=auth", headers=b_headers)
        assert b_logs.status_code == 200, b_logs.text
        b_user_ids = {i["user_id"] for i in b_logs.json()["items"]}

        assert a_user_ids.isdisjoint(b_user_ids)

    def test_requires_admin_role(self, client, seed_superadmin, seed_tenant, seed_roles):
        sa_headers = _token(client, seed_superadmin)

        # SuperAdmin can only assign TenantAdmin directly — bootstrap one to
        # create the Driver-role user.
        ta = client.post(
            "/api/v1/users",
            json={
                "email": "ta.audit@example.com",
                "password": "TestPass123!",
                "first_name": "Tenant",
                "last_name": "Admin",
                "tenant_id": str(seed_tenant.id),
                "role_ids": [str(seed_roles["TenantAdmin"].id)],
            },
            headers=sa_headers,
        )
        assert ta.status_code == 201, ta.text
        ta_headers = _login(client, "ta.audit@example.com")

        # A Driver-role user should not be able to view audit logs
        driver = client.post(
            "/api/v1/users",
            json={
                "email": "driver.audit@example.com",
                "password": "TestPass123!",
                "first_name": "Drive",
                "last_name": "Er",
                "role_ids": [str(seed_roles["Driver"].id)],
            },
            headers=ta_headers,
        )
        assert driver.status_code == 201, driver.text

        driver_headers = _login(client, "driver.audit@example.com")
        resp = client.get("/api/v1/audit-logs", headers=driver_headers)
        assert resp.status_code == 403
