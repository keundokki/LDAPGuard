import logging
from datetime import datetime

from sqlalchemy import select

from api.core.database import AsyncSessionLocal
from api.models.models import Backup, BackupStatus, LDAPServer, RestoreJob
from api.services.backup_service import BackupService
from api.services.ldap_service import LDAPService
from api.services.metrics_service import MetricsService
from api.services.webhook_service import WebhookService

logger = logging.getLogger(__name__)


async def perform_restore(restore_id: int):
    """Perform restore operation."""
    start_time = datetime.utcnow()
    backup_service = BackupService()
    webhook_service = WebhookService()

    async with AsyncSessionLocal() as db:
        # Get restore job
        result = await db.execute(select(RestoreJob).where(RestoreJob.id == restore_id))
        restore_job = result.scalar_one_or_none()

        if not restore_job:
            logger.error(f"Restore job {restore_id} not found")
            return

        # Get backup
        result = await db.execute(
            select(Backup).where(Backup.id == restore_job.backup_id)
        )
        backup = result.scalar_one_or_none()

        if not backup:
            restore_job.status = BackupStatus.FAILED
            restore_job.error_message = "Backup not found"
            await db.commit()
            return

        # Get LDAP server
        result = await db.execute(
            select(LDAPServer).where(LDAPServer.id == restore_job.ldap_server_id)
        )
        ldap_server = result.scalar_one_or_none()

        if not ldap_server:
            restore_job.status = BackupStatus.FAILED
            restore_job.error_message = "LDAP server not found"
            await db.commit()
            return

        try:
            # Update status
            restore_job.status = BackupStatus.IN_PROGRESS
            restore_job.started_at = start_time
            await db.commit()

            # Send webhook notification
            await webhook_service.send_restore_started(restore_id, backup.id)

            # Record metrics
            MetricsService.record_restore_started()

            # Prepare backup file
            file_path = backup.file_path

            # Decrypt if encrypted
            if backup.encrypted:
                file_path = backup_service.decrypt_file(file_path)

            # Decompress if compressed
            if backup.compression_enabled:
                file_path = backup_service.decompress_file(file_path)

            # Create LDAP service
            ldap_service = LDAPService(
                host=ldap_server.host,
                port=ldap_server.port,
                use_ssl=ldap_server.use_ssl,
                base_dn=ldap_server.base_dn,
                bind_dn=ldap_server.bind_dn,
                bind_password=ldap_server.bind_password,
            )

            # Perform restore
            entries_restored = ldap_service.restore_from_ldif(file_path)

            ldap_service.disconnect()

            # Update restore job
            restore_job.status = BackupStatus.COMPLETED
            restore_job.entries_restored = entries_restored
            restore_job.completed_at = datetime.utcnow()
            await db.commit()

            # Calculate duration
            duration = (
                restore_job.completed_at - restore_job.started_at
            ).total_seconds()

            # Send webhook notification
            await webhook_service.send_restore_completed(
                restore_id, backup.id, entries_restored
            )

            # Record metrics
            MetricsService.record_restore_completed(duration)

            logger.info(
                f"Restore job {restore_id} completed successfully. "
                f"Entries restored: {entries_restored}"
            )

        except Exception as e:
            logger.error(f"Restore job {restore_id} failed: {str(e)}")

            restore_job.status = BackupStatus.FAILED
            restore_job.error_message = str(e)
            restore_job.completed_at = datetime.utcnow()
            await db.commit()

            # Record metrics
            MetricsService.record_restore_failed()
