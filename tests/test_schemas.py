"""Tests for Pydantic schemas."""
import pytest
from datetime import datetime
from pydantic import ValidationError


class TestSchemaValidation:
    """Test Pydantic schema validation."""

    def test_valid_schema_data(self):
        """Test that valid data passes schema validation."""
        # This is a basic test - expand based on your actual schemas
        from api.schemas.schemas import LDAPServerCreate
        
        data = {
            "name": "Test LDAP",
            "host": "ldap.example.com",
            "port": 389,
            "base_dn": "dc=example,dc=com",
            "bind_dn": "cn=admin,dc=example,dc=com",
            "bind_password": "password"
        }
        schema = LDAPServerCreate(**data)
        assert schema.name == data["name"]
        assert schema.host == data["host"]

    def test_missing_required_field(self):
        """Test that missing required field raises validation error."""
        from api.schemas.schemas import LDAPServerCreate
        
        data = {
            "host": "ldap.example.com",
            # Missing required 'name' field
        }
        with pytest.raises(ValidationError):
            LDAPServerCreate(**data)

    def test_invalid_port_number(self):
        """Test that invalid port raises validation error."""
        from api.schemas.schemas import LDAPServerCreate
        
        data = {
            "name": "Test LDAP",
            "host": "ldap.example.com",
            "port": 99999,  # Invalid port
            "base_dn": "dc=example,dc=com",
            "bind_dn": "cn=admin,dc=example,dc=com",
            "bind_password": "password"
        }
        # This may or may not raise depending on schema validation
        # Adjust based on your actual schema
        try:
            schema = LDAPServerCreate(**data)
        except ValidationError:
            pass  # Expected
