from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from api.core.database import get_db
from api.models.models import RestoreJob, Backup
from api.schemas.schemas import RestoreJobCreate, RestoreJobResponse

router = APIRouter(prefix="/restores", tags=["Restores"])


@router.get("/", response_model=List[RestoreJobResponse])
async def list_restore_jobs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all restore jobs."""
    result = await db.execute(
        select(RestoreJob).offset(skip).limit(limit).order_by(RestoreJob.created_at.desc())
    )
    jobs = result.scalars().all()
    return jobs


@router.get("/{restore_id}", response_model=RestoreJobResponse)
async def get_restore_job(restore_id: int, db: AsyncSession = Depends(get_db)):
    """Get restore job by ID."""
    result = await db.execute(select(RestoreJob).where(RestoreJob.id == restore_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restore job not found"
        )
    
    return job


@router.post("/", response_model=RestoreJobResponse, status_code=status.HTTP_201_CREATED)
async def create_restore_job(
    restore_data: RestoreJobCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new restore job."""
    # Verify backup exists
    result = await db.execute(select(Backup).where(Backup.id == restore_data.backup_id))
    backup = result.scalar_one_or_none()
    
    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup not found"
        )
    
    # Create restore job
    new_job = RestoreJob(
        backup_id=restore_data.backup_id,
        ldap_server_id=restore_data.ldap_server_id,
        selective_restore=restore_data.selective_restore,
        restore_filter=restore_data.restore_filter,
        point_in_time=restore_data.point_in_time,
        created_by=1  # TODO: Get from authenticated user
    )
    
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)
    
    # TODO: Schedule restore task
    
    return new_job
