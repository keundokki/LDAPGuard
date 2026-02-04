"""Tests for restore routes."""
import pytest
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
            "restore_type": "full",
            "dry_run": True
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

    def test_cancel_restore(self, client):
        """Test canceling restore operation."""
        response = client.post("/restores/1/cancel")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_401_UNAUTHORIZED
        ]

    def test_get_restore_preview(self, client):
        """Test getting restore preview."""
        response = client.get("/restores/1/preview")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_401_UNAUTHORIZED
        ]

    def test_get_restore_status(self, client):
        """Test getting restore status."""
        response = client.get("/restores/status")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED
        ]
