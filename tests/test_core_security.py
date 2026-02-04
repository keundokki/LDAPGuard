"""Tests for security utilities."""
import pytest
from api.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_get_password_hash(self):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert verify_password("WrongPassword", hashed) is False

    def test_different_hashes_same_password(self):
        """Test that same password produces different hashes."""
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        # Hashes should be different due to salt
        assert hash1 != hash2
        # But both should verify
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token creation and decoding."""

    def test_create_access_token(self):
        """Test creating access token."""
        data = {"sub": "testuser", "role": "admin"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self):
        """Test decoding valid access token."""
        data = {"sub": "testuser", "role": "admin"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "testuser"
        assert decoded["role"] == "admin"

    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        invalid_token = "invalid.token.here"
        decoded = decode_access_token(invalid_token)
        assert decoded is None

    def test_decode_expired_token(self):
        """Test decoding expired token."""
        from datetime import timedelta
        data = {"sub": "testuser"}
        # Create token that expires in -1 minute (already expired)
        token = create_access_token(data, expires_delta=timedelta(minutes=-1))
        decoded = decode_access_token(token)
        # Should return None for expired token
        assert decoded is None

    def test_token_contains_exp(self):
        """Test that token contains expiration."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded is not None
        assert "exp" in decoded
