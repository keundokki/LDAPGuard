from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import settings
from api.core.database import get_db
from api.core.security import get_current_user, pwd_hasher
from api.models.models import (
    LDAPServer,
    ScheduledBackup,
    SystemSetting,
    User,
)
from api.schemas.schemas import (
    ConfigurationExport,
    ConfigurationImport,
)

router = APIRouter(prefix="/config", tags=["Configuration"])


@router.get("/export", response_model=ConfigurationExport)
async def export_configuration(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export complete system configuration. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can export configuration",
        )

    # Get all servers
    servers_result = await db.execute(select(LDAPServer))
    servers = servers_result.scalars().all()
    servers_data = [
        {
            "name": s.name,
            "host": s.host,
            "port": s.port,
            "use_ssl": s.use_ssl,
            "base_dn": s.base_dn,
            "bind_dn": s.bind_dn,
            # Don't export bind_password for security
        }
        for s in servers
    ]

    # Get all scheduled backups
    schedules_result = await db.execute(select(ScheduledBackup))
    schedules = schedules_result.scalars().all()
    schedules_data = [
        {
            "name": s.name,
            "ldap_server_id": s.ldap_server_id,
            "backup_type": s.backup_type.value,
            "cron_expression": s.cron_expression,
            "retention_days": s.retention_days,
            "is_active": s.is_active,
        }
        for s in schedules
    ]

    # Get all users (excluding passwords)
    users_result = await db.execute(select(User))
    users = users_result.scalars().all()
    users_data = [
        {
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "is_active": u.is_active,
        }
        for u in users
    ]

    return ConfigurationExport(
        servers=servers_data, scheduled_backups=schedules_data, users=users_data
    )


@router.post("/import")
async def import_configuration(
    config: ConfigurationImport,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import system configuration. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can import configuration",
        )

    imported_counts = {"servers": 0, "scheduled_backups": 0, "users": 0, "errors": []}

    # Import servers
    if config.servers:
        for server_data in config.servers:
            try:
                # Check if server already exists
                result = await db.execute(
                    select(LDAPServer).where(LDAPServer.name == server_data.get("name"))
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    server = LDAPServer(
                        name=server_data.get("name"),
                        host=server_data.get("host"),
                        port=server_data.get("port", 389),
                        use_ssl=server_data.get("use_ssl", False),
                        base_dn=server_data.get("base_dn"),
                        bind_dn=server_data.get("bind_dn"),
                    )
                    db.add(server)
                    imported_counts["servers"] += 1
            except Exception as e:
                imported_counts["errors"].append(f"Server import error: {str(e)}")

    # Commit servers first so we have IDs for scheduled backups
    await db.commit()

    # Import scheduled backups
    if config.scheduled_backups:
        for schedule_data in config.scheduled_backups:
            try:
                # Verify server exists
                server_id = schedule_data.get("ldap_server_id")
                if server_id:
                    result = await db.execute(
                        select(LDAPServer).where(LDAPServer.id == server_id)
                    )
                    server = result.scalar_one_or_none()

                    if server:
                        # Check if schedule already exists
                        result = await db.execute(
                            select(ScheduledBackup).where(
                                ScheduledBackup.name == schedule_data.get("name")
                            )
                        )
                        existing = result.scalar_one_or_none()

                        if not existing:
                            schedule = ScheduledBackup(
                                name=schedule_data.get("name"),
                                ldap_server_id=server_id,
                                backup_type=schedule_data.get("backup_type", "full"),
                                cron_expression=schedule_data.get("cron_expression"),
                                retention_days=schedule_data.get("retention_days", 30),
                                is_active=schedule_data.get("is_active", True),
                            )
                            db.add(schedule)
                            imported_counts["scheduled_backups"] += 1
            except Exception as e:
                imported_counts["errors"].append(f"Schedule import error: {str(e)}")

    # Import users
    if config.users:
        for user_data in config.users:
            try:
                # Check if user already exists
                result = await db.execute(
                    select(User).where(User.username == user_data.get("username"))
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    # Create user with a default password (must be changed)
                    default_password = "changeme123"
                    hashed_password = pwd_hasher.hash(default_password)

                    user = User(
                        username=user_data.get("username"),
                        email=user_data.get("email"),
                        full_name=user_data.get("full_name"),
                        role=user_data.get("role", "viewer"),
                        is_active=user_data.get("is_active", True),
                        hashed_password=hashed_password,
                    )
                    db.add(user)
                    imported_counts["users"] += 1
            except Exception as e:
                imported_counts["errors"].append(f"User import error: {str(e)}")

    await db.commit()

    return {
        "message": "Configuration import completed",
        "imported": imported_counts,
    }


@router.get("/features")
async def get_enabled_features(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get enabled feature flags (e.g., cloud storage)."""
    import logging
    logger = logging.getLogger(__name__)
    
    # Try to get S3 enabled setting from database
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == "s3_enabled")
    )
    s3_setting = result.scalar_one_or_none()
    
    logger.info(f"S3 setting from DB: {s3_setting}")
    if s3_setting:
        logger.info(f"S3 setting value: {s3_setting.value}, type: {type(s3_setting.value)}")
    
    # Check if S3 is enabled in database, fall back to environment variable
    s3_enabled = False
    if s3_setting:
        s3_enabled = s3_setting.value.lower() == "true"
        logger.info(f"S3 enabled (from DB): {s3_enabled}")
    else:
        s3_enabled = settings.S3_ENABLED
        logger.info(f"S3 enabled (from env): {s3_enabled}")
    
    return {
        "cloud_storage_enabled": s3_enabled,
        "cloud_provider": "s3" if s3_enabled else None,
    }
