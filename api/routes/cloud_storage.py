"""
Cloud storage API routes for S3-compatible backup management.

Provides endpoints for:
- Uploading backups to cloud storage
- Downloading backups from cloud storage
- Listing cloud backups
- Deleting from cloud storage
- Testing cloud connection
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.core.database import get_db
from api.core.security import get_current_user
from api.models.models import Backup, SystemSetting, User, UserRole
from api.schemas.schemas import (
    CloudStorageInfo,
    CloudStorageTestResponse,
    CloudStorageUploadResponse,
)
from api.services.storage_service import storage_service

logger = logging.getLogger(__name__)

router = APIRouter()


async def is_s3_enabled(db: AsyncSession) -> bool:
    """Check if S3 is enabled in database settings."""
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == "s3_enabled")
    )
    s3_setting = result.scalar_one_or_none()

    if s3_setting:
        return s3_setting.value.lower() == "true"

    # Fall back to environment variable if not in database
    return storage_service.enabled


@router.post("/{backup_id}/upload", response_model=CloudStorageUploadResponse)
async def upload_backup_to_cloud(
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a backup to cloud storage (S3-compatible).

    Requires: OPERATOR role or higher
    """
    # Check permissions
    if current_user.role not in [
            UserRole.OPERATOR,
            UserRole.BACKUP_ADMIN,
            UserRole.SECURITY_ADMIN,
            UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to upload backups to cloud storage"
        )

    # Check if S3 is enabled (from database or environment)
    if not await is_s3_enabled(db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cloud storage is not enabled. Set S3_ENABLED=true in configuration."
        )

    # Get backup with eagerly loaded ldap_server relationship
    result = await db.execute(
        select(Backup)
        .options(selectinload(Backup.ldap_server))
        .where(Backup.id == backup_id)
    )
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup {backup_id} not found"
        )

    # Check if backup has a file
    if not backup.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Backup {backup_id} has no local file to upload"
        )

    # Check if already uploaded
    if backup.cloud_uploaded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Backup {backup_id} is already uploaded to cloud storage at {backup.cloud_storage_path}")  # noqa: E501

    try:
        # Generate S3 object key
        from pathlib import Path
        from datetime import datetime

        created_at = backup.created_at
        ldap_server = backup.ldap_server  # Should be eagerly loaded

        object_key = (
            f"backups/{created_at.year}/{created_at.month:02d}/{created_at.day:02d}/"
            f"{ldap_server.name}/backup_{backup_id}_{Path(backup.file_path).name}"
        )

        # Prepare metadata
        metadata = {
            'backup-id': str(backup_id),
            'server-name': ldap_server.name,
            'backup-type': backup.backup_type.value,
            'category': backup.category.value,
            'entry-count': str(backup.entry_count or 0),
            'checksum': backup.checksum or '',
            'checksum-algorithm': backup.checksum_algorithm or ''
        }

        # Upload to S3
        logger.info(f"Uploading backup {backup_id} to cloud storage: {object_key}")

        upload_result = await storage_service.upload_backup(
            file_path=backup.file_path,
            object_key=object_key,
            metadata=metadata,
            db=db
        )

        # Update backup record
        backup.cloud_uploaded = True
        backup.cloud_storage_path = object_key
        backup.cloud_uploaded_at = datetime.utcnow()
        backup.cloud_provider = upload_result.get('provider', 'unknown')
        backup.cloud_storage_class = upload_result.get('storage_class', 'STANDARD')
        await db.commit()

        logger.info(f"Successfully uploaded backup {backup_id} to cloud storage")

        return CloudStorageUploadResponse(
            backup_id=backup_id,
            success=True,
            message=f"Backup uploaded successfully to {upload_result['provider']} storage",  # noqa: E501
            cloud_storage_path=object_key,
            cloud_provider=upload_result['provider'],
            cloud_storage_class=upload_result['storage_class'],
            uploaded_at=backup.cloud_uploaded_at)

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup file not found: {backup.file_path}"
        )
    except Exception as e:
        logger.error(f"Failed to upload backup {backup_id} to cloud storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload backup to cloud storage: {str(e)}"
        )


@router.post("/{backup_id}/download")
async def download_backup_from_cloud(
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Download a backup from cloud storage to local storage.

    Useful for restoring a backup that was removed locally after cloud upload.

    Requires: OPERATOR role or higher
    """
    # Check permissions
    if current_user.role not in [
            UserRole.OPERATOR,
            UserRole.BACKUP_ADMIN,
            UserRole.SECURITY_ADMIN,
            UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to download backups from cloud storage"
        )

    # Check if S3 is enabled (from database or environment)
    if not await is_s3_enabled(db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cloud storage is not enabled"
        )

    # Get backup with eagerly loaded ldap_server relationship
    result = await db.execute(
        select(Backup)
        .options(selectinload(Backup.ldap_server))
        .where(Backup.id == backup_id)
    )
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup {backup_id} not found"
        )

    # Check if uploaded to cloud
    if not backup.cloud_uploaded or not backup.cloud_storage_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Backup {backup_id} is not available in cloud storage"
        )

    # Check if file already exists locally
    if backup.file_path:
        from pathlib import Path
        if Path(backup.file_path).exists():
            return {
                "success": True,
                "message": "Backup already exists locally",
                "file_path": backup.file_path
            }

    try:
        # Generate local file path
        from api.core.config import settings
        from pathlib import Path

        backup_dir = Path(settings.BACKUP_DIR)
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Extract filename from cloud path
        filename = Path(backup.cloud_storage_path).name
        destination_path = str(backup_dir / filename)

        # Download from S3
        logger.info(
            f"Downloading backup {backup_id} from cloud storage: {backup.cloud_storage_path}")  # noqa: E501

        download_result = await storage_service.download_backup(
            object_key=backup.cloud_storage_path,
            destination_path=destination_path,
            db=db
        )

        # Update backup record
        backup.file_path = destination_path
        await db.commit()

        logger.info(f"Successfully downloaded backup {backup_id} from cloud storage")

        return {
            "success": True,
            "message": f"Backup downloaded successfully from {backup.cloud_provider} storage",  # noqa: E501
            "file_path": destination_path,
            "size": download_result['size']}

    except Exception as e:
        logger.error(f"Failed to download backup {backup_id} from cloud storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download backup from cloud storage: {str(e)}"
        )


@router.delete("/{backup_id}/cloud")
async def delete_backup_from_cloud(
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a backup from cloud storage (admin only).

    Note: This only deletes from cloud, not the local copy.

    Requires: ADMIN role
    """
    # Check admin role
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete cloud backups"
        )

    # Check if S3 is enabled (from database or environment)
    if not await is_s3_enabled(db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cloud storage is not enabled"
        )

    # Get backup with eagerly loaded ldap_server relationship
    result = await db.execute(
        select(Backup)
        .options(selectinload(Backup.ldap_server))
        .where(Backup.id == backup_id)
    )
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup {backup_id} not found"
        )

    # Check if uploaded to cloud
    if not backup.cloud_uploaded or not backup.cloud_storage_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Backup {backup_id} is not in cloud storage"
        )

    try:
        # Delete from S3
        logger.info(
            f"Deleting backup {backup_id} from cloud storage: {backup.cloud_storage_path}")  # noqa: E501

        await storage_service.delete_backup(backup.cloud_storage_path, db=db)

        # Update backup record
        backup.cloud_uploaded = False
        backup.cloud_storage_path = None
        backup.cloud_uploaded_at = None
        backup.cloud_provider = None
        backup.cloud_storage_class = None
        await db.commit()

        logger.info(f"Successfully deleted backup {backup_id} from cloud storage")

        return {
            "success": True,
            "message": "Backup deleted from cloud storage"
        }

    except Exception as e:
        logger.error(f"Failed to delete backup {backup_id} from cloud storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete backup from cloud storage: {str(e)}"
        )


@router.get("/list", response_model=List[CloudStorageInfo])
async def list_cloud_backups(
    prefix: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all backups in cloud storage.

    Optional prefix filter (e.g., "backups/2026/02/" for February 2026).

    Requires: Any authenticated user
    """
    # Check if S3 is enabled (from database or environment)
    if not await is_s3_enabled(db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cloud storage is not enabled"
        )

    try:
        logger.info(f"Listing cloud backups (prefix: {prefix or 'all'})")

        objects = await storage_service.list_backups(prefix=prefix, db=db)

        return [
            CloudStorageInfo(
                key=obj['key'],
                size=obj['size'],
                last_modified=obj['last_modified'],
                storage_class=obj['storage_class']
            )
            for obj in objects
        ]

    except Exception as e:
        logger.error(f"Failed to list cloud backups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list cloud backups: {str(e)}"
        )


@router.get("/test", response_model=CloudStorageTestResponse)
async def test_cloud_connection(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Test cloud storage connection and credentials (admin only).

    Requires: ADMIN role
    """
    # Check admin role
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can test cloud storage"
        )

    try:
        result = await storage_service.test_connection()
        return CloudStorageTestResponse(**result)

    except Exception as e:
        logger.error(f"Cloud storage connection test failed: {e}")
        return CloudStorageTestResponse(
            success=False,
            message=f"Connection test failed: {str(e)}",
            enabled=await is_s3_enabled(db)
        )


@router.get("/{backup_id}/info", response_model=CloudStorageInfo)
async def get_backup_cloud_info(
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get cloud storage information for a specific backup.

    Requires: Any authenticated user
    """
    # Check if S3 is enabled (from database or environment)
    if not await is_s3_enabled(db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cloud storage is not enabled"
        )

    # Get backup with eagerly loaded ldap_server relationship
    result = await db.execute(
        select(Backup)
        .options(selectinload(Backup.ldap_server))
        .where(Backup.id == backup_id)
    )
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup {backup_id} not found"
        )

    # Check if uploaded to cloud
    if not backup.cloud_uploaded or not backup.cloud_storage_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup {backup_id} is not in cloud storage"
        )

    try:
        obj_info = await storage_service.get_object_info(backup.cloud_storage_path, db=db)  # noqa: E501

        return CloudStorageInfo(
            key=obj_info['key'],
            size=obj_info['size'],
            last_modified=obj_info['last_modified'],
            storage_class=obj_info['storage_class']
        )

    except Exception as e:
        logger.error(f"Failed to get cloud info for backup {backup_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cloud storage info: {str(e)}"
        )
