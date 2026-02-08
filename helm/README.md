# LDAPGuard Helm Chart

A Helm chart for deploying LDAPGuard - LDAP backup and restore system - on Kubernetes.

## Prerequisites

- Kubernetes 1.25+
- Helm 3.0+
- kubectl configured to communicate with your cluster

## Quick Start

### 1. Create Secrets

**Option A: Manual Secret Creation (Recommended for Production)**

Create secrets manually before deployment:

```bash
kubectl create namespace ldapguard

kubectl create secret generic ldapguard-secrets \
  --from-literal=POSTGRES_PASSWORD="$(openssl rand -base64 24)" \
  --from-literal=SECRET_KEY="$(openssl rand -base64 32)" \
  --from-literal=ENCRYPTION_KEY="$(openssl rand -base64 32)" \
  --from-literal=DATABASE_URL="postgresql+asyncpg://ldapguard:REPLACE_WITH_POSTGRES_PASSWORD@postgres:5432/ldapguard" \
  -n ldapguard
```

**Important:** Replace `REPLACE_WITH_POSTGRES_PASSWORD` in the DATABASE_URL with the actual password shown from the first command.

**Option B: Using values.yaml (Development/Testing Only)**

⚠️ **NOT RECOMMENDED for production** - secrets will be stored in values.yaml/Git

Edit `helm/values.yaml`:

```yaml
secrets:
  create: true  # Enable Helm to create the secret
  values:
    POSTGRES_PASSWORD: "your-postgres-password"
    SECRET_KEY: "your-secret-key-min-32-chars"
    ENCRYPTION_KEY: "your-encryption-key-min-32-chars"
    DATABASE_URL: "postgresql+asyncpg://ldapguard:your-postgres-password@postgres:5432/ldapguard"
```

Or pass via command line:

```bash
helm install ldapguard ./helm -n ldapguard \
  --set secrets.create=true \
  --set secrets.values.POSTGRES_PASSWORD="$(openssl rand -base64 24)" \
  --set secrets.values.SECRET_KEY="$(openssl rand -base64 32)" \
  --set secrets.values.ENCRYPTION_KEY="$(openssl rand -base64 32)" \
  --set secrets.values.DATABASE_URL="postgresql+asyncpg://ldapguard:PASSWORD@postgres:5432/ldapguard"
```

### 2. Deploy with kubectl

```bash
# Install the chart
helm install ldapguard ./helm -n ldapguard

# Upgrade the chart
helm upgrade ldapguard ./helm -n ldapguard

# Uninstall
helm uninstall ldapguard -n ldapguard
```

### 3. Deploy with ArgoCD (Web GUI)

1. **Login to ArgoCD UI**
2. **Click "New App"**
3. **Fill in the following:**

   **General:**
   - Application Name: `ldapguard`
   - Project: `default`
   - Sync Policy: `Automatic` (optional)

   **Source:**
   - Repository URL: `https://github.com/keundokki/LDAPGuard.git`
   - Revision: `main` (or your preferred branch/tag)
   - Path: `helm`

   **Destination:**
   - Cluster URL: `https://kubernetes.default.svc`
   - Namespace: `ldapguard`

   **Helm:**
   - Values Files: `values.yaml`
   - Parameters: (customize as needed - see below)

4. **Click "Create"**
5. **Click "Sync"** to deploy

## Customization via ArgoCD GUI

In the ArgoCD Web UI, you can customize the deployment using **Helm Parameters** without modifying any files:

### Common Customizations

| Parameter | Default | Description |
|-----------|---------|-------------|
| `images.api.tag` | `0.0.7` | API container image tag |
| `images.worker.tag` | `0.0.7` | Worker container image tag |
| `images.web.tag` | `0.0.7` | Web container image tag |
| `api.replicas` | `2` | Number of API pods |
| `web.replicas` | `2` | Number of web pods |
| `postgres.storage.size` | `10Gi` | PostgreSQL storage size |
| `redis.storage.size` | `1Gi` | Redis storage size |
| `config.debug` | `false` | Enable debug mode |
| `config.backupRetentionDays` | `30` | Backup retention period |
| `backup.enabled` | `false` | Enable backup volume (requires RWX storage) |
| `backup.storage.size` | `50Gi` | Backup storage size |
| `ingress.enabled` | `false` | Enable Traefik ingress |
| `ingress.domain` | `ldapguard.example.com` | Your domain name |
| `ingress.certResolver` | `letsencrypt` | TLS certificate resolver |

### Example: Enable Ingress

In ArgoCD Web UI under "Helm" section, add parameters:

```
ingress.enabled = true
ingress.domain = ldapguard.yourdomain.com
```

### Example: Enable Backup Volume

```
backup.enabled = true
backup.storage.size = 100Gi
backup.storage.storageClassName = nfs-client
```

### Example: Increase Resources

```
api.replicas = 3
postgres.storage.size = 20Gi
```

## Customization via values.yaml

For advanced customization, create a custom values file:

```bash
# Copy default values
cp helm/values.yaml my-values.yaml

# Edit your values
vim my-values.yaml

# Deploy with custom values
helm install ldapguard ./helm -f my-values.yaml -n ldapguard
```

### Example Custom Values

```yaml
# my-values.yaml
images:
  api:
    tag: "0.0.8"

api:
  replicas: 3
  resources:
    limits:
      memory: "1Gi"
      cpu: "2000m"

postgres:
  storage:
    size: "20Gi"
    storageClassName: "standard"

ingress:
  enabled: true
  domain: "ldapguard.mycompany.com"
  tls:
    certResolver: "letsencrypt"  # or "cloudflare" for Cloudflare DNS
    # Or use Cloudflare Origin Certificate:
    # secretName: "cloudflare-origin-cert"
    # certResolver: ""

backup:
  enabled: true
  storage:
    size: "100Gi"
    storageClassName: "nfs-client"
```

## Configuration Reference

### Images

All container images can be customized:

```yaml
images:
  api:
    repository: ghcr.io/keundokki/ldapguard-api
    tag: "0.0.7"
    pullPolicy: IfNotPresent
  worker:
    repository: ghcr.io/keundokki/ldapguard-worker
    tag: "0.0.7"
  web:
    repository: ghcr.io/keundokki/ldapguard-web
    tag: "0.0.7"
  postgres:
    repository: postgres
    tag: "16-alpine"
  redis:
    repository: redis
    tag: "7-alpine"
```

### Replica Counts

```yaml
api:
  replicas: 2

worker:
  replicas: 1  # Keep at 1 to avoid duplicate scheduled jobs

web:
  replicas: 2

postgres:
  replicas: 1  # StatefulSet - do not increase

redis:
  replicas: 1  # StatefulSet - do not increase
```

### Resource Limits

```yaml
api:
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "1000m"
```

### Storage

```yaml
postgres:
  storage:
    size: "10Gi"
    accessMode: ReadWriteOnce
    # Optional: specify storage class
    # storageClassName: "standard"

redis:
  storage:
    size: "1Gi"
    accessMode: ReadWriteOnce

backup:
  enabled: false  # Requires ReadWriteMany storage
  storage:
    size: "50Gi"
    accessMode: ReadWriteMany
    # storageClassName: "nfs-client"  # Must support RWX
```

### Application Configuration

```yaml
config:
  debug: "false"
  backupRetentionDays: "30"
  incrementalBackupEnabled: "true"
  prometheusEnabled: "true"
  prometheusPort: "9090"
  accessTokenExpireMinutes: "30"
  webhookEnabled: "false"
```

### Ingress (Traefik)

```yaml
ingress:
  enabled: false
  domain: ldapguard.example.com
  
  tls:
    # Option 1: Use ACME cert resolver (Let's Encrypt or Cloudflare DNS)
    certResolver: letsencrypt  # or 'cloudflare'
    
    # Option 2: Use existing TLS secret (Cloudflare Origin Certificate)
    secretName: ""  # e.g., "cloudflare-origin-cert"
    
    # Optional: Additional domains (SANs)
    # domains:
    #   - main: ldapguard.example.com
    #     sans:
    #       - "*.example.com"
  
  annotations: {}
```

**Cloudflare SSL/TLS:**

For detailed Cloudflare configuration (DNS challenge, Origin Certificates), see:
📘 **[Cloudflare SSL Configuration Guide](../docs/CLOUDFLARE_SSL.md)**

Quick examples:

**Cloudflare DNS + Let's Encrypt:**
```yaml
ingress:
  enabled: true
  domain: ldapguard.yourdomain.com
  tls:
    certResolver: cloudflare  # Requires Traefik configured with Cloudflare DNS
```

**Cloudflare Origin Certificate:**
```bash
# Create secret first
kubectl create secret tls cloudflare-origin-cert \
  --cert=origin-cert.pem --key=origin-key.pem -n ldapguard

# Then deploy
helm install ldapguard ./helm \
  --set ingress.enabled=true \
  --set ingress.tls.secretName=cloudflare-origin-cert \
  --set ingress.tls.certResolver=""
```

### Network Policy

```yaml
networkPolicy:
  enabled: true
```

## Important Notes

### Secrets Management

**Two options for managing secrets:**

**Option 1: Manual Creation (Recommended for Production)**

Create secrets manually using kubectl before deployment:

1. **Never commit secrets to Git**
2. **Create secrets using kubectl** (see Quick Start above)
3. **Secret name must be:** `ldapguard-secrets`
4. **Required secret keys:**
   - `POSTGRES_PASSWORD` - PostgreSQL password
   - `SECRET_KEY` - JWT token signing key (min 32 chars)
   - `ENCRYPTION_KEY` - LDAP password encryption key (min 32 chars)
   - `DATABASE_URL` - Full PostgreSQL connection string

**Option 2: Helm-Managed Secrets (Development/Testing Only)**

⚠️ **NOT RECOMMENDED for production** - Enable Helm to create secrets from values:

```yaml
secrets:
  create: true
  values:
    POSTGRES_PASSWORD: "your-password"
    SECRET_KEY: "your-secret-key"
    ENCRYPTION_KEY: "your-encryption-key"
    DATABASE_URL: "postgresql+asyncpg://ldapguard:your-password@postgres:5432/ldapguard"
```

**Security Warning:** If you use Option 2, ensure:
- Values file is NOT committed to Git
- Use `.gitignore` or separate values file for secrets
- Consider using Sealed Secrets, External Secrets Operator, or similar for GitOps workflows

### Worker Replicas

**Keep `worker.replicas: 1`** - The worker uses APScheduler for scheduled backups. Multiple replicas would create duplicate scheduled jobs.

### Backup Volume

The backup volume requires **ReadWriteMany (RWX)** storage, which is not supported by all storage providers:

- ❌ **Not supported:** `local-path` (k3s default), AWS EBS, GCE PD
- ✅ **Supported:** NFS, CephFS, AWS EFS, Azure Files, GlusterFS

If you don't have RWX storage, leave `backup.enabled: false` (backups will be stored in API/worker pod storage).

### StatefulSet Replicas

**Do not increase replicas for PostgreSQL or Redis** - these are StatefulSets configured for single-instance deployment. Scaling requires additional configuration.

## Verification

After deployment, verify the installation:

```bash
# Check all pods are running
kubectl get pods -n ldapguard

# Expected output:
# NAME                      READY   STATUS    RESTARTS   AGE
# api-xxxxx                 1/1     Running   0          5m
# api-yyyyy                 1/1     Running   0          5m
# worker-zzzzz              1/1     Running   0          5m
# web-aaaaa                 1/1     Running   0          5m
# web-bbbbb                 1/1     Running   0          5m
# postgres-0                1/1     Running   0          5m
# redis-0                   1/1     Running   0          5m

# Check persistent volumes
kubectl get pvc -n ldapguard

# Check services
kubectl get svc -n ldapguard
```

### Access the Web UI

If ingress is disabled (default), use port-forwarding:

```bash
kubectl port-forward svc/web -n ldapguard 8080:80
```

Then access: http://localhost:8080

### Default Credentials

- **Username:** `admin@ldapguard.local`
- **Password:** `changeme123!`

**⚠️ IMPORTANT:** Change the default password immediately after first login!

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n ldapguard

# Check logs
kubectl logs <pod-name> -n ldapguard

# For API/Worker, check database connection
kubectl logs -l app.kubernetes.io/component=api -n ldapguard | grep -i database
```

### Database connection issues

Verify secrets are configured correctly:

```bash
# Check secret exists
kubectl get secret ldapguard-secrets -n ldapguard

# View secret keys (not values)
kubectl describe secret ldapguard-secrets -n ldapguard
```

### Storage issues

```bash
# Check PVC status
kubectl get pvc -n ldapguard

# If pending, check storage class
kubectl get storageclass

# Describe PVC for events
kubectl describe pvc <pvc-name> -n ldapguard
```

### Ingress not working

```bash
# Check IngressRoute exists (if ingress.enabled=true)
kubectl get ingressroute -n ldapguard

# Check middleware exists
kubectl get middleware -n ldapguard

# Verify Traefik is installed and running
kubectl get pods -n kube-system | grep traefik
```

## Upgrading

### Upgrade to new version

```bash
# Update values.yaml with new image tags
images:
  api:
    tag: "0.0.8"  # New version
  worker:
    tag: "0.0.8"
  web:
    tag: "0.0.8"

# Apply upgrade
helm upgrade ldapguard ./helm -n ldapguard
```

### With ArgoCD

Simply update the `Revision` field in the ArgoCD Web UI or update the image tags via Helm Parameters.

## Uninstallation

```bash
# With Helm
helm uninstall ldapguard -n ldapguard

# Delete namespace (this will remove PVCs and data!)
kubectl delete namespace ldapguard

# Or keep data by only deleting the release
helm uninstall ldapguard -n ldapguard
# Then manually delete PVCs if needed
kubectl delete pvc --all -n ldapguard
```

## Comparison with Kustomize

This repository provides **two deployment methods:**

| Feature | Helm | Kustomize |
|---------|------|-----------|
| **Location** | `helm/` directory | `k8s/` directory |
| **Customization** | Key-value parameters | YAML patches |
| **ArgoCD GUI** | ✅ Easy parameter input | ❌ Requires patch files |
| **Learning Curve** | Lower (key=value) | Higher (YAML knowledge) |
| **Flexibility** | High (100+ parameters) | Very high (any YAML field) |
| **Best For** | Simple customizations | Complex customizations |

**Recommendation:** Use Helm for most deployments. Use Kustomize if you need deep customization beyond what Helm values provide.

## Support

- **Repository:** https://github.com/keundokki/LDAPGuard
- **Documentation:** See main README.md in repository root
- **Issues:** Report bugs via GitHub Issues

## License

See LICENSE file in repository root.
