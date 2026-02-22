# Backup Verification & Integrity Checks

## Overview

LDAPGuard includes a comprehensive backup verification system that ensures your LDAP backups are valid, uncorrupted, and restorable. The system automatically calculates checksums, validates LDIF syntax, and performs integrity checks to protect against data corruption, storage failures, and tampering.

## Features

- **Automatic Checksum Calculation**: Generate SHA-256, SHA-512, or MD5 hashes for every backup
- **LDIF Syntax Validation**: Verify backup files contain valid LDAP data
- **Pre-Restore Verification**: Automatically verify backups before restoration
- **Manual Verification**: Trigger verification checks via API or UI
- **Comprehensive Checks**: File existence, size, checksum, and syntax validation
- **Verification Status Tracking**: Monitor which backups have been verified

## Verification Methods

### 1. Checksum Verification

Checksums (cryptographic hashes) are calculated for each backup file to detect:
- File corruption during storage
- Data tampering or modification
- Transfer errors
- Storage media degradation

**Supported algorithms:**
- `sha256` - SHA-256 (default, recommended)
- `sha512` - SHA-512 (more secure, larger hash size)
- `md5` - MD5 (fastest, less secure, backward compatibility)

### 2. LDIF Syntax Validation

The system parses backup files to ensure they contain valid LDIF (LDAP Data Interchange Format) data:
- Validates LDIF structure and syntax
- Checks for valid DN (Distinguished Name) entries
- Verifies attribute formatting
- Ensures file is restorable

### 3. File Integrity Checks

Additional verification includes:
- **File Existence**: Confirms backup file is accessible
- **File Size**: Validates file size matches expected size
- **Readability**: Ensures file can be opened and read
- **Compression**: Handles `.gz` compressed backups

## Configuration

### Environment Variables

Add these settings to your `.env` file:

```bash
# Backup Verification Settings
BACKUP_VERIFY_ON_COMPLETION=true      # Verify after backup creation
BACKUP_VERIFY_BEFORE_RESTORE=true     # Verify before restoration
BACKUP_CHECKSUM_ALGORITHM=sha256      # Hash algorithm (sha256, sha512, md5)
```

### Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `BACKUP_VERIFY_ON_COMPLETION` | `true` | Automatically verify backups after creation |
| `BACKUP_VERIFY_BEFORE_RESTORE` | `true` | Verify backup integrity before restoring |
| `BACKUP_CHECKSUM_ALGORITHM` | `sha256` | Checksum algorithm to use |

### Choosing a Checksum Algorithm

**SHA-256 (Recommended)**
- Strong cryptographic security
- Fast computation
- Standard 64-character hash
- Best balance of speed and security

**SHA-512**
- Maximum security
- Slightly slower than SHA-256
- 128-character hash
- Use for highly sensitive data

**MD5**
- Fastest computation
- Less secure (vulnerable to collisions)
- 32-character hash
- Only use for backward compatibility

## Verification Workflow

### Automatic Verification on Backup

When a backup completes:

1. ✅ Backup file is created
2. 🔢 Checksum is calculated using configured algorithm
3. ✅ Checksum is stored in database
4. 🔍 If `BACKUP_VERIFY_ON_COMPLETION=true`:
   - Run comprehensive verification
   - Validate LDIF syntax
   - Verify file integrity
   - Update `verification_status`
5. 📧 Send notification (if enabled)

### Automatic Verification Before Restore

When a restore is triggered:

1. 🔍 If `BACKUP_VERIFY_BEFORE_RESTORE=true`:
   - Verify checksum matches
   - Validate file size
   - Check LDIF syntax
   - Verify file accessibility
2. ✅ If verification passes: proceed with restore
3. ❌ If verification fails: abort restore and notify

### Manual Verification

Trigger verification via:

**API:**
```bash
curl -X POST http://localhost:8000/api/backups/verification/123 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Web UI:**
1. Navigate to Backups page
2. Find backup to verify
3. Click "Verify" button
4. View verification results

## Verification Status

Each backup has a `verification_status` field:

| Status | Icon | Meaning |
|--------|------|---------|
| `verified` | ✅ | Backup passed all verification checks |
| `failed` | ❌ | Verification failed (corrupted or invalid) |
| `not_verified` | ⚠️ | Backup hasn't been verified yet |
| `pending` | 🔄 | Verification in progress |

## API Endpoints

### Verify Backup

```http
POST /api/backups/verification/{backup_id}
```

**Response:**
```json
{
  "backup_id": 123,
  "verified": true,
  "message": "Backup verified successfully",
  "verification_status": "verified",
  "checksum": "a1b2c3d4...",
  "checksum_algorithm": "sha256",
  "verified_at": "2024-01-15T10:30:00Z",
  "checks_performed": {
    "checksum": true,
    "file_size": true,
    "ldif_syntax": true,
    "file_exists": true
  }
}
```

### Get Verification Status

```http
GET /api/backups/verification/{backup_id}/status
```

**Response:**
```json
{
  "backup_id": 123,
  "verification_status": "verified",
  "checksum": "a1b2c3d4...",
  "checksum_algorithm": "sha256",
  "verified_at": "2024-01-15T10:30:00Z",
  "file_path": "/app/backups/backup_123.ldif.gz",
  "file_size": 524288
}
```

### Recalculate Checksum (Admin)

```http
POST /api/backups/verification/{backup_id}/recalculate-checksum
```

Use this to regenerate checksums for existing backups after algorithm changes.

## Database Schema

Verification fields in the `backups` table:

```sql
-- Checksum hash value
checksum VARCHAR(128)

-- Algorithm used: sha256, sha512, md5
checksum_algorithm VARCHAR(20) DEFAULT 'sha256'

-- Verification timestamp
verified_at TIMESTAMP WITH TIME ZONE

-- Verification status: verified, failed, not_verified, pending
verification_status VARCHAR(20)
```

## Monitoring & Reporting

### Check Unverified Backups

```sql
SELECT id, filename, created_at, verification_status
FROM backups
WHERE verification_status = 'not_verified'
OR verification_status IS NULL
ORDER BY created_at DESC;
```

### Find Failed Verifications

```sql
SELECT id, filename, created_at, verified_at, error
FROM backups
WHERE verification_status = 'failed'
ORDER BY verified_at DESC;
```

### Verification Statistics

```sql
SELECT 
    verification_status,
    COUNT(*) as count,
    ROUND(AVG(size), 2) as avg_size_bytes
FROM backups
WHERE status = 'completed'
GROUP BY verification_status
ORDER BY count DESC;
```

## Troubleshooting

### Backup Shows "Verification Failed"

**Possible causes:**
1. File corruption during storage
2. Storage media failure
3. File was modified after creation
4. Invalid LDIF syntax
5. File size mismatch

**Resolution:**
1. Check verification error message in logs
2. Attempt manual verification via API
3. Review backup file manually
4. Create a new backup
5. Restore from an earlier verified backup

### Checksum Mismatch

**Cause:** File content changed after checksum calculation

**Resolution:**
```bash
# Recalculate checksum (admin only)
curl -X POST http://localhost:8000/api/backups/verification/123/recalculate-checksum \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### LDIF Syntax Validation Fails

**Cause:** Backup file contains invalid LDAP data

**Resolution:**
1. Check backup file manually:
   ```bash
   zcat /app/backups/backup_123.ldif.gz | head -n 50
   ```
2. Run ldapsearch to verify LDAP server data
3. Create a new backup
4. Check for LDAP server issues

### Performance Impact

**Large backups** (>100MB) may take longer to verify:

- **SHA-256**: ~500 MB/s
- **SHA-512**: ~400 MB/s  
- **MD5**: ~800 MB/s

**Optimization tips:**
- Disable `BACKUP_VERIFY_ON_COMPLETION` for very large backups
- Use manual verification during maintenance windows
- Consider `md5` for faster verification (less secure)

## Best Practices

### 1. Use Automatic Verification

✅ **Recommended:**
```bash
BACKUP_VERIFY_ON_COMPLETION=true
BACKUP_VERIFY_BEFORE_RESTORE=true
```

This ensures:
- Corruption is detected immediately
- Restores never use bad backups
- Early warning of storage issues

### 2. Choose Appropriate Algorithm

**Production systems:**
```bash
BACKUP_CHECKSUM_ALGORITHM=sha256  # Best balance
```

**High-security environments:**
```bash
BACKUP_CHECKSUM_ALGORITHM=sha512  # Maximum security
```

**High-volume backups:**
```bash
BACKUP_CHECKSUM_ALGORITHM=md5  # Fastest (use with caution)
```

### 3. Monitor Verification Status

- Regularly check for unverified backups
- Investigate all verification failures
- Set up alerts for failed verifications
- Include verification status in reports

### 4. Verify After Storage Changes

Re-verify backups if you:
- Migrate to new storage
- Restore from archival media
- Copy backups to different location
- Suspect storage corruption

### 5. Keep Verified Backups

- Don't delete the last verified backup
- Maintain at least 3 verified backups
- Test restoration from verified backups
- Document verification failures

## Security Considerations

### Checksum Security

**SHA-256/SHA-512:**
- Cryptographically secure
- Tamper-evident (detects modifications)
- Collision-resistant
- Suitable for compliance requirements

**MD5:**
- NOT cryptographically secure
- Vulnerable to collision attacks
- Only detects accidental corruption
- Should not be used for security purposes

### Verification vs Encryption

**Verification** detects corruption and tampering  
**Encryption** protects confidentiality

LDAPGuard uses both:
- Checksums verify integrity
- Encryption (AES-256) protects LDAP passwords

### Audit Trail

All verification events are logged:
- Verification attempts
- Success/failure results
- Checksum calculations
- Algorithm changes

## Integration Examples

### Backup Verification Script

```python
import requests

API_URL = "http://localhost:8000/api"
TOKEN = "your-api-token"

def verify_all_unverified_backups():
    # Get all backups
    response = requests.get(
        f"{API_URL}/backups",
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    backups = response.json()
    
    # Filter unverified
    unverified = [b for b in backups 
                  if b.get('verification_status') == 'not_verified']
    
    print(f"Found {len(unverified)} unverified backups")
    
    # Verify each
    for backup in unverified:
        backup_id = backup['id']
        print(f"Verifying backup {backup_id}...")
        
        result = requests.post(
            f"{API_URL}/backups/verification/{backup_id}",
            headers={"Authorization": f"Bearer {TOKEN}"}
        )
        
        if result.status_code == 200:
            data = result.json()
            status = "✅ PASS" if data['verified'] else "❌ FAIL"
            print(f"  {status}: {data['message']}")
        else:
            print(f"  ❌ ERROR: {result.text}")

if __name__ == "__main__":
    verify_all_unverified_backups()
```

### Cron Job for Verification

```bash
#!/bin/bash
# /etc/cron.daily/verify-backups.sh

# Verify all unverified backups daily
curl -X POST "http://localhost:8000/api/backups/verification/batch-verify" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"verify_unverified_only": true}'
```

## Migration Guide

### Enabling Verification on Existing Backups

If you have backups created before verification was enabled:

1. **Run database migration:**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

2. **Recalculate checksums for existing backups:**
   ```bash
   # Via API (admin required)
   for backup_id in $(seq 1 100); do
     curl -X POST "http://localhost:8000/api/backups/verification/$backup_id/recalculate-checksum" \
       -H "Authorization: Bearer ADMIN_TOKEN"
   done
   ```

3. **Verify all backups:**
   ```bash
   # Via API
   for backup_id in $(seq 1 100); do
     curl -X POST "http://localhost:8000/api/backups/verification/$backup_id" \
       -H "Authorization: Bearer YOUR_TOKEN"
   done
   ```

4. **Update configuration:**
   ```bash
   echo "BACKUP_VERIFY_ON_COMPLETION=true" >> .env
   echo "BACKUP_VERIFY_BEFORE_RESTORE=true" >> .env
   docker-compose restart api worker
   ```

## See Also

- [Backup Retry Logic](BACKUP_RETRY_LOGIC.md) - Automatic retry for failed backups
- [Email Notifications](EMAIL_NOTIFICATIONS.md) - Get notified of verification results
- [Deployment Procedure](DEPLOYMENT_PROCEDURE.md) - Production deployment guide
