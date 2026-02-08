import asyncio
import logging
import os
import sys

import redis.asyncio as redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from api.core.config import settings
from api.core.database import AsyncSessionLocal
from api.models.models import Backup, BackupStatus, ScheduledBackup
from workers.tasks.backup_task import perform_backup
from workers.tasks.restore_task import perform_restore

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class WorkerService:
    """Main worker service for scheduled tasks."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.redis_client = None

    async def setup_redis(self):
        """Setup Redis connection."""
        try:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL, decode_responses=True
            )
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")

    async def load_scheduled_backups(self):
        """Load scheduled backups from database and sync scheduler jobs."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ScheduledBackup).where(ScheduledBackup.is_active)
            )
            scheduled_backups = result.scalars().all()

        logger.info(f"Found {len(scheduled_backups)} active scheduled backups in database")

        active_ids = {schedule.id for schedule in scheduled_backups}

        for scheduled_backup in scheduled_backups:
            try:
                logger.info(
                    f"Adding scheduled backup: {scheduled_backup.name} "
                    f"(id: {scheduled_backup.id}, cron: {scheduled_backup.cron_expression})"
                )
                # Add or update scheduled job
                self.scheduler.add_job(
                    self.execute_scheduled_backup,
                    CronTrigger.from_crontab(scheduled_backup.cron_expression),
                    args=[scheduled_backup.id],
                    id=f"scheduled_backup_{scheduled_backup.id}",
                    replace_existing=True,
                )
                logger.info(
                    f"Successfully added scheduled backup: {scheduled_backup.name} "
                    f"(cron: {scheduled_backup.cron_expression})"
                )
            except Exception as e:
                logger.error(
                    f"Failed to add scheduled backup {scheduled_backup.id}: {e}", exc_info=True
                )

        # Remove jobs that no longer exist or were deactivated
        for job in self.scheduler.get_jobs():
            if not job.id.startswith("scheduled_backup_"):
                continue
            try:
                schedule_id = int(job.id.replace("scheduled_backup_", ""))
            except ValueError:
                continue
            if schedule_id not in active_ids:
                self.scheduler.remove_job(job.id)
                logger.info(f"Removed scheduled backup job {job.id}")

        # Log all current jobs
        all_jobs = self.scheduler.get_jobs()
        logger.info(f"Scheduler now has {len(all_jobs)} total jobs")
        for job in all_jobs:
            logger.info(f"  - Job ID: {job.id}, Next run scheduled")

    async def execute_scheduled_backup(self, scheduled_backup_id: int):
        """Execute a scheduled backup."""
        logger.info(f"Executing scheduled backup {scheduled_backup_id}")

        async with AsyncSessionLocal() as db:
            # Get scheduled backup
            result = await db.execute(
                select(ScheduledBackup).where(ScheduledBackup.id == scheduled_backup_id)
            )
            scheduled_backup = result.scalar_one_or_none()

            if not scheduled_backup or not scheduled_backup.is_active:
                logger.warning(
                    f"Scheduled backup {scheduled_backup_id} not found or inactive"
                )
                return

            # Get a valid user to attribute the backup to
            # For automatic scheduled backups, we use the first available user
            from api.models.models import User
            logger.info("Querying for available users")
            result = await db.execute(select(User))
            user = result.scalars().first()
            logger.info(f"Found user: {user.id if user else 'None'}")
            
            if not user:
                logger.error("No users found in database, cannot create scheduled backup")
                return

            # Create backup record
            new_backup = Backup(
                ldap_server_id=scheduled_backup.ldap_server_id,
                backup_type=scheduled_backup.backup_type,
                encrypted=True,
                compression_enabled=True,
                status=BackupStatus.PENDING,
                created_by=user.id,  # Use the first available user
            )

            db.add(new_backup)
            await db.commit()
            await db.refresh(new_backup)

            # Perform backup
            await perform_backup(new_backup.id)

    async def process_backup_queue(self):
        """Process backup requests from Redis queue."""
        if not self.redis_client:
            return

        try:
            # Check for pending backup jobs from Redis
            backup_id = await self.redis_client.lpop("backup_queue")

            if backup_id:
                logger.info(f"Processing backup {backup_id} from queue")
                await perform_backup(int(backup_id))
                return

            # Fallback: process oldest pending backup from DB
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Backup)
                    .where(Backup.status == BackupStatus.PENDING)
                    .order_by(Backup.created_at.asc())
                    .limit(1)
                )
                pending_backup = result.scalar_one_or_none()

            if pending_backup:
                logger.info(
                    f"Processing pending backup {pending_backup.id} from database"
                )
                await perform_backup(pending_backup.id)
        except Exception as e:
            logger.error(f"Error processing backup queue: {e}")

    async def process_restore_queue(self):
        """Process restore requests from Redis queue."""
        if not self.redis_client:
            return

        try:
            # Check for pending restore jobs
            restore_id = await self.redis_client.lpop("restore_queue")

            if restore_id:
                logger.info(f"Processing restore {restore_id} from queue")
                await perform_restore(int(restore_id))
        except Exception as e:
            logger.error(f"Error processing restore queue: {e}")

    async def queue_processor_loop(self):
        """Continuous loop to process queues."""
        while True:
            await self.process_backup_queue()
            await self.process_restore_queue()
            await asyncio.sleep(5)  # Check every 5 seconds

    async def start(self):
        """Start the worker service."""
        logger.info("Starting LDAPGuard Worker Service")

        # Setup Redis
        await self.setup_redis()

        # Load scheduled backups
        await self.load_scheduled_backups()

        # Refresh scheduled backups periodically to pick up changes
        self.scheduler.add_job(
            self.load_scheduled_backups,
            "interval",
            minutes=1,
            id="refresh_schedules",
            replace_existing=True,
        )

        # Start scheduler
        self.scheduler.start()
        logger.info("Scheduler started")

        # Run queue processor and keep the service alive
        await self.queue_processor_loop()

    async def stop(self):
        """Stop the worker service."""
        logger.info("Stopping LDAPGuard Worker Service")

        if self.scheduler.running:
            self.scheduler.shutdown()

        if self.redis_client:
            await self.redis_client.close()


async def main():
    """Main entry point."""
    worker = WorkerService()

    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        await worker.stop()
    except Exception as e:
        logger.error(f"Worker error: {e}")
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
