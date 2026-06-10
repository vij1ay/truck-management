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
