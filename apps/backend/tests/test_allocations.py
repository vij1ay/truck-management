"""Tests for Allocation Engine API - Phase 4."""
from datetime import date, timedelta
import pytest


# ── Helpers ────────────────────────────────────────────────────────────────────

def _auth(client, seed_superadmin):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "TestPassword123!"}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _future(days=3):
    return (date.today() + timedelta(days=days)).isoformat()


def _create_truck(client, headers, reg="TN01AA0001", capacity=25.0):
    r = client.post("/api/v1/trucks/", json={
        "registration_no": reg,
        "truck_type": "flatbed",
        "ownership_type": "owned",
        "make": "Tata",
        "model": "Prima",
        "capacity_tons": capacity,
    }, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _create_driver(client, headers, license_no="DL123456", phone="9000000001"):
    r = client.post("/api/v1/drivers/", json={
        "first_name": "Raju",
        "last_name": "Kumar",
        "phone": phone,
        "license_no": license_no,
        "license_class": "hmv",
        "license_expiry": _future(365),
    }, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _create_client_entity(client, headers, name="Test Shipper"):
    r = client.post("/api/v1/clients/", json={
        "company_name": name,
        "phone": "9876543210",
        "client_type": "company",
    }, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _create_confirmed_load(client, headers, client_id, days_pickup=3, days_delivery=5):
    payload = {
        "client_id": client_id,
        "origin": "Mumbai",
        "destination": "Delhi",
        "pickup_date": _future(days_pickup),
        "expected_delivery_date": _future(days_delivery),
        "goods_type": "general",
        "weight_kg": 10000.0,
        "freight_amount": 20000.0,
    }
    r = client.post("/api/v1/loads/", json=payload, headers=headers)
    assert r.status_code == 201, r.text
    load_id = r.json()["id"]

    # Confirm it
    t = client.post(f"/api/v1/loads/{load_id}/transition",
                    json={"to_status": "confirmed"}, headers=headers)
    assert t.status_code == 200, t.text
    return load_id


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestAllocationEndpoints:

    # ── Allocate ─────────────────────────────────────────────────────────────

    def test_allocate_success(self, client, seed_superadmin):
        h = _auth(client, seed_superadmin)
        cid = _create_client_entity(client, h)
        tid = _create_truck(client, h)
        did = _create_driver(client, h)
        load_id = _create_confirmed_load(client, h, cid)

        r = client.post(f"/api/v1/loads/{load_id}/allocate",
                        json={"truck_id": tid, "driver_id": did},
                        headers=h)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "allocated"
        assert data["allocated_truck_id"] == tid
        assert data["allocated_driver_id"] == did
        assert data["allocated_at"] is not None

    def test_allocate_to_draft_load_rejected(self, client, seed_superadmin):
        h = _auth(client, seed_superadmin)
        cid = _create_client_entity(client, h)
        tid = _create_truck(client, h)
        did = _create_driver(client, h)

        payload = {
            "client_id": cid,
            "origin": "Mumbai",
            "destination": "Pune",
            "pickup_date": _future(3),
            "goods_type": "general",
        }
        r = client.post("/api/v1/loads/", json=payload, headers=h)
        load_id = r.json()["id"]

        r2 = client.post(f"/api/v1/loads/{load_id}/allocate",
                         json={"truck_id": tid, "driver_id": did},
                         headers=h)
        assert r2.status_code == 400

    def test_allocate_nonexistent_truck_rejected(self, client, seed_superadmin):
        h = _auth(client, seed_superadmin)
        cid = _create_client_entity(client, h)
        did = _create_driver(client, h)
        load_id = _create_confirmed_load(client, h, cid)

        r = client.post(f"/api/v1/loads/{load_id}/allocate",
                        json={"truck_id": "00000000-0000-0000-0000-000000000000",
                              "driver_id": did},
                        headers=h)
        assert r.status_code == 404

    def test_allocate_driver_with_expired_license_rejected(self, client, seed_superadmin):
        """Driver with already-expired license cannot be allocated."""
        h = _auth(client, seed_superadmin)
        cid = _create_client_entity(client, h)
        tid = _create_truck(client, h)
        load_id = _create_confirmed_load(client, h, cid)

        # Create driver directly with a past expiry date
        r = client.post("/api/v1/drivers/", json={
            "first_name": "Expired",
            "last_name": "Driver",
            "phone": "9000000099",
            "license_no": "EXP-DIRECT-001",
            "license_class": "hmv",
            "license_expiry": "2020-01-01",
        }, headers=h)
        if r.status_code != 201:
            pytest.skip("Driver creation with past expiry blocked at schema level")
        did = r.json()["id"]

        resp = client.post(f"/api/v1/loads/{load_id}/allocate",
                           json={"truck_id": tid, "driver_id": did},
                           headers=h)
        assert resp.status_code == 400

    def test_truck_overlap_conflict(self, client, seed_superadmin):
        """Two loads on overlapping dates for the same truck → 409."""
        h = _auth(client, seed_superadmin)
        cid = _create_client_entity(client, h)
        tid = _create_truck(client, h)
        did1 = _create_driver(client, h, license_no="DRV-A1", phone="9100000001")
        did2 = _create_driver(client, h, license_no="DRV-B2", phone="9100000002")

        # Load A: days 3-7
        load_a = _create_confirmed_load(client, h, cid, days_pickup=3, days_delivery=7)
        # Load B: days 5-9 (overlaps with A)
        load_b = _create_confirmed_load(client, h, cid, days_pickup=5, days_delivery=9)

        # Allocate truck to load A
        r1 = client.post(f"/api/v1/loads/{load_a}/allocate",
                         json={"truck_id": tid, "driver_id": did1}, headers=h)
        assert r1.status_code == 200

        # Try to allocate same truck to load B → conflict
        r2 = client.post(f"/api/v1/loads/{load_b}/allocate",
                         json={"truck_id": tid, "driver_id": did2}, headers=h)
        assert r2.status_code == 409

    def test_driver_overlap_conflict(self, client, seed_superadmin):
        """Same driver assigned to two overlapping loads → 409."""
        h = _auth(client, seed_superadmin)
        cid = _create_client_entity(client, h)
        tid1 = _create_truck(client, h, reg="TN10XX0001")
        tid2 = _create_truck(client, h, reg="TN10XX0002")
        did = _create_driver(client, h)

        load_a = _create_confirmed_load(client, h, cid, days_pickup=3, days_delivery=7)
        load_b = _create_confirmed_load(client, h, cid, days_pickup=5, days_delivery=9)

        r1 = client.post(f"/api/v1/loads/{load_a}/allocate",
                         json={"truck_id": tid1, "driver_id": did}, headers=h)
        assert r1.status_code == 200

        r2 = client.post(f"/api/v1/loads/{load_b}/allocate",
                         json={"truck_id": tid2, "driver_id": did}, headers=h)
        assert r2.status_code == 409

    # ── Get allocation ────────────────────────────────────────────────────────

    def test_get_allocation_after_allocate(self, client, seed_superadmin):
        h = _auth(client, seed_superadmin)
        cid = _create_client_entity(client, h)
        tid = _create_truck(client, h)
        did = _create_driver(client, h)
        load_id = _create_confirmed_load(client, h, cid)

        client.post(f"/api/v1/loads/{load_id}/allocate",
                    json={"truck_id": tid, "driver_id": did}, headers=h)

        r = client.get(f"/api/v1/loads/{load_id}/allocation", headers=h)
        assert r.status_code == 200
        data = r.json()
        assert data["truck_id"] == tid
        assert data["driver_id"] == did
        assert data["is_active"] is True

    def test_get_allocation_returns_null_for_unallocated(self, client, seed_superadmin):
        h = _auth(client, seed_superadmin)
        cid = _create_client_entity(client, h)
        load_id = _create_confirmed_load(client, h, cid)
        r = client.get(f"/api/v1/loads/{load_id}/allocation", headers=h)
        assert r.status_code == 200
        assert r.json() is None

    # ── Reallocate ────────────────────────────────────────────────────────────

    def test_reallocate_to_different_truck(self, client, seed_superadmin):
        h = _auth(client, seed_superadmin)
        cid = _create_client_entity(client, h)
        tid1 = _create_truck(client, h, reg="TN01BB0001")
        tid2 = _create_truck(client, h, reg="TN01BB0002")
        did = _create_driver(client, h)
        load_id = _create_confirmed_load(client, h, cid)

        # Allocate with truck 1
        client.post(f"/api/v1/loads/{load_id}/allocate",
                    json={"truck_id": tid1, "driver_id": did}, headers=h)

        # Reallocate to truck 2
        r = client.put(f"/api/v1/loads/{load_id}/allocate",
                       json={"truck_id": tid2, "driver_id": did}, headers=h)
        assert r.status_code == 200, r.text
        assert r.json()["allocated_truck_id"] == tid2
        assert r.json()["status"] == "allocated"

    def test_reallocate_on_non_allocated_load_rejected(self, client, seed_superadmin):
        h = _auth(client, seed_superadmin)
        cid = _create_client_entity(client, h)
        tid = _create_truck(client, h)
        did = _create_driver(client, h)
        load_id = _create_confirmed_load(client, h, cid)

        r = client.put(f"/api/v1/loads/{load_id}/allocate",
                       json={"truck_id": tid, "driver_id": did}, headers=h)
        assert r.status_code == 400

    # ── Deallocate ────────────────────────────────────────────────────────────

    def test_deallocate_reverts_to_confirmed(self, client, seed_superadmin):
        h = _auth(client, seed_superadmin)
        cid = _create_client_entity(client, h)
        tid = _create_truck(client, h)
        did = _create_driver(client, h)
        load_id = _create_confirmed_load(client, h, cid)

        # Allocate
        client.post(f"/api/v1/loads/{load_id}/allocate",
                    json={"truck_id": tid, "driver_id": did}, headers=h)

        # Deallocate
        r = client.delete(f"/api/v1/loads/{load_id}/allocate", headers=h)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "confirmed"
        assert data["allocated_truck_id"] is None
        assert data["allocated_driver_id"] is None

    def test_deallocate_restores_truck_and_driver_availability(
        self, client, seed_superadmin
    ):
        h = _auth(client, seed_superadmin)
        cid = _create_client_entity(client, h)
        tid = _create_truck(client, h)
        did = _create_driver(client, h)
        load_id = _create_confirmed_load(client, h, cid)

        # Allocate → truck/driver become unavailable
        client.post(f"/api/v1/loads/{load_id}/allocate",
                    json={"truck_id": tid, "driver_id": did}, headers=h)

        truck_resp = client.get(f"/api/v1/trucks/{tid}", headers=h)
        assert truck_resp.json()["is_available"] is False

        # Deallocate → truck/driver become available again
        client.delete(f"/api/v1/loads/{load_id}/allocate", headers=h)

        truck_resp2 = client.get(f"/api/v1/trucks/{tid}", headers=h)
        assert truck_resp2.json()["is_available"] is True

        driver_resp = client.get(f"/api/v1/drivers/{did}", headers=h)
        assert driver_resp.json()["is_available"] is True

    def test_deallocate_then_reallocate(self, client, seed_superadmin):
        """Deallocate frees up resources; can re-allocate to same load."""
        h = _auth(client, seed_superadmin)
        cid = _create_client_entity(client, h)
        tid = _create_truck(client, h)
        did = _create_driver(client, h)
        load_id = _create_confirmed_load(client, h, cid)

        # Allocate → Deallocate → Allocate again
        client.post(f"/api/v1/loads/{load_id}/allocate",
                    json={"truck_id": tid, "driver_id": did}, headers=h)
        client.delete(f"/api/v1/loads/{load_id}/allocate", headers=h)

        r = client.post(f"/api/v1/loads/{load_id}/allocate",
                        json={"truck_id": tid, "driver_id": did}, headers=h)
        assert r.status_code == 200
        assert r.json()["status"] == "allocated"

    # ── Availability endpoints ────────────────────────────────────────────────

    def test_available_trucks_excludes_allocated(self, client, seed_superadmin):
        h = _auth(client, seed_superadmin)
        cid = _create_client_entity(client, h)
        tid1 = _create_truck(client, h, reg="TN01CC0001")
        tid2 = _create_truck(client, h, reg="TN01CC0002")
        did = _create_driver(client, h)
        load_id = _create_confirmed_load(client, h, cid, days_pickup=3, days_delivery=5)

        # Before allocation: both trucks available
        r = client.get(
            f"/api/v1/allocations/trucks/available?pickup_date={_future(3)}&delivery_date={_future(5)}",
            headers=h
        )
        assert r.status_code == 200
        ids_before = [t["id"] for t in r.json()["items"]]
        assert tid1 in ids_before
        assert tid2 in ids_before

        # Allocate truck1
        client.post(f"/api/v1/loads/{load_id}/allocate",
                    json={"truck_id": tid1, "driver_id": did}, headers=h)

        # After allocation: truck1 excluded, truck2 still available
        r2 = client.get(
            f"/api/v1/allocations/trucks/available?pickup_date={_future(3)}&delivery_date={_future(5)}",
            headers=h
        )
        assert r2.status_code == 200
        ids_after = [t["id"] for t in r2.json()["items"]]
        assert tid1 not in ids_after
        assert tid2 in ids_after

    def test_available_drivers_excludes_allocated(self, client, seed_superadmin):
        h = _auth(client, seed_superadmin)
        cid = _create_client_entity(client, h)
        tid = _create_truck(client, h)
        did1 = _create_driver(client, h, license_no="DR-A1", phone="9200000001")
        did2 = _create_driver(client, h, license_no="DR-B2", phone="9200000002")
        load_id = _create_confirmed_load(client, h, cid, days_pickup=3, days_delivery=5)

        # Allocate driver1
        client.post(f"/api/v1/loads/{load_id}/allocate",
                    json={"truck_id": tid, "driver_id": did1}, headers=h)

        r = client.get(
            f"/api/v1/allocations/drivers/available?pickup_date={_future(3)}&delivery_date={_future(5)}",
            headers=h
        )
        assert r.status_code == 200
        ids = [d["id"] for d in r.json()["items"]]
        assert did1 not in ids
        assert did2 in ids

    # ── Full lifecycle ────────────────────────────────────────────────────────

    def test_full_lifecycle_allocated_to_delivered(self, client, seed_superadmin):
        """CONFIRMED → ALLOCATED → IN_TRANSIT → DELIVERED end-to-end."""
        h = _auth(client, seed_superadmin)
        cid = _create_client_entity(client, h)
        tid = _create_truck(client, h)
        did = _create_driver(client, h)
        load_id = _create_confirmed_load(client, h, cid)

        # Allocate
        r1 = client.post(f"/api/v1/loads/{load_id}/allocate",
                         json={"truck_id": tid, "driver_id": did}, headers=h)
        assert r1.status_code == 200
        assert r1.json()["status"] == "allocated"

        # Start transit
        r2 = client.post(f"/api/v1/loads/{load_id}/transition",
                         json={"to_status": "in_transit"}, headers=h)
        assert r2.status_code == 200
        assert r2.json()["status"] == "in_transit"

        # Deliver
        r3 = client.post(f"/api/v1/loads/{load_id}/transition",
                         json={"to_status": "delivered"}, headers=h)
        assert r3.status_code == 200
        assert r3.json()["status"] == "delivered"
        assert r3.json()["actual_delivery_date"] is not None
