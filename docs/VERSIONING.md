# Image Tagging Strategy

LDAPGuard uses a structured tagging strategy with **automatic patch version increment** for staging deployments.

## Version Management

The project version is maintained in the [`VERSION`](../VERSION) file at the repository root.

**Current Version:** See [VERSION](../VERSION) file

### Auto-Increment Strategy

The VERSION file is **automatically incremented** on every push to `dev`:

- **PATCH** - Auto-incremented (0.0.6 → 0.0.7)
- **MINOR/MAJOR** - Manually updated when needed

## Tagging Schemes

### Staging Environment

**Tags Created:**
- `staging` - Rolling latest tag (always points to most recent staging build)
- `staging-X.Y.Z` - Version-based tag (e.g., `staging-0.0.6`)
- `staging-X.Y.Z-abc1234` - Version + commit SHA (e.g., `staging-0.0.6-a1b2c3d`)

**Example:**
```bash
ghcr.io/keundokki/ldapguard-api:staging
ghcr.io/keundokki/ldapguard-api:staging-0.0.6
ghcr.io/keundokki/ldapguard-api:staging-0.0.6-a1b2c3d
```

**When Created:**
- Automatically on every push to `dev` branch
- Reads version from `VERSION` file
- Includes git commit SHA for traceability

### Production Environment

**Tags Created:**
- `vX.Y.Z` - Semantic version (e.g., `v0.0.6`)
- `latest` - Rolling latest production tag

**Example:**
```bash
ghcr.io/keundokki/ldapguard-api:v0.0.6
ghcr.io/keundokki/ldapguard-api:latest
```

**When Created:**
- Manually triggered deployment via GitHub Actions
- Promoted from staging after testing
- Uses same version number as staging (without `staging-` prefix)

## Version Lifecycle

```
1. Push to dev → 2. Auto-increment PATCH → 3. Deploy staging-X.Y.Z → 4. Test → 5. Manual MINOR/MAJOR bump → 6. Create tag vX.Y.Z → 7. Deploy production
```

### Step-by-Step Workflow

**1. Automatic on Dev Push**
```bash
git push origin dev
# GitHub Action automatically:
# - Reads VERSION (0.0.6)
# - Increments PATCH (0.0.7)
# - Commits back to dev
# - Builds and deploys staging-0.0.7
```

**2. Workflow runs automatically:**
- CI/CD builds images with staging-0.0.7
- Auto-increment workflow increments to 0.0.8
- Next push will use 0.0.8

**3. Test in Staging**
```bash
# Test current staging deployment
curl https://staging.ldapguard.local/health
./scripts/test-staging.sh
```

**4. Bump Minor Version (when needed)**
```bash
# Only when you want MINOR or MAJOR version change
echo "0.1.0" > VERSION
git add VERSION
git commit -m "chore: bump to minor version 0.1.0"
git push origin dev
# Next deployment: staging-0.1.0
```

**5. Promote to Production**
```bash
git checkout main
git pull origin main
git merge dev
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0

# Deploy via GitHub Actions
```

## Automatic Increment Details

### How It Works

The `auto-increment-version.yml` workflow:
1. Triggers on push to `dev` (except VERSION file changes)
2. Reads current version from VERSION file
3. Increments PATCH version (Z+1)
4. Commits and pushes back to dev
5. Skips if last commit was already a version bump

### Example Progression

```
Push 1: 0.0.6 → Auto-increments to 0.0.7 ✓
Push 2: 0.0.7 → Auto-increments to 0.0.8 ✓
Push 3: 0.0.8 → Auto-increments to 0.0.9 ✓
Manual: Edit to 0.1.0
Push 4: 0.1.0 → Auto-increments to 0.1.1 ✓
```

### When Does It Trigger?

✅ Triggers on:
- Code changes pushed to dev
- Workflow updates

❌ Does NOT trigger on:
- VERSION file changes (avoids infinite loops)
- Documentation changes
- Comment-only changes

## Semantic Versioning

We follow [Semantic Versioning 2.0.0](https://semver.org/):

**Format:** `MAJOR.MINOR.PATCH`

- **MAJOR** (X): Breaking changes, incompatible API changes
- **MINOR** (Y): New features, backward-compatible
- **PATCH** (Z): Bug fixes, backward-compatible

**Examples:**
- `0.0.5` → `0.0.6` - Bug fix
- `0.0.6` → `0.1.0` - New feature
- `0.1.0` → `1.0.0` - Breaking change / first stable release

## Image Registry

All images are stored in GitHub Container Registry (GHCR):

**Registry URL:** `ghcr.io/keundokki/`

**Images:**
- `ldapguard-api` - FastAPI backend
- `ldapguard-worker` - Background worker (Celery)
- `ldapguard-web` - Nginx web server

## Tag Retention

**Staging:**
- `staging` - Always kept (rolling)
- `staging-X.Y.Z` - Kept for last 10 versions
- `staging-X.Y.Z-commit` - Kept for 30 days

**Production:**
- `latest` - Always kept (rolling)
- `vX.Y.Z` - Kept indefinitely
- All production releases are permanent

## Quick Reference

### Update VERSION File

```bash
echo "0.0.8" > VERSION
```

### Check Current Staging Version

```bash
docker run --rm ghcr.io/keundokki/ldapguard-api:staging /app/api/main.py --version
```

### List All Tags

```bash
# Via GitHub CLI
gh api repos/keundokki/LDAPGuard/tags | jq '.[].name'

# Via Docker
docker pull ghcr.io/keundokki/ldapguard-api --all-tags
docker images ghcr.io/keundokki/ldapguard-api
```

### Pull Specific Version

```bash
# Staging
docker pull ghcr.io/keundokki/ldapguard-api:staging-0.0.7

# Production
docker pull ghcr.io/keundokki/ldapguard-api:v0.0.7
```

## Troubleshooting

### Wrong Version Deployed

```bash
# Check which tag is currently running
docker ps | grep ldapguard-api
docker inspect <container_id> | jq '.[0].Config.Image'

# Redeploy correct version
export STAGING_TAG=staging-0.0.7
docker-compose -f docker-compose.staging.yml pull
docker-compose -f docker-compose.staging.yml up -d
```

### Version Mismatch

```bash
# Ensure VERSION file matches git tag
cat VERSION  # Should be 0.0.7
git tag -l "v*" | tail -1  # Should be v0.0.6 (previous release)

# Staging should be one version ahead of production
```

## Best Practices

1. **Let auto-increment handle PATCH** - Don't manually update for bug fixes
2. **Manual MINOR/MAJOR** - Only edit VERSION file for feature/breaking changes
3. **Test thoroughly in staging** - Version is locked once in production
4. **Tag production releases** - Always create git tags for production versions
5. **Keep VERSION file synced** - Don't manually edit unless intentional bump
6. **Document changes** - Update CHANGELOG.md with each version

## See Also

- [Release Process](./RELEASE_PROCESS.md) (if exists)
- [Deployment Guide](./GITHUB_SETUP_SELFHOSTED.md)
- [Changelog](../CHANGELOG.md)
