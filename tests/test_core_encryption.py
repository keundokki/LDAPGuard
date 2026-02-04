"""Tests for encryption utilities."""
import pytest
from api.core.encryption import encrypt_data, decrypt_data


class TestEncryption:
    """Test encryption and decryption."""

    def test_encrypt_data(self):
        """Test encrypting data."""
        plaintext = "sensitive data"
        encrypted = encrypt_data(plaintext)
        assert encrypted != plaintext
        assert len(encrypted) > 0

    def test_decrypt_data(self):
        """Test decrypting data."""
        plaintext = "sensitive data"
        encrypted = encrypt_data(plaintext)
        decrypted = decrypt_data(encrypted)
        assert decrypted == plaintext

    def test_encrypt_empty_string(self):
        """Test encrypting empty string."""
        plaintext = ""
        encrypted = encrypt_data(plaintext)
        decrypted = decrypt_data(encrypted)
        assert decrypted == plaintext

    def test_encrypt_long_data(self):
        """Test encrypting long data."""
        plaintext = "x" * 10000
        encrypted = encrypt_data(plaintext)
        decrypted = decrypt_data(encrypted)
        assert decrypted == plaintext

    def test_encrypt_special_characters(self):
        """Test encrypting special characters."""
        plaintext = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        encrypted = encrypt_data(plaintext)
        decrypted = decrypt_data(encrypted)
        assert decrypted == plaintext

    def test_different_encryptions_same_data(self):
        """Test that same data produces different ciphertexts."""
        plaintext = "test data"
        encrypted1 = encrypt_data(plaintext)
        encrypted2 = encrypt_data(plaintext)
        # Should be different due to IV/nonce
        assert encrypted1 != encrypted2
        # But both should decrypt to same plaintext
        assert decrypt_data(encrypted1) == plaintext
        assert decrypt_data(encrypted2) == plaintext

    def test_decrypt_invalid_data(self):
        """Test decrypting invalid data."""
        with pytest.raises(Exception):
            decrypt_data("invalid_encrypted_data")
