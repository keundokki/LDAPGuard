from datetime import datetime
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.models.models import Backup, BackupStatus, LDAPServer
from api.schemas.schemas import BackupCreate, BackupResponse

router = APIRouter(prefix="/backups", tags=["Backups"])


@router.get("/", response_model=List[BackupResponse])
async def list_backups(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    """List all backups."""
    result = await db.execute(
        select(Backup).offset(skip).limit(limit).order_by(Backup.created_at.desc())
    )
    backups = result.scalars().all()
    return backups


@router.get("/{backup_id}", response_model=BackupResponse)
async def get_backup(backup_id: int, db: AsyncSession = Depends(get_db)):
    """Get backup by ID."""
    result = await db.execute(select(Backup).where(Backup.id == backup_id))
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found"
        )

    return backup


@router.post("/", response_model=BackupResponse, status_code=status.HTTP_201_CREATED)
async def create_backup(
    backup_data: BackupCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a new backup job."""
    # Verify LDAP server exists
    result = await db.execute(
        select(LDAPServer).where(LDAPServer.id == backup_data.ldap_server_id)
    )
    ldap_server = result.scalar_one_or_none()

    if not ldap_server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="LDAP server not found"
        )

    # Create backup record
    new_backup = Backup(
        ldap_server_id=backup_data.ldap_server_id,
        backup_type=backup_data.backup_type,
        encrypted=backup_data.encrypted,
        compression_enabled=backup_data.compression_enabled,
        status=BackupStatus.PENDING,
        created_by=1,  # TODO: Get from authenticated user
    )

    db.add(new_backup)
    await db.commit()
    await db.refresh(new_backup)

    # Schedule backup task in background
    # background_tasks.add_task(perform_backup, new_backup.id)

    return new_backup


@router.delete("/{backup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup(backup_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a backup."""
    result = await db.execute(select(Backup).where(Backup.id == backup_id))
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found"
        )

    # TODO: Delete backup file from disk

    await db.delete(backup)
    await db.commit()

    return None
