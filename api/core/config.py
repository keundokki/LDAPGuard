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

    # Webhooks
    WEBHOOK_ENABLED: bool = False
    WEBHOOK_URL: Optional[str] = None

    # Metrics
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
