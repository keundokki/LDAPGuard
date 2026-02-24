import re
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_version() -> str:
    """Read version from api/__init__.py to avoid circular imports."""
    try:
        with open(__file__.replace("core/config.py", "__init__.py")) as f:
            match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', f.read())
            if match:
                return match.group(1)
    except Exception:
        pass
    return "1.0.0"


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "LDAPGuard"
    APP_VERSION: str = _get_version()
    APP_URL: str = "http://localhost:3000"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://ldapguard:changeme@postgres:5432/ldapguard"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ENCRYPTION_KEY: str = "your-encryption-key-32-bytes-min"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # LDAP
    LDAP_SERVER: Optional[str] = None
    LDAP_PORT: int = 389
    LDAP_USE_SSL: bool = False
    LDAP_BASE_DN: Optional[str] = None
    LDAP_BIND_DN: Optional[str] = None
    LDAP_BIND_PASSWORD: Optional[str] = None

    # Backup
    BACKUP_DIR: str = "/app/backups"
    BACKUP_RETENTION_DAYS: int = 30
    INCREMENTAL_BACKUP_ENABLED: bool = True

    # Backup Retry Logic
    BACKUP_MAX_RETRIES: int = 3
    BACKUP_RETRY_DELAY: int = 300  # Initial retry delay in seconds (5 minutes)
    BACKUP_RETRY_BACKOFF: float = 2.0  # Exponential backoff multiplier
    BACKUP_RETRY_ENABLED: bool = True

    # Backup Verification
    BACKUP_VERIFY_ON_COMPLETION: bool = True  # Verify immediately after backup
    BACKUP_VERIFY_BEFORE_RESTORE: bool = True  # Verify before restore
    BACKUP_CHECKSUM_ALGORITHM: str = "sha256"  # sha256, sha512, md5

    # S3 Cloud Storage
    S3_ENABLED: bool = False
    S3_BUCKET_NAME: Optional[str] = None
    S3_ACCESS_KEY_ID: Optional[str] = None
    S3_SECRET_ACCESS_KEY: Optional[str] = None
    S3_REGION: str = "us-east-1"
    S3_ENDPOINT_URL: Optional[str] = None  # For MinIO, Backblaze, etc.
    S3_STORAGE_CLASS: str = "STANDARD"  # STANDARD, GLACIER, INTELLIGENT_TIERING, etc.
    S3_AUTO_UPLOAD: bool = True  # Automatically upload backups after creation
    S3_AUTO_DELETE_LOCAL: bool = False  # Delete local backup after successful upload
    S3_KEEP_LAST_LOCAL: int = 3  # Keep last N local backups even if S3_AUTO_DELETE_LOCAL=true  # noqa: E501

    # CORS
    CORS_ALLOWED_ORIGINS: Optional[str] = None

    # Webhooks
    WEBHOOK_ENABLED: bool = False
    WEBHOOK_URL: Optional[str] = None

    # Email Notifications
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    EMAIL_FROM: str = "noreply@ldapguard.local"
    EMAIL_FROM_NAME: str = "LDAPGuard"

    # Metrics
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
