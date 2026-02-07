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

### Docker/Podman Deployment
- Podman or Docker
- Podman Compose or Docker Compose
- Linux NAS or server

### Kubernetes Deployment
- Kubernetes 1.25+ cluster
- kubectl configured
- ArgoCD (recommended) or Helm 3.0+

## 🚀 Quick Start

### Option 1: Docker/Podman (Local Development)

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

### Option 2: Kubernetes (Production)

LDAPGuard supports two Kubernetes deployment methods:

#### 📦 **Helm (Recommended for most users)**

Simplest deployment with key-value customization:

```bash
# 1. Create namespace and secrets
kubectl create namespace ldapguard
kubectl create secret generic ldapguard-secrets \
  --from-literal=POSTGRES_PASSWORD="$(openssl rand -base64 24)" \
  --from-literal=SECRET_KEY="$(openssl rand -base64 32)" \
  --from-literal=ENCRYPTION_KEY="$(openssl rand -base64 32)" \
  --from-literal=DATABASE_URL="postgresql+asyncpg://ldapguard:PASSWORD@postgres:5432/ldapguard" \
  -n ldapguard

# 2. Deploy with Helm
helm install ldapguard ./helm -n ldapguard

# 3. Access via port-forward
kubectl port-forward svc/web -n ldapguard 8080:80
```

**ArgoCD Web UI Deployment:**
- Repository: `https://github.com/keundokki/LDAPGuard.git`
- Path: `helm`
- Customize via Helm Parameters (e.g., `ingress.enabled=true`, `api.replicas=3`)

📖 **Full documentation:** [helm/README.md](helm/README.md)

#### 🔧 **Kustomize (Advanced users)**

For complex customizations using YAML patches:

```bash
# 1. Create namespace and secrets (same as above)

# 2. Deploy with kubectl
kubectl apply -k k8s/

# 3. Customize with patches (optional)
kubectl apply -k k8s/ --kustomization k8s/examples/patches/
```

📖 **Full documentation:** [k8s/README.md](k8s/README.md)

**Comparison:**

| Feature | Helm | Kustomize |
|---------|------|----------|
| **Ease of Use** | ⭐⭐⭐ Simple key-value | ⭐⭐ Requires YAML knowledge |
| **ArgoCD GUI** | ✅ Parameter input | ❌ Requires patch files |
| **Flexibility** | ⭐⭐ 100+ parameters | ⭐⭐⭐ Any YAML field |
| **Best For** | Most deployments | Complex customizations |

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

## ☸️ Kubernetes Deployment

LDAPGuard provides production-ready Kubernetes manifests in two formats:

### Helm Chart (`helm/`)

**Features:**
- Simple key-value customization
- ArgoCD Web GUI support
- 100+ configurable parameters
- Conditional features (ingress, backup volume, network policies)

**Quick Deploy:**
```bash
helm install ldapguard ./helm -n ldapguard
```

**Customize via values.yaml:**
```yaml
images:
  api:
    tag: "0.0.8"

api:
  replicas: 3
  resources:
    limits:
      memory: "1Gi"
      cpu: "2000m"

ingress:
  enabled: true
  domain: "ldapguard.yourdomain.com"

backup:
  enabled: true
  storage:
    size: "100Gi"
    storageClassName: "nfs-client"
```

**ArgoCD Deployment:**
- See [helm/examples/](helm/examples/) for ready-to-use ArgoCD Application manifests
- Customize directly in ArgoCD Web UI using Helm Parameters

📖 **Documentation:** [helm/README.md](helm/README.md)

### Kustomize (`k8s/`)

**Features:**
- YAML-based patching for advanced customizations
- Organized directory structure
- Example patches for common scenarios
- Compatible with ArgoCD

**Directory Structure:**
```
k8s/
├── deployments/        # API, Worker, Web
├── statefulsets/       # PostgreSQL, Redis
├── services/           # Service definitions
├── storage/            # PersistentVolumeClaims
├── config/             # ConfigMaps
├── network/            # NetworkPolicy, Middleware
└── examples/           # ArgoCD manifests and patches
```

**Quick Deploy:**
```bash
kubectl apply -k k8s/
```

**Customize with patches:**
```bash
# Enable ingress
kubectl apply -f k8s/examples/patches/ingress.yaml

# Adjust resource limits
kubectl apply -f k8s/examples/patches/resource-limits.yaml
```

📖 **Documentation:** [k8s/README.md](k8s/README.md)

### Important Notes

**Secrets Management:**
- Secrets are NOT included in Git (security best practice)
- Create manually before deployment:
  ```bash
  kubectl create secret generic ldapguard-secrets \
    --from-literal=POSTGRES_PASSWORD="..." \
    --from-literal=SECRET_KEY="..." \
    --from-literal=ENCRYPTION_KEY="..." \
    --from-literal=DATABASE_URL="..." \
    -n ldapguard
  ```

**Storage Requirements:**
- PostgreSQL & Redis: ReadWriteOnce (RWO) - supported by most storage classes
- Backup volume (optional): ReadWriteMany (RWX) - requires NFS, CephFS, EFS, Azure Files, etc.

**Worker Replicas:**
- Keep worker replicas at 1 (APScheduler - multiple replicas would duplicate scheduled jobs)

**Default Credentials:**
- Username: `admin@ldapguard.local`
- Password: `changeme123!`
- ⚠️ **Change immediately after first login!**

### Monitoring in Kubernetes

**Prometheus Metrics:**
Metrics are exposed at `/metrics` on the API service (port 8000):

```yaml
# ServiceMonitor for Prometheus Operator
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ldapguard
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: ldapguard
      app.kubernetes.io/component: api
  endpoints:
    - port: api
      path: /metrics
```

## 🏥 High Availability

### Docker/Podman Deployments

1. **Database Replication**: Configure PostgreSQL streaming replication
2. **Redis Sentinel**: Enable Redis Sentinel for HA
3. **Load Balancing**: Use HAProxy or Nginx for API load balancing
4. **Backup Storage**: Use network-attached storage (NAS) or S3-compatible storage

### Kubernetes Deployments

1. **Horizontal Scaling**: Increase API and Web replicas
   ```yaml
   api:
     replicas: 3
   web:
     replicas: 3
   ```

2. **Resource Limits**: Configure appropriate limits for production
   ```yaml
   api:
     resources:
       limits:
         memory: "1Gi"
         cpu: "2000m"
   ```

3. **Storage**: Use persistent storage classes with replication
   - RWO for PostgreSQL/Redis (local-ssd, gp3, etc.)
   - RWX for backup volume (NFS, CephFS, EFS)

4. **Ingress**: Enable HTTPS with Let's Encrypt
   ```yaml
   ingress:
     enabled: true
     domain: ldapguard.production.com
     certResolver: letsencrypt
   ```

5. **Monitoring**: Integrate with Prometheus/Grafana for observability

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