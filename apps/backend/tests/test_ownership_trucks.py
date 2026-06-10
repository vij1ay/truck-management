import pytest
from tests.test_trucks import _auth, _get_token

def test_create_contract_truck(client, seed_superadmin):
    headers = _auth(client, seed_superadmin)
    truck_data = {
        "registration_no": "MH12XY8888",
        "truck_type": "container",
        "ownership_type": "contract",
        "contractor_name": "ABC Transport",
        "contractor_contact": "9876543210",
        "contract_start_date": "2026-03-01",
        "contract_end_date": "2027-03-01"
    }
    resp = client.post("/api/v1/trucks/", json=truck_data, headers=headers)
    print("STATUS", resp.status_code)
    if resp.status_code >= 400:
        print("ERROR:", resp.json())
    assert resp.status_code == 201

def test_create_leased_truck(client, seed_superadmin):
    headers = _auth(client, seed_superadmin)
    truck_data = {
        "registration_no": "MH12LL5555",
        "truck_type": "tanker",
        "ownership_type": "leased",
        "lessor_name": "XYZ Leasing",
        "lessor_contact": "xyz@example.com",
        "lease_start_date": "2025-01-01",
        "lease_end_date": "2028-12-31",
        "notes": "Leased tanker"
    }
    resp = client.post("/api/v1/trucks/", json=truck_data, headers=headers)
    print("STATUS", resp.status_code)
    if resp.status_code >= 400:
        print("ERROR", resp.json())
    assert resp.status_code == 201
