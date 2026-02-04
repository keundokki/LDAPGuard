import httpx
from typing import Dict, Any
from api.core.config import settings
import logging

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for sending webhook notifications."""
    
    def __init__(self):
        self.enabled = settings.WEBHOOK_ENABLED
        self.url = settings.WEBHOOK_URL
    
    async def send_backup_started(self, backup_id: int, server_name: str):
        """Send notification when backup starts."""
        if not self.enabled or not self.url:
            return
        
        payload = {
            "event": "backup.started",
            "backup_id": backup_id,
            "server_name": server_name,
            "timestamp": self._get_timestamp()
        }
        
        await self._send_webhook(payload)
    
    async def send_backup_completed(self, backup_id: int, server_name: str, 
                                   entry_count: int, file_size: int):
        """Send notification when backup completes."""
        if not self.enabled or not self.url:
            return
        
        payload = {
            "event": "backup.completed",
            "backup_id": backup_id,
            "server_name": server_name,
            "entry_count": entry_count,
            "file_size": file_size,
            "timestamp": self._get_timestamp()
        }
        
        await self._send_webhook(payload)
    
    async def send_backup_failed(self, backup_id: int, server_name: str, error: str):
        """Send notification when backup fails."""
        if not self.enabled or not self.url:
            return
        
        payload = {
            "event": "backup.failed",
            "backup_id": backup_id,
            "server_name": server_name,
            "error": error,
            "timestamp": self._get_timestamp()
        }
        
        await self._send_webhook(payload)
    
    async def send_restore_started(self, restore_id: int, backup_id: int):
        """Send notification when restore starts."""
        if not self.enabled or not self.url:
            return
        
        payload = {
            "event": "restore.started",
            "restore_id": restore_id,
            "backup_id": backup_id,
            "timestamp": self._get_timestamp()
        }
        
        await self._send_webhook(payload)
    
    async def send_restore_completed(self, restore_id: int, backup_id: int, entries_restored: int):
        """Send notification when restore completes."""
        if not self.enabled or not self.url:
            return
        
        payload = {
            "event": "restore.completed",
            "restore_id": restore_id,
            "backup_id": backup_id,
            "entries_restored": entries_restored,
            "timestamp": self._get_timestamp()
        }
        
        await self._send_webhook(payload)
    
    async def _send_webhook(self, payload: Dict[str, Any]):
        """Send webhook HTTP POST request."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.url,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Webhook sent successfully: {payload['event']}")
        except Exception as e:
            logger.error(f"Failed to send webhook: {str(e)}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
