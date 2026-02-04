import asyncio
import logging
from datetime import datetime

from sqlalchemy import select

from api.core.database import AsyncSessionLocal
from api.models.models import Backup, BackupStatus, BackupType, LDAPServer
from api.services.backup_service import BackupService
from api.services.ldap_service import LDAPService
from api.services.metrics_service import MetricsService
from api.services.webhook_service import WebhookService

logger = logging.getLogger(__name__)


async def perform_backup(backup_id: int):
    """Perform backup operation."""
    start_time = datetime.utcnow()
    backup_service = BackupService()
    webhook_service = WebhookService()

    async with AsyncSessionLocal() as db:
        # Get backup record
        result = await db.execute(select(Backup).where(Backup.id == backup_id))
        backup = result.scalar_one_or_none()

        if not backup:
            logger.error(f"Backup {backup_id} not found")
            return

        # Get LDAP server
        result = await db.execute(
            select(LDAPServer).where(LDAPServer.id == backup.ldap_server_id)
        )
        ldap_server = result.scalar_one_or_none()

        if not ldap_server:
            backup.status = BackupStatus.FAILED
            backup.error_message = "LDAP server not found"
            await db.commit()
            return

        try:
            # Update status
            backup.status = BackupStatus.IN_PROGRESS
            backup.started_at = start_time
            await db.commit()

            # Send webhook notification
            await webhook_service.send_backup_started(backup_id, ldap_server.name)

            # Record metrics
            MetricsService.record_backup_started(backup.backup_type.value)

            # Create LDAP service
            ldap_service = LDAPService(
                host=ldap_server.host,
                port=ldap_server.port,
                use_ssl=ldap_server.use_ssl,
                base_dn=ldap_server.base_dn,
                bind_dn=ldap_server.bind_dn,
                bind_password=ldap_server.bind_password,
            )

            # Generate backup filename
            filename = backup_service.generate_backup_filename(
                ldap_server.name, backup.backup_type.value
            )
            file_path = backup_service.get_backup_path(filename)

            # Perform backup
            if backup.backup_type == BackupType.INCREMENTAL and backup.parent_backup_id:
                # Get parent backup timestamp
                result = await db.execute(
                    select(Backup).where(Backup.id == backup.parent_backup_id)
                )
                parent_backup = result.scalar_one_or_none()

                if parent_backup and parent_backup.completed_at:
                    entry_count = ldap_service.backup_to_ldif(
                        file_path, search_filter="(objectClass=*)"
                    )
                else:
                    entry_count = ldap_service.backup_to_ldif(file_path)
            else:
                entry_count = ldap_service.backup_to_ldif(file_path)

            ldap_service.disconnect()

            # Compress if enabled
            if backup.compression_enabled:
                file_path = backup_service.compress_file(file_path)

            # Encrypt if enabled
            if backup.encrypted:
                file_path = backup_service.encrypt_file(file_path)

            # Get file size
            file_size = backup_service.get_file_size(file_path)

            # Update backup record
            backup.status = BackupStatus.COMPLETED
            backup.file_path = file_path
            backup.file_size = file_size
            backup.entry_count = entry_count
            backup.completed_at = datetime.utcnow()
            await db.commit()

            # Calculate duration
            duration = (backup.completed_at - backup.started_at).total_seconds()

            # Send webhook notification
            await webhook_service.send_backup_completed(
                backup_id, ldap_server.name, entry_count, file_size
            )

            # Record metrics
            MetricsService.record_backup_completed(
                backup.backup_type.value,
                duration,
                ldap_server.name,
                file_size,
                entry_count,
            )

            logger.info(
                f"Backup {backup_id} completed successfully. "
                f"Entries: {entry_count}, Size: {file_size} bytes"
            )

        except Exception as e:
            logger.error(f"Backup {backup_id} failed: {str(e)}")

            backup.status = BackupStatus.FAILED
            backup.error_message = str(e)
            backup.completed_at = datetime.utcnow()
            await db.commit()

            # Send webhook notification
            await webhook_service.send_backup_failed(
                backup_id, ldap_server.name, str(e)
            )

            # Record metrics
            MetricsService.record_backup_failed(backup.backup_type.value)
            MetricsService.record_ldap_connection_error(ldap_server.name)
