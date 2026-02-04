# Versioning Strategy

LDAPGuard follows [Semantic Versioning (SemVer)](https://semver.org/) for version numbers.

## Version Format

Versions follow the pattern: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes to the API or configuration
- **MINOR**: New features or enhancements (backward compatible)
- **PATCH**: Bug fixes and security updates (backward compatible)

Example: `1.0.1`

## Version Sources

The single source of truth for the version is:
- **Python Package**: `api/__init__.py` - `__version__` variable
- **Application Config**: `api/core/config.py` - reads from `api/__init__.py`
- **OpenAPI/Swagger**: Automatically exposed via FastAPI
- **Docker Images**: Tagged with version from `api/__init__.py`

## Releasing a New Version

### 1. Update Version Number

Edit `api/__init__.py`:
```python
__version__ = "1.0.2"
```

Also update `CHANGELOG.md` with the new changes.

### 2. Commit and Create Git Tag

```bash
git add api/__init__.py CHANGELOG.md
git commit -m "Release version 1.0.2"
git tag -a v1.0.2 -m "Release version 1.0.2"
git push origin main
git push origin v1.0.2
```

### 3. Automated CI/CD Process

When a version tag (`v*.*.*`) is pushed:

1. **Release Workflow** (`.github/workflows/release.yml`):
   - Verifies version in `api/__init__.py` matches the tag
   - Builds Docker images for both `linux/amd64` and `linux/arm64`
   - Pushes images to GHCR with three tags:
     - `latest` - always points to the newest release
     - `1.0.2` - specific version tag
     - `<commit-sha>` - Git commit hash
   - Creates a GitHub Release with auto-generated notes

2. **Main CI/CD Pipeline** (`.github/workflows/ci-cd.yml`):
   - Runs on every commit to `main` branch
   - Pushes images with version tag and commit SHA

## Image Tags

Docker images are tagged as follows:

```
ghcr.io/keundokki/ldapguard-api:latest        # Always the latest release
ghcr.io/keundokki/ldapguard-api:1.0.2         # Specific version
ghcr.io/keundokki/ldapguard-api:abc123def...  # Git commit SHA
```

## Checking Your Version

### In Code
```python
from api import __version__
print(__version__)  # e.g., "1.0.2"
```

### Via API
```bash
curl http://localhost:8000/docs
# Check the Swagger UI header or use:
curl http://localhost:8000/openapi.json | grep version
```

### In Docker
```bash
docker run ghcr.io/keundokki/ldapguard-api:1.0.2 \
  python -c "from api import __version__; print(__version__)"
```

## Version Compatibility

- **1.0.x**: Stable releases
- **0.y.z**: Pre-release versions (beta/alpha)

Check `CHANGELOG.md` for detailed release notes and breaking changes between versions.
