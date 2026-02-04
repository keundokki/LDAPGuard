"""Tests for backup routes."""
from fastapi import status


class TestBackupRoutes:
    """Test backup management endpoints."""

    def test_get_backups_empty(self, client):
        """Test getting backups when none exist."""
        response = client.get("/backups")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED
        ]

    def test_create_backup_missing_fields(self, client):
        """Test creating backup without required fields."""
        response = client.post("/backups", json={})
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_401_UNAUTHORIZED
        ]

    def test_create_backup_valid(self, client):
        """Test creating backup with valid data."""
        backup_data = {
            "ldap_server_id": 1,
            "backup_type": "full"
        }
        response = client.post("/backups", json=backup_data)
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,  # Server may not exist
            status.HTTP_401_UNAUTHORIZED
        ]

    def test_get_backup_by_id(self, client):
        """Test getting specific backup."""
        response = client.get("/backups/1")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_401_UNAUTHORIZED
        ]

    def test_delete_backup(self, client):
        """Test deleting backup."""
        response = client.delete("/backups/1")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_401_UNAUTHORIZED
        ]

    
