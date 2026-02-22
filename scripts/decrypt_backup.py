#!/usr/bin/env python3
"""
LDAPGuard Backup Decryption Tool
Decrypt backups without running the full LDAPGuard application

Usage:
    python3 decrypt_backup.py <encrypted_file> <encryption_key> [output_file]

Example:
    python3 decrypt_backup.py backup.ldif.gz.enc 'your-encryption-key-32-bytes-min'
"""

import base64
import gzip
import sys
from pathlib import Path
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class AESDecryption:
    """AES-256 decryption (matches LDAPGuard's encryption)."""

    def __init__(self, key: str):
        # Ensure key is 32 bytes for AES-256 (same as LDAPGuard)
        self.key = key.encode()[:32].ljust(32, b"0")

    def decrypt(self, encrypted_data: str) -> bytes:
        """Decrypt data using AES-256-CBC."""
        # Base64 decode
        combined = base64.b64decode(encrypted_data)

        # Extract IV (first 16 bytes) and encrypted data
        iv = combined[:16]
        encrypted = combined[16:]

        # Decrypt
        cipher = Cipher(
            algorithms.AES(self.key), modes.CBC(iv), backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted) + decryptor.finalize()

        # Unpad
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()

        return data


def decrypt_backup(encrypted_file: str, encryption_key: str, output_file: str = None):
    """Decrypt an LDAPGuard backup file."""
    
    encrypted_path = Path(encrypted_file)
    
    if not encrypted_path.exists():
        print(f"Error: File not found: {encrypted_file}")
        sys.exit(1)
    
    # Determine output filename
    if output_file is None:
        # Remove .enc extension
        if encrypted_path.suffix == '.enc':
            output_file = str(encrypted_path.with_suffix(''))
        else:
            output_file = str(encrypted_path) + '.decrypted'
    
    print(f"Decrypting: {encrypted_file}")
    print(f"Output to: {output_file}")
    
    # Read encrypted data
    with open(encrypted_file, 'r') as f:
        encrypted_data = f.read()
    
    # Decrypt
    decryptor = AESDecryption(encryption_key)
    decrypted_data = decryptor.decrypt(encrypted_data)
    
    # Write decrypted data (still compressed)
    with open(output_file, 'wb') as f:
        f.write(decrypted_data)
    
    print(f"✓ Decryption complete: {output_file}")
    
    # If it's a .gz file, offer to decompress
    if output_file.endswith('.gz'):
        decompress_choice = input("Decompress the .gz file? (y/n): ").lower()
        if decompress_choice == 'y':
            decompressed_file = output_file[:-3]  # Remove .gz
            print(f"Decompressing to: {decompressed_file}")
            
            with gzip.open(output_file, 'rb') as f_in:
                with open(decompressed_file, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            print(f"✓ Decompression complete: {decompressed_file}")
            print(f"\nFinal LDIF file: {decompressed_file}")
            return decompressed_file
    
    return output_file


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    encrypted_file = sys.argv[1]
    encryption_key = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        result_file = decrypt_backup(encrypted_file, encryption_key, output_file)
        print(f"\n✓ Success! Decrypted file: {result_file}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
