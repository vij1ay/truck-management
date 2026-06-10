from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models import Base, Role, User, UserRole, SYSTEM_ROLES
from app.dependencies.database import get_db
from app.core.security import hash_password
from datetime import datetime
import os

os.environ["BCRYPT_COST_FACTOR"] = "4"
RAW_DB_URL = "postgresql://postgres:release@localhost:5432/transport_db"
base, dbname = RAW_DB_URL.rsplit("/", 1)
TEST_DB_URL = f"{base}/{dbname}_test"

engine = create_engine(TEST_DB_URL)
TestingSessionLocal = sessionmaker(bind=engine)

def repro():
    # Setup clean DB
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        tables = ["audit_logs", "documents", "trucks", "drivers", "clients", "user_roles", "refresh_tokens", "users", "roles", "tenants"]
        table_str = ", ".join([f'"{t}"' for t in tables])
        conn.execute(text(f"TRUNCATE TABLE {table_str} RESTART IDENTITY CASCADE"))
        conn.commit()

    db = TestingSessionLocal()
    
    # Seed roles
    roles = {}
    from app.models.tenant import SubscriptionTier, Tenant
    for rd in SYSTEM_ROLES:
        r = Role(**rd)
        db.add(r)
        roles[rd["name"]] = r
    
    # Seed tenant
    tenant = Tenant(
        name="Test Logistics",
        domain="test.local",
        subscription_tier=SubscriptionTier.PREMIUM,
        is_active=True
    )
    db.add(tenant)
    db.flush()

    # Seed superadmin
    user = User(
        email="admin@example.com",
        password_hash=hash_password("TestPassword123!"),
        first_name="Test",
        last_name="Admin",
        tenant_id=tenant.id,
        is_active=True,
        is_verified=True,
        password_changed_at=datetime.utcnow()
    )
    db.add(user)
    db.flush()

    user_role = UserRole(user_id=user.id, role_id=roles["SuperAdmin"].id, tenant_id=tenant.id, assigned_at=datetime.utcnow())
    db.add(user_role)
    db.commit()

    def get_db_override():
        try: yield db
        finally: db.close()

    app.dependency_overrides[get_db] = get_db_override
    client = TestClient(app)

    print("\nAttempting login...")
    resp = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "TestPassword123!"})
    print(f"Login status: {resp.status_code}")
    print(f"Login body: {resp.json()}")
    if resp.status_code != 200:
        return

    token = resp.json()["access_token"]
    from app.core.security import decode_token_unverified
    payload = decode_token_unverified(token)
    print(f"Token payload: {payload}")
    
    headers = {"Authorization": f"Bearer {token}"}

    truck_data = {
        "registration_no": "MH12AB1234",
        "truck_type": "flatbed",
        "ownership_type": "owned",
        "make": "Tata",
        "model": "LPT 2518",
        "year": 2022,
        "capacity_tons": 25.0,
    }

    print("\nAttempting truck creation...")
    resp = client.post("/api/v1/trucks/", json=truck_data, headers=headers)
    print(f"Create truck status: {resp.status_code}")
    if resp.status_code != 201:
        print(f"Create truck failed: {resp.json()}")

if __name__ == "__main__":
    repro()
