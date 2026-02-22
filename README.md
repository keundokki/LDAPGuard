# LDAPGuard

[![CI/CD Pipeline](https://github.com/keundokki/LDAPGuard/actions/workflows/ci-cd.yml/badge.svg?branch=main)](https://github.com/keundokki/LDAPGuard/actions/workflows/ci-cd.yml)
[![Security Checks](https://github.com/keundokki/LDAPGuard/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/keundokki/LDAPGuard/actions/workflows/security.yml)
[![Code Quality](https://github.com/keundokki/LDAPGuard/actions/workflows/linting.yml/badge.svg?branch=main)](https://github.com/keundokki/LDAPGuard/actions/workflows/linting.yml)

**Multi-container Podman application for centralized LDAP backup/restore on Linux NAS**

## 🚀 **[New to LDAPGuard? Start Here →](GETTING_STARTED.md)**

---

## 🎯 Try It in 30 Seconds

Want to see LDAPGuard in action before installing?

```bash
# Quick demo with Docker (testing only, no persistence)
docker run -d -p 3000:3000 -p 8000:8000 ghcr.io/keundokki/ldapguard:latest
```

Then open http://localhost:3000 (login: `demo`/`demo`)

> ⚠️ **Note**: This demo mode stores data in memory only. Use the installation methods below for real deployments.

---

## ⚡ Installation Simplified

We've simplified installation from a **complex, error-prone process** to a **single command**:

### Before vs. After

```
❌ BEFORE (10-20 minutes, 12 manual steps)
┌─────────────────────────────────────────────┐
│ 1. Clone repository                         │
│ 2. Copy .env.example → .env                │
│ 3. Manually edit 8+ configuration fields   │
│ 4. Generate SECRET_KEY with openssl        │
│ 5. Generate ENCRYPTION_KEY                 │
│ 6. Generate database password              │
│ 7. Update .env with generated keys         │
│ 8. Create backup directories               │
│ 9. Run docker-compose up -d                │
│ 10. Hope everything works                  │
│ 11. Search docs for default credentials    │
│ 12. Figure out where to access UI          │
└─────────────────────────────────────────────┘

✅ NOW (2-3 minutes, 1 command)
┌─────────────────────────────────────────────┐
│ curl -fsSL ...install.sh | bash            │
│    ↓                                        │
│ Everything automated!                      │
│ • System checks ✓                          │
│ • Secure key generation ✓                 │
│ • Configuration ✓                          │
│ • Deployment ✓                             │
│ • Health validation ✓                      │
│ • Clear next steps ✓                       │
└─────────────────────────────────────────────┘
```

### Installation Methods Comparison

| Method | Time | Difficulty | Best For |
|--------|------|-----------|----------|
| **One-line installer** | 2-3 min | ⭐ Easy | Everyone (recommended) |
| **Make install** | 3-4 min | ⭐⭐ Medium | Developers |
| **Manual Docker** | 5-10 min | ⭐⭐⭐ Advanced | Power users |
| **Kubernetes Helm** | 10-15 min | ⭐⭐⭐ Advanced | Production clusters |

**Installation Decision Tree:**

```
Want to install LDAPGuard?
        │
        ▼
   Have Docker? ───NO──▶ Install Docker first
        │                (see INSTALL.md)
       YES                      │
        │                       │
        ▼                       ▼
  curl ...install.sh | bash ◀───┘
        │
        ▼
  Quick or Custom mode?
        │
        ▼
  Auto-configure & start
        │
        ▼
  Open http://localhost:3000
        │
        ▼
  Login: admin/admin
        │
        ▼
   ✅ SUCCESS! ✅
```

**Key Improvements:**
- ⏱️ **83% faster** - 10-20 min → 2-3 min
- 🎯 **92% fewer steps** - 12 steps → 1 command
- ✅ **Near-zero errors** - Automatic validation
- 📚 **Better docs** - 4 focused guides

---

## 🚀 Features

- **Multi-Service Architecture**: Web UI, API, Workers, PostgreSQL, Redis, Logging
- **Advanced Backup Capabilities**:
  - Incremental backups
  - Point-in-time recovery
  - Selective restore with LDAP filters
  - AES-256 encryption
  - Compression support
  - **🔄 Automatic retry with exponential backoff** - [Retry Logic Guide](docs/BACKUP_RETRY_LOGIC.md)
- **Security**:
  - LDAP authentication integration
  - Role-Based Access Control (RBAC)
  - Encrypted backup storage
- **Monitoring & Integration**:
  - **📧 Email notifications** (Gmail, SendGrid, Office 365, AWS SES, etc.) - [Setup Guide](docs/EMAIL_NOTIFICATIONS.md)
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

> 🆕 **New to installation?** See our detailed [Installation Guide](INSTALL.md)

### Kubernetes Deployment
- Kubernetes 1.25+ cluster
- kubectl configured
- ArgoCD (recommended) or Helm 3.0+

---

## 🚀 Quick Start

### ⚡ One-Line Install (Recommended)

The fastest way to get started:

```bash
curl -fsSL https://raw.githubusercontent.com/keundokki/LDAPGuard/main/install.sh | bash
```

This interactive installer will:
- ✅ Check system prerequisites
- ✅ Generate secure encryption keys
- ✅ Configure all services
- ✅ Start LDAPGuard automatically
- ✅ Show you exactly where to go next

**Access after install:**
- Web UI: http://localhost:3000
- Default login: `admin` / `admin` (change immediately!)

---

### 🛠️ Manual Installation

For more control over the installation:

#### Option 1: Using Makefile (Simplest)

```bash
git clone https://github.com/keundokki/LDAPGuard.git
cd LDAPGuard
make install
```

Common commands:
```bash
make start      # Start services
make stop       # Stop services
make logs       # View logs
make health     # Check health
make help       # See all commands
```

#### Option 2: Docker/Podman (Traditional)

#### Option 2: Docker/Podman (Traditional)

1. **Clone and configure**:
   ```bash
   git clone https://github.com/keundokki/LDAPGuard.git
   cd LDAPGuard
   cp .env.example .env
   nano .env  # Edit configuration
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   # Or: podman-compose up -d
   ```

3. **Access**: http://localhost:3000

---

### Option 3: Kubernetes (Production)

LDAPGuard supports two Kubernetes deployment methods:

#### 📦 **Helm (Recommended for most users)**

Simplest deployment with key-value customization:

```bash
# 1. Create namespace and secrets
kubectl create namespace ldapguard

# Use a URL-safe password (hex) and reuse it in DATABASE_URL
POSTGRES_PASSWORD="$(openssl rand -hex 16)"
DATABASE_URL="postgresql+asyncpg://ldapguard:${POSTGRES_PASSWORD}@postgres:5432/ldapguard"

kubectl create secret generic ldapguard-secrets \
  --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  --from-literal=SECRET_KEY="$(openssl rand -base64 32)" \
  --from-literal=ENCRYPTION_KEY="$(openssl rand -base64 32)" \
  --from-literal=DATABASE_URL="$DATABASE_URL" \
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

---

## 🔄 Updating an Existing Installation

### Docker/Podman Updates

#### Automated Update (Recommended)

Update to the latest or specific version:

```bash
# Update to latest version
./update.sh

# Update to specific version
./update.sh --version 1.0.1

# Update without database backup (faster, less safe)
./update.sh --version 1.0.1 --skip-backup
```

**What the update script does:**
1. ✅ Creates automatic database backup (unless --skip-backup)
2. ✅ Pulls Docker images for specified version
3. ✅ Updates IMAGE_TAG in .env file
4. ✅ Stops services gracefully  
5. ✅ Runs database migrations
6. ✅ Restarts services with new version
7. ✅ Validates health before completing

**Using Makefile:**
```bash
make update         # Run update script (latest)
make version        # Check current version
make check-updates  # See if updates available
```

#### Version Selection

LDAPGuard images are tagged with each release:

```bash
# Available tags:
ghcr.io/keundokki/ldapguard-api:latest    # Latest stable release
ghcr.io/keundokki/ldapguard-api:1.0.1     # Specific version
ghcr.io/keundokki/ldapguard-api:sha-abc   # Specific commit
```

To manually select a version, edit `.env`:

```bash
IMAGE_TAG=1.0.1  # Pin to specific version
# or
IMAGE_TAG=latest  # Always use latest
```

Then:

```bash
docker-compose pull
docker-compose up -d
```

#### Manual Update

If you prefer manual control:

```bash
# 1. Backup database
make db-backup

# 2. Pull specific version
export IMAGE_TAG=1.0.1
docker-compose pull

# 3. Restart services
docker-compose down
docker-compose up -d

# 4. Run migrations
docker-compose exec api alembic upgrade head
```

---

### Kubernetes Updates

#### Automated K8s Update

Use the dedicated Kubernetes update script:

```bash
# Update to specific version (auto-detects method)
./update-k8s.sh --version 1.0.1

# Specify namespace
./update-k8s.sh --version 1.0.1 --namespace production

# Force specific method
./update-k8s.sh --version 1.0.1 --method kustomize
./update-k8s.sh --version 1.0.1 --method argocd
```

**What the K8s update script does:**
1. ✅ Auto-detects update method (Kustomize or ArgoCD)
2. ✅ Creates database backup from PostgreSQL pod
3. ✅ Updates image tags to specified version
4. ✅ Applies changes via kubectl or ArgoCD
5. ✅ Waits for rollout completion
6. ✅ Verifies pod health

#### Manual Kustomize Update

```bash
# Create temporary overlay for version
cat > /tmp/kustomization.yaml <<EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: ldapguard

resources:
  - ../../k8s

images:
  - name: ghcr.io/keundokki/ldapguard-api
    newTag: "1.0.1"
  - name: ghcr.io/keundokki/ldapguard-worker
    newTag: "1.0.1"
  - name: ghcr.io/keundokki/ldapguard-web
    newTag: "1.0.1"
EOF

# Apply
kubectl apply -k /tmp
```

#### ArgoCD Update

If using ArgoCD, update the Application spec:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ldapguard
spec:
  source:
    kustomize:
      images:
        - ghcr.io/keundokki/ldapguard-api:1.0.1
        - ghcr.io/keundokki/ldapguard-worker:1.0.1
        - ghcr.io/keundokki/ldapguard-web:1.0.1
```

Or use the CLI:

```bash
argocd app patch ldapguard --type merge -p '{
  "spec": {
    "source": {
      "kustomize": {
        "images": [
          "ghcr.io/keundokki/ldapguard-api:1.0.1",
          "ghcr.io/keundokki/ldapguard-worker:1.0.1",
          "ghcr.io/keundokki/ldapguard-web:1.0.1"
        ]
      }
    }
  }
}'
argocd app sync ldapguard
```

---

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
- Create manually before deployment (use the same password in both fields):
  ```bash
  POSTGRES_PASSWORD="$(openssl rand -hex 16)"
  DATABASE_URL="postgresql+asyncpg://ldapguard:${POSTGRES_PASSWORD}@postgres:5432/ldapguard"

  kubectl create secret generic ldapguard-secrets \
    --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
    --from-literal=SECRET_KEY="$(openssl rand -base64 32)" \
    --from-literal=ENCRYPTION_KEY="$(openssl rand -base64 32)" \
    --from-literal=DATABASE_URL="$DATABASE_URL" \
    -n ldapguard
  ```
  - If you use a base64 password, URL-encode it before putting it in `DATABASE_URL`.

**Common Failure (Password Mismatch):**
- If API logs show `password authentication failed`, the password in `POSTGRES_PASSWORD` does not match the one in `DATABASE_URL`.
- See the Recovery section for the full reset procedure.

**Storage Requirements:**
- PostgreSQL & Redis: ReadWriteOnce (RWO) - supported by most storage classes
- Backup volume (optional): ReadWriteMany (RWX) - requires NFS, CephFS, EFS, Azure Files, etc.

**Worker Replicas:**
- Keep worker replicas at 1 (APScheduler - multiple replicas would duplicate scheduled jobs)

**Default Credentials:**
- Username: `admin@ldapguard.local`
- Password: `changeme123!`
- ⚠️ **Change immediately after first login!**

**SSL/TLS with Cloudflare:**
- Supports Let's Encrypt (ACME), Cloudflare Origin Certificates, and Cloudflare DNS challenge
- 📘 **Complete guide:** [docs/CLOUDFLARE_SSL.md](docs/CLOUDFLARE_SSL.md)
- Quick setup with Cloudflare DNS:
  ```yaml
  ingress:
    enabled: true
    domain: ldapguard.yourdomain.com
    tls:
      certResolver: cloudflare
  ```

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

## 🧰 Recovery (Kubernetes)

### Database password mismatch

If the API logs show `password authentication failed`, the PostgreSQL password stored in the database does not match the password in `ldapguard-secrets`.

**Fix (full reset, data loss):**
```bash
kubectl scale deployment api worker -n ldapguard --replicas=0
kubectl delete statefulset postgres -n ldapguard
kubectl delete pvc postgres-data -n ldapguard
kubectl apply -k k8s/ -n ldapguard
kubectl scale deployment api worker -n ldapguard --replicas=2
```

**Prevention:**
- Always reuse the same password in both `POSTGRES_PASSWORD` and `DATABASE_URL`.
- Prefer URL-safe passwords (hex) or URL-encode base64 passwords.

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

---

## 📚 Documentation & Resources

### Getting Started
- **[Getting Started Guide](GETTING_STARTED.md)** - 🆕 Zero to first backup in 10 minutes
- **[Installation Guide](INSTALL.md)** - Detailed step-by-step installation instructions
- **[Installation Summary](docs/INSTALLATION_SUMMARY.md)** - Visual overview of simplified installation
- **[Quick Reference](QUICK_REFERENCE.md)** - Command cheat sheet and quick tips
- **README.md** (this file) - Complete feature documentation

### Deployment Guides
- **[Deployment Procedure](docs/DEPLOYMENT_PROCEDURE.md)** - Production deployment workflow
- **[Kubernetes Guide](k8s/README.md)** - Kubernetes deployment with Kustomize
- **[Helm Guide](helm/README.md)** - Helm chart documentation

### Tools & Scripts
- **install.sh** - Interactive one-line installer
- **Makefile** - Common operations (make help)
- **scripts/setup.sh** - Quick setup script
- **scripts/validate.sh** - Configuration validator

### API & Monitoring
- **API Docs**: http://localhost:8000/docs (Swagger)
- **ReDoc**: http://localhost:8000/redoc (Alternative API docs)
- **Metrics**: http://localhost:8000/metrics (Prometheus)

---

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