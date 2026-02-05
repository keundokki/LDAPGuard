from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserRole(str, Enum):
    ADMIN = "admin"
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
    encrypted: bool = True
    compression_enabled: bool = True


class BackupCreate(BackupBase):
    pass


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
