import difflib
import gzip
import io
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import settings
from api.core.database import get_db
from api.core.encryption import AESEncryption
from api.core.redis import get_redis_client
from api.core.security import get_current_user
from api.models.models import Backup, BackupCategory, BackupStatus, BackupType, LDAPServer
from api.schemas.schemas import BackupCategory as BackupCategorySchema
from api.schemas.schemas import BackupCreate, BackupResponse

router = APIRouter(prefix="/backups", tags=["Backups"])
logger = logging.getLogger(__name__)


class BatchDeleteRequest(BaseModel):
    """Request model for batch deletion."""

    backup_ids: List[int]


def _check_backup_category_access(user, category: BackupCategory):
    """Check if user has access to backup category."""
    user_role = user.role.value

    # ADMIN has access to everything
    if user_role == "admin":
        return True

    # BACKUP_ADMIN has access to all backup types except full_server
    if user_role == "backup_admin" and category != BackupCategory.FULL_SERVER:
        return True

    # SECURITY_ADMIN has access to schema, config, acl, and certificate backups (sensitive data)
    if user_role == "security_admin" and category in [
        BackupCategory.SCHEMA,
        BackupCategory.CONFIG,
        BackupCategory.ACL,
        BackupCategory.CERTIFICATES,
    ]:
        return True

    # OPERATOR has access to directory and incremental backups only
    if user_role == "operator" and category == BackupCategory.DIRECTORY:
        return True

    # Default: deny access
    return False


def _read_backup_bytes(backup: Backup) -> bytes:
    file_path = Path(backup.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backup file not found"
        )

    if backup.encrypted:
        encrypted_data = file_path.read_text()
        decrypted_data = AESEncryption(settings.ENCRYPTION_KEY).decrypt(encrypted_data)
        raw_data = decrypted_data
    else:
        raw_data = file_path.read_bytes()

    if backup.compression_enabled:
        raw_data = gzip.decompress(raw_data)

    return raw_data


def _download_filename(backup: Backup) -> str:
    file_path = Path(backup.file_path)
    name = file_path.name
    for suffix in [".enc", ".gz"]:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    if not name.endswith(".ldif"):
        name = f"backup_{backup.id}.ldif"
    return name


def _decode_backup_content(
    backup: Backup, max_bytes: int, max_lines: int
) -> tuple[str, bool, int]:
    raw_data = _read_backup_bytes(backup)
    text = raw_data.decode("utf-8", errors="replace")
    truncated = False

    # Only truncate by bytes if max_bytes > 0
    if max_bytes > 0 and len(text.encode("utf-8")) > max_bytes:
        text = text.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")
        truncated = True

    lines = text.splitlines()
    # Only truncate by lines if max_lines > 0
    if max_lines > 0 and len(lines) > max_lines:
        text = "\n".join(lines[:max_lines])
        truncated = True

    return text, truncated, len(text.splitlines())


def _diff_backup_content(
    base_backup: Backup,
    other_backup: Backup,
    context_lines: int,
    max_lines: int,
) -> tuple[str, bool, int]:
    base_text = _read_backup_bytes(base_backup).decode("utf-8", errors="replace")
    other_text = _read_backup_bytes(other_backup).decode("utf-8", errors="replace")

    diff_lines = list(
        difflib.unified_diff(
            base_text.splitlines(),
            other_text.splitlines(),
            fromfile=f"backup_{base_backup.id}",
            tofile=f"backup_{other_backup.id}",
            n=context_lines,
            lineterm="",
        )
    )

    truncated = False
    if max_lines > 0 and len(diff_lines) > max_lines:
        diff_lines = diff_lines[:max_lines]
        truncated = True

    return "\n".join(diff_lines), truncated, len(diff_lines)


@router.get("/", response_model=List[BackupResponse])
async def list_backups(
    skip: int = 0,
    limit: int = 100,
    server_id: Optional[int] = Query(None, description="Filter by server ID"),
    status: Optional[BackupStatus] = Query(None, description="Filter by status"),
    backup_type: Optional[BackupType] = Query(None, description="Filter by type"),
    search: Optional[str] = Query(None, description="Search in server name"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
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
                LDAPServer.host.ilike(f"%{search}%"),
            )
        )

    query = query.offset(skip).limit(limit).order_by(Backup.created_at.desc())

    result = await db.execute(query)
    backups = result.scalars().all()
    
    return backups


@router.get("/{backup_id}", response_model=BackupResponse)
async def get_backup(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get backup by ID."""
    result = await db.execute(select(Backup).where(Backup.id == backup_id))
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found"
        )

    return backup


@router.get("/{backup_id}/content")
async def get_backup_content(
    backup_id: int,
    max_lines: int = Query(200, ge=0, le=5000),
    max_bytes: int = Query(200000, ge=0, le=2000000),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Backup).where(Backup.id == backup_id))
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found"
        )


    if backup.status != BackupStatus.COMPLETED or not backup.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backup content is not available",
        )

    # When max_lines is 0 (no limit), also set max_bytes to 0 (no limit)
    if max_lines == 0:
        max_bytes = 0

    content, truncated, lines = _decode_backup_content(
        backup, max_bytes=max_bytes, max_lines=max_lines
    )

    return {
        "content": content,
        "truncated": truncated,
        "lines": lines,
    }


@router.get("/{backup_id}/download")
async def download_backup_content(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Backup).where(Backup.id == backup_id))
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found"
        )

    if backup.status != BackupStatus.COMPLETED or not backup.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backup content is not available",
        )

    raw_data = _read_backup_bytes(backup)
    filename = _download_filename(backup)

    return StreamingResponse(
        io.BytesIO(raw_data),
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{backup_id}/diff")
async def diff_backup_content(
    backup_id: int,
    against_id: int = Query(..., ge=1),
    context: int = Query(3, ge=0, le=10),
    max_lines: int = Query(5000, ge=0, le=20000),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    base_result = await db.execute(select(Backup).where(Backup.id == backup_id))
    base_backup = base_result.scalar_one_or_none()

    other_result = await db.execute(select(Backup).where(Backup.id == against_id))
    other_backup = other_result.scalar_one_or_none()

    if not base_backup or not other_backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found"
        )

    if (
        base_backup.status != BackupStatus.COMPLETED
        or other_backup.status != BackupStatus.COMPLETED
        or not base_backup.file_path
        or not other_backup.file_path
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backup content is not available",
        )

    diff_text, truncated, lines = _diff_backup_content(
        base_backup, other_backup, context, max_lines
    )

    return {
        "diff": diff_text,
        "truncated": truncated,
        "lines": lines,
    }


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

    # Validate incremental backup requirements
    parent_backup = None
    if backup_data.backup_type == BackupType.INCREMENTAL:
        if not backup_data.parent_backup_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="parent_backup_id is required for incremental backups",
            )

        # Verify parent backup exists and is completed
        result = await db.execute(
            select(Backup).where(Backup.id == backup_data.parent_backup_id)
        )
        parent_backup = result.scalar_one_or_none()

        if not parent_backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Parent backup not found"
            )

        if parent_backup.status != BackupStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent backup must be completed before creating incremental backup",
            )

        if parent_backup.ldap_server_id != backup_data.ldap_server_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent backup must be from the same LDAP server",
            )

    # Create backup record
    new_backup = Backup(
        ldap_server_id=backup_data.ldap_server_id,
        backup_type=backup_data.backup_type,
        category=backup_data.category,
        encrypted=backup_data.encrypted,
        compression_enabled=backup_data.compression_enabled,
        parent_backup_id=backup_data.parent_backup_id,
        status=BackupStatus.PENDING,
        created_by=current_user.id,
    )

    db.add(new_backup)
    await db.commit()
    await db.refresh(new_backup)

    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
        queue_length = await redis_client.rpush("backup_queue", str(new_backup.id))
        logger.info(
            "Queued backup %s for processing (queue length: %s)",
            new_backup.id,
            queue_length,
        )
    except Exception as e:
        logger.error(f"Failed to queue backup {new_backup.id}: {e}")
        new_backup.status = BackupStatus.FAILED
        new_backup.error_message = "Failed to queue backup for processing"
        await db.commit()

    return new_backup


@router.delete("/{backup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
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
    current_user=Depends(get_current_user),
):
    """Delete multiple backups at once."""
    # Only admins and operators can delete backups
    if current_user.role.value not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and operators can delete backups",
        )

    if not request.backup_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No backup IDs provided"
        )

    # Fetch all backups
    result = await db.execute(select(Backup).where(Backup.id.in_(request.backup_ids)))
    backups = result.scalars().all()

    if len(backups) != len(request.backup_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Some backups not found"
        )

    # Delete all backups
    deleted_count = 0
    for backup in backups:
        await db.delete(backup)
        deleted_count += 1

    await db.commit()

    return {
        "deleted": deleted_count,
        "message": f"Successfully deleted {deleted_count} backups",
    }
