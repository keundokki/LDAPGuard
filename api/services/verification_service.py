import gzip
import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple

from api.core.config import settings
from api.core.encryption import AESEncryption

logger = logging.getLogger(__name__)


class VerificationService:
    """Service for backup file verification and integrity checks."""

    def __init__(self):
        self.checksum_algorithm = settings.BACKUP_CHECKSUM_ALGORITHM

    def calculate_checksum(self, file_path: str, algorithm: str = None) -> str:
        """Calculate checksum of a file.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm (sha256, sha512, md5)
            
        Returns:
            Hexadecimal checksum string
        """
        if algorithm is None:
            algorithm = self.checksum_algorithm

        # Select hash algorithm
        if algorithm == "sha256":
            hasher = hashlib.sha256()
        elif algorithm == "sha512":
            hasher = hashlib.sha512()
        elif algorithm == "md5":
            hasher = hashlib.md5()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

        # Calculate hash in chunks to handle large files
        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)  # 8KB chunks
                    if not chunk:
                        break
                    hasher.update(chunk)
            
            checksum = hasher.hexdigest()
            logger.info(f"Calculated {algorithm} checksum for {file_path}: {checksum}")
            return checksum
            
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {str(e)}")
            raise

    def verify_checksum(
        self, file_path: str, expected_checksum: str, algorithm: str = None
    ) -> bool:
        """Verify file checksum matches expected value.
        
        Args:
            file_path: Path to the file
            expected_checksum: Expected checksum value
            algorithm: Hash algorithm to use
            
        Returns:
            True if checksum matches, False otherwise
        """
        try:
            actual_checksum = self.calculate_checksum(file_path, algorithm)
            matches = actual_checksum == expected_checksum
            
            if matches:
                logger.info(f"Checksum verification passed for {file_path}")
            else:
                logger.warning(
                    f"Checksum mismatch for {file_path}: "
                    f"expected {expected_checksum}, got {actual_checksum}"
                )
            
            return matches
            
        except Exception as e:
            logger.error(f"Checksum verification failed for {file_path}: {str(e)}")
            return False

    def validate_ldif_syntax(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate LDIF file syntax.
        
        Args:
            file_path: Path to the LDIF file (may be encrypted and/or compressed)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(file_path)
            
            # Handle encrypted files first
            if path.suffix == '.enc':
                # Decrypt the file content
                with open(file_path, 'r') as f:
                    encrypted_data = f.read()
                
                encryption = AESEncryption(settings.ENCRYPTION_KEY)
                decrypted_data = encryption.decrypt(encrypted_data)
                
                # Check if decrypted data is compressed
                if path.stem.endswith('.gz'):
                    # Decompress the decrypted data
                    content = gzip.decompress(decrypted_data).decode('utf-8')[:10000]
                else:
                    # Just decode the decrypted data
                    content = decrypted_data.decode('utf-8')[:10000]
                    
            # Handle compressed but not encrypted files
            elif path.suffix == '.gz':
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    content = f.read(10000)  # Read first 10KB for validation
            # Plain LDIF file
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(10000)
            
            # Basic LDIF validation
            lines = content.split('\n')
            
            # Check for LDIF structure
            has_dn = False
            for line in lines:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Check for DN entries
                if line.startswith('dn:'):
                    has_dn = True
                    
                # Check for attribute format (key: value or key:: base64value)
                if ':' in line and not line.startswith('dn:'):
                    parts = line.split(':', 1)
                    if len(parts) != 2:
                        return False, f"Invalid attribute format: {line}"
            
            if not has_dn:
                return False, "No DN entries found in LDIF file"
            
            logger.info(f"LDIF syntax validation passed for {file_path}")
            return True, None
            
        except UnicodeDecodeError as e:
            error = f"File encoding error: {str(e)}"
            logger.error(f"LDIF validation failed for {file_path}: {error}")
            return False, error
            
        except Exception as e:
            error = f"Validation error: {str(e)}"
            logger.error(f"LDIF validation failed for {file_path}: {error}")
            return False, error

    def verify_file_exists(self, file_path: str) -> bool:
        """Verify backup file exists and is accessible.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file exists and is readable
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                logger.warning(f"File does not exist: {file_path}")
                return False
            
            if not path.is_file():
                logger.warning(f"Path is not a file: {file_path}")
                return False
            
            # Try to open file
            with open(file_path, 'rb') as f:
                f.read(1)  # Read one byte to verify accessibility
            
            return True
            
        except Exception as e:
            logger.error(f"File accessibility check failed for {file_path}: {str(e)}")
            return False

    def verify_file_size(
        self, file_path: str, expected_size: Optional[int] = None
    ) -> Tuple[bool, int]:
        """Verify file size.
        
        Args:
            file_path: Path to the file
            expected_size: Expected file size in bytes (optional)
            
        Returns:
            Tuple of (size_matches, actual_size)
        """
        try:
            actual_size = Path(file_path).stat().st_size
            
            if expected_size is None:
                return True, actual_size
            
            matches = actual_size == expected_size
            
            if not matches:
                logger.warning(
                    f"File size mismatch for {file_path}: "
                    f"expected {expected_size} bytes, got {actual_size} bytes"
                )
            
            return matches, actual_size
            
        except Exception as e:
            logger.error(f"File size check failed for {file_path}: {str(e)}")
            return False, 0

    def comprehensive_verification(
        self,
        file_path: str,
        expected_checksum: Optional[str] = None,
        expected_size: Optional[int] = None,
        validate_syntax: bool = True,
    ) -> Tuple[bool, str]:
        """Perform comprehensive backup verification.
        
        Args:
            file_path: Path to the backup file
            expected_checksum: Expected checksum (if known)
            expected_size: Expected file size (if known)
            validate_syntax: Whether to validate LDIF syntax
            
        Returns:
            Tuple of (is_valid, status_message)
        """
        errors = []
        
        # 1. Check file exists
        if not self.verify_file_exists(file_path):
            return False, "File does not exist or is not accessible"
        
        # 2. Verify file size
        if expected_size is not None:
            size_ok, actual_size = self.verify_file_size(file_path, expected_size)
            if not size_ok:
                errors.append(
                    f"Size mismatch: expected {expected_size}, got {actual_size}"
                )
        
        # 3. Verify checksum
        if expected_checksum:
            if not self.verify_checksum(file_path, expected_checksum):
                errors.append("Checksum verification failed")
        
        # 4. Validate LDIF syntax
        if validate_syntax:
            syntax_ok, syntax_error = self.validate_ldif_syntax(file_path)
            if not syntax_ok:
                errors.append(f"LDIF syntax error: {syntax_error}")
        
        if errors:
            status = "Verification failed: " + "; ".join(errors)
            logger.error(f"Comprehensive verification failed for {file_path}: {status}")
            return False, status
        
        logger.info(f"Comprehensive verification passed for {file_path}")
        return True, "All verification checks passed"
