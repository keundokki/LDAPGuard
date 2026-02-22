# S3-Compatible Cloud Storage Integration

## Overview

LDAPGuard includes comprehensive support for automatically uploading backups to S3-compatible cloud storage providers. This provides offsite backup redundancy, disaster recovery capabilities, and reduces local storage requirements.

## Supported Providers

LDAPGuard supports any S3-compatible storage service, including:

- ✅ **AWS S3** - Amazon's industry-standard object storage
- ✅ **MinIO** - Self-hosted, open-source S3-compatible storage
- ✅ **Backblaze B2** - Cost-effective cloud storage
- ✅ **Wasabi** - Low-cost hot cloud storage
- ✅ **DigitalOcean Spaces** - Simple object storage
- ✅ **Any S3-compatible** storage service

## Features

- **Automatic Upload**: Backups are automatically uploaded to cloud storage after creation
- **Selective Retention**: Keep last N backups locally while storing all in cloud
- **Manual Upload/Download**: Upload existing backups or download from cloud via UI/API
- **Multiple Storage Classes**: Use STANDARD, GLACIER, INTELLIGENT_TIERING, etc.
- **Metadata Tagging**: Backups include metadata (server name, type, checksum, etc.)
- **Test Connection**: Verify cloud storage credentials before use
- **Provider Detection**: Automatically detects storage provider from endpoint

## Quick Start

### 1. AWS S3 Setup

```bash
# Configure AWS credentials
S3_ENABLED=true
S3_BUCKET_NAME=ldapguard-backups
S3_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
S3_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
S3_REGION=us-east-1

# Automatic upload settings
S3_AUTO_UPLOAD=true
S3_STORAGE_CLASS=STANDARD
```

### 2. MinIO (Self-Hosted) Setup

```bash
# Run MinIO locally or on your server
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  -v /path/to/data:/data \
  minio/minio server /data --console-address ":9001"

# Configure LDAPGuard
S3_ENABLED=true
S3_BUCKET_NAME=ldapguard
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
S3_REGION=us-east-1
S3_ENDPOINT_URL=http://minio:9000
S3_AUTO_UPLOAD=true
```

### 3. Backblaze B2 Setup

```bash
# Get credentials from Backblaze dashboard
S3_ENABLED=true
S3_BUCKET_NAME=my-ldap-backups
S3_ACCESS_KEY_ID=your-key-id
S3_SECRET_ACCESS_KEY=your-application-key
S3_REGION=us-west-001
S3_ENDPOINT_URL=https://s3.us-west-001.backblazeb2.com
S3_AUTO_UPLOAD=true
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `S3_ENABLED` | Yes | `false` | Enable cloud storage integration |
| `S3_BUCKET_NAME` | Yes* | - | S3 bucket name for backups |
| `S3_ACCESS_KEY_ID` | Yes* | - | S3 access key ID |
| `S3_SECRET_ACCESS_KEY` | Yes* | - | S3 secret access key |
| `S3_REGION` | No | `us-east-1` | AWS region or zone |
| `S3_ENDPOINT_URL` | No** | - | S3 endpoint URL (for non-AWS) |
| `S3_STORAGE_CLASS` | No | `STANDARD` | Storage class to use |
| `S3_AUTO_UPLOAD` | No | `true` | Automatically upload new backups |
| `S3_AUTO_DELETE_LOCAL` | No | `false` | Delete local file after upload |
| `S3_KEEP_LAST_LOCAL` | No | `3` | Minimum local backups to keep |

\* Required when `S3_ENABLED=true`  
\*\* Required for non-AWS providers (MinIO, Backblaze, etc.)

### Storage Classes

**AWS S3 Storage Classes:**
- `STANDARD` - Default, frequent access (11 9's durability)
- `INTELLIGENT_TIERING` - Automatic cost optimization
- `STANDARD_IA` - Infrequent access (cheaper storage, retrieval fee)
- `GLACIER` - Long-term archive (very cheap, hours retrieval)
- `GLACIER_DEEP_ARCHIVE` - Lowest cost (12+ hour retrieval)
- `ONEZONE_IA` - Lower cost IA in single AZ

**MinIO/Backblaze:**
- `STANDARD` - Only option (default)

### Local File Management

LDAPGuard intelligently manages local backups when cloud storage is enabled:

**Scenario 1: Keep all local backups**
```bash
S3_AUTO_UPLOAD=true
S3_AUTO_DELETE_LOCAL=false
```
- Backups uploaded to cloud
- All local backups retained
- Uses more disk space but maximum redundancy

**Scenario 2: Keep last N local backups**
```bash
S3_AUTO_UPLOAD=true
S3_AUTO_DELETE_LOCAL=true
S3_KEEP_LAST_LOCAL=3
```
- New backups uploaded to cloud
- Oldest local backups deleted (keeps last 3)
- Saves disk space while maintaining recent local access

**Scenario 3: Cloud-only backups**
```bash
S3_AUTO_UPLOAD=true
S3_AUTO_DELETE_LOCAL=true
S3_KEEP_LAST_LOCAL=0  # Warning: May prevent restores if cloud is unavailable
```
- All backups uploaded to cloud
- All local files deleted after upload
- Minimum disk usage (use with caution)

## Cloud Storage Structure

Backups are organized in S3 with the following structure:

```
bucket-name/
  backups/
    2026/
      02/
        14/
          server1.example.com/
            backup_123_full_backup_20260214_103045.ldif.gz
            backup_124_incremental_backup_20260214_143022.ldif.gz
          server2.example.com/
            backup_125_full_backup_20260214_110015.ldif.gz
        15/
          server1.example.com/
            backup_126_full_backup_20260215_030012.ldif.gz
```

**Path Format:**
```
backups/{year}/{month}/{day}/{server_name}/backup_{id}_{filename}
```

This structure provides:
- Easy date-based filtering
- Server-based organization
- Unique backup identification
- Efficient lifecycle policies

## Metadata

Each backup uploaded to S3 includes metadata:

```json
{
  "backup-id": "123",
  "server-name": "ldap.example.com",
  "backup-type": "full",
  "category": "directory",
  "entry-count": "1542",
  "checksum": "a1b2c3d4e5f6...",
  "checksum-algorithm": "sha256"
}
```

This metadata allows:
- Backup verification without downloading
- Cloud-based backup catalogs
- Automated retention policies
- Audit trail

## API Endpoints

### Upload Backup to Cloud

```http
POST /api/backups/cloud/{backup_id}/upload
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/backups/cloud/123/upload" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "backup_id": 123,
  "success": true,
  "message": "Backup uploaded successfully to aws storage",
  "cloud_storage_path": "backups/2026/02/14/server1/backup_123_full.ldif.gz",
  "cloud_provider": "aws",
  "cloud_storage_class": "STANDARD",
  "uploaded_at": "2026-02-14T10:30:45Z"
}
```

### Download Backup from Cloud

```http
POST /api/backups/cloud/{backup_id}/download
```

Downloads a cloud backup to local storage (useful if local file was deleted).

```bash
curl -X POST "http://localhost:8000/api/backups/cloud/123/download" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### List Cloud Backups

```http
GET /api/backups/cloud/list?prefix=backups/2026/02/
```

```bash
curl "http://localhost:8000/api/backups/cloud/list?prefix=backups/2026/02/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
[
  {
    "key": "backups/2026/02/14/server1/backup_123_full.ldif.gz",
    "size": 524288,
    "last_modified": "2026-02-14T10:30:45Z",
    "storage_class": "STANDARD"
  }
]
```

### Delete from Cloud (Admin Only)

```http
DELETE /api/backups/cloud/{backup_id}/cloud
```

```bash
curl -X DELETE "http://localhost:8000/api/backups/cloud/123/cloud" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Test Cloud Connection

```http
GET /api/backups/cloud/test
```

```bash
curl "http://localhost:8000/api/backups/cloud/test" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully connected to S3 storage",
  "enabled": true,
  "provider": "aws",
  "bucket": "ldapguard-backups",
  "region": "us-east-1"
}
```

### Get Cloud Info for Backup

```http
GET /api/backups/cloud/{backup_id}/info
```

Returns cloud storage metadata for a specific backup.

## Web UI Usage

### Upload Backup

1. Navigate to **Backups** page
2. Find completed backup to upload
3. Click **☁️ Upload** button
4. Confirm upload
5. Wait for upload to complete (toast notification)
6. Backup row will show cloud status badge

### Download from Cloud

1. Navigate to **Backups** page
2. Find backup with cloud badge
3. Click **⬇️ Cloud** button
4. Confirm download
5. Wait for download (toast notification)
6. Backup will be available locally

### Cloud Status Indicators

- **☁️ Cloud: aws** - Uploaded to AWS S3
- **☁️ Cloud: minio** - Uploaded to MinIO
- **☁️ Cloud: backblaze** - Uploaded to Backblaze B2
- No badge - Not uploaded to cloud

## Provider-Specific Guides

### AWS S3 Setup

**1. Create S3 Bucket**

```bash
aws s3 mb s3://ldapguard-backups --region us-east-1
```

**2. Create IAM User**

```bash
aws iam create-user --user-name ldapguard-backup
```

**3. Create IAM Policy** (`ldapguard-s3-policy.json`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::ldapguard-backups",
        "arn:aws:s3:::ldapguard-backups/*"
      ]
    }
  ]
}
```

**4. Attach Policy and Create Access Key**

```bash
aws iam put-user-policy --user-name ldapguard-backup \
  --policy-name S3BackupAccess \
  --policy-document file://ldapguard-s3-policy.json

aws iam create-access-key --user-name ldapguard-backup
```

**5. Configure LDAPGuard**

Use the Access Key ID and Secret Access Key from step 4.

### MinIO Setup

**1. Run MinIO Server**

```bash
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin123 \
  -v /mnt/data:/data \
  minio/minio server /data --console-address ":9001"
```

**2. Create Bucket**

Access MinIO console at `http://localhost:9001`:
- Login with `minioadmin` / `minioadmin123`
- Create bucket named `ldapguard`
- Set access policy to "private"

**3. Configure LDAPGuard**

```bash
S3_ENABLED=true
S3_BUCKET_NAME=ldapguard
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin123
S3_REGION=us-east-1
S3_ENDPOINT_URL=http://minio:9000
```

### Backblaze B2 Setup

**1. Create Bucket**

- Login to Backblaze account
- Navigate to "Buckets"
- Click "Create a Bucket"
- Name: `ldapguard-backups`
- Files: Private
- Lifecycle: Keep all versions (or custom)

**2. Generate Application Key**

- Navigate to "App Keys"
- Click "Add New Application Key"
- Name: `ldapguard-backup-key`
- Access: Read and Write
- Buckets: `ldapguard-backups` only
- Save the Key ID and Application Key

**3. Configure LDAPGuard**

```bash
S3_ENABLED=true
S3_BUCKET_NAME=ldapguard-backups
S3_ACCESS_KEY_ID=your-key-id
S3_SECRET_ACCESS_KEY=your-application-key
S3_REGION=us-west-001  # Or your region
S3_ENDPOINT_URL=https://s3.us-west-001.backblazeb2.com
```

**Backblaze Regions:**
- `us-west-001` - US West (Arizona)
- `us-west-002` - US West (California)
- `us-west-004` - US West (Oregon)
- `eu-central-003` - Europe (Amsterdam)

## Cost Optimization

### Storage Class Comparison (AWS S3)

| Storage Class | Cost/GB/Month | Retrieval Cost | Use Case |
|---------------|---------------|----------------|----------|
| STANDARD | $0.023 | None | Frequent access |
| INTELLIGENT_TIERING | $0.023-$0.0125 | None | Automatic optimization |
| STANDARD_IA | $0.0125 | $0.01/GB | Monthly access |
| GLACIER | $0.004 | $0.02/GB | Quarterly access |
| GLACIER_DEEP_ARCHIVE | $0.00099 | $0.02/GB | Yearly access |

**Recommendations:**

- **Daily backups**: Use `INTELLIGENT_TIERING` (auto-optimizes)
- **Weekly backups**: Use `STANDARD_IA` (lower storage cost)
- **Monthly backups**: Use `GLACIER` (very cheap, slower retrieval)
- **Yearly archives**: Use `GLACIER_DEEP_ARCHIVE` (cheapest)

### Lifecycle Policies

Configure S3 lifecycle policies to automatically transition backups:

```xml
<LifecycleConfiguration>
  <Rule>
    <ID>TransitionOldBackups</ID>
    <Status>Enabled</Status>
    <Prefix>backups/</Prefix>
    <Transition>
      <Days>30</Days>
      <StorageClass>STANDARD_IA</StorageClass>
    </Transition>
    <Transition>
      <Days>90</Days>
      <StorageClass>GLACIER</StorageClass>
    </Transition>
    <Expiration>
      <Days>365</Days>
    </Expiration>
  </Rule>
</LifecycleConfiguration>
```

This policy:
- Keeps backups in STANDARD for 30 days
- Moves to STANDARD_IA after 30 days (50% savings)
- Moves to GLACIER after 90 days (80% savings)
- Deletes after 365 days

### Cost Estimation

**Example: 1GB daily backup, 30-day retention**

**AWS S3 STANDARD:**
- Storage: 30 GB × $0.023 = **$0.69/month**
- Uploads: 30 × $0.005 = **$0.15/month**
- Total: **$0.84/month**

**AWS S3 INTELLIGENT_TIERING:**
- Storage: ~20 GB × $0.023 + ~10 GB × $0.0125 = **$0.59/month**
- Monitoring: 30 GB × $0.0025 = **$0.08/month**
- Total: **$0.67/month** (20% savings)

**Backblaze B2:**
- Storage: 30 GB × $0.005 = **$0.15/month**
- Downloads: Free (first 3× storage per day)
- Total: **$0.15/month** (82% savings vs AWS)

**MinIO (Self-Hosted):**
- Storage: Cost of disk space
- No cloud fees
- Total: **$0/month** (plus infrastructure costs)

## Troubleshooting

### Connection Failed

**Error:** `Failed to connect to S3 storage`

**Solutions:**
1. Verify credentials:
   ```bash
   aws s3 ls s3://ldapguard-backups \
     --profile ldapguard
   ```

2. Check endpoint URL (for non-AWS):
   - MinIO: `http://minio:9000` (not `http://localhost:9000` inside Docker)
   - Backblaze: Must use correct region endpoint

3. Verify bucket exists:
   ```bash
   aws s3 mb s3://ldapguard-backups --region us-east-1
   ```

4. Check network connectivity:
   ```bash
   curl -I https://s3.amazonaws.com
   ```

### Upload Failed

**Error:** `Failed to upload backup to cloud storage`

**Solutions:**
1. Check file exists locally:
   ```bash
   ls -lh /app/backups/
   ```

2. Verify permissions:
   - AWS: IAM policy allows `s3:PutObject`
   - MinIO: User has write access

3. Check storage quota:
   - Ensure bucket isn't full or quota-limited

4. Review logs:
   ```bash
   docker-compose logs worker | grep -i "s3\|upload"
   ```

### Slow Uploads

**Symptoms**: Uploads take longer than expected

**Solutions:**
1. Check network bandwidth:
   ```bash
   speedtest-cli
   ```

2. Enable compression (already enabled by default):
   - LDAPGuard uses `.gz` compression
   - Reduces upload size by ~70%

3. Use closer region:
   - AWS: Choose nearest region
   - Backblaze: Select closest datacenter

4. Increase worker timeout:
   ```python
   # In worker configuration
   task_time_limit = 3600  # 1 hour for large backups
   ```

### Download Failed

**Error:** `Failed to download backup from cloud storage`

**Solutions:**
1. Verify object exists in S3:
   ```bash
   aws s3 ls s3://ldapguard-backups/backups/2026/02/14/
   ```

2. Check retrieval tier (for Glacier):
   - Glacier retrieval takes hours
   - Request restoration first

3. Verify local disk space:
   ```bash
   df -h /app/backups
   ```

### Metadata Missing

**Symptoms**: Cloud backups show no metadata

**Solutions:**
1. Re-upload with current version (includes metadata)
2. Metadata is stored in S3 object tags (not affected by download)

## Security Best Practices

### 1. Use IAM Roles (AWS)

Instead of access keys, use IAM roles for EC2 instances:

```bash
# No credentials in .env!
S3_ENABLED=true
S3_BUCKET_NAME=ldapguard-backups
S3_REGION=us-east-1
# AWS SDK automatically uses instance role
```

### 2. Encrypt at Rest

**AWS S3:**
```bash
aws s3api put-bucket-encryption \
  --bucket ldapguard-backups \
  --server-side-encryption-configuration \
  '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'
```

**MinIO:**
```bash
# Enable encryption in MinIO config
mc encrypt set sse-s3 myminio/ldapguard
```

### 3. Enable Versioning

Protect against accidental deletion:

```bash
aws s3api put-bucket-versioning \
  --bucket ldapguard-backups \
  --versioning-configuration Status=Enabled
```

### 4. Restrict Access

**AWS S3 Bucket Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": "arn:aws:s3:::ldapguard-backups/*",
      "Condition": {
        "Bool": {"aws:SecureTransport": "false"}
      }
    }
  ]
}
```

This enforces HTTPS-only access.

### 5. Audit Access

Enable S3 access logging:

```bash
aws s3api put-bucket-logging \
  --bucket ldapguard-backups \
  --bucket-logging-status \
  '{"LoggingEnabled": {"TargetBucket": "ldapguard-logs", "TargetPrefix": "s3-access/"}}'
```

## Monitoring & Alerting

### CloudWatch Metrics (AWS)

Monitor S3 usage:
- `NumberOfObjects` - Total backups stored
- `BucketSizeBytes` - Storage used
- `AllRequests` - API call volume

### Cost Alerts

Set up AWS billing alerts:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name ldapguard-s3-cost \
  --alarm-description "Alert when S3 costs exceed threshold" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 50.0 \
  --comparison-operator GreaterThanThreshold
```

### Backup Verification

Verify cloud backups regularly:

```bash
#!/bin/bash
# cron job: 0 2 * * * /usr/local/bin/verify-cloud-backups.sh

curl -X GET "http://localhost:8000/api/backups/cloud/list" \
  -H "Authorization: Bearer $TOKEN" | \
  jq '.[] | select(.last_modified < (now - 86400 | strftime("%Y-%m-%dT%H:%M:%SZ"))) | .key'
```

## Migration Guide

### Enabling S3 on Existing Installation

**1. Run database migration:**
```bash
docker-compose exec api alembic upgrade head
```

**2. Configure S3 settings:**
```bash
# Edit .env
S3_ENABLED=true
S3_BUCKET_NAME=ldapguard-backups
# ... other settings
```

**3. Restart services:**
```bash
docker-compose restart api worker
```

**4. Test connection:**
```bash
curl "http://localhost:8000/api/backups/cloud/test" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**5. Upload existing backups:**
```bash
# Get all backup IDs
curl "http://localhost:8000/api/backups" \
  -H "Authorization: Bearer TOKEN" | \
  jq '.[] | .id' | \
  while read id; do
    curl -X POST "http://localhost:8000/api/backups/cloud/$id/upload" \
      -H "Authorization: Bearer TOKEN"
    sleep 2
  done
```

### Migrating Between Providers

**AWS S3 → MinIO:**

1. Set up MinIO
2. Use AWS CLI to sync:
   ```bash
   aws s3 sync s3://old-bucket s3://new-bucket \
     --source-region us-east-1 \
     --endpoint-url http://minio:9000
   ```
3. Update LDAPGuard config
4. Verify backups

## See Also

- [Backup Verification](BACKUP_VERIFICATION.md) - Verify backup integrity
- [Backup Retry Logic](BACKUP_RETRY_LOGIC.md) - Automatic retry for failed backups
- [Email Notifications](EMAIL_NOTIFICATIONS.md) - Get notified of uploads
- [Deployment Procedure](DEPLOYMENT_PROCEDURE.md) - Production deployment
