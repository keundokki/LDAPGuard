# LDAPGuard Kubernetes Deployment

## Overview
This directory contains production-ready Kubernetes manifests for deploying LDAPGuard. Customize files with `.example` suffix before applying.

## Quick Start
1. Create secrets.yaml from secrets.example.yaml and update values.
2. Customize ingressroute.example.yaml for your domain and TLS certResolver.
3. Customize storageclass.example.yaml for your storage backend.
4. Optionally adjust resource-limits.example.yaml and kustomization-production.example.yaml.
5. Apply manifests:
   ```bash
   kubectl apply -k k8s/
   ```
6. Verify:
   - All pods Running: `kubectl get pods -n ldapguard`
   - Alembic migrations succeed: `kubectl logs -n ldapguard deployment/api`
   - HTTPS health: `curl https://<your-domain>/health`
   - API reachable: `curl https://<your-domain>/api/auth/login`
   - HTTP redirects to HTTPS: `curl http://<your-domain>/`

## File Structure
- `namespace.yaml` — Namespace definition
- `configmap-app.yaml` — App config (non-secret env vars)
- `configmap-nginx.yaml` — nginx.conf for web
- `secrets.example.yaml` — Secret values (passwords, keys)
- `pvc-postgres.yaml`, `pvc-redis.yaml`, `pvc-backup.yaml` — PersistentVolumeClaims
- `storageclass.example.yaml` — Example NFS StorageClass
- `postgres-statefulset.yaml`, `postgres-service.yaml` — PostgreSQL
- `redis-statefulset.yaml`, `redis-service.yaml` — Redis
- `api-deployment.yaml`, `api-service.yaml` — API
- `worker-deployment.yaml` — Worker
- `web-deployment.yaml`, `web-service.yaml` — Web
- `ingressroute.example.yaml` — Traefik IngressRoute (HTTPS)
- `middleware.yaml` — Traefik Middleware (redirect, headers)
- `networkpolicy.yaml` — NetworkPolicy
- `resource-limits.example.yaml` — Resource limits
- `kustomization.yaml` — Base kustomize config
- `kustomization-production.example.yaml` — Production overlay

## Design Decisions
- Service names match docker-compose for compatibility
- StatefulSets for Postgres/Redis
- Worker is singleton (1 replica)
- initContainers for dependency ordering
- PGDATA set to subdirectory
- DATABASE_URL in Secret, REDIS_URL in ConfigMap
- .example files require customization

## Customization
- Update secrets.example.yaml and create secrets.yaml
- Set domain and certResolver in ingressroute.example.yaml
- Adjust storageclass.example.yaml for your backend
- Tune resource-limits.example.yaml
- Pin image tags in kustomization-production.example.yaml

## Traefik HTTPS
- Uses IngressRoute CRD
- TLS termination via Traefik
- Middleware for HTTPS redirect and security headers

## Troubleshooting
- Check pod logs for errors
- Ensure PVCs are bound
- Verify domain and TLS certs

## References
- [docker-compose.yml](../docker-compose.yml)
- [config/nginx.conf](../config/nginx.conf)
- [api/core/config.py](../api/core/config.py)
- [.env.example](../.env.example)
- [Dockerfile.api](../Dockerfile.api)
