from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, EmailStr


class UserRole(str, Enum):
    ADMIN = "admin"
    BACKUP_ADMIN = "backup_admin"
    SECURITY_ADMIN = "security_admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class BackupType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"


class BackupStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class BackupCategory(str, Enum):
    DIRECTORY = "directory"
    SCHEMA = "schema"
    CONFIG = "config"
    ACL = "acl"
    CERTIFICATES = "certificates"
    FULL_SERVER = "full_server"


# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER
    ldap_auth: bool = False


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class ChangePassword(BaseModel):
    old_password: str
    new_password: str


class AdminResetPassword(BaseModel):
    new_password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# LDAP Server schemas
class LDAPServerBase(BaseModel):
    name: str
    host: str
    port: int = 389
    use_ssl: bool = False
    base_dn: str
    bind_dn: Optional[str] = None
    bind_password: Optional[str] = None
    description: Optional[str] = None


class LDAPServerCreate(LDAPServerBase):
    pass


class LDAPServerUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    use_ssl: Optional[bool] = None
    base_dn: Optional[str] = None
    bind_dn: Optional[str] = None
    bind_password: Optional[str] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class LDAPServerResponse(BaseModel):
    id: int
    name: str
    host: str
    port: int
    use_ssl: bool
    base_dn: str
    is_active: bool
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Backup schemas
class BackupBase(BaseModel):
    ldap_server_id: int
    backup_type: BackupType = BackupType.FULL
    category: BackupCategory = BackupCategory.DIRECTORY
    encrypted: bool = True
    compression_enabled: bool = True


class BackupCreate(BackupBase):
    parent_backup_id: Optional[int] = None  # For incremental backups


class BackupResponse(BackupBase):
    id: int
    status: BackupStatus
    file_path: Optional[str]
    file_size: Optional[int]
    entry_count: Optional[int]
    parent_backup_id: Optional[int]
    created_by: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None
    checksum: Optional[str] = None
    checksum_algorithm: Optional[str] = "sha256"
    verified_at: Optional[datetime] = None
    verification_status: Optional[str] = None
    cloud_uploaded: bool = False
    cloud_storage_path: Optional[str] = None
    cloud_uploaded_at: Optional[datetime] = None
    cloud_provider: Optional[str] = None
    cloud_storage_class: Optional[str] = None

    class Config:
        from_attributes = True


# Restore Job schemas
class RestoreJobBase(BaseModel):
    backup_id: int
    ldap_server_id: int
    selective_restore: bool = False
    restore_filter: Optional[str] = None
    point_in_time: Optional[datetime] = None


class RestoreJobCreate(RestoreJobBase):
    pass


class RestoreJobResponse(RestoreJobBase):
    id: int
    status: BackupStatus
    entries_restored: Optional[int]
    created_by: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# Scheduled Backup schemas
class ScheduledBackupBase(BaseModel):
    name: str
    ldap_server_id: int
    backup_type: BackupType = BackupType.FULL
    cron_expression: str
    retention_days: int = 30


class ScheduledBackupCreate(ScheduledBackupBase):
    pass


class ScheduledBackupUpdate(BaseModel):
    name: Optional[str] = None
    backup_type: Optional[BackupType] = None
    cron_expression: Optional[str] = None
    is_active: Optional[bool] = None
    retention_days: Optional[int] = None


class ScheduledBackupResponse(ScheduledBackupBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    next_run: Optional[datetime] = None
    previous_run: Optional[datetime] = None

    class Config:
        from_attributes = True


# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# Audit log schemas
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str] = None
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    details: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# API Key schemas
class APIKeyCreate(BaseModel):
    name: str
    permissions: Optional[str] = "read,write"
    expires_days: Optional[int] = None  # None means no expiration


class APIKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    permissions: Optional[str]
    created_by: int
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyWithSecret(APIKeyResponse):
    """Response with the actual API key - only returned on creation"""

    api_key: str


# System settings schemas
class SystemSettingUpdate(BaseModel):
    key: str
    value: str


class SystemSettingResponse(BaseModel):
    id: int
    key: str
    value: str
    updated_at: datetime

    class Config:
        from_attributes = True


# Configuration import/export schemas
class ConfigurationExport(BaseModel):
    servers: list
    scheduled_backups: list
    users: list


class ConfigurationImport(BaseModel):
    servers: Optional[list] = []
    scheduled_backups: Optional[list] = []
    users: Optional[list] = []


# Cloud storage schemas
class CloudStorageUploadRequest(BaseModel):
    """Request model for cloud storage upload (currently no parameters needed)."""
    pass


class CloudStorageUploadResponse(BaseModel):
    backup_id: int
    success: bool
    message: str
    cloud_storage_path: str
    cloud_provider: str
    cloud_storage_class: str
    uploaded_at: datetime


class CloudStorageInfo(BaseModel):
    key: str
    size: int
    last_modified: str
    storage_class: str


class CloudStorageTestResponse(BaseModel):
    success: bool
    message: str
    enabled: bool
    provider: Optional[str] = None
    bucket: Optional[str] = None
    region: Optional[str] = None
    error: Optional[str] = None


# Backup Catalog & Search schemas
class BackupSearchParams(BaseModel):
    """Advanced search and filter parameters for backups."""
    search: Optional[str] = None  # Search in server name, filename
    server_id: Optional[int] = None
    status: Optional[str] = None
    backup_type: Optional[str] = None
    category: Optional[str] = None
    verification_status: Optional[str] = None
    cloud_uploaded: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    completed_after: Optional[datetime] = None
    completed_before: Optional[datetime] = None
    min_size: Optional[int] = None  # In bytes
    max_size: Optional[int] = None  # In bytes
    min_entries: Optional[int] = None
    max_entries: Optional[int] = None
    sort_by: Optional[str] = "created_at"  # created_at, size, entry_count, completed_at
    sort_order: Optional[str] = "desc"  # asc, desc
    skip: int = 0
    limit: int = 100


class BackupCatalogStats(BaseModel):
    """Statistics for backup catalog."""
    total_backups: int
    total_size: int
    total_entries: int
    backups_by_status: Dict[str, int]
    backups_by_type: Dict[str, int]
    backups_by_category: Dict[str, int]
    backups_by_server: Dict[str, int]
    verified_backups: int
    cloud_uploaded_backups: int
    failed_backups: int
    oldest_backup: Optional[datetime] = None
    newest_backup: Optional[datetime] = None
    average_backup_size: float
    largest_backup_size: int
    smallest_backup_size: int


class BackupExportResponse(BaseModel):
    """Response for backup export."""
    format: str
    total_records: int
    data: str  # CSV or JSON string
    filename: str
