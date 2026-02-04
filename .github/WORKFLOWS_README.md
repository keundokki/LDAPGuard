# GitHub Actions CI/CD Pipeline

LDAPGuard uses GitHub Actions to automatically test, build, and validate containers on every push and pull request.

## Workflows

### 1. **CI/CD Pipeline** (`.github/workflows/ci-cd.yml`)

Comprehensive pipeline that runs on every push and PR:

#### Jobs:

**Test**
- ✅ Unit tests with pytest
- ✅ Code coverage reporting
- ✅ Python linting with flake8
- **Services**: PostgreSQL + Redis
- **Coverage Reports**: Uploaded to Codecov

**Build**
- 🐳 Builds all Docker images (API, Worker, Web)
- 📦 Uses Docker Buildx for multi-architecture support
- 💾 Caches layers for faster subsequent builds

**Security**
- 🔒 Vulnerability scanning with Trivy
- 📋 SARIF report upload to GitHub Security tab
- ⚠️ Non-blocking (pipeline continues on findings)

**Quality**
- 🎨 Code formatting check with Black
- 📚 Import sorting with isort
- 🔍 Static analysis with pylint

**Docker Compose**
- 🚀 Starts full stack (API, Worker, Web, PostgreSQL, Redis)
- ✓ Health checks for all services
- 🧪 Tests health endpoints
- 📊 Collects logs on failure

**Publish** (only on `main` branch)
- 🚀 Publishes images to Docker Hub
- 🏷️ Tags: `latest` and commit SHA
- 🔐 Requires Docker credentials in secrets

### 2. **Code Quality & Linting** (`.github/workflows/linting.yml`)

Dedicated workflow for code quality checks:
- Black (code formatting)
- isort (import sorting)
- flake8 (PEP8 compliance)
- mypy (type checking)

### 3. **Security Checks** (`.github/workflows/security.yml`)

Weekly security scans + on-demand:
- Filesystem vulnerability scanning
- Dependency vulnerability checking
- Container image scanning
- Reports to GitHub Security tab

## Setup

### 1. Enable GitHub Actions

Actions are enabled by default. Verify in: **Settings → Actions → General**

### 2. Configure Secrets (for Publishing)

To publish images to Docker Hub, add to **Settings → Secrets and variables → Actions**:

```
DOCKER_USERNAME=your-docker-username
DOCKER_PASSWORD=your-docker-password
```

Or for GitHub Container Registry (GHCR):

```
GH_TOKEN=ghp_your_github_token
```

### 3. View Workflow Status

- **Main page**: See status badges in README
- **Actions tab**: Full workflow logs and history
- **Security tab**: Vulnerability reports

## Workflow Triggers

| Trigger | Workflows |
|---------|-----------|
| Push to `main` | All workflows + Publish to registry |
| Push to `develop` | All workflows |
| Pull Request | All workflows (except publish) |
| Weekly (Sunday 00:00 UTC) | Security checks |

## Local Testing

### Run Tests Locally

```bash
# Install test dependencies
pip install -r requirements.txt

# Run pytest
pytest tests/ -v --cov=api

# Run specific test file
pytest tests/test_core_security.py -v

# Run with coverage report
pytest tests/ --cov=api --cov-report=html
```

### Build Docker Images

```bash
# Build API image
docker build -f Dockerfile.api -t ldapguard-api:latest .

# Build all images
docker-compose build

# Run full stack locally
docker-compose up -d
```

### Run Linting Locally

```bash
# Code formatting
black api workers

# Import sorting
isort api workers

# PEP8 compliance
flake8 api workers

# Type checking
mypy api workers --ignore-missing-imports
```

## Troubleshooting

### Tests Failing in CI but Passing Locally

1. **Database URL**: CI uses `postgresql://...@localhost` while Docker uses `postgres` hostname
2. **Environment variables**: Ensure all required `.env` variables are set
3. **Python version**: CI uses Python 3.11, verify your local version matches

### Docker Build Failures

1. **Layer caching**: Clear cache with: `docker-compose build --no-cache`
2. **Missing files**: Ensure `COPY` commands in Dockerfile match actual file structure
3. **Permissions**: Some containers need specific user permissions

### Secrets Not Working

1. Verify secrets are set in **Settings → Secrets and variables → Actions**
2. Check secret names match exactly in workflow file
3. Secrets are not logged in action output (by design)

### Publish to Registry Failing

1. Verify Docker credentials are correct
2. Check Docker Hub login: `docker login -u <username>`
3. Ensure repository exists on Docker Hub
4. Check Docker rate limits (100 pulls per 6 hours for anonymous)

## Performance Optimization

### Reduce Build Time

1. **Cache Strategy**: Uses GitHub Actions cache
2. **Parallel Jobs**: Multiple containers built simultaneously
3. **Skip Publish**: Publish only runs on `main` branch

### Failed Workflow Doesn't Block Main

- ⚠️ Linting failures are non-blocking
- ⚠️ Security findings don't fail the workflow
- ❌ Test failures DO block merging (if branch protection enabled)

## Best Practices

1. **Commit Tests**: Always include tests with code changes
2. **Keep Workflows Updated**: Review monthly for new GitHub Actions updates
3. **Monitor Security Alerts**: Check GitHub Security tab regularly
4. **Cache Dependencies**: Workflows use Python pip cache automatically
5. **Use Meaningful Commit Messages**: Helps track changes in action logs

## Adding New Workflows

To add a new workflow:

1. Create file in `.github/workflows/my-workflow.yml`
2. Use same trigger structure as existing workflows
3. Reference as: `.github/workflows/my-workflow.yml`
4. Commit and push to trigger

Example:

```yaml
name: My Custom Workflow

on:
  push:
    branches: [ main ]

jobs:
  my-job:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: My step
        run: echo "Hello from GitHub Actions!"
```

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Trivy Security Scanner](https://aquasecurity.github.io/trivy/)
- [Docker Buildx](https://docs.docker.com/engine/reference/commandline/buildx_build/)
- [Codecov](https://codecov.io/)
