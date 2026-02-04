from fastapi import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Define metrics
backup_total = Counter(
    "ldapguard_backup_total", "Total number of backups", ["status", "backup_type"]
)

backup_duration = Histogram(
    "ldapguard_backup_duration_seconds", "Backup duration in seconds", ["backup_type"]
)

backup_size_bytes = Gauge(
    "ldapguard_backup_size_bytes", "Size of backup files in bytes", ["server_name"]
)

backup_entries = Gauge(
    "ldapguard_backup_entries", "Number of entries in backup", ["server_name"]
)

restore_total = Counter(
    "ldapguard_restore_total", "Total number of restore operations", ["status"]
)

restore_duration = Histogram(
    "ldapguard_restore_duration_seconds", "Restore duration in seconds"
)

ldap_connection_errors = Counter(
    "ldapguard_ldap_connection_errors_total",
    "Total number of LDAP connection errors",
    ["server_name"],
)

active_backups = Gauge(
    "ldapguard_active_backups", "Number of currently active backup operations"
)

active_restores = Gauge(
    "ldapguard_active_restores", "Number of currently active restore operations"
)


class MetricsService:
    """Service for Prometheus metrics."""

    @staticmethod
    def record_backup_started(backup_type: str):
        """Record backup start."""
        active_backups.inc()

    @staticmethod
    def record_backup_completed(
        backup_type: str, duration: float, server_name: str, size: int, entries: int
    ):
        """Record successful backup completion."""
        backup_total.labels(status="completed", backup_type=backup_type).inc()
        backup_duration.labels(backup_type=backup_type).observe(duration)
        backup_size_bytes.labels(server_name=server_name).set(size)
        backup_entries.labels(server_name=server_name).set(entries)
        active_backups.dec()

    @staticmethod
    def record_backup_failed(backup_type: str):
        """Record failed backup."""
        backup_total.labels(status="failed", backup_type=backup_type).inc()
        active_backups.dec()

    @staticmethod
    def record_restore_started():
        """Record restore start."""
        active_restores.inc()

    @staticmethod
    def record_restore_completed(duration: float):
        """Record successful restore completion."""
        restore_total.labels(status="completed").inc()
        restore_duration.observe(duration)
        active_restores.dec()

    @staticmethod
    def record_restore_failed():
        """Record failed restore."""
        restore_total.labels(status="failed").inc()
        active_restores.dec()

    @staticmethod
    def record_ldap_connection_error(server_name: str):
        """Record LDAP connection error."""
        ldap_connection_errors.labels(server_name=server_name).inc()

    @staticmethod
    def get_metrics() -> Response:
        """Get metrics in Prometheus format."""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
