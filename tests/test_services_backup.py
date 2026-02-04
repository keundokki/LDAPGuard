"""Tests for backup service."""
from api.services.backup_service import BackupService


class TestBackupService:
    """Test backup service functionality."""

    def test_generate_backup_filename(self):
        """Test backup filename generation."""
        service = BackupService()
        filename = service.generate_backup_filename("server1", "full")
        assert filename.startswith("server1_full_")
        assert filename.endswith(".ldif")

    def test_compress_and_decompress_file(self, tmp_path):
        """Test gzip compression and decompression."""
        service = BackupService()
        input_path = tmp_path / "backup.ldif"
        input_path.write_text("test data", encoding="utf-8")

        compressed_path = service.compress_file(str(input_path))
        assert compressed_path.endswith(".gz")

        decompressed_path = service.decompress_file(compressed_path)
        assert decompressed_path.endswith(".ldif")
        assert (tmp_path / "backup.ldif").read_text(encoding="utf-8") == "test data"

    def test_encrypt_and_decrypt_file(self, tmp_path):
        """Test file encryption and decryption."""
        service = BackupService()
        input_path = tmp_path / "backup.ldif"
        input_path.write_text("secret data", encoding="utf-8")

        encrypted_path = service.encrypt_file(str(input_path))
        assert encrypted_path.endswith(".enc")

        decrypted_path = service.decrypt_file(encrypted_path)
        assert decrypted_path.endswith(".ldif")
        assert (tmp_path / "backup.ldif").read_text(encoding="utf-8") == "secret data"
