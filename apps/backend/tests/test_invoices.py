"""Tests for Invoice & Payment API — Phase 10."""
import pytest
from datetime import date, timedelta


# ── Helpers ────────────────────────────────────────────────────────────────────

def _auth(client, seed_superadmin):
    resp = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "TestPassword123!"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_client(client, headers, name="Invoice Test Co"):
    resp = client.post("/api/v1/clients/", json={"company_name": name, "phone": "9876540001", "client_type": "company"}, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _create_load(client, headers, client_id: str, freight: float = 15000.0):
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
            "advance_amount": 3000.0,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _transition(client, headers, load_id: str, status: str):
    resp = client.post(f"/api/v1/loads/{load_id}/status", json={"status": status}, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _create_invoice(client, headers, client_id: str):
    resp = client.post(
        "/api/v1/invoices",
        json={
            "client_id": client_id,
            "issued_date": date.today().isoformat(),
            "due_date": (date.today() + timedelta(days=30)).isoformat(),
            "subtotal": "10000.00",
            "tax_rate": "18.00",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestInvoiceCreate:
    def test_create_invoice_manual(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers)
        inv = _create_invoice(client, headers, client_id)
        assert inv["invoice_no"].startswith("INV-")
        assert inv["status"] == "draft"
        assert float(inv["tax_amount"]) == pytest.approx(1800.0)
        assert float(inv["total_amount"]) == pytest.approx(11800.0)

    def test_create_invoice_requires_auth(self, client, seed_superadmin, seed_tenant):
        resp = client.post("/api/v1/invoices", json={"client_id": "00000000-0000-0000-0000-000000000000", "issued_date": date.today().isoformat(), "subtotal": "1000"})
        assert resp.status_code == 403

    def test_create_duplicate_load_invoice_rejected(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "Dup Invoice Co")
        load = _create_load(client, headers, client_id)
        # Deliver load to auto-create invoice
        _transition(client, headers, load["id"], "confirmed")
        _transition(client, headers, load["id"], "allocated")
        _transition(client, headers, load["id"], "in_transit")
        _transition(client, headers, load["id"], "delivered")
        # Manual create for same load should fail
        resp = client.post(
            "/api/v1/invoices",
            json={"load_id": load["id"], "client_id": client_id, "issued_date": date.today().isoformat(), "subtotal": "5000"},
            headers=headers,
        )
        assert resp.status_code == 409


class TestAutoInvoice:
    def test_deliver_load_creates_draft_invoice(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "AutoInv Co")
        load = _create_load(client, headers, client_id, freight=20000.0)
        _transition(client, headers, load["id"], "confirmed")
        _transition(client, headers, load["id"], "allocated")
        _transition(client, headers, load["id"], "in_transit")
        _transition(client, headers, load["id"], "delivered")

        resp = client.get(f"/api/v1/invoices?load_id={load['id']}", headers=headers)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["status"] == "draft"
        assert float(items[0]["total_amount"]) == pytest.approx(20000.0)

    def test_deliver_zero_freight_no_invoice(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "ZeroFreight Co")
        load = _create_load(client, headers, client_id, freight=0.0)
        _transition(client, headers, load["id"], "confirmed")
        _transition(client, headers, load["id"], "allocated")
        _transition(client, headers, load["id"], "in_transit")
        _transition(client, headers, load["id"], "delivered")

        resp = client.get(f"/api/v1/invoices?load_id={load['id']}", headers=headers)
        assert resp.json()["total"] == 0


class TestInvoiceLifecycle:
    def test_send_invoice(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "Lifecycle Co")
        inv = _create_invoice(client, headers, client_id)
        resp = client.post(f"/api/v1/invoices/{inv['id']}/send", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "sent"

    def test_cannot_send_cancelled_invoice(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "CancelTest Co")
        inv = _create_invoice(client, headers, client_id)
        client.post(f"/api/v1/invoices/{inv['id']}/cancel", headers=headers)
        resp = client.post(f"/api/v1/invoices/{inv['id']}/send", headers=headers)
        assert resp.status_code == 400

    def test_cancel_draft_invoice(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "CancelDraft Co")
        inv = _create_invoice(client, headers, client_id)
        resp = client.post(f"/api/v1/invoices/{inv['id']}/cancel", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"


class TestPayments:
    def test_record_full_payment(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "Payment Co")
        inv = _create_invoice(client, headers, client_id)
        client.post(f"/api/v1/invoices/{inv['id']}/send", headers=headers)

        resp = client.post(
            f"/api/v1/invoices/{inv['id']}/payments",
            json={"amount": "11800.00", "payment_date": date.today().isoformat(), "payment_method": "dummy"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["reference_no"].startswith("DUMMY-")

        detail = client.get(f"/api/v1/invoices/{inv['id']}", headers=headers).json()
        assert detail["status"] == "paid"

    def test_record_partial_payment(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "Partial Pay Co")
        inv = _create_invoice(client, headers, client_id)
        client.post(f"/api/v1/invoices/{inv['id']}/send", headers=headers)

        client.post(
            f"/api/v1/invoices/{inv['id']}/payments",
            json={"amount": "5000.00", "payment_date": date.today().isoformat(), "payment_method": "cash"},
            headers=headers,
        )
        detail = client.get(f"/api/v1/invoices/{inv['id']}", headers=headers).json()
        assert detail["status"] == "partial"
        assert float(detail["paid_amount"]) == pytest.approx(5000.0)

    def test_overpayment_rejected(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "Overpay Co")
        inv = _create_invoice(client, headers, client_id)
        client.post(f"/api/v1/invoices/{inv['id']}/send", headers=headers)

        resp = client.post(
            f"/api/v1/invoices/{inv['id']}/payments",
            json={"amount": "99999.00", "payment_date": date.today().isoformat(), "payment_method": "dummy"},
            headers=headers,
        )
        assert resp.status_code == 400

    def test_payment_on_draft_rejected(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "DraftPay Co")
        inv = _create_invoice(client, headers, client_id)
        resp = client.post(
            f"/api/v1/invoices/{inv['id']}/payments",
            json={"amount": "100.00", "payment_date": date.today().isoformat(), "payment_method": "dummy"},
            headers=headers,
        )
        assert resp.status_code == 400


class TestInvoiceList:
    def test_list_invoices(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "List Co")
        _create_invoice(client, headers, client_id)
        resp = client.get("/api/v1/invoices", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_filter_by_status(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        resp = client.get("/api/v1/invoices?status=draft", headers=headers)
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["status"] == "draft"
