import os
import gzip
import shutil
from datetime import datetime, timedelta
from typing import Optional
from api.core.encryption import AESEncryption
from api.core.config import settings


class BackupService:
    """Service for managing backup operations."""
    
    def __init__(self):
        self.backup_dir = settings.BACKUP_DIR
        self.encryption = AESEncryption(settings.ENCRYPTION_KEY)
    
    def compress_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """Compress a file using gzip."""
        if output_path is None:
            output_path = f"{input_path}.gz"
        
        with open(input_path, 'rb') as f_in:
            with gzip.open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove original file
        os.remove(input_path)
        
        return output_path
    
    def decompress_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """Decompress a gzip file."""
        if output_path is None:
            output_path = input_path.replace('.gz', '')
        
        with gzip.open(input_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        return output_path
    
    def encrypt_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """Encrypt a file using AES-256."""
        if output_path is None:
            output_path = f"{input_path}.enc"
        
        with open(input_path, 'rb') as f:
            data = f.read()
        
        encrypted_data = self.encryption.encrypt(data)
        
        with open(output_path, 'w') as f:
            f.write(encrypted_data)
        
        # Remove original file
        os.remove(input_path)
        
        return output_path
    
    def decrypt_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """Decrypt a file using AES-256."""
        if output_path is None:
            output_path = input_path.replace('.enc', '')
        
        with open(input_path, 'r') as f:
            encrypted_data = f.read()
        
        decrypted_data = self.encryption.decrypt(encrypted_data)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        
        return output_path
    
    def generate_backup_filename(self, server_name: str, backup_type: str) -> str:
        """Generate a unique backup filename."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"{server_name}_{backup_type}_{timestamp}.ldif"
    
    def get_backup_path(self, filename: str) -> str:
        """Get full path for a backup file."""
        return os.path.join(self.backup_dir, filename)
    
    def cleanup_old_backups(self, retention_days: int):
        """Delete backups older than retention period."""
        if not os.path.exists(self.backup_dir):
            return
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        for filename in os.listdir(self.backup_dir):
            file_path = os.path.join(self.backup_dir, filename)
            
            if os.path.isfile(file_path):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_mtime < cutoff_date:
                    os.remove(file_path)
    
    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        return os.path.getsize(file_path)
