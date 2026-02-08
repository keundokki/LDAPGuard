# LDAPGuard — Kubernetes Deployment

Production-ready Kubernetes manifests for deploying LDAPGuard using Kustomize and ArgoCD.

## 🚀 Quick Start

### Prerequisites

- Kubernetes cluster (1.25+)
- `kubectl` configured for your cluster
- (Optional) ArgoCD installed
- (Optional) Traefik ingress controller for external access

### Deploy in 2 Steps

**1. Create secrets:**
```bash
POSTGRES_PASSWORD="$(openssl rand -hex 16)"
DATABASE_URL="postgresql+asyncpg://ldapguard:${POSTGRES_PASSWORD}@postgres:5432/ldapguard"

kubectl create secret generic ldapguard-secrets \
  --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  --from-literal=SECRET_KEY="$(openssl rand -base64 32)" \
  --from-literal=ENCRYPTION_KEY="$(openssl rand -base64 32)" \
  --from-literal=DATABASE_URL="$DATABASE_URL" \
  -n ldapguard --create-namespace
```

**2. Deploy with kubectl or ArgoCD:**

**Option A - kubectl:**
```bash
kubectl apply -k https://github.com/keundokki/LDAPGuard/k8s
```

**Option B - ArgoCD:**
```bash
kubectl apply -f https://raw.githubusercontent.com/keundokki/LDAPGuard/main/k8s/examples/argocd-basic.yaml
```

That's it! LDAPGuard is now running in your cluster.

## 📁 Directory Structure

```
k8s/
├── kustomization.yaml          # Main Kustomize configuration
├── namespace.yaml              # Namespace definition
│
├── deployments/                # Application deployments
│   ├── api-deployment.yaml
│   ├── worker-deployment.yaml
│   └── web-deployment.yaml
│
├── statefulsets/               # Stateful services
│   ├── postgres-statefulset.yaml
│   └── redis-statefulset.yaml
│
├── services/                   # Kubernetes services
│   ├── api-service.yaml
│   ├── web-service.yaml
│   ├── postgres-service.yaml
│   └── redis-service.yaml
│
├── storage/                    # Persistent volume claims
│   ├── pvc-postgres.yaml       # PostgreSQL data (RWO)
│   ├── pvc-redis.yaml          # Redis data (RWO)
│   └── pvc-backup.yaml         # Backup data (RWX - see notes)
│
├── config/                     # Configuration
│   ├── configmap-app.yaml      # Application config
│   └── configmap-nginx.yaml    # Nginx config
│
├── network/                    # Networking policies
│   ├── middleware.yaml         # Traefik middleware
│   └── networkpolicy.yaml      # Network policies
│
└── examples/                   # Deployment examples & patches
    ├── README.md               # Detailed examples documentation
    ├── argocd-basic.yaml       # Basic ArgoCD app
    ├── argocd-with-versions.yaml  # With version pinning
    ├── argocd-full.yaml        # Full customization
    └── patches/
        ├── ingress.yaml            # Add Traefik ingress
        ├── resource-limits.yaml    # Add resource limits
        └── enable-backup-volume.yaml  # Enable RWX backup
```

## 🎯 Deployment Options

### kubectl (Direct Deployment)

```bash
# 1. Create secrets
POSTGRES_PASSWORD="$(openssl rand -hex 16)"
DATABASE_URL="postgresql+asyncpg://ldapguard:${POSTGRES_PASSWORD}@postgres:5432/ldapguard"

kubectl create secret generic ldapguard-secrets \
  --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  --from-literal=SECRET_KEY="$(openssl rand -base64 32)" \
  --from-literal=ENCRYPTION_KEY="$(openssl rand -base64 32)" \
  --from-literal=DATABASE_URL="$DATABASE_URL" \
  -n ldapguard --create-namespace

# 2. Deploy
kubectl apply -k https://github.com/keundokki/LDAPGuard/k8s
```

### ArgoCD (GitOps)

See detailed examples in [`examples/README.md`](examples/README.md)

**Quick Deploy:**
```bash
kubectl apply -f https://raw.githubusercontent.com/keundokki/LDAPGuard/main/k8s/examples/argocd-basic.yaml
```

## 🔧 Customization

All customization is done via **Kustomize patches** - no need to fork or modify the repo!

### Add Ingress (External Access)

**Option 1 - Use patch file:**
```yaml
# In your ArgoCD Application
spec:
  source:
    kustomize:
      patches:
        - path: examples/patches/ingress.yaml
```

Then edit `examples/patches/ingress.yaml` to set your domain.

**Option 2 - Inline patch:**
```yaml
spec:
  source:
    kustomize:
      patches:
        - target:
            kind: IngressRoute
            name: ldapguard-https
          patch: |-
            - op: replace
              path: /spec/routes/0/match
              value: Host(`your-domain.com`)
```

### Add Resource Limits

```yaml
spec:
  source:
    kustomize:
      patches:
        - path: examples/patches/resource-limits.yaml
```

### Pin Image Versions

```yaml
spec:
  source:
    kustomize:
      images:
        - name: ghcr.io/keundokki/ldapguard-api
          newTag: "0.0.7"
        - name: ghcr.io/keundokki/ldapguard-worker
          newTag: "0.0.7"
        - name: ghcr.io/keundokki/ldapguard-web
          newTag: "0.0.7"
```

### Enable Backup Volume (RWX Storage)

**If you have ReadWriteMany storage** (NFS, CephFS, etc.):

**Option 1 - Uncomment in kustomization.yaml:**
```yaml
# Edit kustomization.yaml
resources:
  - storage/pvc-backup.yaml  # Uncomment this line
```

**Option 2 - Use patch:**
```yaml
spec:
  source:
    kustomize:
      patches:
        - path: examples/patches/enable-backup-volume.yaml
```

## 🏗️ Architecture

```
                    ┌─────────┐
                    │ Traefik │  (HTTPS termination - optional)
                    └────┬────┘
                         │ :80
                    ┌────▼────┐
                    │   Web   │  (Nginx — static files + reverse proxy)
                    │ 2 repl. │
                    └────┬────┘
                         │ /api/ → :8000
                    ┌────▼────┐
                    │   API   │  (FastAPI — business logic)
                    │ 2 repl. │
                    └──┬───┬──┘
                       │   │
              ┌────────┘   └────────┐
              ▼                     ▼
        ┌──────────┐         ┌──────────┐
        │ Postgres │         │  Redis   │
        │  (data)  │         │ (queue)  │
        └──────────┘         └──────────┘
              ▲                     ▲
              │                     │
           ┌──┴─────────────────────┴──┐
           │         Worker            │
           │  (scheduled tasks, 1 rep) │
           └───────────────────────────┘
```

## ✅ Verification

```bash
# Check all pods are running
kubectl get pods -n ldapguard

# Check services
kubectl get svc -n ldapguard

# Check PVCs
kubectl get pvc -n ldapguard

# View API logs (should show database migrations)
kubectl logs -n ldapguard deployment/api

# Test internal access
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- curl http://web.ldapguard/health

# If ingress is configured, test external access
curl https://your-domain.com/health
```

## 📝 Important Notes

### Storage

- **PostgreSQL & Redis**: Use ReadWriteOnce (RWO) storage - works with any StorageClass
- **Backup volume**: Requires ReadWriteMany (RWX) storage - commented out by default
  - Enable only if you have NFS, CephFS, EFS, Azure Files, etc.
  - See `examples/patches/enable-backup-volume.yaml`

### Replicas

- **API & Web**: Can scale horizontally (2 replicas by default)
- **Worker**: Keep at 1 replica (APScheduler - multiple replicas would duplicate jobs)
- **Postgres & Redis**: StatefulSets with 1 replica (scale carefully)

### Database Migrations

- API runs `alembic upgrade head` on startup
- Safe with multiple API replicas (Alembic uses PostgreSQL advisory locks)

### Secrets Management

This repo intentionally keeps secrets out of Git for security. Options:
1. **Manual creation** (recommended for quick start)
2. **Sealed Secrets** (for GitOps)
3. **External Secrets Operator** (for vault integration)
4. **ArgoCD Vault Plugin**

### Network Policies

Default NetworkPolicy allows:
- API ↔ PostgreSQL, Redis
- Worker ↔ PostgreSQL, Redis
- Web ↔ API
- External → Web (if ingress configured)

Adjust `network/networkpolicy.yaml` for stricter policies.

## 🛠️ Troubleshooting

If you see `password authentication failed`, the password in `POSTGRES_PASSWORD` does not match the one in `DATABASE_URL`. See the Recovery section below.

### Pods Pending (Storage Issues)

```bash
kubectl describe pvc -n ldapguard
```

**Solution**: Check your StorageClass supports the requested access mode (RWO/RWX)

### Database Connection Errors

Check secret exists and has correct values:
```bash
kubectl get secret ldapguard-secrets -n ldapguard -o yaml
```

If you see `password authentication failed`:

1. Ensure `POSTGRES_PASSWORD` matches the password in `DATABASE_URL`.
2. Use URL-safe passwords (hex) or URL-encode base64 passwords.
3. For a full reset (data loss), reinitialize PostgreSQL with the current secret:
  ```bash
  kubectl scale deployment api worker -n ldapguard --replicas=0
  kubectl delete statefulset postgres -n ldapguard
  kubectl delete pvc postgres-data -n ldapguard
  kubectl apply -k k8s/ -n ldapguard
  kubectl scale deployment api worker -n ldapguard --replicas=2
  ```

## 🧰 Recovery

### Full reset (data loss)

Use this when the database password is out of sync or you want a clean install:

```bash
kubectl scale deployment api worker -n ldapguard --replicas=0
kubectl delete statefulset postgres -n ldapguard
kubectl delete pvc postgres-data -n ldapguard
kubectl apply -k k8s/ -n ldapguard
kubectl scale deployment api worker -n ldapguard --replicas=2
```

### Prevention

- Always reuse the same password in `POSTGRES_PASSWORD` and `DATABASE_URL`.
- Prefer URL-safe passwords (hex) or URL-encode base64 passwords.

### Image Pull Errors

Images are from `ghcr.io/keundokki/ldapguard-*`. If private:
```bash
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=USERNAME \
  --docker-password=TOKEN \
  -n ldapguard
```

Then patch deployments to use `imagePullSecrets`.

## 📚 Additional Resources

- [ArgoCD Examples](examples/README.md) - Detailed deployment examples
- [Kustomize Patches](examples/patches/) - Ready-to-use customization patches
- [Main Documentation](../README.md) - LDAPGuard features and API docs

## 🤝 Contributing

Found an issue or have a suggestion? Open an issue or PR on the [GitHub repository](https://github.com/keundokki/LDAPGuard).
