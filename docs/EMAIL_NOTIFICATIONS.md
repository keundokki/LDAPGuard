# Email Notifications Setup Guide

LDAPGuard supports email notifications for backup and restore operations. You'll receive alerts when:

- Backup operations start, complete, or fail
- Restore operations start, complete, or fail

## Quick Setup

### 1. Configure Email Settings

Add email configuration to your `.env` file:

```bash
# Enable email notifications
EMAIL_ENABLED=true

# SMTP server configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password

# Sender information
EMAIL_FROM=noreply@ldapguard.local
EMAIL_FROM_NAME=LDAPGuard

# Application URL (for links in emails)
APP_URL=https://ldapguard.yourdomain.com
```

### 2. Configure Recipients

Set notification recipients in the LDAPGuard admin interface:

1. Navigate to **Settings** → **System Settings**
2. Add or update the `notification_email` setting
3. Enter comma-separated email addresses:
   ```
   admin@example.com, ops@example.com, backup-team@example.com
   ```

### 3. Restart Services

```bash
# Docker/Podman Compose
make restart

# Or manually
docker compose down
docker compose up -d

# Kubernetes
kubectl rollout restart deployment/ldapguard-worker -n ldapguard
```

## Provider-Specific Configurations

### Gmail

**Requirements:**
- Enable 2-Factor Authentication on your Google account
- Generate an App-Specific Password (not your regular password)

**Steps:**
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification
3. Go to "App passwords" → Generate a new password
4. Use that password in `SMTP_PASSWORD`

**Configuration:**
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # App-specific password
```

### SendGrid

**Requirements:**
- SendGrid account and API key

**Configuration:**
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_USERNAME=apikey
SMTP_PASSWORD=SG.xxxxx  # Your SendGrid API key
EMAIL_FROM=verified-sender@yourdomain.com
```

### Office 365 / Outlook

**Configuration:**
```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_USERNAME=your-email@domain.com
SMTP_PASSWORD=your-password
```

### AWS SES (Simple Email Service)

**Configuration:**
```bash
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_USERNAME=<SES-SMTP-USERNAME>
SMTP_PASSWORD=<SES-SMTP-PASSWORD>
EMAIL_FROM=verified-sender@yourdomain.com
```

### Mailgun

**Configuration:**
```bash
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_USERNAME=postmaster@your-domain.mailgun.org
SMTP_PASSWORD=<your-smtp-password>
```

### Generic SMTP Server

For any SMTP server:

```bash
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587    # or 465 for SSL, 25 for unencrypted
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_USERNAME=your-username
SMTP_PASSWORD=your-password
```

## Email Notification Types

### Backup Started
- Sent when a backup begins
- Contains: Server name, Backup ID
- Link to backup dashboard

### Backup Completed
- Sent when backup finishes successfully
- Contains: Server name, Entry count, File size, Duration
- Link to backup details

### Backup Failed
- Sent when backup encounters an error
- Contains: Server name, Error message, Troubleshooting tips
- Link to backup logs

### Restore Started
- Sent when a restore begins
- Contains: Restore ID, Source Backup ID
- Link to restore dashboard

### Restore Completed
- Sent when restore finishes successfully
- Contains: Restore ID, Entries restored, Duration
- Link to restore details

### Restore Failed
- Sent when restore encounters an error
- Contains: Restore ID, Error message, Troubleshooting tips
- Link to restore logs

## Testing Email Configuration

### Test SMTP Connection

Use the Python SMTP test script:

```python
import smtplib

# Your SMTP settings
host = "smtp.gmail.com"
port = 587
username = "your-email@gmail.com"
password = "your-app-password"

try:
    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(username, password)
        print("✅ SMTP connection successful!")
except Exception as e:
    print(f"❌ SMTP connection failed: {e}")
```

### Trigger Test Backup

1. Create a manual backup from the web UI
2. Watch for email notifications
3. Check worker logs if emails don't arrive:
   ```bash
   # Docker/Podman
   docker compose logs -f worker
   
   # Kubernetes
   kubectl logs -f deployment/ldapguard-worker -n ldapguard
   ```

## Troubleshooting

### Emails Not Arriving

1. **Check configuration:**
   ```bash
   # Verify environment variables
   docker compose exec api env | grep EMAIL
   docker compose exec api env | grep SMTP
   ```

2. **Check worker logs:**
   ```bash
   docker compose logs worker | grep -i email
   ```

3. **Verify EMAIL_ENABLED is true:**
   ```bash
   echo $EMAIL_ENABLED  # Should output: true
   ```

4. **Check notification recipients:**
   - Go to Settings → System Settings
   - Verify `notification_email` exists with valid addresses

### Authentication Errors

- **Gmail:** Use app-specific password, not account password
- **Office 365:** Enable "SMTP AUTH" in admin center
- **AWS SES:** Verify sender email address
- **SendGrid:** Use `apikey` as username (literally)

### Connection Timeouts

- Check firewall rules allow outbound SMTP (ports 25, 587, 465)
- Verify `SMTP_HOST` is correct
- Try different ports (587 with TLS, 465 with SSL)

### SSL/TLS Errors

```bash
# Port 587 (STARTTLS)
SMTP_USE_TLS=true
SMTP_USE_SSL=false

# Port 465 (SSL)
SMTP_USE_TLS=false
SMTP_USE_SSL=true

# Port 25 (No encryption - not recommended)
SMTP_USE_TLS=false
SMTP_USE_SSL=false
```

### Wrong Sender Address

Some providers require `EMAIL_FROM` to match an authenticated/verified address:
- SendGrid: Must verify sender domain/address
- AWS SES: Must verify in SES console
- Gmail: Can use any address but may get warning

## Advanced Configuration

### HTML Templates

Email templates are located in `api/templates/email/`:
- `backup_started.html`
- `backup_success.html`
- `backup_failed.html`
- `restore_started.html`
- `restore_success.html`
- `restore_failed.html`

You can customize these templates. Use `{{variable_name}}` for replacements.

### Multiple Recipients

Add multiple email addresses separated by commas in System Settings:
```
admin@example.com, backup-team@example.com, ops-oncall@example.com
```

### Per-Server Recipients (Future Enhancement)

Currently, all backups send to the same recipient list. To implement per-server recipients, you could:
1. Add `notification_emails` column to `ldap_servers` table
2. Modify worker tasks to check server-specific settings first
3. Fall back to global `notification_email` setting

## Security Recommendations

1. **Never commit passwords to git:**
   - Add `.env` to `.gitignore`
   - Use encrypted environment variables in CI/CD

2. **Use app-specific passwords:**
   - Don't use account passwords
   - Rotate credentials regularly

3. **Restrict SMTP access:**
   - Use firewall rules to limit outbound SMTP
   - Monitor SMTP authentication logs

4. **Encrypt in transit:**
   - Always use TLS/SSL (`SMTP_USE_TLS=true`)
   - Never use port 25 unencrypted in production

## Support

For issues:
1. Check worker logs: `docker compose logs worker`
2. Verify SMTP connectivity manually
3. Review [Gmail](https://support.google.com/mail/answer/7126229), [SendGrid](https://docs.sendgrid.com/for-developers/sending-email/getting-started-smtp), or provider docs
4. Open an issue on GitHub with sanitized logs
