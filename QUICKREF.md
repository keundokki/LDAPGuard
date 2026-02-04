# LDAPGuard - Quick Reference

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        LDAPGuard System                       │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────┐   ┌────────────┐   ┌─────────────────┐      │
│  │  Web UI    │──▶│  API       │──▶│  PostgreSQL     │      │
│  │  (Nginx)   │   │  (FastAPI) │   │  (Database)     │      │
│  └────────────┘   └────────────┘   └─────────────────┘      │
│                          │                   │                │
│                          ▼                   ▼                │
│                   ┌────────────┐     ┌──────────────┐        │
│                   │  Redis     │◀────│  Workers     │        │
│                   │  (Queue)   │     │ (APScheduler)│        │
│                   └────────────┘     └──────────────┘        │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## Key Technologies

| Component | Technology | Purpose |
|-----------|-----------|----------|
| API | FastAPI | REST API, async support |
| Database | PostgreSQL | Data persistence |
| Queue | Redis | Task queue, caching |
| Workers | APScheduler | Scheduled tasks |
| Web UI | HTML/CSS/JS | User interface |
| Encryption | AES-256-CBC | Backup encryption |
| Auth | JWT + bcrypt | Authentication |
| Metrics | Prometheus | Monitoring |

## Core Features

### 1. Backup Types
- **Full Backup**: Complete LDAP directory snapshot
- **Incremental**: Only changes since last backup

### 2. Restore Capabilities
- **Full Restore**: Restore entire directory
- **Selective Restore**: Filter-based partial restore
- **Point-in-Time**: Restore to specific timestamp

### 3. Security Features
- **AES-256 Encryption**: All backups encrypted
- **RBAC**: Three-tier access control
  - Admin: Full access
  - Operator: Backup/restore operations
  - Viewer: Read-only access
- **LDAP Auth**: Integration with LDAP directories
- **JWT Tokens**: Secure API access
- **Audit Logging**: Complete audit trail

### 4. Automation
- **Scheduled Backups**: Cron-based scheduling
- **Auto-cleanup**: Retention policy enforcement
- **Webhooks**: Event notifications
- **Metrics**: Prometheus monitoring

## Quick Commands

### Start Services
```bash
# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Production
docker-compose up -d
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
```

### Database Operations
```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Create migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Database shell
docker-compose exec postgres psql -U ldapguard
```

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get token

### LDAP Servers
- `GET /ldap-servers/` - List servers
- `POST /ldap-servers/` - Add server
- `PUT /ldap-servers/{id}` - Update server
- `DELETE /ldap-servers/{id}` - Delete server

### Backups
- `GET /backups/` - List backups
- `POST /backups/` - Create backup
- `GET /backups/{id}` - Get backup details
- `DELETE /backups/{id}` - Delete backup

### Restores
- `GET /restores/` - List restore jobs
- `POST /restores/` - Create restore job
- `GET /restores/{id}` - Get restore details

### System
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

## Environment Variables

### Required
```env
POSTGRES_PASSWORD=<secure-password>
SECRET_KEY=<32-char-minimum>
ENCRYPTION_KEY=<32-char-minimum>
```

### Optional
```env
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://webhook.example.com
BACKUP_RETENTION_DAYS=30
DEBUG=false
```

## Common Tasks

### Create a Backup
```bash
curl -X POST http://localhost:8000/backups/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ldap_server_id": 1,
    "backup_type": "full",
    "encrypted": true,
    "compression_enabled": true
  }'
```

### Schedule Daily Backup
```bash
curl -X POST http://localhost:8000/scheduled-backups/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Backup",
    "ldap_server_id": 1,
    "backup_type": "full",
    "cron_expression": "0 2 * * *",
    "retention_days": 30
  }'
```

### Restore from Backup
```bash
curl -X POST http://localhost:8000/restores/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "backup_id": 1,
    "ldap_server_id": 1,
    "selective_restore": false
  }'
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose logs api

# Check status
docker-compose ps

# Restart service
docker-compose restart api
```

### Database Connection Issues
```bash
# Verify database is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U ldapguard -c "SELECT 1;"
```

### Worker Not Processing Jobs
```bash
# Check worker logs
docker-compose logs worker

# Verify Redis connection
docker-compose exec redis redis-cli ping

# Restart worker
docker-compose restart worker
```

## File Locations

### In Container
- Backups: `/app/backups`
- Logs: `/app/logs`
- Config: `/app/config`

### On Host
- Config: `./config/`
- Logs: `./logs/`
- Backups: Docker volume `backup_data`

## Performance Tuning

### Scale Workers
```bash
docker-compose up -d --scale worker=3
```

### Database Tuning
Edit `docker-compose.yml`:
```yaml
postgres:
  command:
    - -c
    - shared_buffers=256MB
    - -c
    - max_connections=200
```

### Redis Memory
```yaml
redis:
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

## Security Best Practices

1. ✅ Change default SECRET_KEY and ENCRYPTION_KEY
2. ✅ Use strong PostgreSQL password
3. ✅ Enable LDAPS for LDAP connections
4. ✅ Run behind reverse proxy with SSL/TLS
5. ✅ Implement network isolation
6. ✅ Regular security updates
7. ✅ Enable audit logging
8. ✅ Restrict API access with firewall

## Backup Strategy

### 3-2-1 Rule
- **3** copies of data
- **2** different media types
- **1** off-site copy

### Recommended Schedule
- **Full Backup**: Daily at 2 AM
- **Incremental**: Every 6 hours
- **Retention**: 30 days
- **Off-site**: Weekly export

## Monitoring

### Metrics to Watch
- Backup success rate
- Backup duration
- Backup file size
- LDAP connection errors
- Active jobs count
- Disk space usage

### Alerts to Set
- Backup failures
- Long-running backups
- Disk space low
- Service down
- High error rate

## Resources

- Documentation: `./docs/`
- API Docs: http://localhost:8000/docs
- Examples: `./docs/examples.md`
- Security: `./SECURITY.md`
- Contributing: `./CONTRIBUTING.md`
