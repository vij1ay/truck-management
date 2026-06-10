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
