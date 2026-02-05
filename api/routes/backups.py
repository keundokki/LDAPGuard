import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import settings
from api.core.database import get_db
from api.core.security import get_current_user
from api.models.models import Backup, BackupStatus, BackupType, LDAPServer
from api.schemas.schemas import BackupCreate, BackupResponse

router = APIRouter(prefix="/backups", tags=["Backups"])
logger = logging.getLogger(__name__)


class BatchDeleteRequest(BaseModel):
    """Request model for batch deletion."""

    backup_ids: List[int]


@router.get("/", response_model=List[BackupResponse])
async def list_backups(
    skip: int = 0,
    limit: int = 100,
    server_id: Optional[int] = Query(None, description="Filter by server ID"),
    status: Optional[BackupStatus] = Query(None, description="Filter by status"),
    backup_type: Optional[BackupType] = Query(None, description="Filter by type"),
    search: Optional[str] = Query(None, description="Search in server name"),
    db: AsyncSession = Depends(get_db),
):
    """List all backups with optional filtering."""
    query = select(Backup)
    
    # Apply filters
    if server_id:
        query = query.where(Backup.server_id == server_id)
    if status:
        query = query.where(Backup.status == status)
    if backup_type:
        query = query.where(Backup.backup_type == backup_type)
    if search:
        # Join with LDAPServer to search by server name
        query = query.join(LDAPServer).where(
            or_(
                LDAPServer.name.ilike(f"%{search}%"),
                LDAPServer.host.ilike(f"%{search}%")
            )
        )
    
    query = query.offset(skip).limit(limit).order_by(Backup.created_at.desc())
    
    result = await db.execute(query)
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
    current_user=Depends(get_current_user),
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
        created_by=current_user.id,
    )

    db.add(new_backup)
    await db.commit()
    await db.refresh(new_backup)

    # Schedule backup task in background
    # background_tasks.add_task(perform_backup, new_backup.id)

    return new_backup


@router.delete("/{backup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Delete a backup."""
    result = await db.execute(select(Backup).where(Backup.id == backup_id))
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found"
        )

    # Delete backup file from disk if it exists
    if backup.file_path:
        try:
            file_path = Path(backup.file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted backup file: {backup.file_path}")
        except Exception as e:
            logger.error(f"Failed to delete backup file {backup.file_path}: {str(e)}")
            # Continue with database deletion even if file deletion fails

    await db.delete(backup)
    await db.commit()

    return None

@router.post("/batch-delete", status_code=status.HTTP_200_OK)
async def batch_delete_backups(
    request: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Delete multiple backups at once."""
    if not request.backup_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No backup IDs provided"
        )
    
    # Fetch all backups
    result = await db.execute(
        select(Backup).where(Backup.id.in_(request.backup_ids))
    )
    backups = result.scalars().all()
    
    if len(backups) != len(request.backup_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Some backups not found"
        )
    
    # Delete all backups
    deleted_count = 0
    for backup in backups:
        await db.delete(backup)
        deleted_count += 1
    
    await db.commit()
    
    return {"deleted": deleted_count, "message": f"Successfully deleted {deleted_count} backups"}