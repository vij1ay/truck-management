"""Tests for Authentication endpoints - Phase 1."""

import pytest


class TestAuthEndpoints:
    """Tests for /api/v1/auth endpoints."""

    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_login_success(self, client, seed_superadmin):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "TestPassword123!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "admin@example.com"

    def test_login_with_local_tld_email(self, client, db_session, seed_roles, seed_tenant):
        """Accounts with internal-style domains (e.g. the seeded SuperAdmin's
        admin@system.local) must be able to log in — pydantic's EmailStr rejects
        '.local' as a special-use TLD, so User.email uses a lenient UserEmail type
        instead (see app/schemas/common.py)."""
        from app.models import User, UserRole
        from app.core.security import hash_password
        from app.core.datetime_utils import utc_now

        user = User(
            email="admin@system.local",
            password_hash=hash_password("TestPassword123!"),
            first_name="Super",
            last_name="Admin",
            tenant_id=None,
            is_active=True,
            is_verified=True,
            password_changed_at=utc_now(),
        )
        db_session.add(user)
        db_session.flush()
        db_session.add(UserRole(
            user_id=user.id, role_id=seed_roles["SuperAdmin"].id,
            tenant_id=None, assigned_at=utc_now(),
        ))
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@system.local", "password": "TestPassword123!"}
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["user"]["email"] == "admin@system.local"

    def test_login_invalid_password(self, client, seed_superadmin):
        """Test login with invalid password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "WrongPassword!"
            }
        )
        assert response.status_code == 401

    def test_login_invalid_email(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nobody@example.com",
                "password": "TestPassword123!"
            }
        )
        assert response.status_code == 401

    def test_token_refresh(self, client, seed_superadmin):
        """Test refreshing access token."""
        # Login first
        login_resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "TestPassword123!"
            }
        )
        refresh_token = login_resp.json()["refresh_token"]

        # Refresh
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_logout(self, client, seed_superadmin):
        """Test logout endpoint."""
        # Login first
        login_resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "TestPassword123!"
            }
        )
        token = login_resp.json()["access_token"]
        refresh_token = login_resp.json()["refresh_token"]

        # Logout
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200


class TestPasswordReset:
    """POST /auth/forgot-password + POST /auth/reset-password."""

    def test_forgot_password_unknown_email_returns_generic_message(self, client, seed_superadmin):
        resp = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "message" in data
        assert data.get("reset_token") is None

    def test_forgot_password_known_email_returns_token_in_debug(self, client, seed_superadmin):
        resp = client.post("/api/v1/auth/forgot-password", json={"email": "admin@example.com"})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        # settings.DEBUG=True in the test environment
        assert data["reset_token"]

    def test_full_reset_flow(self, client, seed_superadmin):
        forgot = client.post("/api/v1/auth/forgot-password", json={"email": "admin@example.com"})
        token = forgot.json()["reset_token"]
        assert token

        reset = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "NewPass456"},
        )
        assert reset.status_code == 200, reset.text

        # Old password no longer works
        old = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "TestPassword123!"},
        )
        assert old.status_code == 401

        # New password works
        new = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "NewPass456"},
        )
        assert new.status_code == 200, new.text

    def test_reset_token_is_single_use(self, client, seed_superadmin):
        forgot = client.post("/api/v1/auth/forgot-password", json={"email": "admin@example.com"})
        token = forgot.json()["reset_token"]

        first = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "FirstPass456"},
        )
        assert first.status_code == 200, first.text

        second = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "SecondPass456"},
        )
        assert second.status_code == 400

    def test_reset_with_invalid_token_rejected(self, client, seed_superadmin):
        resp = client.post(
            "/api/v1/auth/reset-password",
            json={"token": "not-a-real-token", "new_password": "NewPass456"},
        )
        assert resp.status_code == 400

    def test_reset_with_weak_password_rejected(self, client, seed_superadmin):
        forgot = client.post("/api/v1/auth/forgot-password", json={"email": "admin@example.com"})
        token = forgot.json()["reset_token"]

        resp = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "weakpassword"},
        )
        assert resp.status_code == 422

    def test_reset_revokes_existing_refresh_tokens(self, client, seed_superadmin):
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "TestPassword123!"},
        )
        refresh_token = login.json()["refresh_token"]

        forgot = client.post("/api/v1/auth/forgot-password", json={"email": "admin@example.com"})
        token = forgot.json()["reset_token"]
        reset = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "NewPass456"},
        )
        assert reset.status_code == 200, reset.text

        refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert refresh.status_code == 401

    def test_requesting_new_reset_invalidates_previous_token(self, client, seed_superadmin):
        first = client.post("/api/v1/auth/forgot-password", json={"email": "admin@example.com"})
        first_token = first.json()["reset_token"]

        second = client.post("/api/v1/auth/forgot-password", json={"email": "admin@example.com"})
        second_token = second.json()["reset_token"]
        assert second_token != first_token

        stale = client.post(
            "/api/v1/auth/reset-password",
            json={"token": first_token, "new_password": "NewPass456"},
        )
        assert stale.status_code == 400

        fresh = client.post(
            "/api/v1/auth/reset-password",
            json={"token": second_token, "new_password": "NewPass456"},
        )
        assert fresh.status_code == 200, fresh.text
