# LDAPGuard — Kubernetes Deployment

Production-ready Kubernetes manifests using Kustomize base/overlays, compatible with ArgoCD and manual `kubectl` deployments.

## Directory Structure

```
k8s/
  base/                        # Shared, environment-agnostic resources
    kustomization.yaml
    ...deployments, services, configmaps, PVCs, networkpolicy...
  overlays/
    production/                # Production-specific: secrets, ingress, image pins
      kustomization.yaml       # References ../../base + secrets + ingress + patches
      secrets.example.yaml     # Template — copy to secrets.yaml
      ingressroute.example.yaml
      resource-limits.example.yaml
      storageclass.example.yaml
```

## Prerequisites

- Kubernetes cluster (1.25+)
- `kubectl` configured for your cluster
- Traefik ingress controller installed (with CRD support)
- Storage provisioner supporting `ReadWriteMany` for shared backup volume (NFS, CephFS, EFS, etc.)

## Quick Start (manual kubectl)

```bash
cd k8s/overlays/production/

# 1. Create secrets
cp secrets.example.yaml secrets.yaml
# Edit secrets.yaml — generate base64-encoded values:
#   echo -n 'your-password' | base64

# 2. Create ingress
cp ingressroute.example.yaml ingressroute.yaml
# Edit ingressroute.yaml — set your domain and certResolver

# 3. Create resource limits
cp resource-limits.example.yaml resource-limits.yaml

# 4. Deploy
kubectl apply -k .
```

## ArgoCD Deployment

Point your ArgoCD Application at the production overlay:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ldapguard
  namespace: argocd
spec:
  source:
    repoURL: https://github.com/keundokki/LDAPGuard
    path: k8s/overlays/production
    targetRevision: main
  destination:
    server: https://kubernetes.default.svc
    namespace: ldapguard
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

**Secrets handling with ArgoCD** (choose one):
- **SealedSecrets**: Encrypt `secrets.yaml` with `kubeseal`, commit the `SealedSecret` resource
- **External Secrets Operator**: Replace `secrets.yaml` with an `ExternalSecret` pointing to Vault/AWS SM
- **Manual**: Apply `secrets.yaml` with `kubectl` before ArgoCD syncs

## Files requiring customization (.example)

| File | What to change |
|------|---------------|
| `secrets.example.yaml` | POSTGRES_PASSWORD, SECRET_KEY, ENCRYPTION_KEY, DATABASE_URL |
| `ingressroute.example.yaml` | Domain name, TLS certResolver |
| `resource-limits.example.yaml` | CPU/memory requests and limits per service |
| `storageclass.example.yaml` | NFS/cloud provisioner (if default StorageClass doesn't support RWX) |

## Architecture

```
                    ┌─────────┐
                    │ Traefik │  (HTTPS termination)
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

## Verifying the Deployment

```bash
# Check all pods are running
kubectl get pods -n ldapguard

# Check API logs (should show alembic migrations)
kubectl logs -n ldapguard deployment/api

# Test health endpoint
curl https://<your-domain>/health

# Test API through nginx proxy
curl https://<your-domain>/api/auth/login

# Verify HTTP redirects to HTTPS
curl -I http://<your-domain>/
```

## Notes

- **Backup volume**: `pvc-backup.yaml` requires `ReadWriteMany` — most default StorageClasses only support `ReadWriteOnce`. Configure an NFS-backed StorageClass if needed (see `storageclass.example.yaml`).
- **Worker replicas**: Keep at 1. The worker runs APScheduler — multiple replicas would duplicate scheduled jobs.
- **Database migrations**: The API runs `alembic upgrade head` on startup. Concurrent migrations are safe (Alembic uses PostgreSQL advisory locks).
- **Service naming**: K8s Service names (`api`, `postgres`, `redis`) match docker-compose, so `nginx.conf` proxy rules work unchanged.
- **Image versions**: Pin image tags in `overlays/production/kustomization.yaml` via the `images:` block.
