"""Tests for Documents API endpoints - Phase 2."""
import pytest
from datetime import date, timedelta


def _token(client, seed_superadmin):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "TestPassword123!"}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _future(days):
    return (date.today() + timedelta(days=days)).isoformat()


def _past(days):
    return (date.today() - timedelta(days=days)).isoformat()


TRUCK = {
    "registration_no": "MH12AA0001",
    "truck_type": "flatbed",
    "ownership_type": "owned",
}

DRIVER = {
    "first_name": "Suresh",
    "last_name": "Babu",
    "phone": "9876543210",
    "license_no": "KA123456789",
    "license_class": "lmv",
    "license_expiry": _future(365),
}


class TestDocumentEndpoints:
    def _create_truck(self, client, headers):
        r = client.post("/api/v1/trucks/", json=TRUCK, headers=headers)
        return r.json()["id"]

    def _create_driver(self, client, headers):
        r = client.post("/api/v1/drivers/", json=DRIVER, headers=headers)
        return r.json()["id"]

    def test_create_document_for_truck(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        truck_id = self._create_truck(client, headers)
        doc = {
            "entity_type": "truck",
            "entity_id": truck_id,
            "document_type": "rc_book",
            "file_name": "rc_book.pdf",
            "expiry_date": _future(365),
        }
        resp = client.post(f"/api/v1/trucks/{truck_id}/documents", json=doc, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["document_type"] == "rc_book"
        assert data["entity_type"] == "truck"

    def test_document_status_active_on_future_expiry(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        truck_id = self._create_truck(client, headers)
        doc = {
            "entity_type": "truck",
            "entity_id": truck_id,
            "document_type": "insurance",
            "file_name": "insurance.pdf",
            "expiry_date": _future(100),
        }
        resp = client.post(f"/api/v1/trucks/{truck_id}/documents", json=doc, headers=headers)
        assert resp.json()["document_status"] == "active"

    def test_document_status_expired_on_past_expiry(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        truck_id = self._create_truck(client, headers)
        doc = {
            "entity_type": "truck",
            "entity_id": truck_id,
            "document_type": "fitness",
            "file_name": "fitness.pdf",
            "expiry_date": _past(5),
        }
        resp = client.post(f"/api/v1/trucks/{truck_id}/documents", json=doc, headers=headers)
        assert resp.json()["document_status"] == "expired"

    def test_list_documents_for_truck(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        truck_id = self._create_truck(client, headers)
        doc = {
            "entity_type": "truck",
            "entity_id": truck_id,
            "document_type": "pollution",
            "file_name": "puc.pdf",
            "expiry_date": _future(100)
        }
        client.post(f"/api/v1/trucks/{truck_id}/documents", json=doc, headers=headers)
        resp = client.get(f"/api/v1/trucks/{truck_id}/documents", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()["items"]) >= 1

    def test_list_all_documents(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        truck_id = self._create_truck(client, headers)
        doc = {
            "entity_type": "truck",
            "entity_id": truck_id,
            "document_type": "permit",
            "file_name": "permit.pdf"
        }
        client.post(f"/api/v1/trucks/{truck_id}/documents", json=doc, headers=headers)
        resp = client.get("/api/v1/documents/", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_get_expiring_documents(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        truck_id = self._create_truck(client, headers)
        doc = {
            "entity_type": "truck",
            "entity_id": truck_id,
            "document_type": "insurance",
            "file_name": "ins.pdf",
            "expiry_date": _future(20),  # Expiring in 20 days
        }
        client.post(f"/api/v1/trucks/{truck_id}/documents", json=doc, headers=headers)
        resp = client.get("/api/v1/documents/expiring?days=30", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_delete_document(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        truck_id = self._create_truck(client, headers)
        doc = {
            "entity_type": "truck",
            "entity_id": truck_id,
            "document_type": "rc_book",
            "file_name": "rc.pdf"
        }
        create = client.post(f"/api/v1/trucks/{truck_id}/documents", json=doc, headers=headers)
        doc_id = create.json()["id"]
        resp = client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
        assert resp.status_code == 204

    def test_invalid_expiry_date_before_issue_date(self, client, seed_superadmin):
        headers = _token(client, seed_superadmin)
        truck_id = self._create_truck(client, headers)
        doc = {
            "entity_type": "truck",
            "entity_id": truck_id,
            "document_type": "rc_book",
            "file_name": "rc.pdf",
            "issue_date": _future(10),
            "expiry_date": _future(5),  # expiry before issue
        }
        resp = client.post(f"/api/v1/trucks/{truck_id}/documents", json=doc, headers=headers)
        assert resp.status_code == 422
