# Backup Retry Logic

LDAPGuard automatically retries failed backup operations using exponential backoff. This feature dramatically improves reliability by handling transient failures like temporary network issues, LDAP server restarts, or brief connectivity problems.

## 🎯 Overview

When a backup fails, LDAPGuard can automatically:
- ✅ **Retry the backup** with intelligent delay spacing
- ✅ **Use exponential backoff** to avoid overwhelming servers
- ✅ **Send notifications** for each retry attempt
- ✅ **Track retry history** in the database
- ✅ **Give up gracefully** after max retries exceeded

## ⚙️ Configuration

Add these settings to your `.env` file:

```bash
# Enable automatic retry (default: true)
BACKUP_RETRY_ENABLED=true

# Maximum number of retry attempts (default: 3)
BACKUP_MAX_RETRIES=3

# Initial retry delay in seconds (default: 300 = 5 minutes)
BACKUP_RETRY_DELAY=300

# Exponential backoff multiplier (default: 2.0)
BACKUP_RETRY_BACKOFF=2.0
```

### Retry Schedule Examples

**Default settings** (`DELAY=300`, `BACKOFF=2.0`, `MAX_RETRIES=3`):
```
Initial attempt:  Fails at 10:00 AM
Retry 1:         10:05 AM  (5 minutes later)
Retry 2:         10:15 AM  (10 minutes later)
Retry 3:         10:35 AM  (20 minutes later)
Final:           Gives up after 3 retries
```

**Conservative settings** (`DELAY=600`, `BACKOFF=3.0`, `MAX_RETRIES=2`):
```
Initial attempt:  Fails at 10:00 AM
Retry 1:         10:10 AM  (10 minutes later)
Retry 2:         10:40 AM  (30 minutes later)
Final:           Gives up after 2 retries
```

**Aggressive settings** (`DELAY=60`, `BACKOFF=1.5`, `MAX_RETRIES=5`):
```
Initial attempt:  Fails at 10:00 AM
Retry 1:         10:01 AM  (1 minute later)
Retry 2:         10:02:30 AM  (1.5 minutes later)
Retry 3:         10:04:45 AM  (2.25 minutes later)
Retry 4:         10:08:08 AM  (3.38 minutes later)
Retry 5:         10:13:11 AM  (5.07 minutes later)
Final:           Gives up after 5 retries
```

## 📐 Exponential Backoff Formula

```
delay = BACKUP_RETRY_DELAY * (BACKUP_RETRY_BACKOFF ^ retry_attempt)
```

Where:
- `retry_attempt` is 0-indexed (0 for 1st retry, 1 for 2nd retry, etc.)
- Maximum delay is capped at 1 hour (3600 seconds)

**Examples:**
```
Attempt 1:  300 * (2.0 ^ 0) = 300 seconds  (5 minutes)
Attempt 2:  300 * (2.0 ^ 1) = 600 seconds  (10 minutes)
Attempt 3:  300 * (2.0 ^ 2) = 1200 seconds (20 minutes)
Attempt 4:  300 * (2.0 ^ 3) = 2400 seconds (40 minutes)
Attempt 5:  300 * (2.0 ^ 4) = 3600 seconds (60 minutes - capped)
```

## 🚫 Non-Retryable Errors

Some errors **will not trigger retries** because they require manual intervention:

- `"not found"` - Missing LDAP entries or configuration
- `"invalid credentials"` - Wrong bind DN or password
- `"permission denied"` - Insufficient LDAP permissions
- `"authentication failed"` - Authentication issues

**Errors that WILL be retried:**
- Network timeouts
- Connection refused
- Temporary unavailability
- Generic I/O errors
- LDAP server overload

## 📊 Monitoring Retries

### Web UI

The backup status shows retry information:

```
┌─────────────────────────────────────────┐
│ Status: pending                         │
│ 🔄 Retry 2/3                           │
│ Next: 10:15:30 AM                      │
└─────────────────────────────────────────┘
```

### Email Notifications

When retries are enabled, you'll receive:

**1. First failure (retry scheduled):**
```
Subject: ⚠️ Backup Failed (Will Retry): Production LDAP

🔄 Automatic Retry Scheduled
Retry Attempt: 1 of 3
Next Retry In: 5 minutes

This backup will be automatically retried.
```

**2. Subsequent retry failures:**
```
Subject: ⚠️ Backup Failed (Will Retry): Production LDAP

🔄 Automatic Retry Scheduled
Retry Attempt: 2 of 3
Next Retry In: 10 minutes
```

**3. Final failure (no more retries):**
```
Subject: ❌ Backup Failed: Production LDAP

The backup has failed after 3 retry attempts.
Manual intervention required.
```

**4. Successful retry:**
```
Subject: ✅ Backup Completed: Production LDAP

Your backup completed successfully after 2 retry attempts.
```

### Worker Logs

Monitor retry activity:

```bash
# Docker/Podman
docker compose logs -f worker | grep -i retry

# Kubernetes
kubectl logs -f deployment/ldapguard-worker -n ldapguard | grep -i retry
```

**Example log output:**
```
INFO: Backup 123 failed: Connection timeout
INFO: Backup 123 will be retried (attempt 1/3) in 300 seconds
INFO: Scheduled retry for backup 123 at 2026-02-14 10:05:00
INFO: Backup 123 retry attempt 1 started
INFO: Backup 123 completed successfully after retry
```

### Database Queries

Check retry status directly:

```sql
-- Backups with active retries
SELECT 
    id, 
    status, 
    retry_count, 
    max_retries, 
    next_retry_at, 
    error_message
FROM backups 
WHERE retry_count > 0 
ORDER BY next_retry_at DESC;

-- Failed backups that exhausted retries
SELECT 
    id, 
    ldap_server_id, 
    retry_count, 
    max_retries, 
    error_message, 
    completed_at
FROM backups 
WHERE status = 'failed' 
  AND retry_count >= max_retries;

-- Success rate after retries
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN status = 'completed' AND retry_count > 0 THEN 1 ELSE 0 END) as recovered_by_retry,
    SUM(CASE WHEN status = 'failed' AND retry_count >= max_retries THEN 1 ELSE 0 END) as permanent_failures
FROM backups 
WHERE created_at > NOW() - INTERVAL '7 days';
```

## 🔧 Advanced Configuration

### Per-Server Retry Settings (Future Enhancement)

Currently, retry settings are global. To implement per-server retry limits:

```python
# In api/models/models.py - LDAPServer model
max_retries = Column(Integer, default=None)  # None = use global default
retry_enabled = Column(Boolean, default=None)  # None = use global default

# Then in backup_task.py
if ldap_server.retry_enabled is not None:
    retry_enabled = ldap_server.retry_enabled
else:
    retry_enabled = settings.BACKUP_RETRY_ENABLED
```

### Disable Retries for Specific Backup Types

Edit `backup_task.py`:

```python
async def should_retry_backup(backup: Backup) -> bool:
    # Don't retry manual backups (only scheduled ones)
    if backup.backup_type == BackupType.MANUAL:
        return False
    
    # Existing logic...
```

### Custom Retry Notification Recipients

To send retry notifications to different recipients than regular notifications:

```python
# In system_settings
notification_email_retry = "ops-oncall@example.com"

# In backup_task.py
if will_retry:
    retry_recipients = await get_setting(db, "notification_email_retry")
    if not retry_recipients:
        retry_recipients = recipients  # Fallback to regular
```

## 🐛 Troubleshooting

### Retries Not Working

**Check if retries are enabled:**
```bash
docker compose exec api env | grep BACKUP_RETRY_ENABLED
# Should output: BACKUP_RETRY_ENABLED=true
```

**Check logs for retry scheduling:**
```bash
docker compose logs worker | grep "will be retried"
```

**Verify database migration ran:**
```bash
docker compose exec api alembic current
# Should show: 005 or later
```

**Check for non-retryable errors:**
```bash
# Look for errors containing these keywords
docker compose logs worker | grep -iE "not found|invalid credentials|permission denied"
```

### Retries Stop After Service Restart

**Problem:** If the worker container restarts, scheduled retries are lost.

**Solution 1 - Quick:** Database cleanup finds and re-schedules pending retries on startup.

**Solution 2 - Robust:** Use persistent job store (Redis or database-backed APScheduler):

```python
# In workers/main.py
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

jobstores = {
    'default': SQLAlchemyJobStore(url=settings.DATABASE_URL)
}
scheduler = AsyncIOScheduler(jobstores=jobstores)
```

**Solution 3 - Immediate:** Run database cleanup:

```sql
-- Find backups pending retry
UPDATE backups 
SET status = 'pending', next_retry_at = NULL 
WHERE status = 'pending' 
  AND retry_count > 0 
  AND next_retry_at < NOW();
```

### Too Many Retries Overwhelming Server

**Reduce retry frequency:**
```bash
BACKUP_RETRY_DELAY=900  # 15 minutes
BACKUP_RETRY_BACKOFF=3.0  # More aggressive backoff
```

**Or reduce max attempts:**
```bash
BACKUP_MAX_RETRIES=2  # Only 2 retries instead of 3
```

### Successful Backups After Retry Not Counted

Check the `retry_count` field to see which backups succeeded after retry:

```sql
SELECT * FROM backups 
WHERE status = 'completed' 
  AND retry_count > 0;
```

These should appear as successful in metrics and dashboards.

## 📈 Retry Statistics

### Success Rate by Retry Attempt

```sql
SELECT 
    retry_count,
    COUNT(*) as attempts,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successes,
    ROUND(100.0 * SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM backups 
WHERE retry_count > 0 
GROUP BY retry_count 
ORDER BY retry_count;
```

**Example output:**
```
retry_count | attempts | successes | success_rate
------------|----------|-----------|-------------
     1      |    145   |    127    |    87.59
     2      |     18   |     12    |    66.67
     3      |      6   |      2    |    33.33
```

### Average Time to Success

```sql
SELECT 
    AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) / 60 as avg_minutes_to_success
FROM backups 
WHERE status = 'completed' 
  AND retry_count > 0;
```

## 🎯 Best Practices

1. **Start conservative** - Default settings (3 retries, 5-10-20 minute delays) work well

2. **Monitor retry patterns** - High retry rates indicate underlying issues:
   ```sql
   SELECT COUNT(*) FROM backups WHERE retry_count > 0;
   ```

3. **Alert on exhausted retries** - Set up alerts when backups fail after all retries

4. **Investigate non-retryable errors** - These need manual fixes:
   ```bash
   docker compose logs worker | grep -iE "not found|invalid credentials"
   ```

5. **Test retry behavior** - Temporarily break LDAP connectivity to verify:
   ```bash
   # Block LDAP port temporarily
   sudo iptables -A OUTPUT -p tcp --dport 389 -j DROP
   # Create backup (will fail and retry)
   # Restore connectivity
   sudo iptables -D OUTPUT -p tcp --dport 389 -j DROP
   # Watch backup succeed on retry
   ```

6. **Use persistent job store** in production - Survives container restarts

7. **Set realistic retry windows** - If backups run hourly, don't retry for 2 hours

## 🔮 Future Enhancements

Potential improvements:

- **Jitter** - Add random delay to avoid thundering herd
- **Adaptive backoff** - Increase backoff if many failures
- **Per-server settings** - Different retry config per LDAP server
- **Retry priority queue** - Critical servers retry faster
- **Slack/Teams notifications** - Real-time retry alerts
- **Retry metrics** - Prometheus counters for retry attempts
- **Manual retry trigger** - UI button to force immediate retry
- **Retry history** - Detailed audit log of all retry attempts

## 📚 Related Documentation

- [Email Notifications](EMAIL_NOTIFICATIONS.md) - Configure email alerts for retries
- [Backup Operations](../README.md#backup-operations) - Main backup documentation
- [Monitoring & Metrics](../README.md#monitoring) - Track backup health
