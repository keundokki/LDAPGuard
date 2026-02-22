import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional

from api.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""

    def __init__(self):
        self.enabled = settings.EMAIL_ENABLED
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_use_tls = settings.SMTP_USE_TLS
        self.smtp_use_ssl = settings.SMTP_USE_SSL
        self.from_email = settings.EMAIL_FROM
        self.from_name = settings.EMAIL_FROM_NAME

    def configure_from_settings_map(
        self, settings_map: dict, recipients: Optional[List[str]] = None
    ) -> None:
        """Override SMTP settings from system settings."""
        if not settings_map:
            return

        smtp_host = settings_map.get("smtp_server")
        if smtp_host:
            self.smtp_host = smtp_host

        smtp_port = settings_map.get("smtp_port")
        if smtp_port:
            try:
                self.smtp_port = int(smtp_port)
            except (TypeError, ValueError):
                logger.warning("Invalid smtp_port in system settings: %s", smtp_port)

        smtp_username = settings_map.get("smtp_username")
        if smtp_username is not None:
            self.smtp_username = smtp_username

        smtp_password = settings_map.get("smtp_password")
        if smtp_password is not None:
            self.smtp_password = smtp_password

        from_email = settings_map.get("from_email")
        smtp_from_email = settings_map.get("smtp_from_email")
        if smtp_from_email:
            self.from_email = smtp_from_email
        elif from_email:
            self.from_email = from_email

        smtp_encryption = settings_map.get("smtp_encryption")
        if smtp_encryption:
            encryption = smtp_encryption.strip().lower()
            if encryption == "ssl":
                self.smtp_use_ssl = True
                self.smtp_use_tls = False
            elif encryption == "tls":
                self.smtp_use_tls = True
                self.smtp_use_ssl = False
            elif encryption in {"none", "off", "false", "0"}:
                self.smtp_use_tls = False
                self.smtp_use_ssl = False

        if self.smtp_host and self.from_email and (recipients or smtp_host):
            self.enabled = True

    def _should_send(self, recipients: List[str], event: str) -> bool:
        if not self.enabled:
            logger.info("Email suppressed (disabled): %s", event)
            return False
        if not recipients:
            logger.info("Email suppressed (no recipients): %s", event)
            return False
        return True

    async def send_backup_started(
        self, backup_id: int, server_name: str, recipients: List[str]
    ):
        """Send notification when backup starts."""
        if not self._should_send(recipients, "backup_started"):
            return

        subject = f"🔄 Backup Started: {server_name}"
        
        html_content = self._render_template(
            "backup_started.html",
            {
                "backup_id": backup_id,
                "server_name": server_name,
                "backup_url": f"{settings.APP_URL}/backups",
            },
        )

        text_content = f"""
Backup Started

Server: {server_name}
Backup ID: {backup_id}

The backup process has been initiated.
You will receive another notification when it completes.

View backup: {settings.APP_URL}/backups
"""

        await self._send_email(recipients, subject, html_content, text_content)

    async def send_backup_completed(
        self,
        backup_id: int,
        server_name: str,
        entry_count: int,
        file_size: int,
        duration: float,
        recipients: List[str],
    ):
        """Send notification when backup completes successfully."""
        if not self._should_send(recipients, "backup_completed"):
            return

        subject = f"✅ Backup Completed: {server_name}"
        
        # Format file size
        file_size_mb = file_size / (1024 * 1024)
        duration_min = int(duration / 60)
        duration_sec = int(duration % 60)

        html_content = self._render_template(
            "backup_success.html",
            {
                "backup_id": backup_id,
                "server_name": server_name,
                "entry_count": entry_count,
                "file_size": f"{file_size_mb:.2f} MB",
                "duration": f"{duration_min}m {duration_sec}s" if duration_min > 0 else f"{duration_sec}s",
                "backup_url": f"{settings.APP_URL}/backups",
            },
        )

        text_content = f"""
Backup Completed Successfully

Server: {server_name}
Backup ID: {backup_id}
Entries: {entry_count:,}
Size: {file_size_mb:.2f} MB
Duration: {duration_min}m {duration_sec}s

Your LDAP directory has been backed up successfully.

View backup: {settings.APP_URL}/backups
"""

        await self._send_email(recipients, subject, html_content, text_content)

    async def send_backup_failed(
        self, 
        backup_id: int, 
        server_name: str, 
        error: str, 
        recipients: List[str],
        will_retry: bool = False,
        retry_count: int = 0,
        max_retries: int = 0,
        retry_delay: int = 0
    ):
        """Send notification when backup fails.
        
        Args:
            backup_id: ID of the backup
            server_name: Name of the LDAP server
            error: Error message
            recipients: List of email recipients
            will_retry: Whether the backup will be automatically retried
            retry_count: Current retry attempt number
            max_retries: Maximum number of retries allowed
            retry_delay: Delay in seconds before next retry
        """
        if not self._should_send(recipients, "backup_failed"):
            return

        if will_retry:
            subject = f"⚠️ Backup Failed (Will Retry): {server_name}"
        else:
            subject = f"❌ Backup Failed: {server_name}"
        
        # Calculate retry time for display
        retry_minutes = retry_delay // 60 if retry_delay > 0 else 0
        
        # Build retry-specific content
        if will_retry:
            icon = "⚠️"
            status_text = "Failed (Will Retry)"
            action_required = "An automatic retry has been scheduled."
            retry_warning = f'''
            <div class="retry-warning">
                <h2>🔄 Automatic Retry Scheduled</h2>
                <p><strong>Retry Attempt:</strong> {retry_count} of {max_retries}</p>
                <p><strong>Next Retry In:</strong> {retry_minutes} minutes</p>
                <p style="margin-top: 15px;">This backup will be automatically retried. You'll receive another notification when the retry attempt completes.</p>
            </div>
            '''
            retry_info_rows = f'''
                <div class="info-row">
                    <div class="info-label">Retry Status:</div>
                    <div class="info-value"><strong>Scheduled ({retry_count}/{max_retries})</strong></div>
                </div>
                <div class="info-row">
                    <div class="info-label">Next Attempt:</div>
                    <div class="info-value">In ~{retry_minutes} minutes</div>
                </div>
            '''
        else:
            icon = "❌"
            status_text = "Failed"
            action_required = "Immediate attention may be required."
            retry_warning = ""
            retry_info_rows = ""
        
        html_content = self._render_template(
            "backup_failed.html",
            {
                "backup_id": backup_id,
                "server_name": server_name,
                "error": error,
                "backup_url": f"{settings.APP_URL}/backups",
                "will_retry": will_retry,
                "retry_count": retry_count,
                "max_retries": max_retries,
                "retry_delay": retry_delay,
                "retry_minutes": retry_minutes,
                "icon": icon,
                "status_text": status_text,
                "action_required": action_required,
                "retry_warning": retry_warning,
                "retry_info_rows": retry_info_rows,
            },
        )

        retry_info = ""
        if will_retry:
            retry_info = f"""
🔄 AUTOMATIC RETRY SCHEDULED
Retry attempt: {retry_count} of {max_retries}
Next retry in: {retry_minutes} minutes

This backup will be automatically retried. You will receive another notification
when the retry attempt completes.
"""
        
        text_content = f"""
Backup Failed

Server: {server_name}
Backup ID: {backup_id}
Error: {error}
{retry_info}
The backup process encountered an error and could not complete.
Please check the logs and verify LDAP server connectivity.

View details: {settings.APP_URL}/backups

Troubleshooting:
- Verify LDAP server is accessible
- Check bind credentials
- Ensure sufficient disk space
- Review worker logs for details
"""

        await self._send_email(recipients, subject, html_content, text_content)

    async def send_restore_started(
        self, restore_id: int, backup_id: int, recipients: List[str]
    ):
        """Send notification when restore starts."""
        if not self._should_send(recipients, "restore_started"):
            return

        subject = f"🔄 Restore Started: Backup #{backup_id}"
        
        html_content = self._render_template(
            "restore_started.html",
            {
                "restore_id": restore_id,
                "backup_id": backup_id,
                "restore_url": f"{settings.APP_URL}/restores",
            },
        )

        text_content = f"""
Restore Started

Restore ID: {restore_id}
Backup ID: {backup_id}

The restore process has been initiated.
You will receive another notification when it completes.

View restore: {settings.APP_URL}/restores
"""

        await self._send_email(recipients, subject, html_content, text_content)

    async def send_restore_completed(
        self,
        restore_id: int,
        backup_id: int,
        entries_restored: int,
        duration: float,
        recipients: List[str],
    ):
        """Send notification when restore completes successfully."""
        if not self._should_send(recipients, "restore_completed"):
            return

        subject = f"✅ Restore Completed: Backup #{backup_id}"
        
        duration_min = int(duration / 60)
        duration_sec = int(duration % 60)

        html_content = self._render_template(
            "restore_success.html",
            {
                "restore_id": restore_id,
                "backup_id": backup_id,
                "entries_restored": entries_restored,
                "duration": f"{duration_min}m {duration_sec}s" if duration_min > 0 else f"{duration_sec}s",
                "restore_url": f"{settings.APP_URL}/restores",
            },
        )

        text_content = f"""
Restore Completed Successfully

Restore ID: {restore_id}
Backup ID: {backup_id}
Entries Restored: {entries_restored:,}
Duration: {duration_min}m {duration_sec}s

Your LDAP directory has been restored successfully.

View restore: {settings.APP_URL}/restores
"""

        await self._send_email(recipients, subject, html_content, text_content)

    async def send_restore_failed(
        self, restore_id: int, backup_id: int, error: str, recipients: List[str]
    ):
        """Send notification when restore fails."""
        if not self._should_send(recipients, "restore_failed"):
            return

        subject = f"❌ Restore Failed: Backup #{backup_id}"
        
        html_content = self._render_template(
            "restore_failed.html",
            {
                "restore_id": restore_id,
                "backup_id": backup_id,
                "error": error,
                "restore_url": f"{settings.APP_URL}/restores",
            },
        )

        text_content = f"""
Restore Failed

Restore ID: {restore_id}
Backup ID: {backup_id}
Error: {error}

The restore process encountered an error and could not complete.
Please check the logs and verify target LDAP server configuration.

View details: {settings.APP_URL}/restores

Troubleshooting:
- Verify target LDAP server is accessible
- Check bind credentials
- Ensure target DN exists or can be created
- Review worker logs for details
"""

        await self._send_email(recipients, subject, html_content, text_content)

    async def _send_email(
        self,
        recipients: List[str],
        subject: str,
        html_content: str,
        text_content: str,
    ):
        """Send email via SMTP."""
        if not recipients:
            logger.warning("No recipients specified for email")
            return

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = ", ".join(recipients)

            # Attach text and HTML versions
            part1 = MIMEText(text_content, "plain", "utf-8")
            part2 = MIMEText(html_content, "html", "utf-8")
            msg.attach(part1)
            msg.attach(part2)

            # Send email
            if self.smtp_use_ssl:
                # Use SSL (typically port 465)
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    if self.smtp_username and self.smtp_password:
                        server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
            else:
                # Use TLS (typically port 587) or no encryption (port 25)
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    if self.smtp_use_tls:
                        server.starttls()
                    if self.smtp_username and self.smtp_password:
                        server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)

            logger.info(f"Email sent successfully to {recipients}: {subject}")

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            # Don't raise - we don't want email failures to break backup/restore

    def _render_template(self, template_name: str, context: dict) -> str:
        """Render email template with context."""
        template_dir = Path(__file__).parent.parent / "templates" / "email"
        template_path = template_dir / template_name

        # If template exists, use it
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()
            
            # Simple template rendering (replace {{variable}} with value)
            for key, value in context.items():
                template = template.replace(f"{{{{{key}}}}}", str(value))
            
            return template

        # Fallback to basic HTML if template doesn't exist
        return self._get_fallback_template(template_name, context)

    def _get_fallback_template(self, template_name: str, context: dict) -> str:
        """Get fallback HTML template."""
        base_style = """
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
            .content { background: white; padding: 30px; border: 1px solid #e2e8f0; border-top: none; }
            .footer { background: #f8fafc; padding: 20px; text-align: center; color: #64748b; font-size: 14px; border-radius: 0 0 8px 8px; }
            .button { display: inline-block; padding: 12px 24px; background: #2563eb; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }
            .info-box { background: #f1f5f9; padding: 15px; border-radius: 6px; margin: 15px 0; }
            .success { border-left: 4px solid #16a34a; }
            .error { border-left: 4px solid #dc2626; }
            .warning { border-left: 4px solid #ea580c; }
        </style>
        """

        if "failed" in template_name:
            icon = "❌"
            status_class = "error"
        elif "success" in template_name or "completed" in template_name:
            icon = "✅"
            status_class = "success"
        else:
            icon = "🔄"
            status_class = "warning"

        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8">{base_style}</head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{icon} LDAPGuard</h1>
                </div>
                <div class="content">
                    <div class="info-box {status_class}">
                        {self._get_fallback_content(template_name, context)}
                    </div>
                    <a href="{context.get('backup_url', context.get('restore_url', '#'))}" class="button">
                        View Details
                    </a>
                </div>
                <div class="footer">
                    <p>This is an automated notification from LDAPGuard</p>
                    <p>Do not reply to this email</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_fallback_content(self, template_name: str, context: dict) -> str:
        """Get fallback content for template."""
        if "backup_failed" in template_name:
            return f"""
                <h2>Backup Failed</h2>
                <p><strong>Server:</strong> {context.get('server_name')}</p>
                <p><strong>Backup ID:</strong> {context.get('backup_id')}</p>
                <p><strong>Error:</strong> {context.get('error')}</p>
            """
        elif "backup_success" in template_name:
            return f"""
                <h2>Backup Completed Successfully</h2>
                <p><strong>Server:</strong> {context.get('server_name')}</p>
                <p><strong>Backup ID:</strong> {context.get('backup_id')}</p>
                <p><strong>Entries:</strong> {context.get('entry_count')}</p>
                <p><strong>Size:</strong> {context.get('file_size')}</p>
                <p><strong>Duration:</strong> {context.get('duration')}</p>
            """
        elif "backup_started" in template_name:
            return f"""
                <h2>Backup Started</h2>
                <p><strong>Server:</strong> {context.get('server_name')}</p>
                <p><strong>Backup ID:</strong> {context.get('backup_id')}</p>
            """
        elif "restore_failed" in template_name:
            return f"""
                <h2>Restore Failed</h2>
                <p><strong>Restore ID:</strong> {context.get('restore_id')}</p>
                <p><strong>Backup ID:</strong> {context.get('backup_id')}</p>
                <p><strong>Error:</strong> {context.get('error')}</p>
            """
        elif "restore_success" in template_name:
            return f"""
                <h2>Restore Completed Successfully</h2>
                <p><strong>Restore ID:</strong> {context.get('restore_id')}</p>
                <p><strong>Backup ID:</strong> {context.get('backup_id')}</p>
                <p><strong>Entries Restored:</strong> {context.get('entries_restored')}</p>
                <p><strong>Duration:</strong> {context.get('duration')}</p>
            """
        elif "restore_started" in template_name:
            return f"""
                <h2>Restore Started</h2>
                <p><strong>Restore ID:</strong> {context.get('restore_id')}</p>
                <p><strong>Backup ID:</strong> {context.get('backup_id')}</p>
            """
        else:
            return "<p>Notification from LDAPGuard</p>"
