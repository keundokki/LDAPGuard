# LDAPGuard - Quick Reference Card

## 🚀 Installation

### Fastest (One Command)
```bash
curl -fsSL https://raw.githubusercontent.com/keundokki/LDAPGuard/main/install.sh | bash
```

### Using Make
```bash
git clone https://github.com/keundokki/LDAPGuard.git
cd LDAPGuard
make install
```

## 🔄 Updating Existing Installation

### Docker/Podman Updates

#### Automated Update (Recommended)
```bash
# Update to latest
./update.sh

# Update to specific version
./update.sh --version 1.0.1

# Or using make
make update
```

**What happens during update:**
1. ✓ Database backup created automatically
2. ✓ Docker images pulled for specified version
3. ✓ IMAGE_TAG updated in .env
4. ✓ Services stopped gracefully
5. ✓ Database migrations run
6. ✓ Services restarted with new version
7. ✓ Health check performed

### Kubernetes Updates

```bash
# Update K8s deployment to specific version
./update-k8s.sh --version 1.0.1

# With custom namespace
./update-k8s.sh --version 1.0.1 --namespace production

# Force specific method
./update-k8s.sh --version 1.0.1 --method kustomize
./update-k8s.sh --version 1.0.1 --method argocd
```

### Version Management

```bash
make version        # Show current version
make check-updates  # Check if updates available
```

**Image Tags:**
- `latest` - Latest stable release
- `1.0.1` - Specific version
- `sha-abc123` - Specific commit

### Manual Version Selection

Edit `.env`:
```bash
IMAGE_TAG=1.0.1  # Pin to specific version
```

Then:
```bash
docker-compose pull && docker-compose up -d
```

## 🎮 Common Commands

### Service Control
```bash
make start         # Start all services
make stop          # Stop all services
make restart       # Restart all services
make status        # Show container status
```

### Monitoring
```bash
make logs          # View all logs (live)
make logs-api      # API logs only
make logs-web      # Web logs only
make health        # Health check
```

### Maintenance
```bash
make update        # Pull latest code & restart
make clean         # Remove containers
make rebuild       # Rebuild from scratch
```

### Database Operations
```bash
make db-shell      # Open PostgreSQL shell
make db-backup     # Backup database
make db-restore    # Restore database
```

## 🔗 Access Points

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| **Web UI** | http://localhost:3000 | admin / admin |
| **API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **Metrics** | http://localhost:8000/metrics | - |

## 📁 Important Directories

```
ldapguard/
├── .env              # Main configuration file
├── backups/          # Backup storage directory
├── logs/             # Application logs
└── docker-compose.yml
```

## ⚙️ Configuration Files

### .env (Main Config)
```bash
# Security (CHANGE THESE!)
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
POSTGRES_PASSWORD=your-db-password

# Backup Settings
BACKUP_RETENTION_DAYS=30
BACKUP_DIR=/app/backups

# Debug
DEBUG=false
```

## 🔐 Security Checklist

- [ ] Change default admin password immediately
- [ ] Update SECRET_KEY in .env
- [ ] Update ENCRYPTION_KEY in .env
- [ ] Update POSTGRES_PASSWORD in .env
- [ ] Set DEBUG=false for production
- [ ] Configure firewall rules
- [ ] Enable HTTPS for production
- [ ] Set up regular database backups

## 🆘 Troubleshooting

### Services won't start
```bash
# Check logs
make logs

# Check container status
make status

# Rebuild everything
make clean && make rebuild
```

### Can't access web interface
```bash
# Check if web container is running
docker ps | grep web

# Check web logs
make logs-web

# Restart web service
docker-compose restart web
```

### Database connection errors
```bash
# Check database status
docker ps | grep postgres

# View database logs
docker-compose logs postgres

# Access database shell
make db-shell
```

### "Permission denied" errors
```bash
# Fix directory permissions
sudo chown -R $USER:$USER backups/ logs/

# Or run with sudo
sudo make start
```

## 🔄 Backup & Restore Workflow

### Create Backup (Web UI)
1. Navigate to "Servers" tab
2. Click "Add Server" → Configure LDAP server
3. Navigate to "Backups" tab
4. Click "Create Backup"
5. Select server, type, and options
6. Click "Create"

### Create Backup (API)
```bash
curl -X POST http://localhost:8000/backups/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ldap_server_id": 1,
    "backup_type": "full",
    "category": "directory",
    "encrypted": true,
    "compression_enabled": true
  }'
```

### Restore Backup
1. Navigate to "Backups" tab
2. Find the backup you want to restore
3. Click "Restore" button
4. Confirm the restore operation
5. Monitor progress in "Restores" tab

## 📊 Monitoring

### View Metrics
```bash
# Prometheus metrics
curl http://localhost:8000/metrics

# Health check
curl http://localhost:8000/health
```

### Check Logs
```bash
# All services
make logs

# Specific service
docker-compose logs -f api
docker-compose logs -f web
docker-compose logs -f worker
```

## 🔧 Advanced Operations

### Run Database Migration
```bash
docker-compose exec api alembic upgrade head
```

### Access API Container Shell
```bash
docker-compose exec api bash
```

### View Scheduled Jobs
```bash
docker-compose logs worker | grep "Scheduled"
```

### Clear Redis Cache
```bash
docker-compose exec redis redis-cli FLUSHALL
```

## 📱 Support

- **Documentation**: [github.com/keundokki/LDAPGuard](https://github.com/keundokki/LDAPGuard)
- **Issues**: [github.com/keundokki/LDAPGuard/issues](https://github.com/keundokki/LDAPGuard/issues)
- **API Docs**: http://localhost:8000/docs

## 🎓 Learning Resources

### First Steps
1. Install LDAPGuard ✓
2. Change admin password
3. Add your first LDAP server
4. Create a test backup
5. Restore the test backup
6. Set up scheduled backups

### Next Level
1. Configure webhooks
2. Set up monitoring
3. Configure RBAC roles
4. Enable incremental backups
5. Test disaster recovery

---

**Quick Tip**: Bookmark this page for easy reference!
