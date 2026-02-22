# Backup Catalog & Search

## Overview

LDAPGuard includes a powerful backup catalog and search system that allows you to filter, search, and export backup data with advanced criteria. This feature provides comprehensive discovery and analysis capabilities for your backup inventory.

## Features

- **Advanced Filtering** - Filter by dates, size, status, server, category, and more
- **Full-Text Search** - Search across server names, hostnames, and file paths
- **Multiple Sort Options** - Sort by date, size, entry count, or completion time
- **Export Capabilities** - Export filtered results to CSV or JSON
- **Catalog Statistics** - View aggregated statistics across all backups
- **Visual Filter Panel** - User-friendly UI for building complex queries
- **API Access** - Programmatic access to catalog and search features

## Quick Start

### Using the Web UI

1. **Navigate to Backups page**
2. **Click "🔍 Filters" button** to show advanced filter panel
3. **Build your filter:**
   - Select server, status, type, category
   - Set date ranges
   - Set size or entry count limits
   - Choose verification or cloud upload status
   - Select sort options
4. **Click "Apply Filters"** to search
5. **Export results** using "📄 Export CSV" or "📊 Export JSON" buttons

### Using the API

```bash
# Advanced search
curl -X POST "http://localhost:8000/api/backups/catalog/search" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "search": "ldap",
    "status": "completed",
    "created_after": "2026-01-01T00:00:00",
    "verified_only": true,
    "sort_by": "file_size",
    "sort_order": "desc",
    "limit": 50
  }'

# Get catalog statistics
curl "http://localhost:8000/api/backups/catalog/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Export to CSV
curl "http://localhost:8000/api/backups/catalog/export?format=csv&status=completed" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -O -J
```

## Filter Options

### Search & Text Filters

| Filter | Description | Example |
|--------|-------------|---------|
| `search` | Search server name, hostname, or filename | `"ldap.example.com"` |

### Server & Type Filters

| Filter | Description | Values |
|--------|-------------|--------|
| `server_id` | Filter by specific LDAP server | Server ID (integer) |
| `status` | Backup status | `pending`, `in_progress`, `completed`, `failed` |
| `backup_type` | Backup type | `full`, `incremental` |
| `category` | Backup category | `directory`, `schema`, `config`, `acl`, `certificates`, `full_server` |

### Verification & Cloud Filters

| Filter | Description | Values |
|--------|-------------|--------|
| `verification_status` | Verification status | `verified`, `failed`, `not_verified`, `pending` |
| `cloud_uploaded` | Cloud upload status | `true`, `false` |

### Date Range Filters

| Filter | Description | Format |
|--------|-------------|--------|
| `created_after` | Created on or after date | ISO 8601: `2026-01-01T00:00:00` |
| `created_before` | Created on or before date | ISO 8601: `2026-12-31T23:59:59` |
| `completed_after` | Completed on or after date | ISO 8601 |
| `completed_before` | Completed on or before date | ISO 8601 |

### Size & Entry Filters

| Filter | Description | Unit |
|--------|-------------|------|
| `min_size` | Minimum file size | Bytes (UI: MB) |
| `max_size` | Maximum file size | Bytes (UI: MB) |
| `min_entries` | Minimum LDAP entries | Count |
| `max_entries` | Maximum LDAP entries | Count |

### Sort Options

| Sort Field | Description |
|------------|-------------|
| `created_at` | Creation date (default) |
| `completed_at` | Completion date |
| `file_size` | File size |
| `entry_count` | Number of LDAP entries |

**Sort Order:** `asc` (oldest/smallest first) or `desc` (newest/largest first)

### Pagination

| Parameter | Description | Default |
|-----------|-------------|---------|
| `skip` | Number of records to skip | 0 |
| `limit` | Maximum records to return | 100 |

## API Endpoints

### Advanced Search

```http
POST /api/backups/catalog/search
```

**Request Body:**
```json
{
  "search": "production",
  "server_id": 1,
  "status": "completed",
  "backup_type": "full",
  "category": "directory",
  "verification_status": "verified",
  "cloud_uploaded": true,
  "created_after": "2026-02-01T00:00:00",
  "created_before": "2026-02-28T23:59:59",
  "min_size": 1048576,
  "max_size": 104857600,
  "min_entries": 100,
  "max_entries": 10000,
  "sort_by": "created_at",
  "sort_order": "desc",
  "skip": 0,
  "limit": 50
}
```

**Response:**
```json
[
  {
    "id": 123,
    "ldap_server_id": 1,
    "backup_type": "full",
    "category": "directory",
    "status": "completed",
    "file_size": 5242880,
    "entry_count": 1532,
    "created_at": "2026-02-14T10:30:00Z",
    "completed_at": "2026-02-14T10:35:22Z",
    "verification_status": "verified",
    "cloud_uploaded": true,
    "cloud_provider": "aws",
    "checksum": "a1b2c3d4...",
    ...
  }
]
```

### Catalog Statistics

```http
GET /api/backups/catalog/stats?server_id=1
```

**Response:**
```json
{
  "total_backups": 1247,
  "total_size": 52428800000,
  "total_entries": 1532456,
  "backups_by_status": {
    "completed": 1200,
    "failed": 35,
    "pending": 12
  },
  "backups_by_type": {
    "full": 247,
    "incremental": 1000
  },
  "backups_by_category": {
    "directory": 1100,
    "schema": 50,
    "config": 47,
    "acl": 30,
    "certificates": 20
  },
  "backups_by_server": {
    "ldap1.example.com": 623,
    "ldap2.example.com": 624
  },
  "verified_backups": 1180,
  "cloud_uploaded_backups": 1150,
  "failed_backups": 35,
  "oldest_backup": "2025-06-15T08:22:10Z",
  "newest_backup": "2026-02-14T14:30:45Z",
  "average_backup_size": 42048000.5,
  "largest_backup_size": 524288000,
  "smallest_backup_size": 102400
}
```

### Export Backups

```http
GET /api/backups/catalog/export?format=csv&status=completed&server_id=1
```

**Query Parameters:**
- `format` - Export format: `csv` or `json` (required)
- `server_id` - Filter by server (optional)
- `status` - Filter by status (optional)
- `created_after` - Filter by creation date (optional)
- `created_before` - Filter by creation date (optional)

**Response:**
Downloadable file with `Content-Disposition` header.

**CSV Format:**
```csv
ID,Server Name,Server Host,Backup Type,Category,Status,File Size (bytes),Entry Count,Created At,Completed At,Verification Status,Cloud Uploaded,Cloud Provider,Checksum,File Path
123,ldap1.example.com,10.0.1.100,full,directory,completed,5242880,1532,2026-02-14T10:30:00Z,2026-02-14T10:35:22Z,verified,Yes,aws,a1b2c3d4...,/app/backups/backup_123.ldif.gz
```

**JSON Format:**
```json
{
  "export_date": "2026-02-14T15:30:00Z",
  "total_records": 125,
  "backups": [
    {
      "id": 123,
      "server_name": "ldap1.example.com",
      "server_host": "10.0.1.100",
      "backup_type": "full",
      "category": "directory",
      "status": "completed",
      "file_size": 5242880,
      "entry_count": 1532,
      "created_at": "2026-02-14T10:30:00Z",
      "completed_at": "2026-02-14T10:35:22Z",
      "verification_status": "verified",
      "cloud_uploaded": true,
      "cloud_provider": "aws",
      "cloud_storage_path": "backups/2026/02/14/ldap1/backup_123.ldif.gz",
      "checksum": "a1b2c3d4...",
      "checksum_algorithm": "sha256",
      "file_path": "/app/backups/backup_123.ldif.gz",
      "error_message": null
    }
  ]
}
```

## Common Use Cases

### Find Large Backups

**Web UI:**
1. Click "🔍 Filters"
2. Set "Min Size (MB)" to 100
3. Set "Sort By" to "Size"
4. Set "Order" to "Newest First"
5. Click "Apply Filters"

**API:**
```bash
curl -X POST "http://localhost:8000/api/backups/catalog/search" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "min_size": 104857600,
    "sort_by": "file_size",
    "sort_order": "desc",
    "limit": 20
  }'
```

### Find Recently Failed Backups

**Web UI:**
1. Click "🔍 Filters"
2. Set "Status" to "Failed"
3. Set "Created After" to last week
4. Click "Apply Filters"

**API:**
```bash
curl -X POST "http://localhost:8000/api/backups/catalog/search" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "failed",
    "created_after": "2026-02-07T00:00:00",
    "sort_by": "created_at",
    "sort_order": "desc"
  }'
```

### Find Unverified Backups

**Web UI:**
1. Click "🔍 Filters"
2. Set "Verification" to "Not Verified"
3. Set "Status" to "Completed"
4. Click "Apply Filters"

**API:**
```bash
curl -X POST "http://localhost:8000/api/backups/catalog/search" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "verification_status": "not_verified"
  }'
```

### Find Backups Not Uploaded to Cloud

**Web UI:**
1. Click "🔍 Filters"
2. Set "Cloud Status" to "Not Uploaded"
3. Set "Status" to "Completed"
4. Click "Apply Filters"

**API:**
```bash
curl -X POST "http://localhost:8000/api/backups/catalog/search" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "cloud_uploaded": false
  }'
```

### Monthly Backup Report

**Export all backups from last month:**
```bash
curl "http://localhost:8000/api/backups/catalog/export?format=csv&created_after=2026-01-01T00:00:00&created_before=2026-01-31T23:59:59" \
  -H "Authorization: Bearer TOKEN" \
  -O -J
```

### Server-Specific Analysis

**Get stats for specific server:**
```bash
curl "http://localhost:8000/api/backups/catalog/stats?server_id=1" \
  -H "Authorization: Bearer TOKEN"
```

## Scripting Examples

### Python: Find and Delete Old Backups

```python
import requests
from datetime import datetime, timedelta

API_URL = "http://localhost:8000/api"
TOKEN = "your-api-token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Find backups older than 90 days
ninety_days_ago = (datetime.utcnow() - timedelta(days=90)).isoformat()

response = requests.post(
    f"{API_URL}/backups/catalog/search",
    headers=headers,
    json={
        "created_before": ninety_days_ago,
        "status": "completed",
        "limit": 1000
    }
)

old_backups = response.json()

print(f"Found {len(old_backups)} old backups")

# Delete them (with confirmation)
for backup in old_backups:
    print(f"Deleting backup {backup['id']} from {backup['created_at']}")
    # Uncomment to actually delete:
    # requests.delete(f"{API_URL}/backups/{backup['id']}", headers=headers)
```

### Bash: Weekly Backup Report

```bash
#!/bin/bash
# Generate weekly backup report

TOKEN="your-api-token"
API_URL="http://localhost:8000/api"

# Get stats
stats=$(curl -s "${API_URL}/backups/catalog/stats" \
  -H "Authorization: Bearer ${TOKEN}")

# Export last week's backups
one_week_ago=$(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S)

curl "${API_URL}/backups/catalog/export?format=csv&created_after=${one_week_ago}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -O -J

echo "Weekly Backup Report"
echo "===================="
echo "$stats" | jq -r '
  "Total Backups: \(.total_backups)",
  "Total Size: \(.total_size / 1024 / 1024 / 1024 | floor)GB",
  "Verified: \(.verified_backups)",
  "Failed: \(.failed_backups)",
  "Cloud Uploaded: \(.cloud_uploaded_backups)"
'
```

### PowerShell: Find Unverified Backups

```powershell
$ApiUrl = "http://localhost:8000/api"
$Token = "your-api-token"

$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

$body = @{
    status = "completed"
    verification_status = "not_verified"
    limit = 100
} | ConvertTo-Json

$response = Invoke-RestMethod `
    -Uri "$ApiUrl/backups/catalog/search" `
    -Method Post `
    -Headers $headers `
    -Body $body

Write-Host "Found $($response.Count) unverified backups:"
$response | ForEach-Object {
    Write-Host "  - Backup $($_.id): $($_.file_path)"
}
```

## Search Performance

The catalog search is optimized for fast queries:

- **Indexed Fields**: `ldap_server_id`, `status`, `backup_type`, `category`, `created_at`
- **Full-Text Search**: Uses PostgreSQL `ILIKE` with index support
- **Query Optimization**: Filters applied before joins
- **Pagination**: Limits result sets for large catalogs

**Performance Tips:**
- Use specific filters to narrow results
- Avoid very large date ranges without other filters
- Use pagination (`skip`/`limit`) for large result sets
- Export in batches for very large datasets

## Security Considerations

### Role-Based Access

Catalog features respect user roles:
- **Admin**: Full access to all backups
- **Backup Admin**: Access to directory, schema, config backups
- **Security Admin**: Access to schema, config, ACL, certificates
- **Operator**: Access to directory backups only
- **Viewer**: Read-only access to allowed categories

### Sensitive Data

Exports include:
- ✅ Backup metadata
- ✅ File paths
- ✅ Checksums
- ❌ Actual backup content (not included)
- ❌ LDAP passwords (not included)

### API Security

- All endpoints require authentication
- Rate limiting applies to exports
- Large exports may be throttled
- File downloads respect access control

## Troubleshooting

### No Results Found

**Symptoms**: Search returns zero results

**Solutions:**
1. Check filters are not too restrictive
2. Verify date formats (ISO 8601: `YYYY-MM-DDTHH:MM:SS`)
3. Reset filters and try again
4. Check user role has access to backup categories

### Export Fails

**Symptoms**: Export button doesn't download file

**Solutions:**
1. Check browser allows downloads from site
2. Verify sufficient permissions
3. Try smaller date range/filter set
4. Check server logs for errors

### Slow Searches

**Symptoms**: Search takes>5 seconds

**Solutions:**
1. Add more specific filters
2. Reduce date range
3. Use pagination with smaller `limit`
4. Check database has proper indexes:
   ```sql
   CREATE INDEX ON backups(ldap_server_id);
   CREATE INDEX ON backups(status);
   CREATE INDEX ON backups(created_at);
   ```

## Integration Examples

### Grafana Dashboard

Create Grafana panel querying catalog stats:

```sql
-- Get daily backup counts
SELECT
  DATE(created_at) as date,
  COUNT(*) as total_backups,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
FROM backups
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date;
```

### Prometheus Metrics

Export catalog metrics for monitoring:

```python
from prometheus_client import Gauge

backup_total = Gauge('ldapg uard_backups_total', 'Total backups')
backup_verified = Gauge('ldapguard_backups_verified', 'Verified backups')
backup_cloud = Gauge('ldapguard_backups_cloud', 'Cloud uploaded backups')

# Update from catalog stats
stats = get_catalog_stats()
backup_total.set(stats['total_backups'])
backup_verified.set(stats['verified_backups'])
backup_cloud.set(stats['cloud_uploaded_backups'])
```

## See Also

- [Backup Verification](BACKUP_VERIFICATION.md) - Verify backup integrity
- [S3 Integration](S3_INTEGRATION.md) - Cloud storage for backups
- [Backup Retry Logic](BACKUP_RETRY_LOGIC.md) - Automatic retry
- [Email Notifications](EMAIL_NOTIFICATIONS.md) - Get notified of events
