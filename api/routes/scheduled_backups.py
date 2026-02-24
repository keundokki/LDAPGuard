from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from croniter import croniter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.core.security import get_current_user
from api.models.models import Backup, BackupStatus, LDAPServer, ScheduledBackup
from api.schemas.schemas import (
    BackupResponse,
    ScheduledBackupCreate,
    ScheduledBackupResponse,
    ScheduledBackupUpdate,
)

router = APIRouter(prefix="/scheduled-backups", tags=["Scheduled Backups"])


def _enrich_scheduled_backup(schedule: ScheduledBackup) -> dict:
    """Add next_run and previous_run computed fields to a scheduled backup."""
    data = {
        "id": schedule.id,
        "name": schedule.name,
        "ldap_server_id": schedule.ldap_server_id,
        "backup_type": schedule.backup_type.value if hasattr(
            schedule.backup_type,
            'value') else schedule.backup_type,
        "cron_expression": schedule.cron_expression,
        "retention_days": schedule.retention_days,
        "is_active": schedule.is_active,
        "created_at": schedule.created_at,
        "updated_at": schedule.updated_at,
        "next_run": None,
        "previous_run": None,
    }

    try:
        cron = croniter(schedule.cron_expression, datetime.now())
        data["next_run"] = cron.get_next(datetime)
        cron = croniter(schedule.cron_expression, datetime.now())
        data["previous_run"] = cron.get_prev(datetime)
    except Exception:
        pass

    return data


@router.get("/", response_model=List[ScheduledBackupResponse])
async def list_scheduled_backups(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    """List all scheduled backups."""
    result = await db.execute(
        select(ScheduledBackup)
        .offset(skip)
        .limit(limit)
        .order_by(ScheduledBackup.created_at.desc())
    )
    scheduled = result.scalars().all()
    return [_enrich_scheduled_backup(s) for s in scheduled]


@router.get("/{schedule_id}", response_model=ScheduledBackupResponse)
async def get_scheduled_backup(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """Get scheduled backup by ID."""
    result = await db.execute(
        select(ScheduledBackup).where(ScheduledBackup.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled backup not found",
        )

    return _enrich_scheduled_backup(schedule)


@router.post(
    "/", response_model=ScheduledBackupResponse, status_code=status.HTTP_201_CREATED
)
async def create_scheduled_backup(
    schedule_data: ScheduledBackupCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new scheduled backup."""
    # Only admins and operators can create scheduled backups
    if current_user.role.value not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and operators can create scheduled backups",
        )

    if not croniter.is_valid(schedule_data.cron_expression):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid cron expression",
        )
    result = await db.execute(
        select(LDAPServer).where(LDAPServer.id == schedule_data.ldap_server_id)
    )
    ldap_server = result.scalar_one_or_none()

    if not ldap_server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="LDAP server not found"
        )

    new_schedule = ScheduledBackup(**schedule_data.model_dump())
    db.add(new_schedule)
    await db.commit()
    await db.refresh(new_schedule)

    return _enrich_scheduled_backup(new_schedule)


@router.put("/{schedule_id}", response_model=ScheduledBackupResponse)
async def update_scheduled_backup(
    schedule_id: int,
    schedule_data: ScheduledBackupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update scheduled backup."""
    # Only admins and operators can update scheduled backups
    if current_user.role.value not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and operators can update scheduled backups",
        )

    if schedule_data.cron_expression and not croniter.is_valid(
        schedule_data.cron_expression
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid cron expression",
        )
    result = await db.execute(
        select(ScheduledBackup).where(ScheduledBackup.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled backup not found",
        )

    for field, value in schedule_data.model_dump(exclude_unset=True).items():
        setattr(schedule, field, value)

    await db.commit()
    await db.refresh(schedule)

    return _enrich_scheduled_backup(schedule)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_backup(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete scheduled backup."""
    # Only admins and operators can delete scheduled backups
    if current_user.role.value not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and operators can delete scheduled backups",
        )

    result = await db.execute(
        select(ScheduledBackup).where(ScheduledBackup.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled backup not found",
        )

    await db.delete(schedule)
    await db.commit()

    return None


@router.post("/{schedule_id}/run", response_model=BackupResponse)
async def run_scheduled_backup(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Run a scheduled backup immediately."""
    result = await db.execute(
        select(ScheduledBackup).where(ScheduledBackup.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled backup not found",
        )

    result = await db.execute(
        select(LDAPServer).where(LDAPServer.id == schedule.ldap_server_id)
    )
    ldap_server = result.scalar_one_or_none()

    if not ldap_server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="LDAP server not found"
        )

    new_backup = Backup(
        ldap_server_id=schedule.ldap_server_id,
        backup_type=schedule.backup_type,
        encrypted=True,
        compression_enabled=True,
        status=BackupStatus.PENDING,
        created_by=current_user.id,
    )

    db.add(new_backup)
    await db.commit()
    await db.refresh(new_backup)

    return new_backup
