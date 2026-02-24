import logging
from typing import Any, Dict

import httpx

from api.core.config import settings

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for sending webhook notifications."""

    def __init__(self):
        self.enabled = settings.WEBHOOK_ENABLED
        self.url = settings.WEBHOOK_URL

    def configure_from_settings_map(self, settings_map: dict) -> None:
        """Override webhook settings from system settings."""
        if not settings_map:
            return

        webhook_url = settings_map.get("notification_webhook_url")
        if webhook_url:
            self.url = webhook_url
            self.enabled = True

    def _should_send(self, event: str) -> bool:
        if not self.enabled:
            logger.info("Webhook suppressed (disabled): %s", event)
            return False
        if not self.url:
            logger.info("Webhook suppressed (no URL): %s", event)
            return False
        return True

    async def send_backup_started(self, backup_id: int, server_name: str):
        """Send notification when backup starts."""
        if not self._should_send("backup.started"):
            return

        payload = {
            "event": "backup.started",
            "backup_id": backup_id,
            "server_name": server_name,
            "timestamp": self._get_timestamp(),
        }

        await self._send_webhook(payload)

    async def send_backup_completed(
        self, backup_id: int, server_name: str, entry_count: int, file_size: int
    ):
        """Send notification when backup completes."""
        if not self._should_send("backup.completed"):
            return

        payload = {
            "event": "backup.completed",
            "backup_id": backup_id,
            "server_name": server_name,
            "entry_count": entry_count,
            "file_size": file_size,
            "timestamp": self._get_timestamp(),
        }

        await self._send_webhook(payload)

    async def send_backup_failed(self, backup_id: int, server_name: str, error: str):
        """Send notification when backup fails."""
        if not self._should_send("backup.failed"):
            return

        payload = {
            "event": "backup.failed",
            "backup_id": backup_id,
            "server_name": server_name,
            "error": error,
            "timestamp": self._get_timestamp(),
        }

        await self._send_webhook(payload)

    async def send_restore_started(self, restore_id: int, backup_id: int):
        """Send notification when restore starts."""
        if not self._should_send("restore.started"):
            return

        payload = {
            "event": "restore.started",
            "restore_id": restore_id,
            "backup_id": backup_id,
            "timestamp": self._get_timestamp(),
        }

        await self._send_webhook(payload)

    async def send_restore_completed(
        self, restore_id: int, backup_id: int, entries_restored: int
    ):
        """Send notification when restore completes."""
        if not self._should_send("restore.completed"):
            return

        payload = {
            "event": "restore.completed",
            "restore_id": restore_id,
            "backup_id": backup_id,
            "entries_restored": entries_restored,
            "timestamp": self._get_timestamp(),
        }

        await self._send_webhook(payload)

    async def _send_webhook(self, payload: Dict[str, Any]):
        """Send webhook HTTP POST request."""
        if not self.url:
            logger.info("Webhook suppressed (no URL): %s", payload.get("event"))
            return

        webhook_payload = payload
        if "discord.com/api/webhooks" in self.url:
            webhook_payload = {
                "content": self._format_discord_content(payload),
            }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.url, json=webhook_payload, timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Webhook sent successfully: {payload['event']}")
        except httpx.HTTPStatusError as e:
            response_text = e.response.text.strip()
            detail = response_text if response_text else str(e)
            logger.error(f"Failed to send webhook: {detail}")
        except Exception as e:
            logger.error(f"Failed to send webhook: {str(e)}")

    def _format_discord_content(self, payload: Dict[str, Any]) -> str:
        event = payload.get("event", "event")
        if event == "backup.started":
            return (
                f"[LDAPGuard] Backup started for {payload.get('server_name')}"
                f" (id: {payload.get('backup_id')})."
            )
        if event == "backup.completed":
            return (
                f"[LDAPGuard] Backup completed for {payload.get('server_name')}"
                f" (id: {payload.get('backup_id')}, entries: {payload.get('entry_count')}).")  # noqa: E501
        if event == "backup.failed":
            return (
                f"[LDAPGuard] Backup failed for {payload.get('server_name')}"
                f" (id: {payload.get('backup_id')})."
            )
        if event == "restore.started":
            return (
                f"[LDAPGuard] Restore started (restore id: {payload.get('restore_id')},"
                f" backup id: {payload.get('backup_id')})."
            )
        if event == "restore.completed":
            return (
                f"[LDAPGuard] Restore completed (restore id: {payload.get('restore_id')},"  # noqa: E501
                f" backup id: {payload.get('backup_id')}, entries: {payload.get('entries_restored')}).")  # noqa: E501
        return f"[LDAPGuard] {event}"

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime

        return datetime.utcnow().isoformat()
