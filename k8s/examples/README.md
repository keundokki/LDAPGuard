# LDAPGuard ArgoCD Examples

This directory contains example ArgoCD Application manifests and kustomize patches for deploying LDAPGuard.

## Quick Start

### 1. Create Secrets (Required)

Before deploying, create the secrets on your cluster:

```bash
kubectl create secret generic ldapguard-secrets \
  --from-literal=POSTGRES_PASSWORD="$(openssl rand -base64 24)" \
  --from-literal=SECRET_KEY="$(openssl rand -base64 32)" \
  --from-literal=ENCRYPTION_KEY="$(openssl rand -base64 32)" \
  --from-literal=DATABASE_URL="postgresql+asyncpg://ldapguard:$(openssl rand -base64 24)@postgres:5432/ldapguard" \
  -n ldapguard
```

### 2. Choose Your Deployment Method

## ArgoCD Application Examples

### Basic Deployment
**File:** `argocd-basic.yaml`

Minimal configuration - deploys LDAPGuard with defaults.

```bash
kubectl apply -f examples/argocd-basic.yaml
```

### With Version Pinning
**File:** `argocd-with-versions.yaml`

Pin specific image versions for stability.

```bash
kubectl apply -f examples/argocd-with-versions.yaml
```

### Full Customization
**File:** `argocd-full.yaml`

Includes ingress and resource limits using patches.

```bash
# Edit patches/ingress.yaml to set your domain first
kubectl apply -f examples/argocd-full.yaml
```

## Available Patches

Located in `patches/` directory:

### `ingress.yaml`
Adds Traefik IngressRoute for HTTPS access.

**Customize:**
- Replace `ldapguard.example.com` with your domain
- Update `certResolver` if needed

### `resource-limits.yaml`
Adds CPU/memory requests and limits to all workloads.

**Adjust values** based on your cluster capacity.

### `enable-backup-volume.yaml`
Enables the ReadWriteMany backup volume.

**Requirements:**
- Cluster must support RWX storage (NFS, CephFS, etc.)

## Using Patches in ArgoCD

### Method 1: Reference in Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
spec:
  source:
    path: k8s
    kustomize:
      patches:
        - path: examples/patches/ingress.yaml
        - path: examples/patches/resource-limits.yaml
```

### Method 2: Fork and Customize

1. Fork the LDAPGuard repository
2. Edit patches directly in your fork
3. Point ArgoCD to your fork

### Method 3: Inline Patches

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
              value: Host(`my-domain.com`)
```

## ArgoCD Web GUI Deployment

1. Log in to ArgoCD Web UI
2. Click **"+ NEW APP"**
3. Fill in:
   - **Application Name:** ldapguard
   - **Project:** default
   - **Sync Policy:** Automatic (optional)
   - **Repository URL:** https://github.com/keundokki/LDAPGuard
   - **Revision:** main
   - **Path:** k8s
   - **Cluster URL:** https://kubernetes.default.svc
   - **Namespace:** ldapguard
4. (Optional) Add kustomize overrides:
   - Click **KUSTOMIZE**
   - Add image overrides
   - Add patches
5. Click **CREATE**

## Customization Tips

### Override Environment Variables

```yaml
spec:
  source:
    kustomize:
      patches:
        - target:
            kind: ConfigMap
            name: app-config
          patch: |-
            - op: add
              path: /data/MY_CUSTOM_VAR
              value: "custom-value"
```

### Change Replica Counts

```yaml
spec:
  source:
    kustomize:
      patches:
        - target:
            kind: Deployment
            name: api
          patch: |-
            - op: replace
              path: /spec/replicas
              value: 3
```

### Use Different Image Registry

```yaml
spec:
  source:
    kustomize:
      images:
        - name: ghcr.io/keundokki/ldapguard-api
          newName: my-registry.com/ldapguard-api
          newTag: "custom"
```

## Troubleshooting

### Secrets Not Found
Ensure you created the secret before ArgoCD syncs:
```bash
kubectl get secret ldapguard-secrets -n ldapguard
```

### Storage Issues
If PVCs are pending, check your StorageClass:
```bash
kubectl get storageclass
kubectl describe pvc -n ldapguard
```

For RWX issues, see `patches/enable-backup-volume.yaml` notes.

### Ingress Not Working
Verify Traefik is installed and IngressRoute CRDs exist:
```bash
kubectl get crd ingressroutes.traefik.io
kubectl get middleware -n ldapguard
```
