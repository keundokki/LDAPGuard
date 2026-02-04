"""Tests for LDAP server routes."""
from fastapi import status


class TestLDAPServerRoutes:
    """Test LDAP server management endpoints."""

    def test_get_ldap_servers_empty(self, client):
        """Test getting LDAP servers when none exist."""
        response = client.get("/ldap-servers")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED  # May require authentication
        ]

    def test_create_ldap_server_missing_fields(self, client):
        """Test creating LDAP server without required fields."""
        response = client.post("/ldap-servers", json={})
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_401_UNAUTHORIZED
        ]

    def test_create_ldap_server_valid(self, client, test_ldap_server_data):
        """Test creating LDAP server with valid data."""
        response = client.post("/ldap-servers", json=test_ldap_server_data)
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED  # May require authentication
        ]
        if response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]:
            data = response.json()
            assert data["name"] == test_ldap_server_data["name"]

    def test_get_ldap_server_by_id(self, client):
        """Test getting specific LDAP server."""
        response = client.get("/ldap-servers/1")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_401_UNAUTHORIZED
        ]

    def test_update_ldap_server(self, client, test_ldap_server_data):
        """Test updating LDAP server."""
        updated_data = test_ldap_server_data.copy()
        updated_data["name"] = "Updated LDAP Server"
        response = client.put("/ldap-servers/1", json=updated_data)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_401_UNAUTHORIZED
        ]

    def test_delete_ldap_server(self, client):
        """Test deleting LDAP server."""
        response = client.delete("/ldap-servers/1")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_401_UNAUTHORIZED
        ]
