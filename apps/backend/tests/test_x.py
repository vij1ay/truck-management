from tests.test_drivers import DRIVER, _auth

def test_debug_list_empty(client, seed_superadmin):
    from tests.test_drivers import _auth
    headers = _auth(client, seed_superadmin)
    resp = client.get("/api/v1/loads/", headers=headers)
    
    with open("out_error2.txt", "w") as f:
        f.write(f"STATUS: {resp.status_code}\nBODY: {resp.text}")
    assert resp.status_code == 200
