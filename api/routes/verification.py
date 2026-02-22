import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.core.security import get_current_user
from api.models.models import Backup, User
from api.services.verification_service import VerificationService

router = APIRouter(prefix="/backups/verification", tags=["Backup Verification"])

logger = logging.getLogger(__name__)


@router.post("/{backup_id}")
async def verify_backup(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually verify a backup's integrity.
    
    This endpoint performs comprehensive verification including:
    - File existence check
    - Checksum verification (if checksum exists)
    - File size verification
    - LDIF syntax validation
    """
    # Get backup
    result = await db.execute(select(Backup).where(Backup.id == backup_id))
    backup = result.scalar_one_or_none()
    
    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup {backup_id} not found"
        )
    
    if not backup.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backup has no file path - cannot verify"
        )
    
    # Perform verification
    verification_service = VerificationService()
    
    try:
        is_valid, verification_msg = verification_service.comprehensive_verification(
            backup.file_path,
            expected_checksum=backup.checksum,
            expected_size=backup.file_size,
            validate_syntax=True
        )
        
        # Update backup record
        if is_valid:
            backup.verification_status = "verified"
            backup.verified_at = datetime.utcnow()
            logger.info(f"Backup {backup_id} manually verified by user {current_user.id}")
        else:
            backup.verification_status = "failed"
            logger.warning(
                f"Backup {backup_id} verification failed: {verification_msg}"
            )
        
        await db.commit()
        
        return {
            "backup_id": backup_id,
            "verified": is_valid,
            "verification_status": backup.verification_status,
            "verified_at": backup.verified_at,
            "message": verification_msg,
            "checksum": backup.checksum,
            "checksum_algorithm": backup.checksum_algorithm,
        }
        
    except Exception as e:
        error_msg = f"Verification error: {str(e)}"
        logger.error(f"Backup {backup_id} verification failed: {error_msg}")
        
        backup.verification_status = "failed"
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.post("/{backup_id}/recalculate-checksum")
async def recalculate_checksum(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recalculate and update backup checksum.
    
    Use this if the checksum is missing or needs to be regenerated.
    Only admins can perform this operation.
    """
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can recalculate checksums"
        )
    
    # Get backup
    result = await db.execute(select(Backup).where(Backup.id == backup_id))
    backup = result.scalar_one_or_none()
    
    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup {backup_id} not found"
        )
    
    if not backup.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backup has no file path"
        )
    
    # Recalculate checksum
    verification_service = VerificationService()
    
    try:
        checksum = verification_service.calculate_checksum(
            backup.file_path,
            backup.checksum_algorithm or "sha256"
        )
        
        old_checksum = backup.checksum
        backup.checksum = checksum
        backup.verification_status = "not_verified"  # Reset status
        
        await db.commit()
        
        logger.info(
            f"Checksum recalculated for backup {backup_id} by user {current_user.id}"
        )
        
        return {
            "backup_id": backup_id,
            "old_checksum": old_checksum,
            "new_checksum": checksum,
            "algorithm": backup.checksum_algorithm,
            "message": "Checksum recalculated successfully"
        }
        
    except Exception as e:
        error_msg = f"Failed to recalculate checksum: {str(e)}"
        logger.error(f"Backup {backup_id}: {error_msg}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.get("/{backup_id}/status")
async def get_verification_status(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get verification status for a backup."""
    result = await db.execute(select(Backup).where(Backup.id == backup_id))
    backup = result.scalar_one_or_none()
    
    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup {backup_id} not found"
        )
    
    return {
        "backup_id": backup_id,
        "verification_status": backup.verification_status,
        "verified_at": backup.verified_at,
        "checksum": backup.checksum,
        "checksum_algorithm": backup.checksum_algorithm,
        "file_size": backup.file_size,
        "file_path": backup.file_path,
    }
