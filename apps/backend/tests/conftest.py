import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load .env and override bcrypt cost so tests run fast
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except Exception:
    pass

# Use a low bcrypt cost factor for tests (4 vs production 12 = 250× faster)
os.environ["BCRYPT_COST_FACTOR"] = "4"

from app.main import app
from app.models import Base
from app.dependencies.database import get_db

# ── Database URL ──────────────────────────────────────────────────────────────
_RAW_DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:release@localhost:5432/transport_db"
)
_base, _dbname = _RAW_DB_URL.rsplit("/", 1)
TEST_DB_URL = f"{_base}/{_dbname}_test"

# ── Ensure test database exists (one-time at startup) ─────────────────────────
try:
    _admin_eng = create_engine(f"{_base}/postgres", isolation_level="AUTOCOMMIT")
    with _admin_eng.connect() as _c:
        _exists = _c.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"),
            {"n": f"{_dbname}_test"}
        ).scalar()
        if not _exists:
            _c.execute(text(f'CREATE DATABASE "{_dbname}_test"'))
    _admin_eng.dispose()
except Exception as e:
    print(f"WARNING: Could not create test DB: {e}")

# ── Create engine ─────────────────────────────────────────────────────────────
engine = create_engine(TEST_DB_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _truncate_all(connection):
    """Truncate every application table to ensure clean state between tests."""
    tables = [
        "load_allocations", "load_history", "audit_logs", "documents", "loads",
        "trucks", "drivers", "clients",
        "user_roles", "refresh_tokens", "users", "roles", "tenants"
    ]
    # Join tables and run a single TRUNCATE...CASCADE
    table_str = ", ".join([f'"{t}"' for t in tables])
    try:
        connection.execute(text(f"TRUNCATE TABLE {table_str} RESTART IDENTITY CASCADE"))
        connection.commit()
    except Exception as e:
        print(f"WARNING: Truncate failed: {e}")
        connection.rollback()


# ── Fixtures ──────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    """
    Recreate all tables at the start of every test session.
    drop_all + create_all ensures the schema always mirrors the current
    SQLAlchemy metadata — avoids stale schema issues when models evolve.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="function")
def db_session(_create_tables):
    """Return a clean DB session — truncates all tables before each test."""
    conn = engine.connect()
    _truncate_all(conn)
    conn.close()

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient backed by the isolated test DB session."""
    def _get_db_override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()


@pytest.fixture
def seed_roles(db_session):
    """Seed system roles."""
    from app.models import Role, SYSTEM_ROLES
    roles = {}
    for rd in SYSTEM_ROLES:
        r = Role(**rd)
        db_session.add(r)
        roles[rd["name"]] = r
    db_session.commit()
    return roles


@pytest.fixture
def seed_tenant(db_session):
    """Seed a default test tenant."""
    from app.models.tenant import Tenant, SubscriptionTier
    tenant = Tenant(
        name="Test Logistics",
        domain="test.local",
        subscription_tier=SubscriptionTier.premium,
        is_active=True
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def seed_superadmin(db_session, seed_roles, seed_tenant):
    """Seed a SuperAdmin user associated with the test tenant."""
    from app.models import User, UserRole
    from app.core.security import hash_password
    from app.core.datetime_utils import utc_now

    user = User(
        email="admin@example.com",
        password_hash=hash_password("TestPassword123!"),
        first_name="Test",
        last_name="Admin",
        tenant_id=seed_tenant.id,
        is_active=True,
        is_verified=True,
        password_changed_at=utc_now()
    )
    db_session.add(user)
    db_session.flush()

    user_role = UserRole(
        user_id=user.id,
        role_id=seed_roles["SuperAdmin"].id,
        tenant_id=seed_tenant.id,
        assigned_at=utc_now()
    )
    db_session.add(user_role)
    db_session.commit()
    return user


@pytest.fixture
def second_tenant(client, seed_superadmin):
    """
    Create a second tenant (with its own TenantAdmin) via the SuperAdmin API, for
    tests that verify SuperAdmin cross-tenant `tenant_id` filtering.

    Returns a dict with `tenant_id`, `headers` (the second tenant's TenantAdmin),
    and `superadmin_headers`.
    """
    su_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "TestPassword123!"}
    )
    su_headers = {"Authorization": f"Bearer {su_login.json()['access_token']}"}

    resp = client.post(
        "/api/v1/tenants",
        json={
            "name": "Second Tenant Co",
            "subscription_tier": "trial",
            "max_users": 10,
            "admin_email": "admin@second-tenant.example",
            "admin_password": "SecondPass123",
            "admin_first_name": "Second",
            "admin_last_name": "Admin",
        },
        headers=su_headers,
    )
    assert resp.status_code == 201, resp.text
    tenant_id = resp.json()["id"]

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@second-tenant.example", "password": "SecondPass123"}
    )
    admin_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    return {"tenant_id": tenant_id, "headers": admin_headers, "superadmin_headers": su_headers}


@pytest.fixture
def tiny_png_bytes() -> bytes:
    """A minimal valid in-memory PNG, for avatar-upload tests."""
    import io
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (4, 4), color="red").save(buf, format="PNG")
    return buf.getvalue()
