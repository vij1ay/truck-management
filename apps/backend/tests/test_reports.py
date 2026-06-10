"""Tests for Reports API endpoints - Phase 9."""
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


def _create_client(client, headers, name="Report Test Shipper"):
    resp = client.post(
        "/api/v1/clients/",
        json={"company_name": name, "phone": "9876543210", "client_type": "company"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _create_load(client, headers, client_id: str, days_ahead: int = 2):
    resp = client.post(
        "/api/v1/loads/",
        json={
            "client_id": client_id,
            "origin": "Mumbai",
            "destination": "Pune",
            "pickup_date": (date.today() + timedelta(days=days_ahead)).isoformat(),
            "goods_type": "general",
            "weight_kg": 5000.0,
            "freight_amount": 15000.0,
            "advance_amount": 5000.0,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestReportsSummary:

    def test_summary_empty_db(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        resp = client.get("/api/v1/reports/summary", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_loads"] == 0
        assert data["total_freight"] == 0.0
        assert data["total_outstanding"] == 0.0
        assert "loads_by_status" in data
        assert "active_trucks" in data
        assert "available_drivers" in data

    def test_summary_with_loads(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        _create_load(client, headers, cid, days_ahead=2)
        _create_load(client, headers, cid, days_ahead=3)

        resp = client.get("/api/v1/reports/summary", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_loads"] == 2
        assert data["loads_by_status"]["draft"] == 2

    def test_summary_requires_auth(self, client, seed_superadmin):
        resp = client.get("/api/v1/reports/summary")
        assert resp.status_code == 403

    def test_summary_schema_complete(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        resp = client.get("/api/v1/reports/summary", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        required_keys = [
            "total_loads", "loads_by_status", "total_freight",
            "total_advance_collected", "total_outstanding",
            "active_trucks", "available_trucks",
            "active_drivers", "available_drivers",
            "loads_this_month", "revenue_this_month",
        ]
        for key in required_keys:
            assert key in data, f"Missing key: {key}"


class TestReportsLoadTrend:

    def test_load_trend_empty(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        resp = client.get("/api/v1/reports/loads/trend", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_load_trend_with_data(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers)
        _create_load(client, headers, cid, days_ahead=2)

        resp = client.get("/api/v1/reports/loads/trend?months=12", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1
        point = data[0]
        assert "period" in point
        assert "total" in point
        assert "delivered" in point
        assert "cancelled" in point

    def test_load_trend_months_validation(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        resp = client.get("/api/v1/reports/loads/trend?months=0", headers=headers)
        assert resp.status_code == 422

        resp = client.get("/api/v1/reports/loads/trend?months=25", headers=headers)
        assert resp.status_code == 422


class TestReportsRevenue:

    def test_revenue_empty(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        resp = client.get("/api/v1/reports/revenue", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["by_client"] == []
        assert data["total_freight"] == 0.0
        assert data["total_outstanding"] == 0.0

    def test_revenue_with_loads(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        cid = _create_client(client, headers, "Revenue Client")
        _create_load(client, headers, cid, days_ahead=2)

        resp = client.get("/api/v1/reports/revenue", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["by_client"]) == 1
        row = data["by_client"][0]
        assert row["client_name"] == "Revenue Client"
        assert row["load_count"] == 1
        assert row["total_freight"] == 15000.0
        assert row["total_advance"] == 5000.0


class TestReportsDriverPerformance:

    def test_driver_performance_empty(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        resp = client.get("/api/v1/reports/drivers/performance", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["drivers"] == []

    def test_driver_performance_requires_auth(self, client, seed_superadmin):
        resp = client.get("/api/v1/reports/drivers/performance")
        assert resp.status_code == 403


class TestReportsTruckUtilization:

    def test_truck_utilization_empty(self, client, seed_superadmin):
        headers = _auth(client, seed_superadmin)
        resp = client.get("/api/v1/reports/trucks/utilization", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["trucks"] == []
        assert isinstance(data["by_status"], dict)

    def test_truck_utilization_requires_auth(self, client, seed_superadmin):
        resp = client.get("/api/v1/reports/trucks/utilization")
        assert resp.status_code == 403
