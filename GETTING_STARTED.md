# Getting Started with LDAPGuard

Welcome! This guide will take you from zero to your first LDAP backup in **under 10 minutes**.

---

## 🎯 What You'll Accomplish

By the end of this guide, you will:
- ✅ Have LDAPGuard installed and running
- ✅ Connect to your first LDAP server
- ✅ Create your first backup
- ✅ Understand the basics of scheduling and restoring

---

## 📋 Prerequisites

Before starting, ensure you have:

### Required
- **Container Runtime**: Docker or Podman installed
  - Test: `docker --version` or `podman --version`
  - Install: [Docker Desktop](https://www.docker.com/products/docker-desktop/) | [Podman](https://podman.io/getting-started/installation)

- **Compose Tool**: docker-compose or podman-compose
  - Test: `docker-compose --version` or `podman-compose --version`
  - Usually included with Docker Desktop

- **Git** (optional, for cloning)
  - Test: `git --version`

### Recommended
- **LDAP Server** to backup (OpenLDAP, Active Directory, FreeIPA)
  - Host/IP, port, admin credentials
  - If you don't have one, see [Testing with Demo LDAP](#testing-with-demo-ldap) below

---

## 🚀 Step 1: Install LDAPGuard

Choose your installation method:

### Option A: One-Line Install (Fastest)

```bash
curl -fsSL https://raw.githubusercontent.com/keundokki/LDAPGuard/main/install.sh | bash
```

**What happens:**
1. Checks your system for Docker/Podman
2. Generates secure encryption keys automatically
3. Creates configuration files
4. Starts all services
5. Shows you where to access the UI

**Expected output:**
```
✓ Docker found
✓ Generating secure keys...
✓ Starting services...
✓ Health check passed

╔════════════════════════════════════════════════╗
║   🎉  LDAPGuard is now running!               ║
╚════════════════════════════════════════════════╝

📍 Access: http://localhost:3000
🔑 Login:  admin / admin
```

### Option B: Git Clone + Makefile

```bash
git clone https://github.com/keundokki/LDAPGuard.git
cd LDAPGuard
make install
```

### Option C: Manual Setup

```bash
git clone https://github.com/keundokki/LDAPGuard.git
cd LDAPGuard
cp .env.example .env

# Generate secure keys
export SECRET_KEY=$(openssl rand -base64 32)
export ENCRYPTION_KEY=$(openssl rand -base64 32)
export POSTGRES_PASSWORD=$(openssl rand -base64 24)

# Update .env file (macOS)
sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
sed -i '' "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env
sed -i '' "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env

# Or for Linux
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
sed -i "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env
sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env

# Start services
docker-compose up -d
```

---

## 🔐 Step 2: First Login

1. **Open your browser** to http://localhost:3000

2. **Login with default credentials:**
   - Username: `admin`
   - Password: `admin`

3. **⚠️ CRITICAL: Change your password immediately**
   - Click on "👤 admin" in the top right
   - Select "Change Password"
   - Use a strong password (minimum 8 characters)

---

## 🌐 Step 3: Add Your First LDAP Server

### Quick Start

1. **Navigate to "Servers"** tab in the UI

2. **Click "+ Add Server"**

3. **Enter your LDAP details:**

   **For OpenLDAP:**
   ```
   Server Name:     Production LDAP
   Host:            ldap.example.com
   Port:            389
   Use SSL/TLS:     ☐ (uncheck for LDAP, check for LDAPS on port 636)
   Base DN:         dc=example,dc=com
   Bind DN:         cn=admin,dc=example,dc=com
   Bind Password:   your_admin_password
   ```

   **For Active Directory:**
   ```
   Server Name:     AD Domain Controller
   Host:            dc01.corp.local
   Port:            389
   Use SSL/TLS:     ☐
   Base DN:         dc=corp,dc=local
   Bind DN:         CN=backup_user,CN=Users,DC=corp,DC=local
   Bind Password:   your_backup_user_password
   ```

4. **Click "Test Connection"**
   - ✅ Success: You'll see entry count and connection confirmation
   - ❌ Failed: Check host, port, credentials, and firewall

5. **Click "Save"**

### Troubleshooting Connection Issues

| Error | Solution |
|-------|----------|
| **Connection timeout** | Check firewall, ensure LDAP server is accessible |
| **Authentication failed** | Verify bind DN and password |
| **Invalid DN** | Check base DN format (dc=example,dc=com) |
| **SSL/TLS error** | For LDAPS, ensure port 636 and check certificates |

---

## 💾 Step 4: Create Your First Backup

### Manual Backup (Immediate)

1. **Go to "Backups"** tab

2. **Click "+ Create Backup"**

3. **Configure your backup:**
   ```
   LDAP Server:      [Select your server]
   Backup Type:      Full Backup
   Encrypt:          ✅ Recommended
   Compress:         ✅ Recommended
   ```

4. **Click "Create Backup"**

5. **Watch the progress:**
   - Status changes: Pending → In Progress → Completed
   - Refresh the page to see updates
   - Typical backup time: 30 seconds to 5 minutes (depending on size)

6. **Verify success:**
   - Status shows "Completed" in green
   - Entry count matches your LDAP directory
   - File size appears reasonable

### Understanding Backup Types

| Type | When to Use | Description |
|------|-------------|-------------|
| **Full** | Daily/Weekly | Complete copy of all LDAP entries |
| **Incremental** | Hourly | Only changes since last backup (requires full backup first) |

---

## ⏰ Step 5: Schedule Automatic Backups

Don't want to create backups manually? Automate it!

1. **Go to "Scheduled Backups"** tab

2. **Click "+ Add Schedule"**

3. **Configure your schedule:**

   **Example: Daily Full Backup at 2 AM**
   ```
   Schedule Name:    Daily Full Backup
   LDAP Server:      [Your server]
   Backup Type:      Full Backup
   Cron Schedule:    0 2 * * *
   Encrypt:          ✅
   Compress:         ✅
   Enabled:          ✅
   ```

   **Example: Hourly Incremental Backup**
   ```
   Schedule Name:    Hourly Incremental
   LDAP Server:      [Your server]
   Backup Type:      Incremental
   Cron Schedule:    0 * * * *
   Encrypt:          ✅
   Compress:         ✅
   Enabled:          ✅
   ```

4. **Click "Save"**

### Cron Schedule Quick Reference

| Schedule | Cron Expression | Description |
|----------|----------------|-------------|
| Every hour | `0 * * * *` | At minute 0 |
| Every 6 hours | `0 */6 * * *` | At 00:00, 06:00, 12:00, 18:00 |
| Daily at 2 AM | `0 2 * * *` | Once per day |
| Weekly on Sunday | `0 3 * * 0` | Sunday at 3 AM |
| Monthly on 1st | `0 4 1 * *` | 1st day at 4 AM |

**Need help?** Use [crontab.guru](https://crontab.guru) to build your cron expression

---

## 🔄 Step 6: Test a Restore (Optional but Recommended)

Verify your backups are restorable:

### ⚠️ Important Warnings

- **NEVER restore to production LDAP without testing first**
- Restoring **overwrites existing data** in the target LDAP server
- Always test restores on a **separate test LDAP instance**
- Consider using a **different base DN** for testing

### Safe Restore Test

1. **Set up a test LDAP server** (or use a test OU)

2. **Go to "Restores"** tab

3. **Click "Restore Backup"** next to a completed backup

4. **Configure restore:**
   ```
   Target Server:    [Test LDAP server - NOT production!]
   Backup:           [Select your backup]
   Target DN:        ou=test,dc=example,dc=com  (different from production)
   ```

5. **Click "Start Restore"**

6. **Monitor progress:**
   - Watch status change from Pending → In Progress → Completed
   - Check entry count matches backup

7. **Verify on LDAP server:**
   ```bash
   # Using ldapsearch to verify
   ldapsearch -x -H ldap://test-server -D "cn=admin,dc=example,dc=com" \
     -w password -b "ou=test,dc=example,dc=com"
   ```

---

## 📊 Step 7: Monitor Your Backups

### Dashboard Overview

Visit the **Dashboard** tab to see:
- **Total Servers**: How many LDAP servers you're backing up
- **Total Backups**: Number of backups created
- **Active Jobs**: Currently running backups/restores
- **Backup Health**: Success rates, recent failures, schedule status

### Daily Monitoring Checklist

✅ Check dashboard for failed backups (should be 0)  
✅ Verify scheduled backups are running on time  
✅ Monitor disk space usage (`docker-compose exec api df -h /app/backups`)  
✅ Review audit logs for suspicious activity (Admin → Audit Log)

### Setting Up Notifications

Get alerted when backups fail:

1. **Go to Admin → Notifications**

2. **Configure webhook (Slack/Discord/Teams):**
   ```
   Webhook URL:    https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   Events:         ✅ Backup Failure (critical)
                   ☐ Backup Success (optional, can be noisy)
                   ✅ Restore Complete
   ```

3. **Click "Save Settings"**

**Slack Webhook Setup:**
- Go to https://api.slack.com/apps
- Create new app → Incoming Webhooks
- Copy webhook URL
- Paste into LDAPGuard

---

## 🎓 Next Steps - Becoming a Power User

### Week 1: Basic Operations
- [x] Install LDAPGuard
- [x] Add LDAP server
- [x] Create manual backup
- [x] Schedule automatic backups
- [ ] Test a restore on non-production
- [ ] Set up notifications
- [ ] Monitor for one week

### Week 2: Advanced Features
- [ ] Set up incremental backups
- [ ] Configure backup retention policies (Admin → Settings)
- [ ] Create multiple backup schedules (full daily, incremental hourly)
- [ ] Export configuration backup (Admin → Settings → Export Config)
- [ ] Set up API keys for automation (Admin → API Keys)

### Week 3: Production Hardening
- [ ] Review [SECURITY.md](SECURITY.md) checklist
- [ ] Change all default passwords
- [ ] Enable 2FA (when available)
- [ ] Set up off-site backup copies
- [ ] Create disaster recovery runbook
- [ ] Test full disaster recovery

### Advanced Topics
- [ ] **Kubernetes deployment** - See [k8s/README.md](k8s/README.md)
- [ ] **Prometheus monitoring** - Integrate with Grafana
- [ ] **Multi-server setups** - Backup multiple LDAP instances
- [ ] **API automation** - Use REST API for custom workflows
- [ ] **Selective restores** - Restore specific OUs or objects

---

## 🧪 Testing with Demo LDAP

Don't have an LDAP server? Spin up a demo one:

### Option A: Use Online Test LDAP
```
Host:         ldap.forumsys.com
Port:         389
Base DN:      dc=example,dc=com
Bind DN:      cn=read-only-admin,dc=example,dc=com
Bind Pwd:     password
```

### Option B: Local OpenLDAP Container

```bash
# In the LDAPGuard/LDAP directory
docker-compose up -d

# This creates a test LDAP server with sample data
# Access details:
Host:         localhost
Port:         389
Base DN:      dc=example,dc=com
Bind DN:      cn=admin,dc=example,dc=com
Password:     admin
```

See [LDAP/README.md](LDAP/README.md) for full demo LDAP setup.

---

## 📚 Essential Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Feature overview, installation options |
| [INSTALL.md](INSTALL.md) | Detailed installation guide |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Command cheat sheet |
| [SECURITY.md](SECURITY.md) | Security best practices |
| [k8s/README.md](k8s/README.md) | Kubernetes deployment |
| [API Docs](http://localhost:8000/docs) | Interactive API documentation |

---

## 🆘 Common Issues & Solutions

### Installation Issues

**Problem:** "Docker/Podman not found"
```bash
# Solution: Install Docker Desktop or Podman
# macOS: brew install --cask docker
# or: brew install podman podman-compose
```

**Problem:** "Port 3000 or 8000 already in use"
```bash
# Solution: Edit docker-compose.yml and change ports
# Change "3000:80" to "8080:80" for web UI
# Change "8000:8000" to "8001:8000" for API
```

### Connection Issues

**Problem:** "Cannot connect to LDAP server"
```bash
# Test LDAP connectivity manually
ldapsearch -x -H ldap://your-ldap-server:389 \
  -D "cn=admin,dc=example,dc=com" -w password \
  -b "dc=example,dc=com" -LLL "(objectClass=*)"

# If this fails, LDAPGuard will also fail
# Check: Firewall, LDAP server running, credentials
```

**Problem:** "SSL/TLS handshake failed"
```bash
# For LDAPS (port 636), ensure certificates are valid
# Or disable SSL verification (not recommended for production)
```

### Backup Issues

**Problem:** "Backup stuck in 'Pending' status"
```bash
# Check worker logs
docker-compose logs worker

# Restart worker if needed
docker-compose restart worker
```

**Problem:** "Database backup disk space full"
```bash
# Check disk space
df -h

# Clean old backups manually
rm -rf /path/to/LDAPGuard/backups/old-backups/

# Or configure retention policy in Admin → Settings
```

### Access Issues

**Problem:** "Forgot admin password"
```bash
# Reset via database
docker-compose exec db psql -U ldapguard -d ldapguard -c \
  "UPDATE users SET hashed_password = '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyJ3H6B6NeSm' WHERE username = 'admin';"

# New password: admin (CHANGE IMMEDIATELY after login)
```

---

## 💬 Getting Help

### Self-Service
1. Check this Getting Started guide
2. Review [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
3. Search [GitHub Issues](https://github.com/keundokki/LDAPGuard/issues)

### Community Support
- **GitHub Issues**: [Report bugs or request features](https://github.com/keundokki/LDAPGuard/issues/new)
- **Discussions**: [Ask questions](https://github.com/keundokki/LDAPGuard/discussions)

### When Reporting Issues
Include:
- LDAPGuard version: `cat VERSION`
- Container runtime: `docker --version` or `podman --version`
- Logs: `docker-compose logs api worker`
- Steps to reproduce
- Expected vs actual behavior

---

## ✅ Quick Start Checklist

Use this checklist for your first deployment:

### Installation (5 minutes)
- [ ] Docker/Podman installed and running
- [ ] Ran installation command
- [ ] Services started successfully
- [ ] Can access http://localhost:3000
- [ ] Logged in with admin/admin
- [ ] Changed default password

### Configuration (3 minutes)
- [ ] Added first LDAP server
- [ ] Tested connection successfully
- [ ] Server saved

### First Backup (2 minutes)
- [ ] Created manual backup
- [ ] Backup completed successfully
- [ ] Verified backup in list

### Automation (5 minutes)
- [ ] Created backup schedule
- [ ] Schedule enabled
- [ ] Next run time shows correctly

### Verification (Optional)
- [ ] Tested restore on non-production server
- [ ] Verified restored data
- [ ] Set up notifications
- [ ] Reviewed dashboard

---

## 🎉 You're Ready!

Congratulations! You now have:
- ✅ LDAPGuard running and accessible
- ✅ Your first LDAP server configured
- ✅ Backups being created automatically
- ✅ Understanding of basic operations

**Remember:**
- Check the dashboard regularly
- Test restores periodically
- Keep LDAPGuard updated
- Monitor disk space for backups
- Have a disaster recovery plan

Welcome to worry-free LDAP backup management! 🚀

---

**Next:** Explore advanced features in [README.md](README.md) or dive into [API documentation](http://localhost:8000/docs)
