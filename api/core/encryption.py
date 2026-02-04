from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from typing import Optional
import os
import base64

from api.core.config import settings


class AESEncryption:
    """AES-256 encryption for backup data."""
    
    def __init__(self, key: str):
        # Ensure key is 32 bytes for AES-256
        self.key = key.encode()[:32].ljust(32, b'0')
    
    def encrypt(self, data: bytes) -> str:
        """Encrypt data using AES-256-CBC."""
        # Generate random IV
        iv = os.urandom(16)
        
        # Pad data
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        # Encrypt
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Combine IV and encrypted data, then base64 encode
        combined = iv + encrypted_data
        return base64.b64encode(combined).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> bytes:
        """Decrypt data using AES-256-CBC."""
        # Base64 decode
        combined = base64.b64decode(encrypted_data)
        
        # Extract IV and encrypted data
        iv = combined[:16]
        encrypted = combined[16:]
        
        # Decrypt
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted) + decryptor.finalize()
        
        # Unpad
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        return data


def encrypt_data(data: str, key: Optional[str] = None) -> str:
    """Encrypt a UTF-8 string using the configured encryption key."""
    encryption = AESEncryption(key or settings.ENCRYPTION_KEY)
    return encryption.encrypt(data.encode("utf-8"))


def decrypt_data(encrypted_data: str, key: Optional[str] = None) -> str:
    """Decrypt a UTF-8 string using the configured encryption key."""
    encryption = AESEncryption(key or settings.ENCRYPTION_KEY)
    return encryption.decrypt(encrypted_data).decode("utf-8")
