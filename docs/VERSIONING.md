# Image Tagging Strategy

LDAPGuard uses a structured tagging strategy to distinguish between staging and production deployments.

## Version Management

The project version is maintained in the [`VERSION`](../VERSION) file at the repository root.

**Current Version:** See [VERSION](../VERSION) file

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
1. Update VERSION file → 2. Push to dev → 3. Auto-deploy staging-X.Y.Z → 4. Test in staging → 5. Manually deploy vX.Y.Z to production
```

### Step-by-Step Workflow

**1. Prepare New Version**
```bash
# Update version file
echo "0.0.7" > VERSION
git add VERSION
git commit -m "chore: bump version to 0.0.7"
git push origin dev
```

**2. Automatic Staging Deployment**
- GitHub Actions builds images
- Tags: `staging`, `staging-0.0.7`, `staging-0.0.7-abc1234`
- Deploys to staging environment
- Image used: `staging-0.0.7`

**3. Test in Staging**
```bash
# Verify staging deployment
curl https://staging.ldapguard.local/health

# Run integration tests
./scripts/test-staging.sh
```

**4. Promote to Production**
```bash
# Create production release tag
git checkout main
git pull origin main
git merge dev
git tag -a v0.0.7 -m "Release v0.0.7"
git push origin v0.0.7

# Deploy via GitHub Actions
# Actions → Deploy to Production
# Image Tag: v0.0.7
```

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

1. **Update VERSION before pushing to dev** - Ensures staging gets correct version
2. **Test thoroughly in staging** - Version is locked, same image goes to production
3. **Use semantic versioning** - Clear communication of change impact
4. **Document changes** - Update CHANGELOG.md with each version
5. **Tag production releases** - Create git tags for all production deployments
6. **Never skip versions** - Always increment sequentially

## See Also

- [Release Process](./RELEASE_PROCESS.md) (if exists)
- [Deployment Guide](./GITHUB_SETUP_SELFHOSTED.md)
- [Changelog](../CHANGELOG.md)
