# LDAPGuard Disaster Recovery Guide

## Critical Information to Backup

If your LDAPGuard application goes down completely, you need **two things** to recover your backups:

### 1. The Encryption Key ⚠️ **CRITICAL**
- **Location**: Environment variable `ENCRYPTION_KEY` 
- **Default**: `your-encryption-key-32-bytes-min` (MUST be changed in production!)
- **Where set**: 
  - In `.env` file (if you created one)
  - In `docker-compose.yml` as `${ENCRYPTION_KEY:-your-encryption-key-32-bytes-min}`
  - In environment variables when starting containers

**⚠️ WITHOUT THIS KEY, YOUR BACKUPS ARE UNRECOVERABLE!**

### 2. The Backup Files
- **Local storage**: `/app/backups/` inside containers (mapped to Docker volume `backup_data`)
- **Cloud storage**: S3 bucket (if S3 is enabled)

---

## Backup File Format

Encrypted backup files have this naming pattern:
```
ServerName_backuptype_YYYYMMDD_HHMMSS.ldif.gz.enc
```

**Example**: `Test LDAP_full_20260222_170455.ldif.gz.enc`

**File layers**:
1. `.enc` - AES-256 encrypted (requires `ENCRYPTION_KEY`)
2. `.gz` - Gzip compressed
3. `.ldif` - LDAP Data Interchange Format (raw LDAP data)

---

## Manual Decryption Procedure (Without LDAPGuard)

If LDAPGuard is down but you have the encryption key and backup files, follow these steps:

### Step 1: Save Your Encryption Key

**Right now, before disaster strikes, save your encryption key!**

```bash
# Check your current encryption key
podman-compose -f docker-compose.yml -f docker-compose.dev.yml exec api printenv ENCRYPTION_KEY

# Or check docker-compose.yml
grep ENCRYPTION_KEY docker-compose.yml
```

**Store this key securely** in:
- Password manager (1Password, LastPass, Bitwarden)
- Encrypted vault (HashiCorp Vault, AWS Secrets Manager)
- Secure offline location (encrypted USB drive, safe)

### Step 2: Export Backup Files

Get your backup files from:

**Option A: From Docker volume**
```bash
# List backups in the volume
podman-compose exec api ls -lh /app/backups/

# Copy all backups to local machine
mkdir -p ~/ldapguard-backup-export
podman cp ldapguard-api:/app/backups/. ~/ldapguard-backup-export/
```

**Option B: From S3** (if cloud storage enabled)
```bash
# Using AWS CLI (or compatible tool)
aws s3 sync s3://your-bucket-name/backups/ ~/ldapguard-backup-export/
```

### Step 3: Create Decryption Script

Create `decrypt_backup.py`:

```python
#!/usr/bin/env python3
"""
LDAPGuard Backup Decryption Tool
Decrypt backups without running the full LDAPGuard application
"""

import base64
import gzip
import sys
from pathlib import Path
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class AESDecryption:
    """AES-256 decryption (matches LDAPGuard's encryption)."""

    def __init__(self, key: str):
        # Ensure key is 32 bytes for AES-256 (same as LDAPGuard)
        self.key = key.encode()[:32].ljust(32, b"0")

    def decrypt(self, encrypted_data: str) -> bytes:
        """Decrypt data using AES-256-CBC."""
        # Base64 decode
        combined = base64.b64decode(encrypted_data)

        # Extract IV (first 16 bytes) and encrypted data
        iv = combined[:16]
        encrypted = combined[16:]

        # Decrypt
        cipher = Cipher(
            algorithms.AES(self.key), modes.CBC(iv), backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted) + decryptor.finalize()

        # Unpad
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()

        return data


def decrypt_backup(encrypted_file: str, encryption_key: str, output_file: str = None):
    """Decrypt an LDAPGuard backup file."""
    
    encrypted_path = Path(encrypted_file)
    
    if not encrypted_path.exists():
        print(f"Error: File not found: {encrypted_file}")
        sys.exit(1)
    
    # Determine output filename
    if output_file is None:
        # Remove .enc extension
        if encrypted_path.suffix == '.enc':
            output_file = str(encrypted_path.with_suffix(''))
        else:
            output_file = str(encrypted_path) + '.decrypted'
    
    print(f"Decrypting: {encrypted_file}")
    print(f"Output to: {output_file}")
    
    # Read encrypted data
    with open(encrypted_file, 'r') as f:
        encrypted_data = f.read()
    
    # Decrypt
    decryptor = AESDecryption(encryption_key)
    decrypted_data = decryptor.decrypt(encrypted_data)
    
    # Write decrypted data (still compressed)
    with open(output_file, 'wb') as f:
        f.write(decrypted_data)
    
    print(f"✓ Decryption complete: {output_file}")
    
    # If it's a .gz file, offer to decompress
    if output_file.endswith('.gz'):
        decompress_choice = input("Decompress the .gz file? (y/n): ").lower()
        if decompress_choice == 'y':
            decompressed_file = output_file[:-3]  # Remove .gz
            print(f"Decompressing to: {decompressed_file}")
            
            with gzip.open(output_file, 'rb') as f_in:
                with open(decompressed_file, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            print(f"✓ Decompression complete: {decompressed_file}")
            print(f"\nFinal LDIF file: {decompressed_file}")
            return decompressed_file
    
    return output_file


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 decrypt_backup.py <encrypted_file> <encryption_key> [output_file]")
        print("\nExample:")
        print("  python3 decrypt_backup.py backup.ldif.gz.enc 'your-encryption-key-32-bytes-min'")
        sys.exit(1)
    
    encrypted_file = sys.argv[1]
    encryption_key = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        result_file = decrypt_backup(encrypted_file, encryption_key, output_file)
        print(f"\n✓ Success! Decrypted file: {result_file}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
```

### Step 4: Install Dependencies

```bash
pip3 install cryptography
```

### Step 5: Decrypt Your Backups

```bash
# Decrypt a single backup
python3 decrypt_backup.py \
  "Test LDAP_full_20260222_170455.ldif.gz.enc" \
  "your-encryption-key-32-bytes-min"

# Batch decrypt all backups
for file in *.enc; do
  python3 decrypt_backup.py "$file" "your-encryption-key-32-bytes-min"
done
```

**Result**: You'll have `.ldif` files that contain your LDAP directory data in plain text.

### Step 6: Restore to LDAP Server

Use standard LDAP tools to restore:

```bash
# Using ldapadd (for new entries)
ldapadd -x -D "cn=admin,dc=example,dc=com" \
  -w admin_password \
  -f "Test LDAP_full_20260222_170455.ldif"

# Using ldapmodify (for existing entries)
ldapmodify -x -D "cn=admin,dc=example,dc=com" \
  -w admin_password \
  -f "Test LDAP_full_20260222_170455.ldif"

# Using slapadd (offline restore - stop LDAP server first)
systemctl stop slapd
slapadd -l "Test LDAP_full_20260222_170455.ldif"
systemctl start slapd
```

---

## Quick Recovery Checklist

- [ ] **Encryption key saved securely** (in password manager + offline backup)
- [ ] **Backup files exported** (from Docker volume or S3 to external storage)
- [ ] **Decryption script saved** (keep `decrypt_backup.py` with backups)
- [ ] **Test recovery once** (decrypt one backup to verify process works)
- [ ] **Document LDAP connection details** (host, port, bind DN, bind password)
- [ ] **S3 credentials saved** (if using cloud storage)

---

## Prevention: What to Backup Regularly

### Application Configuration
```bash
# Export critical files
tar -czf ldapguard-config-backup.tar.gz \
  docker-compose.yml \
  docker-compose.dev.yml \
  .env \
  DISASTER_RECOVERY.md
```

### Database (PostgreSQL)
```bash
# Dump LDAPGuard database
podman-compose exec postgres pg_dump -U ldapguard ldapguard > ldapguard-db-backup.sql
```

### Complete System Backup
```bash
# Everything in one archive
mkdir -p ~/ldapguard-disaster-backup
podman-compose exec api tar -czf - /app/backups | cat > ~/ldapguard-disaster-backup/backups.tar.gz
podman-compose exec postgres pg_dump -U ldapguard ldapguard > ~/ldapguard-disaster-backup/database.sql
cp docker-compose*.yml .env ~/ldapguard-disaster-backup/
cp DISASTER_RECOVERY.md ~/ldapguard-disaster-backup/

# Store encryption key separately!
echo "ENCRYPTION_KEY=your-actual-key-here" > ~/ldapguard-disaster-backup/ENCRYPTION_KEY.txt
chmod 600 ~/ldapguard-disaster-backup/ENCRYPTION_KEY.txt
```

---

## Recovery Scenarios

### Scenario 1: Application Down, Data Intact
**Problem**: LDAPGuard containers crashed but volumes are intact

**Solution**: 
```bash
podman-compose -f docker-compose.yml -f docker-compose.dev.yml down
podman-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Scenario 2: Complete Server Loss
**Problem**: Server destroyed, need to recover from backups

**Solution**:
1. Get encryption key from secure storage
2. Download backups from S3 or offline backup
3. Use decryption script (Step 3-5 above)
4. Restore to new LDAP server

### Scenario 3: Lost Encryption Key
**Problem**: Encryption key lost/forgotten

**Solution**: 
⚠️ **Backups are UNRECOVERABLE without the encryption key!**
- This is why storing the key securely is critical
- No backdoor exists - this is by design for security
- Only option: Restore LDAP from source or alternative backups

---

## Testing Your Disaster Recovery

**Test this procedure NOW while everything is working:**

```bash
# 1. Get your encryption key
ENCRYPTION_KEY=$(podman-compose exec api printenv ENCRYPTION_KEY)
echo "Your encryption key: $ENCRYPTION_KEY"

# 2. Copy one backup file
podman cp ldapguard-api:/app/backups/. /tmp/dr-test/

# 3. Decrypt it
cd /tmp/dr-test
python3 decrypt_backup.py *.enc "$ENCRYPTION_KEY"

# 4. Verify the LDIF file is readable
less *.ldif
```

If this works, you're prepared for disaster recovery!

---

## Support & Notes

- **Encryption**: AES-256-CBC with random IV (industry standard)
- **Compression**: Standard gzip
- **LDIF Format**: RFC 2849 compliant
- **Key Length**: Must be at least 1 character (padded to 32 bytes)
- **Security**: Never store encryption key with backups!

**Questions?** Review this guide regularly and test the procedure annually.
