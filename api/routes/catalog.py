"""
Backup catalog and search API routes.

Provides advanced filtering, search, and export capabilities for backups.
"""

import csv
import io
import json
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.core.security import get_current_user
from api.models.models import Backup, BackupStatus, BackupType, BackupCategory, LDAPServer, User
from api.schemas.schemas import (
    BackupCatalogStats,
    BackupExportResponse,
    BackupResponse,
    BackupSearchParams,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/search", response_model=List[BackupResponse])
async def search_backups(
    params: BackupSearchParams,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Advanced backup search with comprehensive filtering.
    
    Supports:
    - Text search (server name, filename)
    - Date range filtering
    - Status, type, category filtering
    - Size and entry count filtering
    - Verification and cloud upload status
    - Flexible sorting
    """
    query = select(Backup).join(LDAPServer)
    
    filters = []
    
    # Text search
    if params.search:
        search_filter = or_(
            LDAPServer.name.ilike(f"%{params.search}%"),
            LDAPServer.host.ilike(f"%{params.search}%"),
            Backup.file_path.ilike(f"%{params.search}%")
        )
        filters.append(search_filter)
    
    # Server filter
    if params.server_id:
        filters.append(Backup.ldap_server_id == params.server_id)
    
    # Status filter
    if params.status:
        filters.append(Backup.status == params.status)
    
    # Backup type filter
    if params.backup_type:
        filters.append(Backup.backup_type == params.backup_type)
    
    # Category filter
    if params.category:
        filters.append(Backup.category == params.category)
    
    # Verification status filter
    if params.verification_status:
        filters.append(Backup.verification_status == params.verification_status)
    
    # Cloud upload filter
    if params.cloud_uploaded is not None:
        filters.append(Backup.cloud_uploaded == params.cloud_uploaded)
    
    # Date range filters
    if params.created_after:
        filters.append(Backup.created_at >= params.created_after)
    if params.created_before:
        filters.append(Backup.created_at <= params.created_before)
    if params.completed_after:
        filters.append(Backup.completed_at >= params.completed_after)
    if params.completed_before:
        filters.append(Backup.completed_at <= params.completed_before)
    
    # Size range filters
    if params.min_size:
        filters.append(Backup.file_size >= params.min_size)
    if params.max_size:
        filters.append(Backup.file_size <= params.max_size)
    
    # Entry count filters
    if params.min_entries:
        filters.append(Backup.entry_count >= params.min_entries)
    if params.max_entries:
        filters.append(Backup.entry_count <= params.max_entries)
    
    # Apply all filters
    if filters:
        query = query.where(and_(*filters))
    
    # Sorting
    sort_field = params.sort_by or "created_at"
    sort_order = params.sort_order or "desc"
    
    sort_column = getattr(Backup, sort_field, Backup.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Pagination
    query = query.offset(params.skip).limit(params.limit)
    
    result = await db.execute(query)
    backups = result.scalars().all()
    
    logger.info(
        f"Search returned {len(backups)} backups "
        f"(filters: {len(filters)}, skip: {params.skip}, limit: {params.limit})"
    )
    
    return backups


@router.get("/stats", response_model=BackupCatalogStats)
async def get_catalog_stats(
    server_id: Optional[int] = Query(None, description="Filter stats by server"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive backup catalog statistics.
    
    Returns:
    - Total counts
    - Breakdowns by status, type, category, server
    - Size statistics
    - Date ranges
    """
    base_query = select(Backup)
    
    if server_id:
        base_query = base_query.where(Backup.ldap_server_id == server_id)
    
    # Get all backups for statistics
    result = await db.execute(base_query)
    all_backups = result.scalars().all()
    
    if not all_backups:
        return BackupCatalogStats(
            total_backups=0,
            total_size=0,
            total_entries=0,
            backups_by_status={},
            backups_by_type={},
            backups_by_category={},
            backups_by_server={},
            verified_backups=0,
            cloud_uploaded_backups=0,
            failed_backups=0,
            average_backup_size=0.0,
            largest_backup_size=0,
            smallest_backup_size=0
        )
    
    # Calculate statistics
    total_size = sum(b.file_size or 0 for b in all_backups)
    total_entries = sum(b.entry_count or 0 for b in all_backups)
    
    # Group by status
    backups_by_status = {}
    for backup in all_backups:
        status_value = backup.status.value if hasattr(backup.status, 'value') else str(backup.status)
        backups_by_status[status_value] = backups_by_status.get(status_value, 0) + 1
    
    # Group by type
    backups_by_type = {}
    for backup in all_backups:
        type_value = backup.backup_type.value if hasattr(backup.backup_type, 'value') else str(backup.backup_type)
        backups_by_type[type_value] = backups_by_type.get(type_value, 0) + 1
    
    # Group by category
    backups_by_category = {}
    for backup in all_backups:
        category_value = backup.category.value if hasattr(backup.category, 'value') else str(backup.category)
        backups_by_category[category_value] = backups_by_category.get(category_value, 0) + 1
    
    # Group by server
    backups_by_server = {}
    for backup in all_backups:
        server_name = backup.ldap_server.name if backup.ldap_server else "Unknown"
        backups_by_server[server_name] = backups_by_server.get(server_name, 0) + 1
    
    # Count verified and cloud uploaded
    verified_backups = sum(1 for b in all_backups if b.verification_status == "verified")
    cloud_uploaded_backups = sum(1 for b in all_backups if b.cloud_uploaded)
    failed_backups = sum(1 for b in all_backups if b.status == BackupStatus.FAILED)
    
    # Date ranges
    dates = [b.created_at for b in all_backups if b.created_at]
    oldest_backup = min(dates) if dates else None
    newest_backup = max(dates) if dates else None
    
    # Size statistics
    sizes = [b.file_size for b in all_backups if b.file_size]
    average_size = sum(sizes) / len(sizes) if sizes else 0.0
    largest_size = max(sizes) if sizes else 0
    smallest_size = min(sizes) if sizes else 0
    
    return BackupCatalogStats(
        total_backups=len(all_backups),
        total_size=total_size,
        total_entries=total_entries,
        backups_by_status=backups_by_status,
        backups_by_type=backups_by_type,
        backups_by_category=backups_by_category,
        backups_by_server=backups_by_server,
        verified_backups=verified_backups,
        cloud_uploaded_backups=cloud_uploaded_backups,
        failed_backups=failed_backups,
        oldest_backup=oldest_backup,
        newest_backup=newest_backup,
        average_backup_size=average_size,
        largest_backup_size=largest_size,
        smallest_backup_size=smallest_size
    )


@router.get("/export")
async def export_backups(
    format: str = Query("csv", description="Export format: csv or json"),
    server_id: Optional[int] = Query(None, description="Filter by server"),
    status: Optional[str] = Query(None, description="Filter by status"),
    created_after: Optional[datetime] = Query(None, description="Filter by creation date"),
    created_before: Optional[datetime] = Query(None, description="Filter by creation date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export backups to CSV or JSON format.
    
    Supports filtering by:
    - Server
    - Status
    - Date range
    
    Returns downloadable file.
    """
    if format not in ["csv", "json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be 'csv' or 'json'"
        )
    
    # Build query with filters
    query = select(Backup).join(LDAPServer)
    
    filters = []
    if server_id:
        filters.append(Backup.ldap_server_id == server_id)
    if status:
        filters.append(Backup.status == status)
    if created_after:
        filters.append(Backup.created_at >= created_after)
    if created_before:
        filters.append(Backup.created_at <= created_before)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(Backup.created_at.desc())
    
    result = await db.execute(query)
    backups = result.scalars().all()
    
    if format == "csv":
        return _export_csv(backups)
    else:
        return _export_json(backups)


def _export_csv(backups: List[Backup]) -> Response:
    """Export backups to CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "ID",
        "Server Name",
        "Server Host",
        "Backup Type",
        "Category",
        "Status",
        "File Size (bytes)",
        "Entry Count",
        "Created At",
        "Completed At",
        "Verification Status",
        "Cloud Uploaded",
        "Cloud Provider",
        "Checksum",
        "File Path"
    ])
    
    # Write data
    for backup in backups:
        writer.writerow([
            backup.id,
            backup.ldap_server.name if backup.ldap_server else "",
            backup.ldap_server.host if backup.ldap_server else "",
            backup.backup_type.value if hasattr(backup.backup_type, 'value') else str(backup.backup_type),
            backup.category.value if hasattr(backup.category, 'value') else str(backup.category),
            backup.status.value if hasattr(backup.status, 'value') else str(backup.status),
            backup.file_size or 0,
            backup.entry_count or 0,
            backup.created_at.isoformat() if backup.created_at else "",
            backup.completed_at.isoformat() if backup.completed_at else "",
            backup.verification_status or "",
            "Yes" if backup.cloud_uploaded else "No",
            backup.cloud_provider or "",
            backup.checksum or "",
            backup.file_path or ""
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"ldapguard_backups_{timestamp}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


def _export_json(backups: List[Backup]) -> Response:
    """Export backups to JSON format."""
    data = []
    
    for backup in backups:
        data.append({
            "id": backup.id,
            "server_name": backup.ldap_server.name if backup.ldap_server else None,
            "server_host": backup.ldap_server.host if backup.ldap_server else None,
            "backup_type": backup.backup_type.value if hasattr(backup.backup_type, 'value') else str(backup.backup_type),
            "category": backup.category.value if hasattr(backup.category, 'value') else str(backup.category),
            "status": backup.status.value if hasattr(backup.status, 'value') else str(backup.status),
            "file_size": backup.file_size,
            "entry_count": backup.entry_count,
            "created_at": backup.created_at.isoformat() if backup.created_at else None,
            "completed_at": backup.completed_at.isoformat() if backup.completed_at else None,
            "verification_status": backup.verification_status,
            "cloud_uploaded": backup.cloud_uploaded,
            "cloud_provider": backup.cloud_provider,
            "cloud_storage_path": backup.cloud_storage_path,
            "checksum": backup.checksum,
            "checksum_algorithm": backup.checksum_algorithm,
            "file_path": backup.file_path,
            "error_message": backup.error_message
        })
    
    json_content = json.dumps({
        "export_date": datetime.utcnow().isoformat(),
        "total_records": len(data),
        "backups": data
    }, indent=2)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"ldapguard_backups_{timestamp}.json"
    
    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
