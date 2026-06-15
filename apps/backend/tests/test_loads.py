"""Tests for Loads API endpoints - Phase 3."""
import pytest
from datetime import date, timedelta


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_token(client, seed_superadmin):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "TestPassword123!"}
    )
    return resp.json()["access_token"]


def _auth(client, seed_superadmin):
    return {"Authorization": f"Bearer {_get_token(client, seed_superadmin)}"}


def _create_client(client, headers, name="Test Shipper"):
    resp = client.post(
        "/api/v1/clients/",
        json={
            "company_name": name,
            "phone": "9876543210",
            "client_type": "company",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _load_payload(client_id: str, days_ahead: int = 2) -> dict:
    """Return a minimal valid load creation payload."""
    return {
        "client_id": client_id,
        "origin": "Mumbai",
        "destination": "Pune",
        "pickup_date": (date.today() + timedelta(days=days_ahead)).isoformat(),
        "goods_type": "general",
        "weight_kg": 5000.0,
        "freight_amount": 15000.0,
        "advance_amount": 5000.0,
    }


def _create_tenant_admin(client, superadmin_headers, seed_roles, seed_tenant, email):
    """SuperAdmin can only assign the TenantAdmin role — bootstrap one to
    create Driver-role users (mirrors `tests/test_portal.py`)."""
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

    login = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass123"})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _create_truck(client, headers, reg="DLV01AA0001"):
    resp = client.post(
        "/api/v1/trucks/",
        json={
            "registration_no": reg,
            "truck_type": "flatbed",
            "ownership_type": "owned",
            "capacity_tons": 10.0,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _create_driver_user(client, headers, seed_roles, email, license_no):
    """Create a Driver-role login + linked Driver record. Returns
    (driver_headers, driver_id)."""
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
            "phone": "9000000099",
            "license_no": license_no,
            "license_class": "hmv",
            "license_expiry": (date.today() + timedelta(days=365)).isoformat(),
            "user_id": user_id,
        },
        headers=headers,
    )
    assert driver_resp.status_code == 201, driver_resp.text
    driver_id = driver_resp.json()["id"]

    login = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass123"})
    assert login.status_code == 200, login.text
    driver_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    return driver_headers, driver_id


def _create_allocated_load(client, headers, client_id, truck_id, driver_id, days_ahead=2):
    """Create a load, confirm it, and allocate the given truck/driver."""
    load_id = client.post("/api/v1/loads/", json=_load_payload(client_id, days_ahead), headers=headers).json()["id"]
    confirm = client.post(f"/api/v1/loads/{load_id}/transition", json={"to_status": "confirmed"}, headers=headers)
    assert confirm.status_code == 200, confirm.text
    alloc = client.post(
        f"/api/v1/loads/{load_id}/allocate",
        json={"truck_id": truck_id, "driver_id": driver_id},
        headers=headers,
    )
    assert alloc.status_code == 200, alloc.text
    return load_id


# ── Test class ─────────────────────────────────────────────────────────────────

class TestLoadEndpoints:

    # ── Create ────────────────────────────────────────────────────────────────

    def test_create_load_success(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        resp = client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["status"] == "draft"
        assert data["load_no"].startswith("LD-")
        assert data["origin"] == "Mumbai"
        assert data["destination"] == "Pune"
        assert data["balance_amount"] == 10000.0
        assert data["is_editable"] is True
        assert data["is_deletable"] is True

    def test_create_load_missing_required_fields(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        resp = client.post("/api/v1/loads/", json={"origin": "Mumbai"}, headers=headers)
        assert resp.status_code == 422

    def test_create_load_past_pickup_date(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        payload = _load_payload(cid)
        payload["pickup_date"] = (date.today() - timedelta(days=1)).isoformat()
        resp = client.post("/api/v1/loads/", json=payload, headers=headers)
        assert resp.status_code == 422

    def test_create_load_advance_exceeds_freight(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        payload = _load_payload(cid)
        payload["advance_amount"] = 20000.0  # > freight_amount 15000
        resp = client.post("/api/v1/loads/", json=payload, headers=headers)
        assert resp.status_code == 422

    def test_duplicate_booking_rejected(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        payload = _load_payload(cid)
        r1 = client.post("/api/v1/loads/", json=payload, headers=headers)
        assert r1.status_code == 201
        r2 = client.post("/api/v1/loads/", json=payload, headers=headers)
        assert r2.status_code == 409

    def test_load_no_sequence_increments(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        c1 = _create_client(client, headers, "Shipper Alpha")
        c2 = _create_client(client, headers, "Shipper Beta")
        payload_a = _load_payload(c1, days_ahead=3)
        payload_b = _load_payload(c2, days_ahead=4)
        r1 = client.post("/api/v1/loads/", json=payload_a, headers=headers)
        r2 = client.post("/api/v1/loads/", json=payload_b, headers=headers)
        assert r1.status_code == 201
        assert r2.status_code == 201
        seq1 = r1.json()["load_seq_no"]
        seq2 = r2.json()["load_seq_no"]
        assert seq2 == seq1 + 1

    # ── List ─────────────────────────────────────────────────────────────────

    def test_list_loads_empty(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        resp = client.get("/api/v1/loads/", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_loads_with_data(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers)
        resp = client.get("/api/v1/loads/", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_list_loads_filter_by_status(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers)
        resp = client.get("/api/v1/loads/?status=draft", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    # ── Get ───────────────────────────────────────────────────────────────────

    def test_get_load_by_id(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        create = client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers)
        load_id = create.json()["id"]
        resp = client.get(f"/api/v1/loads/{load_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == load_id

    def test_get_nonexistent_load(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        resp = client.get(
            "/api/v1/loads/00000000-0000-0000-0000-000000000000",
            headers=headers
        )
        assert resp.status_code == 404

    # ── Update ────────────────────────────────────────────────────────────────

    def test_update_load_in_draft(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        create = client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers)
        load_id = create.json()["id"]
        resp = client.patch(
            f"/api/v1/loads/{load_id}",
            json={"notes": "Handle with care"},
            headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["notes"] == "Handle with care"

    def test_update_load_in_delivered_rejected(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        create = client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers)
        load_id = create.json()["id"]
        # Walk through to DELIVERED
        for s in ["confirmed", "allocated", "in_transit", "delivered"]:
            client.post(
                f"/api/v1/loads/{load_id}/transition",
                json={"to_status": s},
                headers=headers
            )
        resp = client.patch(
            f"/api/v1/loads/{load_id}",
            json={"notes": "Should fail"},
            headers=headers
        )
        assert resp.status_code == 400

    # ── Status transitions ────────────────────────────────────────────────────

    def test_transition_draft_to_confirmed(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        create = client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers)
        load_id = create.json()["id"]
        resp = client.post(
            f"/api/v1/loads/{load_id}/transition",
            json={"to_status": "confirmed", "remarks": "Booking confirmed"},
            headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "confirmed"
        assert resp.json()["is_editable"] is True

    def test_invalid_transition_draft_to_allocated(self, client, seed_superadmin):
        """DRAFT → ALLOCATED is not allowed (must go through CONFIRMED first)."""
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        create = client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers)
        load_id = create.json()["id"]
        resp = client.post(
            f"/api/v1/loads/{load_id}/transition",
            json={"to_status": "allocated"},
            headers=headers
        )
        assert resp.status_code == 400

    def test_full_lifecycle_to_delivered(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        create = client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers)
        load_id = create.json()["id"]

        transitions = [
            ("confirmed", 200),
            ("allocated", 200),
            ("in_transit", 200),
            ("delivered", 200),
        ]
        for status, expected_code in transitions:
            r = client.post(
                f"/api/v1/loads/{load_id}/transition",
                json={"to_status": status},
                headers=headers
            )
            assert r.status_code == expected_code, f"Failed on {status}: {r.text}"
            assert r.json()["status"] == status

        # DELIVERED is terminal — cannot transition further
        r = client.post(
            f"/api/v1/loads/{load_id}/transition",
            json={"to_status": "cancelled"},
            headers=headers
        )
        assert r.status_code == 400

    def test_cancel_draft_load(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        create = client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers)
        load_id = create.json()["id"]
        resp = client.post(
            f"/api/v1/loads/{load_id}/cancel",
            json={"reason": "Client withdrew the booking"},
            headers=headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "cancelled"
        assert data["cancellation_reason"] == "Client withdrew the booking"
        assert data["cancelled_at"] is not None

    def test_cancel_reason_too_short(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        create = client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers)
        load_id = create.json()["id"]
        resp = client.post(
            f"/api/v1/loads/{load_id}/cancel",
            json={"reason": "No"},   # < 5 chars
            headers=headers
        )
        assert resp.status_code == 422

    # ── Delete ────────────────────────────────────────────────────────────────

    def test_delete_draft_load(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        create = client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers)
        load_id = create.json()["id"]
        del_resp = client.delete(f"/api/v1/loads/{load_id}", headers=headers)
        assert del_resp.status_code == 204
        # Should not appear in list
        list_resp = client.get("/api/v1/loads/", headers=headers)
        assert list_resp.json()["total"] == 0

    def test_delete_in_transit_load_rejected(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        create = client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers)
        load_id = create.json()["id"]
        for s in ["confirmed", "allocated", "in_transit"]:
            client.post(
                f"/api/v1/loads/{load_id}/transition",
                json={"to_status": s},
                headers=headers
            )
        resp = client.delete(f"/api/v1/loads/{load_id}", headers=headers)
        assert resp.status_code == 400

    # ── History ───────────────────────────────────────────────────────────────

    def test_load_history_on_creation(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        create = client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers)
        load_id = create.json()["id"]
        resp = client.get(f"/api/v1/loads/{load_id}/history", headers=headers)
        assert resp.status_code == 200
        history = resp.json()
        assert len(history) == 1
        assert history[0]["from_status"] is None
        assert history[0]["to_status"] == "draft"

    def test_load_history_grows_with_transitions(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        create = client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers)
        load_id = create.json()["id"]
        for s in ["confirmed", "allocated"]:
            client.post(
                f"/api/v1/loads/{load_id}/transition",
                json={"to_status": s},
                headers=headers
            )
        resp = client.get(f"/api/v1/loads/{load_id}/history", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 3  # creation + 2 transitions


class TestLoadDocuments:
    def test_add_pod_document_to_load(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        load_id = client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers).json()["id"]

        doc = {
            "entity_type": "load",
            "entity_id": load_id,
            "document_type": "pod",
            "file_name": "pod-signed.pdf",
            "file_url": "https://example.com/pods/pod-signed.pdf",
        }
        resp = client.post(f"/api/v1/loads/{load_id}/documents", json=doc, headers=headers)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["document_type"] == "pod"
        assert data["entity_type"] == "load"
        assert data["entity_id"] == load_id
        assert data["file_url"] == "https://example.com/pods/pod-signed.pdf"

    def test_list_load_documents(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        load_id = client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers).json()["id"]

        client.post(
            f"/api/v1/loads/{load_id}/documents",
            json={
                "entity_type": "load",
                "entity_id": load_id,
                "document_type": "pod",
                "file_name": "pod.pdf",
                "file_url": "https://example.com/pod.pdf",
            },
            headers=headers,
        )

        resp = client.get(f"/api/v1/loads/{load_id}/documents", headers=headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["total"] == 1
        assert resp.json()["items"][0]["document_type"] == "pod"

    def test_add_document_entity_mismatch_rejected(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        load_id = client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers).json()["id"]
        other_load_id = client.post("/api/v1/loads/", json=_load_payload(cid, days_ahead=3), headers=headers).json()["id"]

        # entity_id doesn't match the load in the URL
        resp = client.post(
            f"/api/v1/loads/{load_id}/documents",
            json={
                "entity_type": "load",
                "entity_id": other_load_id,
                "document_type": "pod",
                "file_name": "pod.pdf",
            },
            headers=headers,
        )
        assert resp.status_code == 400


class TestLoadTenantFilter:
    def test_superadmin_filters_loads_by_tenant(self, client, seed_superadmin, seed_tenant, second_tenant):
        su_headers = _auth(client, seed_superadmin)

        # A load in the SuperAdmin's own (seed) tenant
        own_client_id = _create_client(client, su_headers, "Tenant A Shipper")
        own_load = client.post("/api/v1/loads/", json=_load_payload(own_client_id), headers=su_headers)
        assert own_load.status_code == 201, own_load.text

        # A load in the second tenant, created by its own TenantAdmin
        other_headers = second_tenant["headers"]
        other_tenant_id = second_tenant["tenant_id"]
        other_client_id = _create_client(client, other_headers, "Tenant B Shipper")
        other_load = client.post(
            "/api/v1/loads/", json=_load_payload(other_client_id, days_ahead=3), headers=other_headers
        )
        assert other_load.status_code == 201, other_load.text

        # Unfiltered list (SuperAdmin) includes loads from both tenants
        unfiltered = client.get("/api/v1/loads/", headers=su_headers)
        assert unfiltered.status_code == 200, unfiltered.text
        tenant_ids = {l["tenant_id"] for l in unfiltered.json()["items"]}
        assert str(seed_tenant.id) in tenant_ids
        assert other_tenant_id in tenant_ids

        # Filtering by the second tenant only returns its loads
        filtered = client.get("/api/v1/loads/", params={"tenant_id": other_tenant_id}, headers=su_headers)
        assert filtered.status_code == 200, filtered.text
        filtered_data = filtered.json()
        assert filtered_data["total"] >= 1
        assert all(l["tenant_id"] == other_tenant_id for l in filtered_data["items"])

        # TenantAdmin of the second tenant still only sees their own loads, regardless of tenant_id
        scoped = client.get("/api/v1/loads/", params={"tenant_id": str(seed_tenant.id)}, headers=other_headers)
        assert scoped.status_code == 200, scoped.text
        assert all(l["tenant_id"] == other_tenant_id for l in scoped.json()["items"])


class TestLoadClientName:
    def test_client_name_present_on_load_response(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers, "Client Name Co")
        load_id = client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers).json()["id"]

        resp = client.get(f"/api/v1/loads/{load_id}", headers=headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["client_name"] == "Client Name Co"


class TestLoadDeliver:
    def test_driver_starts_and_delivers_own_load(self, client, seed_superadmin, seed_roles, seed_tenant):
        sa_headers = _auth(client, seed_superadmin)
        headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.deliver1@example.com")
        cid = _create_client(client, headers, "Deliver Co")
        truck_id = _create_truck(client, headers, "DLV01AA0001")
        driver_headers, driver_id = _create_driver_user(
            client, headers, seed_roles, "deliver.driver@example.com", "DLV1111111"
        )
        load_id = _create_allocated_load(client, headers, cid, truck_id, driver_id)

        start = client.post(f"/api/v1/loads/{load_id}/start-trip", headers=driver_headers)
        assert start.status_code == 200, start.text
        assert start.json()["status"] == "in_transit"

        deliver = client.post(f"/api/v1/loads/{load_id}/deliver", headers=driver_headers)
        assert deliver.status_code == 200, deliver.text
        data = deliver.json()
        assert data["status"] == "delivered"
        assert data["actual_delivery_date"] is not None

        # Auto-created draft invoice
        invoices = client.get("/api/v1/invoices", params={"client_id": cid}, headers=headers)
        assert invoices.status_code == 200, invoices.text
        assert any(i["load_no"] == data["load_no"] for i in invoices.json()["items"])

    def test_driver_cannot_deliver_unassigned_load(self, client, seed_superadmin, seed_roles, seed_tenant):
        sa_headers = _auth(client, seed_superadmin)
        headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.deliver2@example.com")
        cid = _create_client(client, headers, "Deliver Co 2")
        truck_id = _create_truck(client, headers, "DLV02AA0002")
        driver_headers, driver_id = _create_driver_user(
            client, headers, seed_roles, "deliver.driver2@example.com", "DLV2222222"
        )
        load_id = _create_allocated_load(client, headers, cid, truck_id, driver_id)
        client.post(f"/api/v1/loads/{load_id}/start-trip", headers=driver_headers)

        # A second driver, not allocated to this load
        other_headers, _ = _create_driver_user(
            client, headers, seed_roles, "deliver.driver3@example.com", "DLV3333333"
        )
        resp = client.post(f"/api/v1/loads/{load_id}/deliver", headers=other_headers)
        assert resp.status_code == 403

    def test_deliver_draft_load_rejected(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers, "Deliver Co 3")
        load_id = client.post("/api/v1/loads/", json=_load_payload(cid), headers=headers).json()["id"]

        resp = client.post(f"/api/v1/loads/{load_id}/deliver", headers=headers)
        assert resp.status_code == 400


class TestLoadPodUpload:
    def test_driver_uploads_pod_to_own_load(self, client, seed_superadmin, seed_roles, seed_tenant, tiny_png_bytes):
        sa_headers = _auth(client, seed_superadmin)
        headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.pod1@example.com")
        cid = _create_client(client, headers, "POD Upload Co")
        truck_id = _create_truck(client, headers, "POD01AA0001")
        driver_headers, driver_id = _create_driver_user(
            client, headers, seed_roles, "pod.driver@example.com", "POD1111111"
        )
        load_id = _create_allocated_load(client, headers, cid, truck_id, driver_id)
        client.post(f"/api/v1/loads/{load_id}/start-trip", headers=driver_headers)

        upload = client.post(
            f"/api/v1/loads/{load_id}/documents/pod",
            files={"file": ("pod.png", tiny_png_bytes, "image/png")},
            headers=driver_headers,
        )
        assert upload.status_code == 201, upload.text
        doc = upload.json()
        assert doc["has_file"] is True
        assert doc["document_type"] == "pod"

        file_resp = client.get(
            f"/api/v1/loads/{load_id}/documents/{doc['id']}/file",
            headers=driver_headers,
        )
        assert file_resp.status_code == 200, file_resp.text
        assert file_resp.headers["content-type"] == "image/png"

    def test_driver_cannot_upload_pod_to_unassigned_load(self, client, seed_superadmin, seed_roles, seed_tenant, tiny_png_bytes):
        sa_headers = _auth(client, seed_superadmin)
        headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.pod2@example.com")
        cid = _create_client(client, headers, "POD Upload Co 2")
        truck_id = _create_truck(client, headers, "POD02AA0002")
        driver_headers, driver_id = _create_driver_user(
            client, headers, seed_roles, "pod.driver2@example.com", "POD2222222"
        )
        load_id = _create_allocated_load(client, headers, cid, truck_id, driver_id)

        other_headers, _ = _create_driver_user(
            client, headers, seed_roles, "pod.driver3@example.com", "POD3333333"
        )
        resp = client.post(
            f"/api/v1/loads/{load_id}/documents/pod",
            files={"file": ("pod.png", tiny_png_bytes, "image/png")},
            headers=other_headers,
        )
        assert resp.status_code == 403

    def test_pod_upload_rejects_non_image(self, client, seed_superadmin, seed_roles, seed_tenant):
        sa_headers = _auth(client, seed_superadmin)
        headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.pod3@example.com")
        cid = _create_client(client, headers, "POD Upload Co 3")
        truck_id = _create_truck(client, headers, "POD03AA0003")
        driver_headers, driver_id = _create_driver_user(
            client, headers, seed_roles, "pod.driver4@example.com", "POD4444444"
        )
        load_id = _create_allocated_load(client, headers, cid, truck_id, driver_id)

        resp = client.post(
            f"/api/v1/loads/{load_id}/documents/pod",
            files={"file": ("notes.txt", b"not an image", "text/plain")},
            headers=driver_headers,
        )
        assert resp.status_code == 400


class TestLoadCheckpoint:
    def test_driver_adds_checkpoint(self, client, seed_superadmin, seed_roles, seed_tenant):
        sa_headers = _auth(client, seed_superadmin)
        headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.checkpoint1@example.com")
        cid = _create_client(client, headers, "Checkpoint Co")
        truck_id = _create_truck(client, headers, "CHK01AA0001")
        driver_headers, driver_id = _create_driver_user(
            client, headers, seed_roles, "checkpoint.driver@example.com", "CHK1111111"
        )
        load_id = _create_allocated_load(client, headers, cid, truck_id, driver_id)
        client.post(f"/api/v1/loads/{load_id}/start-trip", headers=driver_headers)

        resp = client.post(
            f"/api/v1/loads/{load_id}/checkpoints",
            json={"label": "Reached Pickup"},
            headers=driver_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "in_transit"  # unchanged

        history = client.get(f"/api/v1/loads/{load_id}/history", headers=driver_headers)
        assert history.status_code == 200, history.text
        entries = history.json()
        checkpoint = next(h for h in entries if h["remarks"] == "Reached Pickup")
        assert checkpoint["from_status"] == checkpoint["to_status"] == "in_transit"

    def test_checkpoint_label_too_short_rejected(self, client, seed_superadmin, seed_roles, seed_tenant):
        sa_headers = _auth(client, seed_superadmin)
        headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.checkpoint2@example.com")
        cid = _create_client(client, headers, "Checkpoint Co 2")
        truck_id = _create_truck(client, headers, "CHK02AA0002")
        driver_headers, driver_id = _create_driver_user(
            client, headers, seed_roles, "checkpoint.driver2@example.com", "CHK2222222"
        )
        load_id = _create_allocated_load(client, headers, cid, truck_id, driver_id)
        client.post(f"/api/v1/loads/{load_id}/start-trip", headers=driver_headers)

        resp = client.post(
            f"/api/v1/loads/{load_id}/checkpoints",
            json={"label": "X"},
            headers=driver_headers,
        )
        assert resp.status_code == 422

    def test_driver_cannot_add_checkpoint_to_unassigned_load(self, client, seed_superadmin, seed_roles, seed_tenant):
        sa_headers = _auth(client, seed_superadmin)
        headers = _create_tenant_admin(client, sa_headers, seed_roles, seed_tenant, "ta.checkpoint3@example.com")
        cid = _create_client(client, headers, "Checkpoint Co 3")
        truck_id = _create_truck(client, headers, "CHK03AA0003")
        driver_headers, driver_id = _create_driver_user(
            client, headers, seed_roles, "checkpoint.driver3@example.com", "CHK3333333"
        )
        load_id = _create_allocated_load(client, headers, cid, truck_id, driver_id)
        client.post(f"/api/v1/loads/{load_id}/start-trip", headers=driver_headers)

        other_headers, _ = _create_driver_user(
            client, headers, seed_roles, "checkpoint.driver4@example.com", "CHK4444444"
        )
        resp = client.post(
            f"/api/v1/loads/{load_id}/checkpoints",
            json={"label": "Reached Pickup"},
            headers=other_headers,
        )
        assert resp.status_code == 403
