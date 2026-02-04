"""Tests for LDAP service."""
from api.services.ldap_service import LDAPService


class TestLDAPService:
    """Test LDAP service functionality."""

    def test_connect_to_ldap_server(self, mock_ldap):
        """Test connecting to LDAP server."""
        service = LDAPService(
            host="ldap.example.com",
            port=389,
            use_ssl=False,
            base_dn="dc=example,dc=com"
        )
        service.connect()
        connection = mock_ldap.return_value
        connection.set_option.assert_called_once()
        connection.simple_bind_s.assert_called()

    def test_search_all_entries(self, mock_ldap):
        """Test searching LDAP directory."""
        mock_ldap.return_value.search_s.return_value = [("cn=admin,dc=example,dc=com", {"cn": [b"admin"]})]
        service = LDAPService(
            host="ldap.example.com",
            port=389,
            use_ssl=False,
            base_dn="dc=example,dc=com"
        )
        service.conn = mock_ldap.return_value
        result = service.search_all_entries("(objectClass=*)")
        assert isinstance(result, list)
        assert len(result) == 1

    def test_test_connection(self, mock_ldap):
        """Test LDAP connection test helper."""
        service = LDAPService(
            host="ldap.example.com",
            port=389,
            use_ssl=False,
            base_dn="dc=example,dc=com"
        )
        assert service.test_connection() is True
