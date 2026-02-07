# ArgoCD Applications for Helm Deployment

This directory contains example ArgoCD Application manifests for deploying LDAPGuard using Helm.

## Prerequisites

1. **Create namespace and secrets first:**

```bash
kubectl create namespace ldapguard

kubectl create secret generic ldapguard-secrets \
  --from-literal=POSTGRES_PASSWORD="$(openssl rand -base64 24)" \
  --from-literal=SECRET_KEY="$(openssl rand -base64 32)" \
  --from-literal=ENCRYPTION_KEY="$(openssl rand -base64 32)" \
  --from-literal=DATABASE_URL="postgresql+asyncpg://ldapguard:REPLACE_PASSWORD@postgres:5432/ldapguard" \
  -n ldapguard
```

Replace `REPLACE_PASSWORD` with the actual PostgreSQL password from above.

## Example 1: Basic Deployment

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ldapguard
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/keundokki/LDAPGuard.git
    targetRevision: main
    path: helm
    helm:
      values: |
        # Use default values
  destination:
    server: https://kubernetes.default.svc
    namespace: ldapguard
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=false  # Create namespace manually (for secrets)
```

## Example 2: With Custom Image Version

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ldapguard
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/keundokki/LDAPGuard.git
    targetRevision: main
    path: helm
    helm:
      parameters:
        - name: images.api.tag
          value: "0.0.8"
        - name: images.worker.tag
          value: "0.0.8"
        - name: images.web.tag
          value: "0.0.8"
  destination:
    server: https://kubernetes.default.svc
    namespace: ldapguard
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## Example 3: With Ingress Enabled

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ldapguard
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/keundokki/LDAPGuard.git
    targetRevision: main
    path: helm
    helm:
      parameters:
        - name: ingress.enabled
          value: "true"
        - name: ingress.domain
          value: "ldapguard.yourdomain.com"
        - name: ingress.certResolver
          value: "letsencrypt"
  destination:
    server: https://kubernetes.default.svc
    namespace: ldapguard
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## Example 4: Production Configuration

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ldapguard
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/keundokki/LDAPGuard.git
    targetRevision: main
    path: helm
    helm:
      parameters:
        # Replicas
        - name: api.replicas
          value: "3"
        - name: web.replicas
          value: "3"
        
        # Storage
        - name: postgres.storage.size
          value: "20Gi"
        - name: postgres.storage.storageClassName
          value: "fast-ssd"
        
        # Backup volume (requires RWX storage)
        - name: backup.enabled
          value: "true"
        - name: backup.storage.size
          value: "100Gi"
        - name: backup.storage.storageClassName
          value: "nfs-client"
        
        # Ingress
        - name: ingress.enabled
          value: "true"
        - name: ingress.domain
          value: "ldapguard.production.com"
        
        # Configuration
        - name: config.backupRetentionDays
          value: "60"
        - name: config.prometheusEnabled
          value: "true"
        
        # Resources
        - name: api.resources.limits.memory
          value: "1Gi"
        - name: api.resources.limits.cpu
          value: "2000m"
  destination:
    server: https://kubernetes.default.svc
    namespace: ldapguard
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=false
```

## Available Helm Parameters

See [helm/README.md](../README.md) for complete list of available parameters.

### Most Common Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `images.api.tag` | `0.0.7` | API image version |
| `images.worker.tag` | `0.0.7` | Worker image version |
| `images.web.tag` | `0.0.7` | Web image version |
| `api.replicas` | `2` | Number of API pods |
| `web.replicas` | `2` | Number of Web pods |
| `postgres.storage.size` | `10Gi` | PostgreSQL storage |
| `redis.storage.size` | `1Gi` | Redis storage |
| `backup.enabled` | `false` | Enable backup volume |
| `backup.storage.size` | `50Gi` | Backup storage size |
| `ingress.enabled` | `false` | Enable Traefik ingress |
| `ingress.domain` | `ldapguard.example.com` | Your domain |
| `config.debug` | `false` | Debug mode |
| `config.backupRetentionDays` | `30` | Backup retention |

## Deployment Methods

### Via ArgoCD Web UI

**Recommended for simplicity:**

1. Login to ArgoCD UI
2. Click "New App"
3. Fill in fields:
   - App Name: `ldapguard`
   - Project: `default`
   - Sync Policy: `Automatic`
   - Repository URL: `https://github.com/keundokki/LDAPGuard.git`
   - Revision: `main`
   - Path: `helm`
   - Cluster URL: `https://kubernetes.default.svc`
   - Namespace: `ldapguard`
4. Under "Helm" section, add parameters as needed
5. Click "Create"

### Via kubectl

```bash
# Choose an example above and save to argocd-app.yaml
kubectl apply -f argocd-app.yaml
```

## Troubleshooting

### Application shows "OutOfSync"

This is normal if you haven't created secrets yet. Create secrets first:

```bash
kubectl create secret generic ldapguard-secrets ... -n ldapguard
```

Then sync the application in ArgoCD UI.

### Pods CrashLoopBackOff

Check logs:

```bash
kubectl logs -l app.kubernetes.io/component=api -n ldapguard
```

Common issues:
- Missing secrets
- Incorrect DATABASE_URL in secret
- Storage issues (PVC pending)

### Compare with Kustomize

If you prefer YAML patches over Helm parameters, see `k8s/examples/` for Kustomize-based ArgoCD Applications.

## Support

See [helm/README.md](../README.md) for complete documentation.
