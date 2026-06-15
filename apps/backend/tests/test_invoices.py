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
            "advance_amount": min(3000.0, freight),
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _transition(client, headers, load_id: str, status: str):
    resp = client.post(f"/api/v1/loads/{load_id}/transition", json={"to_status": status}, headers=headers)
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
        assert resp.status_code == 401

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


class TestInvoicePdf:
    def test_download_invoice_pdf(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "PDF Co")
        inv = _create_invoice(client, headers, client_id)

        resp = client.get(f"/api/v1/invoices/{inv['id']}/pdf", headers=headers)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"

    def test_download_pdf_requires_auth(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "PDF NoAuth Co")
        inv = _create_invoice(client, headers, client_id)

        resp = client.get(f"/api/v1/invoices/{inv['id']}/pdf")
        assert resp.status_code == 401

    def test_pdf_for_load_linked_invoice(self, client, seed_superadmin, seed_tenant):
        """Auto-generated invoice (with a linked load) renders a PDF with a load line item."""
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "PDF Load Co")
        load = _create_load(client, headers, client_id, freight=12000.0)
        _transition(client, headers, load["id"], "confirmed")
        _transition(client, headers, load["id"], "allocated")
        _transition(client, headers, load["id"], "in_transit")
        _transition(client, headers, load["id"], "delivered")

        listed = client.get(f"/api/v1/invoices?load_id={load['id']}", headers=headers)
        inv_id = listed.json()["items"][0]["id"]

        resp = client.get(f"/api/v1/invoices/{inv_id}/pdf", headers=headers)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"

    def test_pdf_includes_payment_history(self, client, seed_superadmin, seed_tenant):
        """PDF generation succeeds once payments have been recorded against the invoice."""
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "PDF Payment Co")
        inv = _create_invoice(client, headers, client_id)

        send = client.post(f"/api/v1/invoices/{inv['id']}/send", headers=headers)
        assert send.status_code == 200, send.text

        pay = client.post(
            f"/api/v1/invoices/{inv['id']}/payments",
            json={"amount": "1000.00", "payment_date": date.today().isoformat(), "payment_method": "cash"},
            headers=headers,
        )
        assert pay.status_code == 201, pay.text

        resp = client.get(f"/api/v1/invoices/{inv['id']}/pdf", headers=headers)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"


class TestInvoiceOverdue:
    def test_overdue_auto_detection_on_list(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "Overdue Co")

        resp = client.post(
            "/api/v1/invoices",
            json={
                "client_id": client_id,
                "issued_date": (date.today() - timedelta(days=40)).isoformat(),
                "due_date": (date.today() - timedelta(days=10)).isoformat(),
                "subtotal": "5000.00",
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        inv = resp.json()

        send = client.post(f"/api/v1/invoices/{inv['id']}/send", headers=headers)
        assert send.status_code == 200, send.text
        assert send.json()["status"] == "sent"

        listed = client.get("/api/v1/invoices", headers=headers)
        assert listed.status_code == 200
        match = next(i for i in listed.json()["items"] if i["id"] == inv["id"])
        assert match["status"] == "overdue"

    def test_refresh_overdue_endpoint(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "Refresh Overdue Co")

        resp = client.post(
            "/api/v1/invoices",
            json={
                "client_id": client_id,
                "issued_date": (date.today() - timedelta(days=40)).isoformat(),
                "due_date": (date.today() - timedelta(days=5)).isoformat(),
                "subtotal": "2000.00",
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        inv = resp.json()
        send = client.post(f"/api/v1/invoices/{inv['id']}/send", headers=headers)
        assert send.status_code == 200, send.text

        refresh = client.post("/api/v1/invoices/refresh-overdue", headers=headers)
        assert refresh.status_code == 200, refresh.text
        body = refresh.json()
        assert body["count"] >= 1
        assert inv["invoice_no"] in body["updated"]

        check = client.get(f"/api/v1/invoices/{inv['id']}", headers=headers)
        assert check.json()["status"] == "overdue"

    def test_refresh_overdue_multiple_invoices(self, client, seed_superadmin, seed_tenant):
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "Multi Overdue Co")

        invoice_nos = []
        for i in range(2):
            resp = client.post(
                "/api/v1/invoices",
                json={
                    "client_id": client_id,
                    "issued_date": (date.today() - timedelta(days=40)).isoformat(),
                    "due_date": (date.today() - timedelta(days=1 + i)).isoformat(),
                    "subtotal": "1000.00",
                },
                headers=headers,
            )
            assert resp.status_code == 201, resp.text
            inv = resp.json()
            invoice_nos.append(inv["invoice_no"])
            send = client.post(f"/api/v1/invoices/{inv['id']}/send", headers=headers)
            assert send.status_code == 200, send.text

        refresh = client.post("/api/v1/invoices/refresh-overdue", headers=headers)
        assert refresh.status_code == 200, refresh.text
        body = refresh.json()
        for invoice_no in invoice_nos:
            assert invoice_no in body["updated"]

        # Calling again should be a no-op — all candidates already flipped to OVERDUE
        refresh_again = client.post("/api/v1/invoices/refresh-overdue", headers=headers)
        assert refresh_again.status_code == 200, refresh_again.text
        for invoice_no in invoice_nos:
            assert invoice_no not in refresh_again.json()["updated"]

    def test_non_overdue_invoice_unaffected(self, client, seed_superadmin, seed_tenant):
        """An invoice with a future due_date should never be flagged overdue."""
        headers = _auth(client, seed_superadmin)
        client_id = _create_client(client, headers, "Future Due Co")
        inv = _create_invoice(client, headers, client_id)  # due_date 30 days from now

        send = client.post(f"/api/v1/invoices/{inv['id']}/send", headers=headers)
        assert send.status_code == 200, send.text

        listed = client.get("/api/v1/invoices", headers=headers)
        match = next(i for i in listed.json()["items"] if i["id"] == inv["id"])
        assert match["status"] == "sent"


class TestInvoiceTenantFilter:
    def test_superadmin_filters_invoices_by_tenant(self, client, seed_superadmin, seed_tenant, second_tenant):
        su_headers = _auth(client, seed_superadmin)

        own_client_id = _create_client(client, su_headers, "Tenant A Invoice Co")
        own_inv = _create_invoice(client, su_headers, own_client_id)

        other_headers = second_tenant["headers"]
        other_tenant_id = second_tenant["tenant_id"]
        other_client_id = _create_client(client, other_headers, "Tenant B Invoice Co")
        other_inv = _create_invoice(client, other_headers, other_client_id)

        unfiltered = client.get("/api/v1/invoices", headers=su_headers)
        assert unfiltered.status_code == 200, unfiltered.text
        tenant_ids = {i["tenant_id"] for i in unfiltered.json()["items"]}
        assert str(seed_tenant.id) in tenant_ids
        assert other_tenant_id in tenant_ids

        filtered = client.get("/api/v1/invoices", params={"tenant_id": other_tenant_id}, headers=su_headers)
        assert filtered.status_code == 200, filtered.text
        filtered_data = filtered.json()
        assert filtered_data["total"] >= 1
        assert all(i["tenant_id"] == other_tenant_id for i in filtered_data["items"])
        ids = {i["id"] for i in filtered_data["items"]}
        assert other_inv["id"] in ids
        assert own_inv["id"] not in ids
