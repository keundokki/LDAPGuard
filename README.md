# LDAPGuard

[![CI/CD Pipeline](https://github.com/keundokki/LDAPGuard/actions/workflows/ci-cd.yml/badge.svg?branch=main)](https://github.com/keundokki/LDAPGuard/actions/workflows/ci-cd.yml)
[![Security Checks](https://github.com/keundokki/LDAPGuard/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/keundokki/LDAPGuard/actions/workflows/security.yml)
[![Code Quality](https://github.com/keundokki/LDAPGuard/actions/workflows/linting.yml/badge.svg?branch=main)](https://github.com/keundokki/LDAPGuard/actions/workflows/linting.yml)

**Multi-container Podman application for centralized LDAP backup/restore on Linux NAS**

## 🚀 Features

- **Multi-Service Architecture**: Web UI, API, Workers, PostgreSQL, Redis, Logging
- **Advanced Backup Capabilities**:
  - Incremental backups
  - Point-in-time recovery
  - Selective restore with LDAP filters
  - AES-256 encryption
  - Compression support
- **Security**:
  - LDAP authentication integration
  - Role-Based Access Control (RBAC)
  - Encrypted backup storage
- **Monitoring & Integration**:
  - Webhook notifications
  - Prometheus metrics
  - Comprehensive audit logging
- **Scheduling**: APScheduler-based automated backups
- **Production-Ready**: High Availability, disaster recovery, compliance support

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Web UI    │────▶│   API       │────▶│  PostgreSQL │
│  (Nginx)    │     │  (FastAPI)  │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   Redis     │     │   Workers   │
                    │             │◀────│ (APScheduler)│
                    └─────────────┘     └─────────────┘
```

## 📋 Prerequisites

- Podman or Docker
- Podman Compose or Docker Compose
- Linux NAS or server

## 🚀 Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/keundokki/LDAPGuard.git
   cd LDAPGuard
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   nano .env
   ```
  > **Note**: Never commit `.env` files. They are gitignored by default.

3. **Start services**:
   ```bash
   # Using Docker Compose
   docker-compose up -d
   
   # Or using Podman Compose
   podman-compose up -d
   ```

4. **Access the web interface**:
   - Open http://localhost:3000 in your browser
   - API documentation: http://localhost:8000/docs
   - Metrics: http://localhost:8000/metrics

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

- `POSTGRES_PASSWORD`: PostgreSQL database password
- `SECRET_KEY`: JWT token secret key (min 32 characters)
- `ENCRYPTION_KEY`: AES-256 encryption key (min 32 bytes)
- `BACKUP_DIR`: Directory for storing backups
- `BACKUP_RETENTION_DAYS`: Number of days to retain backups
- `WEBHOOK_URL`: Optional webhook endpoint for notifications
- `PROMETHEUS_ENABLED`: Enable/disable Prometheus metrics

### LDAP Server Configuration

Configure LDAP servers through the Web UI or API:

```json
{
  "name": "Primary LDAP",
  "host": "ldap.example.com",
  "port": 389,
  "use_ssl": false,
  "base_dn": "dc=example,dc=com",
  "bind_dn": "cn=admin,dc=example,dc=com",
  "bind_password": "password"
}
```

## 📚 API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

- `POST /auth/login` - Authenticate and get token
- `GET /ldap-servers/` - List LDAP servers
- `POST /backups/` - Create a new backup
- `POST /restores/` - Create a restore job
- `GET /metrics` - Prometheus metrics

## 🔒 Security

### Encryption

All backups are encrypted using AES-256-CBC encryption:
- Unique IV for each backup
- PKCS7 padding
- Base64 encoding for storage

### Authentication

Supports multiple authentication methods:
- Local user accounts with bcrypt password hashing
- LDAP authentication integration
- JWT token-based API access

### RBAC (Role-Based Access Control)

Three user roles:
- **Admin**: Full system access
- **Operator**: Create/restore backups, view servers
- **Viewer**: Read-only access

## 📊 Monitoring

### Prometheus Metrics

Available at `/metrics`:
- `ldapguard_backup_total` - Total backups by status and type
- `ldapguard_backup_duration_seconds` - Backup duration histogram
- `ldapguard_backup_size_bytes` - Backup file sizes
- `ldapguard_restore_total` - Total restore operations
- `ldapguard_active_backups` - Currently running backups
- `ldapguard_ldap_connection_errors_total` - LDAP connection errors

### Webhooks

Receive notifications for:
- Backup started/completed/failed
- Restore started/completed
- Custom event data in JSON format

## 🔄 Backup & Restore

### Full Backup

```bash
curl -X POST http://localhost:8000/backups/ \
  -H "Content-Type: application/json" \
  -d '{
    "ldap_server_id": 1,
    "backup_type": "full",
    "encrypted": true,
    "compression_enabled": true
  }'
```

### Incremental Backup

Incremental backups only capture changes since the last backup:
```json
{
  "ldap_server_id": 1,
  "backup_type": "incremental",
  "encrypted": true,
  "compression_enabled": true
}
```

### Selective Restore

Restore specific entries using LDAP filters:
```json
{
  "backup_id": 1,
  "ldap_server_id": 1,
  "selective_restore": true,
  "restore_filter": "(ou=users)"
}
```

### Point-in-Time Recovery

Restore to a specific timestamp:
```json
{
  "backup_id": 1,
  "ldap_server_id": 1,
  "point_in_time": "2024-01-01T12:00:00Z"
}
```

## 📅 Scheduled Backups

Configure automated backups with cron expressions:

```json
{
  "name": "Daily Full Backup",
  "ldap_server_id": 1,
  "backup_type": "full",
  "cron_expression": "0 2 * * *",
  "retention_days": 30
}
```

## 🏥 High Availability

For production deployments:

1. **Database Replication**: Configure PostgreSQL streaming replication
2. **Redis Sentinel**: Enable Redis Sentinel for HA
3. **Load Balancing**: Use HAProxy or Nginx for API load balancing
4. **Backup Storage**: Use network-attached storage (NAS) or S3-compatible storage

## 🐳 Container Management

### View logs
```bash
docker-compose logs -f api
docker-compose logs -f worker
```

### Restart services
```bash
docker-compose restart api
docker-compose restart worker
```

### Scale workers
```bash
docker-compose up -d --scale worker=3
```

## 🛠️ Development

### Run database migrations
```bash
docker-compose exec api alembic upgrade head
```

### Create new migration
```bash
docker-compose exec api alembic revision --autogenerate -m "Description"
```

### Run tests (when implemented)
```bash
docker-compose exec api pytest
```

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please use the GitHub issue tracker.

## 🙏 Acknowledgments

Built with:
- FastAPI - Modern Python web framework
- SQLAlchemy - SQL toolkit and ORM
- APScheduler - Advanced Python Scheduler
- PostgreSQL - Reliable relational database
- Redis - In-memory data structure store
- Prometheus - Monitoring and alerting