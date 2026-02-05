# Production Deployment Procedure

This document defines the **exact workflow** to follow when deploying to production.

## When User Says: "Push to Production"

Follow this checklist in order:

---

## Pre-Deployment Checklist

### 1. Version Verification
- [ ] Confirm current version in `api/__init__.py`
- [ ] Verify `CHANGELOG.md` has entry for this version
- [ ] Check all security improvements are documented

### 2. Code Quality Checks
- [ ] All tests passing (run if available)
- [ ] No `TODO` or `FIXME` comments blocking release
- [ ] Security scan completed (Trivy or similar)
- [ ] Dependencies up to date and secure

### 3. Environment Validation
- [ ] Development environment working (`podman-compose up -d`)
- [ ] Database migrations tested and ready
- [ ] All containers healthy

---

## Deployment Steps

### Step 1: Prepare Release Branch
```bash
# Ensure you're on the correct branch
CURRENT_VERSION=$(grep -oP '__version__\s*=\s*"\K[^"]+' api/__init__.py)
git checkout -b release-${CURRENT_VERSION}

# Or if branch exists, switch to it
git checkout release-${CURRENT_VERSION}

# Ensure all changes are committed
git status
git add -A
git commit -m "Prepare release v${CURRENT_VERSION}"
```

### Step 2: Create Annotated Tag
```bash
# Create tag with detailed release notes
git tag -a v${CURRENT_VERSION} -m "Release v${CURRENT_VERSION}

$(head -n 30 CHANGELOG.md | tail -n 25)
"

# Verify tag was created
git tag -l "v${CURRENT_VERSION}"
git show v${CURRENT_VERSION}
```

### Step 3: Push to GitHub
```bash
# Push release branch
git push origin release-${CURRENT_VERSION}

# Push the tag
git push origin v${CURRENT_VERSION}
```

### Step 4: Create Pull Request to Main
1. Go to: `https://github.com/keundokki/LDAPGuard/pull/new/release-${CURRENT_VERSION}`
2. Fill in PR template:
   - **Title:** `Release v${CURRENT_VERSION}`
   - **Description:** Copy from CHANGELOG.md for this version
   - Add labels: `release`, `production`
3. Request review (if team exists)
4. Wait for CI/CD checks to pass
5. Get approval

### Step 5: Merge to Main
- Click **Merge pull request**
- Choose merge strategy (recommend: **Squash and merge** or **Create merge commit**)
- Confirm merge
- **DO NOT** delete release branch yet (wait for production verification)

### Step 6: Verify Production Deployment
```bash
# Pull latest main
git checkout main
git pull origin main

# Verify tag exists on main
git describe --tags --exact-match HEAD

# Check that version matches
grep __version__ api/__init__.py
```

### Step 7: Build and Push Docker Images
```bash
# Build production images
podman build -f Dockerfile.api -t ghcr.io/keundokki/ldapguard-api:${CURRENT_VERSION} .
podman build -f Dockerfile.api -t ghcr.io/keundokki/ldapguard-api:latest .
podman build -f Dockerfile.worker -t ghcr.io/keundokki/ldapguard-worker:${CURRENT_VERSION} .
podman build -f Dockerfile.worker -t ghcr.io/keundokki/ldapguard-worker:latest .
podman build -f Dockerfile.web -t ghcr.io/keundokki/ldapguard-web:${CURRENT_VERSION} .
podman build -f Dockerfile.web -t ghcr.io/keundokki/ldapguard-web:latest .

# Login to GitHub Container Registry
echo $GITHUB_TOKEN | podman login ghcr.io -u keundokki --password-stdin

# Push versioned images
podman push ghcr.io/keundokki/ldapguard-api:${CURRENT_VERSION}
podman push ghcr.io/keundokki/ldapguard-worker:${CURRENT_VERSION}
podman push ghcr.io/keundokki/ldapguard-web:${CURRENT_VERSION}

# Push latest tags
podman push ghcr.io/keundokki/ldapguard-api:latest
podman push ghcr.io/keundokki/ldapguard-worker:latest
podman push ghcr.io/keundokki/ldapguard-web:latest
```

### Step 8: Create GitHub Release
1. Go to: `https://github.com/keundokki/LDAPGuard/releases/new`
2. Select tag: `v${CURRENT_VERSION}`
3. Release title: `v${CURRENT_VERSION}`
4. Description: Copy from CHANGELOG.md
5. Attach binaries/artifacts (if any)
6. Check **Set as latest release**
7. Click **Publish release**

### Step 9: Deploy to Production Server
```bash
# On production server
cd /path/to/ldapguard
git pull origin main
git checkout v${CURRENT_VERSION}

# Backup database
podman exec ldapguard-postgres pg_dump -U ldapguard ldapguard > backup_$(date +%Y%m%d_%H%M%S).sql

# Run migrations
podman exec ldapguard-api alembic upgrade head

# Restart services with new version
podman-compose down
podman-compose pull  # Pull new images
podman-compose up -d

# Verify health
curl -f http://localhost:8000/health
```

### Step 10: Post-Deployment Verification
```bash
# Check all containers are running
podman ps

# Check API health
curl http://localhost:8000/health | jq

# Verify version
curl http://localhost:8000/ | jq '.version'

# Check logs for errors
podman logs ldapguard-api --tail 50
podman logs ldapguard-worker --tail 50

# Test critical endpoints
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Step 11: Cleanup (After Successful Deployment)
```bash
# Delete release branch locally and remotely
git checkout main
git branch -d release-${CURRENT_VERSION}
git push origin --delete release-${CURRENT_VERSION}

# Update local repository
git fetch --prune
```

---

## Rollback Procedure (If Issues Found)

### Quick Rollback
```bash
# On production server
PREVIOUS_VERSION="0.0.4"  # Previous stable version

# Checkout previous tag
git checkout v${PREVIOUS_VERSION}

# Restore database backup (if needed)
podman exec -i ldapguard-postgres psql -U ldapguard ldapguard < backup_YYYYMMDD_HHMMSS.sql

# Restart with previous version
podman-compose down
podman-compose up -d

# Verify
curl http://localhost:8000/health | jq
```

---

## Security Checklist Before Production

- [ ] All secrets are using environment variables (no hardcoded secrets)
- [ ] `SECRET_KEY` and `ENCRYPTION_KEY` are strong (32+ characters)
- [ ] `DEBUG=false` in production
- [ ] CORS origins restricted (not wildcard)
- [ ] Rate limiting enabled
- [ ] HTTPS configured (not in docker-compose, handled by reverse proxy)
- [ ] Database passwords changed from defaults
- [ ] Firewall rules configured
- [ ] Backup strategy in place

---

## Environment Variables for Production

Create `.env.production` file:

```bash
# Application
DEBUG=false
APP_NAME=LDAPGuard
APP_VERSION=0.0.5

# Security (CHANGE THESE!)
SECRET_KEY=generate-strong-32-char-secret-here
ENCRYPTION_KEY=generate-strong-32-char-secret-here

# Database
POSTGRES_PASSWORD=change-this-strong-password
DATABASE_URL=postgresql+asyncpg://ldapguard:${POSTGRES_PASSWORD}@postgres:5432/ldapguard

# Redis
REDIS_URL=redis://redis:6379

# Backup
BACKUP_DIR=/app/backups
BACKUP_RETENTION_DAYS=30

# Webhooks (optional)
WEBHOOK_ENABLED=false
WEBHOOK_URL=

# Prometheus
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
```

---

## Production Deployment Checklist Summary

When user says **"push to production"**, execute:

1. ✅ Verify version and changelog
2. ✅ Create/update release branch
3. ✅ Create annotated tag
4. ✅ Push branch and tag to GitHub
5. ✅ Create Pull Request to main
6. ✅ Get approval and merge PR
7. ✅ Build and push Docker images
8. ✅ Create GitHub release
9. ✅ Deploy to production server
10. ✅ Verify deployment health
11. ✅ Cleanup release branch
12. ✅ Monitor for 24 hours

---

## Quick Command Reference

```bash
# Get current version
grep __version__ api/__init__.py | cut -d'"' -f2

# Create and push release
VERSION=$(grep __version__ api/__init__.py | cut -d'"' -f2)
git checkout -b release-${VERSION}
git tag -a v${VERSION} -m "Release v${VERSION}"
git push origin release-${VERSION} v${VERSION}

# After PR merge: Build and push images
podman-compose build
podman tag localhost/ldapguard-api:latest ghcr.io/keundokki/ldapguard-api:${VERSION}
podman push ghcr.io/keundokki/ldapguard-api:${VERSION}

# Deploy
ssh production-server "cd /path/to/ldapguard && git pull && podman-compose down && podman-compose pull && podman-compose up -d"
```

---

## Monitoring After Deployment

- Check error logs: `podman logs ldapguard-api -f`
- Monitor metrics: `http://localhost:9090/metrics`
- Check backup jobs: `podman logs ldapguard-worker -f`
- Database health: `podman exec ldapguard-postgres pg_isready`
- Disk space: `df -h /app/backups`

---

## Emergency Contacts

- GitHub Repository: https://github.com/keundokki/LDAPGuard
- Issues: https://github.com/keundokki/LDAPGuard/issues
- Releases: https://github.com/keundokki/LDAPGuard/releases

---

## Notes

- Always create a database backup before deploying
- Never skip the PR process, even for hotfixes
- Tag protection prevents accidental tag deletion
- Keep release branches until verified in production
- Document any manual steps in CHANGELOG.md
