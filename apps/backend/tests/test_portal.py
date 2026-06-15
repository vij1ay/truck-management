"""Tests for the Customer (Client) Portal — Phase 11."""
from datetime import date, timedelta

import pytest


def _superadmin_auth(client, seed_superadmin):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "TestPassword123!"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _login(client, email, password="TestPass123"):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _create_tenant_admin(client, superadmin_headers, seed_roles, seed_tenant, email):
    """SuperAdmin can only assign the TenantAdmin role — bootstrap one to manage Clients/Users."""
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
        headers=superadmin_headers,
    )
    assert resp.status_code == 201, resp.text
    return _login(client, email)


def _create_client(client, headers, name="Acme Logistics"):
    resp = client.post(
        "/api/v1/clients/",
        json={"company_name": name, "phone": "9876540001", "client_type": "company"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _create_portal_user(client, admin_headers, seed_roles, email, client_id=None):
    payload = {
        "email": email,
        "password": "TestPass123",
        "first_name": "Portal",
        "last_name": "User",
        "role_ids": [str(seed_roles["Client"].id)],
    }
    if client_id is not None:
        payload["client_id"] = client_id
    resp = client.post("/api/v1/users", json=payload, headers=admin_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_load_as_admin(client, admin_headers, client_id, freight=15000.0):
    resp = client.post(
        "/api/v1/loads/",
        json={
            "client_id": client_id,
            "origin": "Mumbai",
            "destination": "Delhi",
            "pickup_date": (date.today() + timedelta(days=2)).isoformat(),
            "goods_type": "general",
            "weight_kg": 5000.0,
            "freight_amount": freight,
            "advance_amount": 0,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestPortal:
    def test_get_my_profile(self, client, seed_superadmin, seed_tenant, seed_roles):
        sa_headers = _superadmin_auth(client, seed_superadmin)
        ta_headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.profile@example.com")

        client_id = _create_client(client, ta_headers, "Acme Logistics")
        _create_portal_user(client, ta_headers, seed_roles, "acme.me@example.com", client_id)

        portal_headers = _login(client, "acme.me@example.com")
        resp = client.get("/api/v1/portal/me", headers=portal_headers)
        assert resp.status_code == 200, resp.text
        carriers = resp.json()["carriers"]
        assert len(carriers) == 1
        assert carriers[0]["tenant_id"] == str(seed_tenant.id)
        assert carriers[0]["tenant_name"] == seed_tenant.name
        assert carriers[0]["client"]["id"] == client_id
        assert carriers[0]["client"]["company_name"] == "Acme Logistics"

    def test_create_and_list_my_shipment(self, client, seed_superadmin, seed_tenant, seed_roles):
        sa_headers = _superadmin_auth(client, seed_superadmin)
        ta_headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.booking@example.com")

        client_id = _create_client(client, ta_headers, "Booking Co")
        _create_portal_user(client, ta_headers, seed_roles, "booking.user@example.com", client_id)
        portal_headers = _login(client, "booking.user@example.com")

        create = client.post(
            "/api/v1/portal/loads",
            json={
                "tenant_id": str(seed_tenant.id),
                "origin": "Pune",
                "destination": "Bangalore",
                "pickup_date": (date.today() + timedelta(days=3)).isoformat(),
                "goods_type": "general",
                "weight_kg": 1000.0,
            },
            headers=portal_headers,
        )
        assert create.status_code == 201, create.text
        load = create.json()
        assert load["client_id"] == client_id
        assert load["status"] == "draft"

        listed = client.get("/api/v1/portal/loads", headers=portal_headers)
        assert listed.status_code == 200, listed.text
        ids = [item["id"] for item in listed.json()["items"]]
        assert load["id"] in ids

    def test_cannot_see_other_clients_shipments(self, client, seed_superadmin, seed_tenant, seed_roles):
        sa_headers = _superadmin_auth(client, seed_superadmin)
        ta_headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.isolation@example.com")

        client_a = _create_client(client, ta_headers, "Client A")
        client_b = _create_client(client, ta_headers, "Client B")
        _create_portal_user(client, ta_headers, seed_roles, "a.user@example.com", client_a)

        # Admin books a load for Client B
        load_b = _create_load_as_admin(client, ta_headers, client_b)

        portal_headers_a = _login(client, "a.user@example.com")

        # Client A's list shouldn't include Client B's load
        listed = client.get("/api/v1/portal/loads", headers=portal_headers_a)
        assert listed.status_code == 200
        ids = [item["id"] for item in listed.json()["items"]]
        assert load_b["id"] not in ids

        # Direct access to Client B's load is not found (it's not among A's linked clients)
        detail = client.get(f"/api/v1/portal/loads/{load_b['id']}", headers=portal_headers_a)
        assert detail.status_code == 404

        history = client.get(f"/api/v1/portal/loads/{load_b['id']}/history", headers=portal_headers_a)
        assert history.status_code == 404

        documents = client.get(f"/api/v1/portal/loads/{load_b['id']}/documents", headers=portal_headers_a)
        assert documents.status_code == 404

    def test_shipment_detail_and_history(self, client, seed_superadmin, seed_tenant, seed_roles):
        sa_headers = _superadmin_auth(client, seed_superadmin)
        ta_headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.timeline@example.com")

        client_id = _create_client(client, ta_headers, "Timeline Co")
        _create_portal_user(client, ta_headers, seed_roles, "timeline.user@example.com", client_id)
        portal_headers = _login(client, "timeline.user@example.com")

        create = client.post(
            "/api/v1/portal/loads",
            json={
                "tenant_id": str(seed_tenant.id),
                "origin": "Chennai",
                "destination": "Hyderabad",
                "pickup_date": (date.today() + timedelta(days=4)).isoformat(),
                "goods_type": "general",
                "weight_kg": 2000.0,
            },
            headers=portal_headers,
        )
        assert create.status_code == 201, create.text
        load_id = create.json()["id"]

        detail = client.get(f"/api/v1/portal/loads/{load_id}", headers=portal_headers)
        assert detail.status_code == 200
        assert detail.json()["origin"] == "Chennai"
        assert detail.json()["client_name"] == "Timeline Co"

        history = client.get(f"/api/v1/portal/loads/{load_id}/history", headers=portal_headers)
        assert history.status_code == 200, history.text
        entries = history.json()
        assert len(entries) >= 1
        assert entries[0]["to_status"] == "draft"

    def test_view_pod_document_for_my_shipment(self, client, seed_superadmin, seed_tenant, seed_roles):
        sa_headers = _superadmin_auth(client, seed_superadmin)
        ta_headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.pod@example.com")

        client_id = _create_client(client, ta_headers, "POD Co")
        _create_portal_user(client, ta_headers, seed_roles, "pod.user@example.com", client_id)
        portal_headers = _login(client, "pod.user@example.com")

        load = _create_load_as_admin(client, ta_headers, client_id)

        # No documents yet
        empty = client.get(f"/api/v1/portal/loads/{load['id']}/documents", headers=portal_headers)
        assert empty.status_code == 200, empty.text
        assert empty.json()["total"] == 0

        # Admin attaches a POD
        add = client.post(
            f"/api/v1/loads/{load['id']}/documents",
            json={
                "entity_type": "load",
                "entity_id": load["id"],
                "document_type": "pod",
                "file_name": "pod.pdf",
                "file_url": "https://example.com/pod.pdf",
            },
            headers=ta_headers,
        )
        assert add.status_code == 201, add.text

        # Client can now see it
        listed = client.get(f"/api/v1/portal/loads/{load['id']}/documents", headers=portal_headers)
        assert listed.status_code == 200, listed.text
        assert listed.json()["total"] == 1
        doc = listed.json()["items"][0]
        assert doc["document_type"] == "pod"
        assert doc["file_url"] == "https://example.com/pod.pdf"

    def test_portal_requires_client_role(self, client, seed_superadmin, seed_tenant):
        sa_headers = _superadmin_auth(client, seed_superadmin)
        resp = client.get("/api/v1/portal/me", headers=sa_headers)
        assert resp.status_code == 403

    def test_portal_unlinked_user_returns_404(self, client, seed_superadmin, seed_tenant, seed_roles):
        sa_headers = _superadmin_auth(client, seed_superadmin)
        ta_headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.unlinked@example.com")

        # A Client-role user with no linked Client record
        _create_portal_user(client, ta_headers, seed_roles, "unlinked.client@example.com")

        portal_headers = _login(client, "unlinked.client@example.com")
        me = client.get("/api/v1/portal/me", headers=portal_headers)
        assert me.status_code == 404


class TestPortalLoadUpdate:
    def _booking(self, client, portal_headers, tenant_id, **overrides):
        payload = {
            "tenant_id": tenant_id,
            "origin": "Pune",
            "destination": "Nashik",
            "pickup_date": (date.today() + timedelta(days=3)).isoformat(),
            "goods_type": "general",
            "weight_kg": 1000.0,
            **overrides,
        }
        resp = client.post("/api/v1/portal/loads", json=payload, headers=portal_headers)
        assert resp.status_code == 201, resp.text
        return resp.json()

    def test_update_own_draft_load(self, client, seed_superadmin, seed_tenant, seed_roles):
        sa_headers = _superadmin_auth(client, seed_superadmin)
        ta_headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.update@example.com")
        client_id = _create_client(client, ta_headers, "Update Co")
        _create_portal_user(client, ta_headers, seed_roles, "update.user@example.com", client_id)
        portal_headers = _login(client, "update.user@example.com")

        load = self._booking(client, portal_headers, str(seed_tenant.id))

        resp = client.patch(
            f"/api/v1/portal/loads/{load['id']}",
            json={"origin": "Pune Hub", "weight_kg": 1500.0},
            headers=portal_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["origin"] == "Pune Hub"
        assert resp.json()["weight_kg"] == "1500.00"

    def test_cannot_update_other_clients_load(self, client, seed_superadmin, seed_tenant, seed_roles):
        sa_headers = _superadmin_auth(client, seed_superadmin)
        ta_headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.update2@example.com")

        client_a = _create_client(client, ta_headers, "Update Client A")
        client_b = _create_client(client, ta_headers, "Update Client B")
        _create_portal_user(client, ta_headers, seed_roles, "update.a@example.com", client_a)
        _create_portal_user(client, ta_headers, seed_roles, "update.b@example.com", client_b)

        headers_a = _login(client, "update.a@example.com")
        headers_b = _login(client, "update.b@example.com")
        load_b = self._booking(client, headers_b, str(seed_tenant.id))

        resp = client.patch(
            f"/api/v1/portal/loads/{load_b['id']}",
            json={"origin": "Hijacked"},
            headers=headers_a,
        )
        assert resp.status_code == 404

    def test_update_non_editable_load_rejected(self, client, seed_superadmin, seed_tenant, seed_roles):
        sa_headers = _superadmin_auth(client, seed_superadmin)
        ta_headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.update3@example.com")
        client_id = _create_client(client, ta_headers, "Update Co 3")
        _create_portal_user(client, ta_headers, seed_roles, "update3.user@example.com", client_id)
        portal_headers = _login(client, "update3.user@example.com")

        load = self._booking(client, portal_headers, str(seed_tenant.id))

        # Carrier confirms then cancels — CANCELLED is terminal, not editable
        for to_status in ("confirmed",):
            t = client.post(
                f"/api/v1/loads/{load['id']}/transition",
                json={"to_status": to_status},
                headers=ta_headers,
            )
            assert t.status_code == 200, t.text
        cancel = client.post(
            f"/api/v1/loads/{load['id']}/cancel",
            json={"reason": "Carrier cancelled this booking"},
            headers=ta_headers,
        )
        assert cancel.status_code == 200, cancel.text

        resp = client.patch(
            f"/api/v1/portal/loads/{load['id']}",
            json={"origin": "Too Late"},
            headers=portal_headers,
        )
        assert resp.status_code == 400


class TestPortalLoadCancel:
    def _booking(self, client, portal_headers, tenant_id, **overrides):
        payload = {
            "tenant_id": tenant_id,
            "origin": "Surat",
            "destination": "Vadodara",
            "pickup_date": (date.today() + timedelta(days=3)).isoformat(),
            "goods_type": "general",
            "weight_kg": 800.0,
            **overrides,
        }
        resp = client.post("/api/v1/portal/loads", json=payload, headers=portal_headers)
        assert resp.status_code == 201, resp.text
        return resp.json()

    def test_cancel_own_draft_load(self, client, seed_superadmin, seed_tenant, seed_roles):
        sa_headers = _superadmin_auth(client, seed_superadmin)
        ta_headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.cancel@example.com")
        client_id = _create_client(client, ta_headers, "Cancel Co")
        _create_portal_user(client, ta_headers, seed_roles, "cancel.user@example.com", client_id)
        portal_headers = _login(client, "cancel.user@example.com")

        load = self._booking(client, portal_headers, str(seed_tenant.id))

        resp = client.post(
            f"/api/v1/portal/loads/{load['id']}/cancel",
            json={"reason": "Plans changed"},
            headers=portal_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "cancelled"

        history = client.get(f"/api/v1/portal/loads/{load['id']}/history", headers=portal_headers)
        assert history.status_code == 200
        assert any(h["to_status"] == "cancelled" for h in history.json())

    def test_cancel_reason_too_short_rejected(self, client, seed_superadmin, seed_tenant, seed_roles):
        sa_headers = _superadmin_auth(client, seed_superadmin)
        ta_headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.cancel2@example.com")
        client_id = _create_client(client, ta_headers, "Cancel Co 2")
        _create_portal_user(client, ta_headers, seed_roles, "cancel2.user@example.com", client_id)
        portal_headers = _login(client, "cancel2.user@example.com")

        load = self._booking(client, portal_headers, str(seed_tenant.id))

        resp = client.post(
            f"/api/v1/portal/loads/{load['id']}/cancel",
            json={"reason": "no"},
            headers=portal_headers,
        )
        assert resp.status_code == 422

    def test_cannot_cancel_in_transit_load(self, client, seed_superadmin, seed_tenant, seed_roles):
        sa_headers = _superadmin_auth(client, seed_superadmin)
        ta_headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.cancel3@example.com")
        client_id = _create_client(client, ta_headers, "Cancel Co 3")
        _create_portal_user(client, ta_headers, seed_roles, "cancel3.user@example.com", client_id)
        portal_headers = _login(client, "cancel3.user@example.com")

        load = self._booking(client, portal_headers, str(seed_tenant.id))

        for to_status in ("confirmed", "allocated", "in_transit"):
            t = client.post(
                f"/api/v1/loads/{load['id']}/transition",
                json={"to_status": to_status},
                headers=ta_headers,
            )
            assert t.status_code == 200, t.text

        resp = client.post(
            f"/api/v1/portal/loads/{load['id']}/cancel",
            json={"reason": "Too late, but trying anyway"},
            headers=portal_headers,
        )
        assert resp.status_code == 403

    def test_cannot_cancel_other_clients_load(self, client, seed_superadmin, seed_tenant, seed_roles):
        sa_headers = _superadmin_auth(client, seed_superadmin)
        ta_headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.cancel4@example.com")

        client_a = _create_client(client, ta_headers, "Cancel Client A")
        client_b = _create_client(client, ta_headers, "Cancel Client B")
        _create_portal_user(client, ta_headers, seed_roles, "cancel.a@example.com", client_a)
        _create_portal_user(client, ta_headers, seed_roles, "cancel.b@example.com", client_b)

        headers_a = _login(client, "cancel.a@example.com")
        headers_b = _login(client, "cancel.b@example.com")
        load_b = self._booking(client, headers_b, str(seed_tenant.id))

        resp = client.post(
            f"/api/v1/portal/loads/{load_b['id']}/cancel",
            json={"reason": "Not my shipment to cancel"},
            headers=headers_a,
        )
        assert resp.status_code == 404


class TestPortalDocumentUpload:
    def _booking(self, client, portal_headers, tenant_id, **overrides):
        payload = {
            "tenant_id": tenant_id,
            "origin": "Lucknow",
            "destination": "Kanpur",
            "pickup_date": (date.today() + timedelta(days=3)).isoformat(),
            "goods_type": "general",
            "weight_kg": 600.0,
            **overrides,
        }
        resp = client.post("/api/v1/portal/loads", json=payload, headers=portal_headers)
        assert resp.status_code == 201, resp.text
        return resp.json()

    def test_upload_and_view_document(self, client, seed_superadmin, seed_tenant, seed_roles, tiny_png_bytes):
        sa_headers = _superadmin_auth(client, seed_superadmin)
        ta_headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.doc@example.com")
        client_id = _create_client(client, ta_headers, "Doc Co")
        _create_portal_user(client, ta_headers, seed_roles, "doc.user@example.com", client_id)
        portal_headers = _login(client, "doc.user@example.com")

        load = self._booking(client, portal_headers, str(seed_tenant.id))

        upload = client.post(
            f"/api/v1/portal/loads/{load['id']}/documents",
            files={"file": ("packing-list.png", tiny_png_bytes, "image/png")},
            headers=portal_headers,
        )
        assert upload.status_code == 201, upload.text
        doc = upload.json()
        assert doc["has_file"] is True
        assert doc["entity_type"] == "load"
        assert doc["entity_id"] == load["id"]

        listed = client.get(f"/api/v1/portal/loads/{load['id']}/documents", headers=portal_headers)
        assert listed.status_code == 200, listed.text
        assert listed.json()["total"] == 1
        assert listed.json()["items"][0]["has_file"] is True

        file_resp = client.get(
            f"/api/v1/portal/loads/{load['id']}/documents/{doc['id']}/file",
            headers=portal_headers,
        )
        assert file_resp.status_code == 200, file_resp.text
        assert file_resp.headers["content-type"] == "image/png"

    def test_upload_rejects_non_image(self, client, seed_superadmin, seed_tenant, seed_roles):
        sa_headers = _superadmin_auth(client, seed_superadmin)
        ta_headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.doc2@example.com")
        client_id = _create_client(client, ta_headers, "Doc Co 2")
        _create_portal_user(client, ta_headers, seed_roles, "doc2.user@example.com", client_id)
        portal_headers = _login(client, "doc2.user@example.com")

        load = self._booking(client, portal_headers, str(seed_tenant.id))

        upload = client.post(
            f"/api/v1/portal/loads/{load['id']}/documents",
            files={"file": ("notes.txt", b"not an image", "text/plain")},
            headers=portal_headers,
        )
        assert upload.status_code == 400

    def test_cannot_upload_to_other_clients_load(self, client, seed_superadmin, seed_tenant, seed_roles, tiny_png_bytes):
        sa_headers = _superadmin_auth(client, seed_superadmin)
        ta_headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.doc3@example.com")

        client_a = _create_client(client, ta_headers, "Doc Client A")
        client_b = _create_client(client, ta_headers, "Doc Client B")
        _create_portal_user(client, ta_headers, seed_roles, "doc.a@example.com", client_a)
        _create_portal_user(client, ta_headers, seed_roles, "doc.b@example.com", client_b)

        headers_a = _login(client, "doc.a@example.com")
        headers_b = _login(client, "doc.b@example.com")
        load_b = self._booking(client, headers_b, str(seed_tenant.id))

        upload = client.post(
            f"/api/v1/portal/loads/{load_b['id']}/documents",
            files={"file": ("sneaky.png", tiny_png_bytes, "image/png")},
            headers=headers_a,
        )
        assert upload.status_code == 404

    def test_cannot_fetch_file_for_document_of_another_load(self, client, seed_superadmin, seed_tenant, seed_roles, tiny_png_bytes):
        sa_headers = _superadmin_auth(client, seed_superadmin)
        ta_headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.doc4@example.com")
        client_id = _create_client(client, ta_headers, "Doc Co 4")
        _create_portal_user(client, ta_headers, seed_roles, "doc4.user@example.com", client_id)
        portal_headers = _login(client, "doc4.user@example.com")

        load_1 = self._booking(client, portal_headers, str(seed_tenant.id))
        load_2 = self._booking(client, portal_headers, str(seed_tenant.id), origin="Agra")

        upload = client.post(
            f"/api/v1/portal/loads/{load_1['id']}/documents",
            files={"file": ("packing-list.png", tiny_png_bytes, "image/png")},
            headers=portal_headers,
        )
        assert upload.status_code == 201, upload.text
        doc_id = upload.json()["id"]

        resp = client.get(
            f"/api/v1/portal/loads/{load_2['id']}/documents/{doc_id}/file",
            headers=portal_headers,
        )
        assert resp.status_code == 404


class TestPortalMultiTenant:
    """A shipper with relationships (linked Client records) in TWO tenants sees
    an aggregated portal: /portal/me lists both carriers, /portal/loads merges
    shipments from both, and bookings target a chosen carrier."""

    def _create_second_tenant(self, client, sa_headers, name, admin_email):
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

    def _setup_multi_carrier_shipper(self, client, seed_superadmin, seed_tenant, seed_roles,
                                      shipper_email="multi.shipper@example.com"):
        """Build a shipper linked to a Client record in TWO tenants ("Test Logistics"
        i.e. seed_tenant, and a fresh "Carrier B"). Returns a dict with auth headers
        and IDs needed by callers."""
        sa_headers = _superadmin_auth(client, seed_superadmin)

        # Tenant A (seed_tenant) — TenantAdmin, a client, and the shipper's portal login
        ta_headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.multi.a@example.com")
        client_a = _create_client(client, ta_headers, "Carrier A's View of Shipper")
        _create_portal_user(client, ta_headers, seed_roles, shipper_email, client_a)

        # Tenant B — a second tenant with its own TenantAdmin and client record,
        # linked to the SAME shipper login by email
        tenant_b = self._create_second_tenant(client, sa_headers, "Carrier B", "ta.multi.b@example.com")
        tb_headers = _login(client, "ta.multi.b@example.com", password="TestPass123!")
        client_b = _create_client(client, tb_headers, "Carrier B's View of Shipper")

        link = client.post(
            f"/api/v1/clients/{client_b}/link-portal-account",
            json={"email": shipper_email},
            headers=tb_headers,
        )
        assert link.status_code == 200, link.text

        return {
            "sa_headers": sa_headers,
            "ta_headers": ta_headers,
            "tb_headers": tb_headers,
            "client_a": client_a,
            "client_b": client_b,
            "tenant_b": tenant_b,
            "portal_headers": _login(client, shipper_email),
        }

    def test_multi_carrier_portal(self, client, seed_superadmin, seed_tenant, seed_roles):
        ctx = self._setup_multi_carrier_shipper(client, seed_superadmin, seed_tenant, seed_roles)
        ta_headers, tb_headers = ctx["ta_headers"], ctx["tb_headers"]
        client_a, client_b, tenant_b = ctx["client_a"], ctx["client_b"], ctx["tenant_b"]
        portal_headers = ctx["portal_headers"]

        load_a = _create_load_as_admin(client, ta_headers, client_a, freight=10000.0)
        load_b = _create_load_as_admin(client, tb_headers, client_b, freight=20000.0)

        # /portal/me lists both carriers
        me = client.get("/api/v1/portal/me", headers=portal_headers)
        assert me.status_code == 200, me.text
        carriers = me.json()["carriers"]
        assert len(carriers) == 2
        tenant_ids = {c["tenant_id"] for c in carriers}
        assert str(seed_tenant.id) in tenant_ids
        assert tenant_b["id"] in tenant_ids
        names_by_tenant = {c["tenant_id"]: c["tenant_name"] for c in carriers}
        assert names_by_tenant[tenant_b["id"]] == "Carrier B"

        # /portal/loads aggregates shipments from both carriers
        loads = client.get("/api/v1/portal/loads", headers=portal_headers)
        assert loads.status_code == 200, loads.text
        items = loads.json()["items"]
        ids_to_carrier = {i["id"]: i["carrier_name"] for i in items}
        assert load_a["id"] in ids_to_carrier
        assert load_b["id"] in ids_to_carrier
        assert ids_to_carrier[load_b["id"]] == "Carrier B"

        # Loads in either tenant are individually accessible
        detail_a = client.get(f"/api/v1/portal/loads/{load_a['id']}", headers=portal_headers)
        assert detail_a.status_code == 200
        detail_b = client.get(f"/api/v1/portal/loads/{load_b['id']}", headers=portal_headers)
        assert detail_b.status_code == 200

        # Booking with tenant_id=B creates the load under Carrier B for client_b
        create = client.post(
            "/api/v1/portal/loads",
            json={
                "tenant_id": tenant_b["id"],
                "origin": "Kolkata",
                "destination": "Patna",
                "pickup_date": (date.today() + timedelta(days=5)).isoformat(),
                "goods_type": "general",
                "weight_kg": 500.0,
            },
            headers=portal_headers,
        )
        assert create.status_code == 201, create.text
        new_load = create.json()
        assert new_load["tenant_id"] == tenant_b["id"]
        assert new_load["client_id"] == client_b

        # Booking against an unlinked tenant is forbidden
        bad = client.post(
            "/api/v1/portal/loads",
            json={
                "tenant_id": "00000000-0000-0000-0000-000000000000",
                "origin": "Kolkata",
                "destination": "Patna",
                "pickup_date": (date.today() + timedelta(days=5)).isoformat(),
                "goods_type": "general",
                "weight_kg": 500.0,
            },
            headers=portal_headers,
        )
        assert bad.status_code == 403

    def test_multi_carrier_invoices(self, client, seed_superadmin, seed_tenant, seed_roles):
        ctx = self._setup_multi_carrier_shipper(client, seed_superadmin, seed_tenant, seed_roles,
                                                  shipper_email="invoices.shipper@example.com")
        ta_headers, tb_headers = ctx["ta_headers"], ctx["tb_headers"]
        client_a, client_b, tenant_b = ctx["client_a"], ctx["client_b"], ctx["tenant_b"]
        portal_headers = ctx["portal_headers"]

        inv_a = client.post(
            "/api/v1/invoices",
            json={
                "client_id": client_a,
                "issued_date": date.today().isoformat(),
                "due_date": (date.today() + timedelta(days=15)).isoformat(),
                "subtotal": 10000.0,
                "tax_rate": 18.0,
            },
            headers=ta_headers,
        )
        assert inv_a.status_code == 201, inv_a.text
        inv_a = inv_a.json()

        inv_b = client.post(
            "/api/v1/invoices",
            json={
                "client_id": client_b,
                "issued_date": date.today().isoformat(),
                "subtotal": 5000.0,
                "tax_rate": 0,
            },
            headers=tb_headers,
        )
        assert inv_b.status_code == 201, inv_b.text
        inv_b = inv_b.json()

        # /portal/invoices aggregates invoices from both carriers
        listed = client.get("/api/v1/portal/invoices", headers=portal_headers)
        assert listed.status_code == 200, listed.text
        items = listed.json()["items"]
        ids_to_carrier = {i["id"]: i["carrier_name"] for i in items}
        assert inv_a["id"] in ids_to_carrier
        assert inv_b["id"] in ids_to_carrier
        assert ids_to_carrier[inv_a["id"]] == "Test Logistics"
        assert ids_to_carrier[inv_b["id"]] == "Carrier B"

        # Status filter narrows results (both invoices are DRAFT)
        filtered = client.get("/api/v1/portal/invoices?status=draft", headers=portal_headers)
        assert filtered.status_code == 200, filtered.text
        assert {i["id"] for i in filtered.json()["items"]} >= {inv_a["id"], inv_b["id"]}

        sent_only = client.get("/api/v1/portal/invoices?status=sent", headers=portal_headers)
        assert sent_only.status_code == 200, sent_only.text
        assert {i["id"] for i in sent_only.json()["items"]}.isdisjoint({inv_a["id"], inv_b["id"]})

        # PDF download works for invoices in either tenant
        pdf_a = client.get(f"/api/v1/portal/invoices/{inv_a['id']}/pdf", headers=portal_headers)
        assert pdf_a.status_code == 200, pdf_a.text
        assert pdf_a.headers["content-type"] == "application/pdf"

        pdf_b = client.get(f"/api/v1/portal/invoices/{inv_b['id']}/pdf", headers=portal_headers)
        assert pdf_b.status_code == 200, pdf_b.text
        assert pdf_b.headers["content-type"] == "application/pdf"

        # An invoice belonging to neither linked client is not found
        missing = client.get(
            "/api/v1/portal/invoices/00000000-0000-0000-0000-000000000000/pdf",
            headers=portal_headers,
        )
        assert missing.status_code == 404
