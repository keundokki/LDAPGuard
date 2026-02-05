# Staging Auto-Deployment Setup

This guide configures GitHub Actions to automatically deploy the `dev` branch to a staging server.

## Prerequisites

- Staging server with Docker and docker-compose installed
- SSH access to staging server
- GitHub repository with Actions enabled

## GitHub Secrets Configuration

Configure these secrets in: **Settings → Secrets and variables → Actions**

### Required Secrets

1. **`STAGING_HOST`**
   - Value: IP address or hostname of staging server
   - Example: `staging.example.com` or `192.168.1.100`

2. **`STAGING_USER`**
   - Value: SSH username for staging server
   - Example: `ubuntu` or `deploy`

3. **`STAGING_SSH_KEY`**
   - Value: Private SSH key for authentication
   - To generate:
     ```bash
     ssh-keygen -t ed25519 -f staging_key -C "ldapguard-staging"
     cat staging_key  # Copy this value
     ```
   - Add public key to staging server: `ssh-copy-id -i staging_key.pub user@host`

### Optional Secrets

4. **`STAGING_SSH_PORT`** (optional)
   - Value: SSH port (default: 22)
   - Example: `2222`

5. **`STAGING_URL`** (optional)
   - Value: URL for health checks
   - Example: `http://staging.example.com:8001`
   - Default: `http://localhost:8001`

## Step-by-Step Setup

### 1. Generate SSH Key for GitHub Actions

```bash
# Generate key (use default location)
ssh-keygen -t ed25519 -f ~/.ssh/ldapguard_staging -C "ldapguard-github-actions"

# View private key (for GitHub secret)
cat ~/.ssh/ldapguard_staging

# View public key (for staging server)
cat ~/.ssh/ldapguard_staging.pub
```

### 2. Add Public Key to Staging Server

```bash
# On staging server
mkdir -p ~/.ssh
echo "PASTE_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

### 3. Add GitHub Secrets

1. Go to: https://github.com/keundokki/LDAPGuard/settings/secrets/actions
2. Click "New repository secret"
3. Add each secret:

```
STAGING_HOST = staging.yourdomain.com
STAGING_USER = deploy
STAGING_SSH_KEY = -----BEGIN OPENSSH PRIVATE KEY-----
...entire private key...
-----END OPENSSH PRIVATE KEY-----
STAGING_SSH_PORT = 22  (optional)
STAGING_URL = http://staging.yourdomain.com:8001  (optional)
```

### 4. Verify Staging Server Setup

```bash
# On staging server
cd /opt/ldapguard-staging

# Create .env.staging with secrets
cat > .env.staging << 'EOF'
SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -base64 32)
ENVIRONMENT=staging
DATABASE_URL=postgresql+asyncpg://ldapguard:PASSWORD@postgres:5432/ldapguard_staging
REDIS_URL=redis://redis:6379/0
ALLOWED_ORIGINS=http://staging.yourdomain.com:8081
LOG_LEVEL=DEBUG
EOF

# Initial setup (do once)
docker-compose -f docker-compose.staging.yml --env-file .env.staging pull
docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d
docker-compose -f docker-compose.staging.yml exec api alembic upgrade head
```

## How It Works

### Workflow Trigger
- Automatically runs when code is pushed to `dev` branch
- Manual trigger via GitHub Actions UI

### Build Phase
- Builds Docker images for API, Worker, Web
- Tags with commit SHA and `staging` label
- Pushes to GitHub Container Registry

### Deployment Phase
- SSH to staging server
- Pulls latest `dev` code
- Pulls latest Docker images
- Restarts services with new images
- Runs database migrations

### Health Check
- Verifies staging API is responsive
- Retries for 60 seconds
- Reports status in commit checks

## Monitoring Deployments

### Via GitHub UI
- Go to: **Actions** tab
- Click on "Deploy to Staging" workflow
- View deployment progress and logs

### Via SSH
```bash
# SSH to staging server
ssh user@staging-server

# View logs
cd /opt/ldapguard-staging
docker-compose -f docker-compose.staging.yml logs -f api

# Check status
docker-compose -f docker-compose.staging.yml ps
```

### Via Staging URL
- Health check: `http://staging.yourdomain.com:8001/health`
- API docs: `http://staging.yourdomain.com:8001/api/docs`
- Web UI: `http://staging.yourdomain.com:8081`

## Troubleshooting

### SSH Connection Failed
```
Error: SSH key permission denied
```
- Check SSH key is added to staging server: `grep "AAAAB3..." ~/.ssh/authorized_keys`
- Verify permissions: `chmod 600 ~/.ssh/authorized_keys && chmod 700 ~/.ssh`
- Test locally: `ssh -i ~/.ssh/ldapguard_staging user@host`

### Docker Pull Failed
```
Error: Error response from daemon: pull access denied
```
- Verify staging server has GHCR access
- Or use public images instead of private

### Deployment Hangs
- Check staging server disk space: `df -h`
- Check Docker: `docker system df`
- Clean up old images: `docker system prune -a`

### Health Check Fails
```
Staging deployment status: Check logs
```
- SSH to staging and check service logs
- Verify network access to health endpoint
- Check PostgreSQL/Redis are running

## Deployment Workflow Example

```
Feature Development
    ↓
git commit & git push origin feature/xyz
    ↓
Create PR: feature/xyz → dev
    ↓
PR approved & merged to dev
    ↓
GitHub Actions: Deploy to Staging (automatic)
    ↓
Manual testing on staging (8-24 hours)
    ↓
Create PR: dev → release-X.X.X
    ↓
Release PR approved & merged to main
    ↓
GitHub Actions: Production deployment (manual trigger)
```

## Disabling Auto-Deployment

To temporarily disable staging deployment:
1. Go to: **Settings → Actions → General**
2. Disable "Deploy to Staging" workflow
3. Or delete `.github/workflows/deploy-staging.yml`

## Related Documentation

- [Staging Setup Guide](../docs/STAGING_SETUP.md)
- [Deployment Procedure](../docs/DEPLOYMENT_PROCEDURE.md)
- [Branch Protection Rules](../docs/BRANCH_PROTECTION.md)

---

**Last Updated:** February 5, 2026
