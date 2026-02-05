import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class BackupType(str, enum.Enum):
    FULL = "full"
    INCREMENTAL = "incremental"


class BackupStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.VIEWER,
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    ldap_auth = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    backups = relationship("Backup", back_populates="created_by_user")


class LDAPServer(Base):
    __tablename__ = "ldap_servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, default=389, nullable=False)
    use_ssl = Column(Boolean, default=False, nullable=False)
    base_dn = Column(String(500), nullable=False)
    bind_dn = Column(String(500))
    bind_password = Column(String(500))  # Encrypted if password_encrypted=True
    password_encrypted = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    backups = relationship("Backup", back_populates="ldap_server")


class Backup(Base):
    __tablename__ = "backups"

    id = Column(Integer, primary_key=True, index=True)
    ldap_server_id = Column(Integer, ForeignKey("ldap_servers.id"), nullable=False)
    backup_type = Column(
        Enum(BackupType, values_callable=lambda x: [e.value for e in x]),
        default=BackupType.FULL,
        nullable=False,
    )
    status = Column(
        Enum(BackupStatus, values_callable=lambda x: [e.value for e in x]),
        default=BackupStatus.PENDING,
        nullable=False,
    )
    file_path = Column(String(1000))
    file_size = Column(Integer)  # Size in bytes
    encrypted = Column(Boolean, default=True, nullable=False)
    compression_enabled = Column(Boolean, default=True, nullable=False)
    entry_count = Column(Integer)  # Number of LDAP entries backed up
    parent_backup_id = Column(
        Integer, ForeignKey("backups.id")
    )  # For incremental backups
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    ldap_server = relationship("LDAPServer", back_populates="backups")
    created_by_user = relationship("User", back_populates="backups")
    parent_backup = relationship(
        "Backup", remote_side=[id], backref="incremental_backups"
    )


class RestoreJob(Base):
    __tablename__ = "restore_jobs"

    id = Column(Integer, primary_key=True, index=True)
    backup_id = Column(Integer, ForeignKey("backups.id"), nullable=False)
    ldap_server_id = Column(Integer, ForeignKey("ldap_servers.id"), nullable=False)
    status = Column(
        Enum(BackupStatus, values_callable=lambda x: [e.value for e in x]),
        default=BackupStatus.PENDING,
        nullable=False,
    )
    selective_restore = Column(Boolean, default=False, nullable=False)
    restore_filter = Column(Text)  # LDAP filter for selective restore
    point_in_time = Column(DateTime(timezone=True))  # For point-in-time recovery
    entries_restored = Column(Integer)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ScheduledBackup(Base):
    __tablename__ = "scheduled_backups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    ldap_server_id = Column(Integer, ForeignKey("ldap_servers.id"), nullable=False)
    backup_type = Column(
        Enum(BackupType, values_callable=lambda x: [e.value for e in x]),
        default=BackupType.FULL,
        nullable=False,
    )
    cron_expression = Column(String(100), nullable=False)  # Cron schedule
    is_active = Column(Boolean, default=True, nullable=False)
    retention_days = Column(Integer, default=30, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(Integer)
    details = Column(Text)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)  # Hashed API key
    key_prefix = Column(String(10), nullable=False)  # First few chars for display
    permissions = Column(String(255))  # Comma-separated permissions
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True))
    last_used_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
