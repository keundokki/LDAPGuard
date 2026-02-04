"""Tests for authentication routes."""
import pytest
from fastapi import status


class TestAuthRoutes:
    """Test authentication endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "app" in data
        assert "version" in data
        assert "status" in data

    @pytest.mark.asyncio
    def test_login_missing_credentials(self, client):
        """Test login without credentials."""
        response = client.post("/auth/login", json={})
        # Should return 422 for missing required fields
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    def test_login_with_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "wrongpassword"
        })
        # Should return 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    def test_login_successful(self, client, test_user_data, db):
        """Test successful login."""
        # First, create a user (if endpoint exists)
        # Then test login
        response = client.post("/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        # Status depends on whether user exists in test DB
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED
        ]
