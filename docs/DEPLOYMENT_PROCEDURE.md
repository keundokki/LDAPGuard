# Production Deployment Procedure

This document defines the complete workflow for deploying LDAPGuard to production.

**Project:** LDAPGuard  
**Repository:** keundokki/LDAPGuard  
**Automation Trigger:** User says "push to production"

---

## Table of Contents

1. [Quick Command Reference](#quick-command-reference)
2. [Standard Release Workflow](#standard-release-workflow)
3. [Development Branch Workflow](#development-branch-workflow)
4. [Hotfix Workflow](#hotfix-workflow)
5. [Rollback Procedure](#rollback-procedure)
6. [Environment Configuration](#environment-configuration)
7. [Pre-Deployment Checklist](#pre-deployment-checklist)
8. [Post-Deployment Verification](#post-deployment-verification)

---

## Quick Command Reference

### When User Says "Push to Production"

```bash
# 1. Ensure you're on the correct release branch
git checkout release-0.0.X  # X = current version

# 2. Verify all changes committed
git status

# 3. Push release branch if not already pushed
git push -u origin release-0.0.X

# 4. Create tag
git tag -a v0.0.X -m "Release 0.0.X: <description>"
git push origin v0.0.X

# 5. Create PR to main via GitHub URL (displayed after push)
# Or: https://github.com/keundokki/LDAPGuard/compare/main...release-0.0.X

# 6. After PR merge, build and push Docker images
docker build -f Dockerfile.api -t ghcr.io/keundokki/ldapguard-api:0.0.X .
docker build -f Dockerfile.web -t ghcr.io/keundokki/ldapguard-web:0.0.X .
docker build -f Dockerfile.worker -t ghcr.io/keundokki/ldapguard-worker:0.0.X .

docker push ghcr.io/keundokki/ldapguard-api:0.0.X
docker push ghcr.io/keundokki/ldapguard-web:0.0.X
docker push ghcr.io/keundokki/ldapguard-worker:0.0.X

# Tag as latest
docker tag ghcr.io/keundokki/ldapguard-api:0.0.X ghcr.io/keundokki/ldapguard-api:latest
docker tag ghcr.io/keundokki/ldapguard-web:0.0.X ghcr.io/keundokki/ldapguard-web:latest
docker tag ghcr.io/keundokki/ldapguard-worker:0.0.X ghcr.io/keundokki/ldapguard-worker:latest

docker push ghcr.io/keundokki/ldapguard-api:latest
docker push ghcr.io/keundokki/ldapguard-web:latest
docker push ghcr.io/keundokki/ldapguard-worker:latest

# 7. Deploy to production (on production server)
cd /opt/ldapguard
git pull origin main
docker-compose pull
docker-compose down
docker-compose up -d

# 8. Run migrations (if any)
docker-compose exec api alembic upgrade head

# 9. Merge back to dev
git checkout dev
git merge main --no-ff -m "Merge main into dev after v0.0.X release"
git push origin dev

# 10. Cleanup release branch (after successful deployment)
git branch -d release-0.0.X
git push origin --delete release-0.0.X
```

---

## Standard Release Workflow

### Overview

```
feature/xyz → dev → release-0.0.X → main → production
                ↑                            ↓
                └────────── merge back ──────┘
```

### Step-by-Step Process

#### Phase 1: Development (on dev branch)

1. **Create feature branch from dev**
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/your-feature-name
   ```

2. **Develop feature**
   ```bash
   # Make changes
   git add .
   git commit -m "feat: description following conventional commits"
   git push -u origin feature/your-feature-name
   ```

3. **Create PR: feature → dev**
   - Review changes in GitHub
   - Run tests locally or via CI/CD
   - Request review if team member available
   - Merge after approval

4. **Test in dev environment** (if staging server exists)
   ```bash
   # On staging server
   cd /opt/ldapguard-staging
   git checkout dev
   git pull origin dev
   docker-compose -f docker-compose.dev.yml up -d --build
   ```

#### Phase 2: Release Preparation

5. **Create release branch from dev**
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b release-0.0.X  # Increment version
   ```

6. **Update version and changelog**
   ```bash
   # Edit api/__init__.py
   __version__ = "0.0.X"
   
   # Edit CHANGELOG.md - add release notes
   # Edit web/js/app.js - update version if displayed
   
   git add api/__init__.py CHANGELOG.md
   git commit -m "chore: bump version to 0.0.X"
   git push -u origin release-0.0.X
   ```

7. **Create and push tag**
   ```bash
   git tag -a v0.0.X -m "Release 0.0.X

   Security:
   - List security improvements
   
   Added:
   - New features
   
   Fixed:
   - Bug fixes
   
   Changed:
   - Breaking changes"
   
   git push origin v0.0.X
   ```

#### Phase 3: Production Deployment

8. **Create PR: release-0.0.X → main**
   - URL: https://github.com/keundokki/LDAPGuard/compare/main...release-0.0.X
   - Title: "Release v0.0.X"
   - Description: Copy from CHANGELOG.md
   - Label: `release`
   - Assign to yourself
   - Review and approve

9. **Merge PR to main**
   - Wait for status checks (if configured)
   - Click "Squash and merge" or "Merge pull request"
   - Delete release branch on GitHub (or keep until deployment verified)

10. **Build and push Docker images**
    ```bash
    # Authenticate to GitHub Container Registry
    echo $GITHUB_TOKEN | docker login ghcr.io -u keundokki --password-stdin
    
    # Build all images
    docker build -f Dockerfile.api -t ghcr.io/keundokki/ldapguard-api:0.0.X .
    docker build -f Dockerfile.web -t ghcr.io/keundokki/ldapguard-web:0.0.X .
    docker build -f Dockerfile.worker -t ghcr.io/keundokki/ldapguard-worker:0.0.X .
    
    # Push versioned images
    docker push ghcr.io/keundokki/ldapguard-api:0.0.X
    docker push ghcr.io/keundokki/ldapguard-web:0.0.X
    docker push ghcr.io/keundokki/ldapguard-worker:0.0.X
    
    # Tag and push as latest
    docker tag ghcr.io/keundokki/ldapguard-api:0.0.X ghcr.io/keundokki/ldapguard-api:latest
    docker tag ghcr.io/keundokki/ldapguard-web:0.0.X ghcr.io/keundokki/ldapguard-web:latest
    docker tag ghcr.io/keundokki/ldapguard-worker:0.0.X ghcr.io/keundokki/ldapguard-worker:latest
    
    docker push ghcr.io/keundokki/ldapguard-api:latest
    docker push ghcr.io/keundokki/ldapguard-web:latest
    docker push ghcr.io/keundokki/ldapguard-worker:latest
    ```

11. **Create GitHub Release**
    - Navigate to: https://github.com/keundokki/LDAPGuard/releases/new
    - Choose tag: v0.0.X
    - Release title: "LDAPGuard v0.0.X"
    - Description: Copy from CHANGELOG.md
    - Attach binaries if applicable
    - Publish release

12. **Deploy to production server**
    ```bash
    # SSH to production server
    ssh user@production-server
    
    # Navigate to deployment directory
    cd /opt/ldapguard
    
    # Backup current state
    docker-compose exec postgres pg_dump -U ldapguard ldapguard > backup_pre_0.0.X.sql
    
    # Pull latest code
    git fetch --all --tags
    git checkout main
    git pull origin main
    
    # Pull new images
    docker-compose pull
    
    # Stop services
    docker-compose down
    
    # Start services with new images
    docker-compose up -d
    
    # Run migrations
    docker-compose exec api alembic upgrade head
    
    # Verify all containers running
    docker-compose ps
    ```

#### Phase 4: Post-Deployment

13. **Verify deployment**
    ```bash
    # Check health endpoint
    curl https://ldapguard.yourdomain.com/health
    
    # Check version
    curl https://ldapguard.yourdomain.com/api/version
    
    # Check logs
    docker-compose logs --tail=50 api
    docker-compose logs --tail=50 worker
    
    # Test critical functionality
    # - Login
    # - Create backup
    # - View backups
    ```

14. **Merge main back to dev**
    ```bash
    git checkout dev
    git pull origin dev
    git merge main --no-ff -m "Merge main into dev after v0.0.X release"
    git push origin dev
    ```

15. **Cleanup (optional, after successful deployment)**
    ```bash
    # Delete local release branch
    git branch -d release-0.0.X
    
    # Delete remote release branch
    git push origin --delete release-0.0.X
    ```

---

## Development Branch Workflow

### Purpose of Dev Branch

The `dev` branch serves as:
- Integration point for all feature branches
- Staging/testing environment
- Pre-release stabilization
- Continuous integration target

### Workflow Diagram

```
main (production)
  ↑
  │ PR: release-0.0.X → main
  │
release-0.0.X (final testing)
  ↑
  │ Created from dev when ready
  │
dev (integration/staging)
  ↑
  ├─ feature/add-ldap-sync → PR → dev
  ├─ feature/email-notifications → PR → dev
  ├─ bugfix/auth-token-expiry → PR → dev
  └─ refactor/database-queries → PR → dev
```

### When to Use Dev Branch

**Use dev branch when:**
- Multiple developers working simultaneously
- Need staging environment for testing
- Want to batch features into releases
- Implementing complex features that need integration testing

**Skip dev branch when:**
- Solo developer with simple changes
- Hotfix needed immediately in production
- Small documentation updates

### Dev Branch Best Practices

1. **Keep dev stable** - All PRs must pass tests before merge
2. **Deploy dev to staging** - Auto-deploy dev branch to staging server
3. **Regular merges from main** - Keep dev in sync with production
4. **Feature flags** - Use flags for incomplete features in dev
5. **Database migrations** - Test migrations in dev environment first

---

## Hotfix Workflow

### When to Use Hotfix

Critical production bugs that cannot wait for regular release cycle:
- Security vulnerabilities discovered
- Data corruption issues
- Service outages
- Critical functionality broken

### Hotfix Process

1. **Create hotfix branch from main**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b hotfix/0.0.X  # Increment patch version
   ```

2. **Implement fix**
   ```bash
   # Make minimal changes to fix issue
   git add .
   git commit -m "fix: critical issue description"
   ```

3. **Update version**
   ```bash
   # Bump version in api/__init__.py
   # Add to CHANGELOG.md under ## [0.0.X] - YYYY-MM-DD (Hotfix)
   git add api/__init__.py CHANGELOG.md
   git commit -m "chore: bump version to 0.0.X (hotfix)"
   git push -u origin hotfix/0.0.X
   ```

4. **Create tag**
   ```bash
   git tag -a v0.0.X -m "Hotfix 0.0.X: critical bug description"
   git push origin v0.0.X
   ```

5. **Create PR to main**
   - Mark as urgent
   - Skip waiting for normal review cycle if emergency
   - Merge immediately after basic verification

6. **Deploy using standard process**
   ```bash
   # Build and push images
   # Deploy to production
   # See "Quick Command Reference" above
   ```

7. **Backport to dev**
   ```bash
   git checkout dev
   git cherry-pick <hotfix-commit-sha>
   # OR
   git merge main --no-ff -m "Merge hotfix 0.0.X into dev"
   git push origin dev
   ```

8. **Cleanup**
   ```bash
   git branch -d hotfix/0.0.X
   git push origin --delete hotfix/0.0.X
   ```

---

## Rollback Procedure

### When to Rollback

- Deployment causes production outages
- Critical bugs discovered post-deployment
- Data integrity issues
- Performance degradation

### Quick Rollback Steps

1. **Identify previous working version**
   ```bash
   git tag -l  # List all tags
   # Example: v0.0.4 was working
   ```

2. **Revert docker-compose.yml to previous version**
   ```bash
   # On production server
   cd /opt/ldapguard
   
   # Option A: Use git to revert
   git checkout v0.0.4 docker-compose.yml
   
   # Option B: Edit docker-compose.yml manually
   # Change image tags from :0.0.5 to :0.0.4
   ```

3. **Pull old images and restart**
   ```bash
   docker-compose pull
   docker-compose down
   docker-compose up -d
   ```

4. **Rollback database migrations if needed**
   ```bash
   # Check current migration
   docker-compose exec api alembic current
   
   # Downgrade to previous version
   docker-compose exec api alembic downgrade -1
   # OR specify exact revision
   docker-compose exec api alembic downgrade <revision_id>
   ```

5. **Restore database from backup if corrupted**
   ```bash
   # Stop services
   docker-compose down
   
   # Restore database
   docker-compose up -d postgres
   docker-compose exec postgres psql -U ldapguard ldapguard < backup_pre_0.0.5.sql
   
   # Restart all services
   docker-compose up -d
   ```

6. **Verify rollback success**
   ```bash
   curl https://ldapguard.yourdomain.com/health
   docker-compose logs --tail=50 api
   ```

7. **Document incident**
   - Create GitHub issue describing what went wrong
   - Document root cause
   - Plan fix for next release

---

## Environment Configuration

### Production Environment Variables

**File:** `/opt/ldapguard/.env` (on production server)

```bash
# Application
SECRET_KEY=<generate-random-64-char-hex>
ENCRYPTION_KEY=<generate-random-base64-key>
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql+asyncpg://ldapguard:secure_password@postgres:5432/ldapguard

# Redis
REDIS_URL=redis://redis:6379/0

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
ALLOWED_ORIGINS=https://ldapguard.yourdomain.com

# Security
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
PASSWORD_MIN_LENGTH=12

# Backup Settings
BACKUP_RETENTION_DAYS=30
MAX_BACKUP_SIZE_MB=1024

# Monitoring
LOG_LEVEL=INFO
SENTRY_DSN=<optional-sentry-url>

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@yourdomain.com
SMTP_PASSWORD=<app-password>
SMTP_FROM=ldapguard@yourdomain.com
```

### Generate Secrets

```bash
# SECRET_KEY (64 characters)
openssl rand -hex 32

# ENCRYPTION_KEY (base64, 32 bytes)
openssl rand -base64 32

# Database password
openssl rand -base64 24
```

### Development Environment

**File:** `.env` (in repository root, NOT committed)

```bash
# Application
SECRET_KEY=dev_secret_key_not_for_production
ENCRYPTION_KEY=dev_encryption_key_base64==
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+asyncpg://ldapguard:ldapguard@localhost:5432/ldapguard_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

# Development
DEBUG=true
RELOAD=true
LOG_LEVEL=DEBUG
```

---

## Pre-Deployment Checklist

### Code Quality

- [ ] All tests passing locally
- [ ] No linting errors (`flake8`, `black`, `isort`)
- [ ] No type checking errors (`mypy`)
- [ ] Code reviewed (if team member available)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated

### Database

- [ ] Migrations created for schema changes
- [ ] Migrations tested on dev database
- [ ] Migration rollback tested
- [ ] Database backup created before deployment
- [ ] No breaking changes to existing data

### Security

- [ ] No hardcoded secrets in code
- [ ] Environment variables documented
- [ ] No TODO security items remaining
- [ ] Dependencies up to date (no critical vulnerabilities)
- [ ] Rate limiting tested
- [ ] Authentication/authorization working
- [ ] CORS configured correctly
- [ ] Input validation on all endpoints

### Infrastructure

- [ ] Docker images build successfully
- [ ] All containers start without errors
- [ ] Health check endpoint responding
- [ ] Log aggregation working
- [ ] Monitoring alerts configured
- [ ] Backup system tested
- [ ] SSL certificates valid

### Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Load testing (if high traffic expected)
- [ ] Security scanning (OWASP ZAP, etc.)
- [ ] Browser compatibility tested

### Documentation

- [ ] API documentation updated
- [ ] README.md reflects new features
- [ ] Configuration examples updated
- [ ] Deployment procedure followed
- [ ] Known issues documented

---

## Post-Deployment Verification

### Immediate Checks (0-5 minutes)

```bash
# 1. All containers running
docker-compose ps

# 2. Health endpoint
curl https://ldapguard.yourdomain.com/health
# Expected: {"status": "healthy", "version": "0.0.X"}

# 3. API responding
curl https://ldapguard.yourdomain.com/api/docs
# Expected: Swagger UI HTML

# 4. No error logs
docker-compose logs --tail=100 api | grep ERROR
docker-compose logs --tail=100 worker | grep ERROR

# 5. Database connected
docker-compose exec api python -c "from api.core.database import get_db; print('DB OK')"
```

### Functional Tests (5-15 minutes)

- [ ] User can log in
- [ ] New LDAP server can be added
- [ ] Backup can be created
- [ ] Backup appears in list
- [ ] Backup can be downloaded
- [ ] Restore can be initiated
- [ ] Settings can be updated
- [ ] Admin panel accessible

### Monitoring (ongoing)

- [ ] Error rate in logs (should be near zero)
- [ ] Response times (< 200ms for most endpoints)
- [ ] CPU usage (< 50% steady state)
- [ ] Memory usage (< 80% allocated)
- [ ] Disk usage (backups not filling disk)
- [ ] Database connections (no leaks)

### Rollback Decision

**Rollback if:**
- Error rate > 5%
- Critical functionality broken
- Data corruption detected
- Performance 10x worse than previous version

**Do NOT rollback if:**
- Minor UI glitches
- Non-critical features broken
- Performance slightly degraded (< 20%)
- Can be fixed with hotfix

---

## Appendix: Common Issues

### Issue: "Migration fails on production"

**Solution:**
```bash
# Check current migration
docker-compose exec api alembic current

# Check pending migrations
docker-compose exec api alembic history

# Manually apply specific migration
docker-compose exec api alembic upgrade <revision>

# If migration corrupt, stamp current state
docker-compose exec api alembic stamp head
```

### Issue: "Containers won't start after deployment"

**Solution:**
```bash
# Check logs
docker-compose logs api
docker-compose logs worker

# Common causes:
# - Environment variable missing: Check .env file
# - Port conflict: Check what's using port 8000
# - Volume permission: Check file ownership
# - Database not ready: Wait 30s and retry
```

### Issue: "Old version still showing"

**Solution:**
```bash
# Force pull images
docker-compose pull --ignore-pull-failures

# Remove old containers
docker-compose down
docker rm -f $(docker ps -aq)

# Remove old images
docker rmi ghcr.io/keundokki/ldapguard-api:old-version

# Restart
docker-compose up -d --force-recreate
```

---

**Last Updated:** February 5, 2026  
**Maintained By:** GitHub Copilot  
**Review Schedule:** After each production deployment
