import logging
from datetime import datetime, timedelta

from sqlalchemy import select

from api.core.config import settings
from api.core.database import AsyncSessionLocal
from api.core.encryption import decrypt_ldap_password
from api.models.models import Backup, BackupCategory, BackupStatus, BackupType, LDAPServer, SystemSetting
from api.services.backup_service import BackupService
from api.services.email_service import EmailService
from api.services.ldap_service import LDAPService
from api.services.metrics_service import MetricsService
from api.services.storage_service import storage_service
from api.services.verification_service import VerificationService
from api.services.webhook_service import WebhookService

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


def calculate_retry_delay(retry_count: int) -> int:
    """Calculate retry delay with exponential backoff.
    
    Args:
        retry_count: Current retry attempt number (0-based)
        
    Returns:
        Delay in seconds before next retry
    """
    base_delay = settings.BACKUP_RETRY_DELAY
    backoff = settings.BACKUP_RETRY_BACKOFF
    
    # Exponential backoff: delay * (backoff ^ retry_count)
    # Example: 300s * (2.0 ^ 0) = 300s (5 min)
    #          300s * (2.0 ^ 1) = 600s (10 min)
    #          300s * (2.0 ^ 2) = 1200s (20 min)
    delay = int(base_delay * (backoff ** retry_count))
    
    # Cap at 1 hour maximum
    max_delay = 3600
    return min(delay, max_delay)


async def should_retry_backup(backup: Backup) -> bool:
    """Determine if a failed backup should be retried.
    
    Args:
        backup: Backup instance that failed
        
    Returns:
        True if backup should be retried, False otherwise
    """
    if not settings.BACKUP_RETRY_ENABLED:
        return False
        
    if backup.retry_count >= backup.max_retries:
        logger.info(f"Backup {backup.id} exceeded max retries ({backup.max_retries})")
        return False
        
    # Don't retry certain types of errors that won't benefit from retry
    non_retryable_errors = [
        "not found",
        "invalid credentials",
        "permission denied",
        "authentication failed",
    ]
    
    if backup.error_message:
        error_lower = backup.error_message.lower()
        for non_retryable in non_retryable_errors:
            if non_retryable in error_lower:
                logger.info(
                    f"Backup {backup.id} has non-retryable error: {non_retryable}"
                )
                return False
    
    return True


async def schedule_backup_retry(backup_id: int, retry_delay: int):
    """Schedule a backup retry.
    
    Args:
        backup_id: ID of backup to retry
        retry_delay: Delay in seconds before retry
    """
    # Import here to avoid circular dependency
    from workers.main import scheduler
    
    retry_time = datetime.utcnow() + timedelta(seconds=retry_delay)
    
    # Schedule retry using APScheduler
    scheduler.add_job(
        perform_backup,
        'date',
        run_date=retry_time,
        args=[backup_id],
        id=f"retry_backup_{backup_id}_{datetime.utcnow().timestamp()}",
        replace_existing=False,
    )
    
    logger.info(
        f"Scheduled retry for backup {backup_id} at {retry_time} "
        f"({retry_delay} seconds from now)"
    )


async def perform_backup(backup_id: int):
    """Perform backup operation."""
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
                "notification_on_backup_success",
                "notification_on_backup_failure",
            ],
        )
        email_service.configure_from_settings_map(settings_map, recipients)
        webhook_service.configure_from_settings_map(settings_map)
        notify_backup_success = parse_bool_setting(
            settings_map.get("notification_on_backup_success")
        )
        notify_backup_failure = parse_bool_setting(
            settings_map.get("notification_on_backup_failure")
        )

        logger.info(
            "Notification settings loaded: recipients=%s webhook_url=%s smtp_host=%s notify_success=%s notify_failure=%s",
            len(recipients),
            settings_map.get("notification_webhook_url"),
            settings_map.get("smtp_server"),
            notify_backup_success,
            notify_backup_failure,
        )

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

            # Send email notification
            await email_service.send_backup_started(backup_id, ldap_server.name, recipients)

            # Record metrics
            MetricsService.record_backup_started(backup.backup_type.value)

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

            # Generate backup filename
            filename = backup_service.generate_backup_filename(
                ldap_server.name, backup.backup_type.value
            )
            file_path = backup_service.get_backup_path(filename)

            # Perform backup based on category
            if backup.category == BackupCategory.SCHEMA:
                entry_count = ldap_service.backup_schema(file_path)
            elif backup.category == BackupCategory.CONFIG:
                entry_count = ldap_service.backup_config(file_path)
            elif backup.category == BackupCategory.ACL:
                entry_count = ldap_service.backup_acls(file_path)
            elif backup.category == BackupCategory.CERTIFICATES:
                entry_count = ldap_service.backup_certificates(file_path)
            elif backup.backup_type == BackupType.INCREMENTAL and backup.parent_backup_id:
                # Get parent backup timestamp for incremental filtering
                result = await db.execute(
                    select(Backup).where(Backup.id == backup.parent_backup_id)
                )
                parent_backup = result.scalar_one_or_none()

                if parent_backup and parent_backup.completed_at:
                    # Convert parent backup timestamp to LDAP format (YYYYMMDDHHMMSSZ)
                    # e.g., 20260212175000Z for 2026-02-12 17:50:00 UTC
                    ldap_timestamp = parent_backup.completed_at.strftime("%Y%m%d%H%M%SZ")
                    # Search filter: entries modified since parent backup completion
                    # (&(objectClass=*)(modifyTimestamp>=20260212175000Z))
                    search_filter = f"(&(objectClass=*)(modifyTimestamp>={ldap_timestamp}))"
                    logger.info(
                        f"Incremental backup for {backup.id}: using timestamp filter {ldap_timestamp}"
                    )
                    entry_count = ldap_service.backup_to_ldif(
                        file_path, search_filter=search_filter
                    )
                else:
                    # Fallback to full backup if parent timestamp not available
                    logger.warning(
                        f"Incremental backup {backup.id}: parent backup missing/incomplete, falling back to full backup"
                    )
                    entry_count = ldap_service.backup_to_ldif(file_path)
            else:
                # Full backup (FULL_SERVER, DIRECTORY, CERTIFICATES, or standard full)
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

            # Calculate checksum and verify if enabled
            if settings.BACKUP_VERIFY_ON_COMPLETION:
                try:
                    checksum = verification_service.calculate_checksum(
                        file_path, settings.BACKUP_CHECKSUM_ALGORITHM
                    )
                    backup.checksum = checksum
                    backup.checksum_algorithm = settings.BACKUP_CHECKSUM_ALGORITHM
                    
                    # Perform comprehensive verification
                    is_valid, verification_msg = verification_service.comprehensive_verification(
                        file_path,
                        expected_checksum=checksum,
                        expected_size=file_size,
                        validate_syntax=True
                    )
                    
                    if is_valid:
                        backup.verification_status = "verified"
                        backup.verified_at = datetime.utcnow()
                        logger.info(f"Backup {backup_id} verification passed")
                    else:
                        backup.verification_status = "failed"
                        logger.warning(
                            f"Backup {backup_id} verification failed: {verification_msg}"
                        )
                        
                except Exception as e:
                    logger.error(f"Backup {backup_id} verification error: {str(e)}")
                    backup.verification_status = "failed"
                    backup.checksum = None
            else:
                # Just calculate checksum without full verification
                try:
                    checksum = verification_service.calculate_checksum(
                        file_path, settings.BACKUP_CHECKSUM_ALGORITHM
                    )
                    backup.checksum = checksum
                    backup.checksum_algorithm = settings.BACKUP_CHECKSUM_ALGORITHM
                    backup.verification_status = "not_verified"
                except Exception as e:
                    logger.error(f"Failed to calculate checksum for backup {backup_id}: {str(e)}")

            # Update backup record
            backup.status = BackupStatus.COMPLETED
            backup.file_path = file_path
            backup.file_size = file_size
            backup.entry_count = entry_count
            backup.completed_at = datetime.utcnow()
            await db.commit()
            
            # Upload to cloud storage if enabled
            if settings.S3_ENABLED and settings.S3_AUTO_UPLOAD:
                try:
                    logger.info(f"Uploading backup {backup_id} to cloud storage")
                    
                    # Generate S3 object key (path in bucket)
                    # Format: backups/YYYY/MM/DD/server_name/backup_id_filename.ldif.gz
                    from pathlib import Path
                    now = datetime.utcnow()
                    object_key = f"backups/{now.year}/{now.month:02d}/{now.day:02d}/{ldap_server.name}/backup_{backup_id}_{Path(file_path).name}"
                    
                    # Prepare metadata
                    metadata = {
                        'backup-id': str(backup_id),
                        'server-name': ldap_server.name,
                        'backup-type': backup.backup_type.value,
                        'category': backup.category.value,
                        'entry-count': str(entry_count),
                        'checksum': backup.checksum or '',
                        'checksum-algorithm': backup.checksum_algorithm or ''
                    }
                    
                    # Upload to S3
                    upload_result = await storage_service.upload_backup(
                        file_path=file_path,
                        object_key=object_key,
                        metadata=metadata,
                        storage_class=settings.S3_STORAGE_CLASS
                    )
                    
                    # Update backup record with cloud storage info
                    backup.cloud_uploaded = True
                    backup.cloud_storage_path = object_key
                    backup.cloud_uploaded_at = datetime.utcnow()
                    backup.cloud_provider = upload_result.get('provider', 'unknown')
                    backup.cloud_storage_class = settings.S3_STORAGE_CLASS
                    await db.commit()
                    
                    logger.info(
                        f"Successfully uploaded backup {backup_id} to {upload_result['provider']} "
                        f"storage at {object_key}"
                    )
                    
                    # Delete local file if auto-delete is enabled and we're keeping enough local backups
                    if settings.S3_AUTO_DELETE_LOCAL and settings.S3_KEEP_LAST_LOCAL > 0:
                        # Count local backups for this server
                        result = await db.execute(
                            select(Backup)
                            .where(
                                Backup.ldap_server_id == ldap_server.id,
                                Backup.status == BackupStatus.COMPLETED,
                                Backup.file_path.isnot(None)
                            )
                            .order_by(Backup.created_at.desc())
                        )
                        local_backups = result.scalars().all()
                        
                        # Only delete if we have more than the minimum to keep
                        if len(local_backups) > settings.S3_KEEP_LAST_LOCAL:
                            # Delete this backup's local file (it's uploaded to cloud)
                            import os
                            try:
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                    logger.info(f"Deleted local backup file: {file_path}")
                                    # Clear file_path but keep record
                                    backup.file_path = None
                                    await db.commit()
                            except Exception as del_error:
                                logger.warning(f"Failed to delete local backup file {file_path}: {del_error}")
                    
                except Exception as s3_error:
                    logger.error(f"Failed to upload backup {backup_id} to cloud storage: {s3_error}")
                    # Don't fail the backup if cloud upload fails
                    # The backup is still successful locally

            # Calculate duration
            duration = (backup.completed_at - backup.started_at).total_seconds()

            # Send webhook notification
            await webhook_service.send_backup_completed(
                backup_id, ldap_server.name, entry_count, file_size
            )

            # Send email notification
            if notify_backup_success:
                await email_service.send_backup_completed(
                    backup_id,
                    ldap_server.name,
                    entry_count,
                    file_size,
                    duration,
                    recipients,
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
            
            # Check if we should retry this backup
            will_retry = await should_retry_backup(backup)
            
            if will_retry:
                # Increment retry count
                backup.retry_count += 1
                
                # Calculate retry delay with exponential backoff
                retry_delay = calculate_retry_delay(backup.retry_count - 1)
                
                # Set next retry timestamp
                backup.next_retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)
                
                # Update status to show it will be retried
                backup.status = BackupStatus.PENDING  # Reset to pending for retry
                
                await db.commit()
                
                logger.info(
                    f"Backup {backup_id} will be retried (attempt {backup.retry_count}/{backup.max_retries}) "
                    f"in {retry_delay} seconds"
                )
                
                # Schedule the retry
                await schedule_backup_retry(backup_id, retry_delay)
                
                # Send email notification about retry
                if notify_backup_failure:
                    await email_service.send_backup_failed(
                        backup_id,
                        ldap_server.name,
                        str(e),
                        recipients,
                        will_retry=True,
                        retry_count=backup.retry_count,
                        max_retries=backup.max_retries,
                        retry_delay=retry_delay,
                    )
            else:
                # No retry - permanent failure
                await db.commit()
                
                # Send webhook notification
                await webhook_service.send_backup_failed(
                    backup_id, ldap_server.name, str(e)
                )
                
                # Send email notification (no retry)
                if notify_backup_failure:
                    await email_service.send_backup_failed(
                        backup_id, ldap_server.name, str(e), recipients
                    )

            # Record metrics
            MetricsService.record_backup_failed(backup.backup_type.value)
            MetricsService.record_ldap_connection_error(ldap_server.name)
