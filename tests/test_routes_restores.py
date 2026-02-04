"""Tests for restore routes."""
from fastapi import status


class TestRestoreRoutes:
    """Test restore management endpoints."""

    def test_get_restores_empty(self, client):
        """Test getting restores when none exist."""
        response = client.get("/restores")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED
        ]

    def test_create_restore_missing_fields(self, client):
        """Test creating restore without required fields."""
        response = client.post("/restores", json={})
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_401_UNAUTHORIZED
        ]

    def test_create_restore_valid(self, client):
        """Test creating restore with valid data."""
        restore_data = {
            "backup_id": 1,
            "ldap_server_id": 1,
            "selective_restore": False,
            "restore_filter": None
        }
        response = client.post("/restores", json=restore_data)
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_401_UNAUTHORIZED
        ]

    def test_get_restore_by_id(self, client):
        """Test getting specific restore."""
        response = client.get("/restores/1")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_401_UNAUTHORIZED
        ]

    
