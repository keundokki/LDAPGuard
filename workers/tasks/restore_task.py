import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from api.core.config import settings
from api.core.database import AsyncSessionLocal
from api.core.encryption import decrypt_ldap_password
from api.models.models import Backup, BackupStatus, LDAPServer, RestoreJob, SystemSetting
from api.services.backup_service import BackupService
from api.services.email_service import EmailService
from api.services.ldap_service import LDAPService
from api.services.metrics_service import MetricsService
from api.services.verification_service import VerificationService
from api.services.webhook_service import WebhookService
from api.services.storage_service import storage_service

logger = logging.getLogger(__name__)


async def get_notification_recipients(db):
    """Get email notification recipients from system settings."""
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == "notification_email")
    )
    setting = result.scalar_one_or_none()
    
    if not setting or not setting.value:
        return []
    
    # Parse comma-separated email list
    recipients = [email.strip() for email in setting.value.split(",") if email.strip()]
    return recipients


async def get_system_settings(db, keys):
    """Fetch a set of system settings as a dict."""
    result = await db.execute(select(SystemSetting).where(SystemSetting.key.in_(keys)))
    return {setting.key: setting.value for setting in result.scalars().all()}


def parse_bool_setting(value) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


async def perform_restore(restore_id: int):
    """Perform restore operation."""
    start_time = datetime.utcnow()
    backup_service = BackupService()
    webhook_service = WebhookService()
    email_service = EmailService()
    verification_service = VerificationService()

    async with AsyncSessionLocal() as db:
        # Get notification recipients
        recipients = await get_notification_recipients(db)
        settings_map = await get_system_settings(
            db,
            [
                "smtp_server",
                "smtp_port",
                "smtp_username",
                "smtp_password",
                "smtp_encryption",
                "from_email",
                "smtp_from_email",
                "notification_webhook_url",
                "notification_on_restore_complete",
            ],
        )
        email_service.configure_from_settings_map(settings_map, recipients)
        webhook_service.configure_from_settings_map(settings_map)
        notify_restore_complete = parse_bool_setting(
            settings_map.get("notification_on_restore_complete")
        )

        logger.info(
            "Notification settings loaded: recipients=%s webhook_url=%s smtp_host=%s notify_restore_complete=%s",
            len(recipients),
            settings_map.get("notification_webhook_url"),
            settings_map.get("smtp_server"),
            notify_restore_complete,
        )

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

            # Send email notification
            await email_service.send_restore_started(restore_id, backup.id, recipients)

            # Record metrics
            MetricsService.record_restore_started()

            # Verify backup integrity before restore if enabled
            if settings.BACKUP_VERIFY_BEFORE_RESTORE and backup.file_path:
                logger.info(f"Verifying backup {backup.id} before restore")
                
                is_valid, verification_msg = verification_service.comprehensive_verification(
                    backup.file_path,
                    expected_checksum=backup.checksum,
                    expected_size=backup.file_size,
                    validate_syntax=True
                )
                
                if not is_valid:
                    error_msg = f"Backup verification failed: {verification_msg}"
                    logger.error(f"Restore {restore_id}: {error_msg}")
                    
                    restore_job.status = BackupStatus.FAILED
                    restore_job.error_message = error_msg
                    restore_job.completed_at = datetime.utcnow()
                    await db.commit()
                    
                    # Send failure notifications
                    await email_service.send_restore_failed(
                        restore_id, backup.id, error_msg, recipients
                    )
                    MetricsService.record_restore_failed()
                    return
                    
                logger.info(f"Backup {backup.id} verification passed")

            # Auto-download from cloud storage if local file is missing
            if backup.file_path:
                # Check if local file exists
                local_file_exists = Path(backup.file_path).exists()
            else:
                local_file_exists = False
            
            if not local_file_exists and backup.cloud_uploaded and backup.cloud_storage_path:
                logger.info(f"Restore {restore_id}: Local file missing, auto-downloading from cloud storage: {backup.cloud_storage_path}")
                
                try:
                    # Generate local file path
                    backup_dir = Path(settings.BACKUP_DIR)
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Extract filename from cloud path
                    filename = Path(backup.cloud_storage_path).name
                    destination_path = str(backup_dir / filename)
                    
                    # Download from S3
                    download_result = await storage_service.download_backup(
                        object_key=backup.cloud_storage_path,
                        destination_path=destination_path,
                        db=db
                    )
                    
                    # Update backup record with local file path
                    backup.file_path = destination_path
                    await db.commit()
                    
                    logger.info(f"Restore {restore_id}: Successfully downloaded backup from cloud storage to {destination_path}")
                    
                except Exception as download_error:
                    error_msg = f"Failed to download backup from cloud storage: {str(download_error)}"
                    logger.error(f"Restore {restore_id}: {error_msg}")
                    
                    restore_job.status = BackupStatus.FAILED
                    restore_job.error_message = error_msg
                    restore_job.completed_at = datetime.utcnow()
                    await db.commit()
                    
                    # Send failure notifications
                    await email_service.send_restore_failed(
                        restore_id, backup.id, error_msg, recipients
                    )
                    MetricsService.record_restore_failed()
                    return
            
            # Verify we have a file to restore
            if not backup.file_path or not Path(backup.file_path).exists():
                error_msg = "Backup file not found locally and not available in cloud storage"
                logger.error(f"Restore {restore_id}: {error_msg}")
                
                restore_job.status = BackupStatus.FAILED
                restore_job.error_message = error_msg
                restore_job.completed_at = datetime.utcnow()
                await db.commit()
                
                # Send failure notifications
                await email_service.send_restore_failed(
                    restore_id, backup.id, error_msg, recipients
                )
                MetricsService.record_restore_failed()
                return

            # Prepare backup file
            file_path = backup.file_path

            # Decrypt if encrypted
            if backup.encrypted:
                file_path = backup_service.decrypt_file(file_path)

            # Decompress if compressed
            if backup.compression_enabled:
                file_path = backup_service.decompress_file(file_path)

            # Decrypt bind password if encrypted
            bind_password = decrypt_ldap_password(
                ldap_server.bind_password, ldap_server.password_encrypted
            )

            # Create LDAP service
            ldap_service = LDAPService(
                host=ldap_server.host,
                port=ldap_server.port,
                use_ssl=ldap_server.use_ssl,
                base_dn=ldap_server.base_dn,
                bind_dn=ldap_server.bind_dn,
                bind_password=bind_password,
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

            # Send email notification
            if notify_restore_complete:
                await email_service.send_restore_completed(
                    restore_id, backup.id, entries_restored, duration, recipients
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

            # Send email notification
            await email_service.send_restore_failed(
                restore_id, backup.id, str(e), recipients
            )

            # Record metrics
            MetricsService.record_restore_failed()
