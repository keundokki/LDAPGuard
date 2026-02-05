# GitHub Configuration for Self-Hosted Runner

## Required GitHub Variables

Since you're using a self-hosted runner on your internal network, you need to configure **variables** (not secrets) for VM IP addresses.

### Setting Up Variables

1. Go to https://github.com/keundokki/LDAPGuard
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click the **Variables** tab
4. Click **New repository variable**

### Required Variables

| Variable Name | Value | Description |
|---------------|-------|-------------|
| `STAGING_VM_IP` | `192.168.x.x` | Internal IP of staging VM |
| `PRODUCTION_VM_IP` | `192.168.x.x` | Internal IP of production VM |

Example:
- `STAGING_VM_IP` = `192.168.1.10`
- `PRODUCTION_VM_IP` = `192.168.1.20`

## Required GitHub Secrets

Only **ONE** secret is needed now:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `GHCR_TOKEN` | `ghp_xxxxx` | GitHub Personal Access Token for container registry |

### Creating GHCR_TOKEN

1. Go to GitHub: **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token (classic)**
3. Select scopes:
   - ✅ `write:packages`
   - ✅ `read:packages`
   - ✅ `delete:packages`
4. Click **Generate token**
5. Copy the token
6. Add it as `GHCR_TOKEN` secret in repository settings

## Branch Protection Rules

### For `main` branch:

1. Go to **Settings** → **Branches** → **Add branch protection rule**
2. Branch name pattern: `main`
3. Enable:
   - ✅ **Require a pull request before merging**
     - Required approvals: **1**
   - ✅ **Require status checks to pass before merging**
     - ✅ Require branches to be up to date
     - Required checks:
       - `test`
       - `build (Dockerfile.api)`
       - `build (Dockerfile.worker)`
       - `build (Dockerfile.web)`
       - `linting`
       - `dependency-check`
       - `security`
       - `quality`
       - `docker-compose`
   - ✅ **Require conversation resolution before merging**
   - ✅ **Do not allow bypassing the above settings**

### For `dev` branch:

1. Add branch protection rule
2. Branch name pattern: `dev`
3. Enable:
   - ✅ **Require status checks to pass before merging**
     - Same required checks as `main`
   - ✅ **Do not allow bypassing settings**

## Environment Protection

### Production Environment

1. Go to **Settings** → **Environments** → **New environment**
2. Name: `production`
3. Configure:
   - ✅ **Required reviewers**: Add 1-2 team members
   - ✅ **Wait timer**: 0 minutes (or add delay if needed)
   - ✅ **Deployment branches**: Only protected branches (main)

## Self-Hosted Runner Setup

After configuring GitHub settings above, follow the [Self-Hosted Runner Setup Guide](./SELF_HOSTED_RUNNER.md) to:

1. Install GitHub Actions runner on a VM in your network
2. Configure SSH access from runner to staging/production VMs
3. Test the runner
4. Deploy your first release

## Workflow Summary

### Updated Workflows

All deployment workflows now use `runs-on: self-hosted`:

- **CI/CD Pipeline** (`ci-cd.yml`) - Still uses GitHub-hosted runners (free unlimited for public repos)
- **Deploy to Staging** (`deploy-staging.yml`) - Uses self-hosted runner, SSHs to staging VM
- **Deploy to Production** (`deploy-production.yml`) - Uses self-hosted runner, SSHs to production VM
- **Rollback Production** (`rollback-production.yml`) - Uses self-hosted runner, SSHs to production VM

### Deployment Flow

```
GitHub Push → GitHub-hosted Runner (build & push images to GHCR)
    ↓
Self-hosted Runner (triggered by workflow)
    ↓
SSH to Staging/Production VM → Pull images → Deploy
```

## No Longer Needed

Since you're using self-hosted runner with direct network access, these secrets are **NOT needed**:

- ~~STAGING_SSH_HOST~~
- ~~STAGING_SSH_USER~~
- ~~STAGING_SSH_KEY~~
- ~~STAGING_SSH_PORT~~
- ~~PRODUCTION_SSH_HOST~~
- ~~PRODUCTION_SSH_USER~~
- ~~PRODUCTION_SSH_KEY~~
- ~~PRODUCTION_SSH_PORT~~

## Testing Configuration

After setup, test with:

```bash
# Push a change to dev
git checkout dev
git commit --allow-empty -m "test: trigger CI/CD"
git push origin dev

# Watch Actions tab for:
# 1. CI/CD builds images
# 2. Self-hosted runner deploys to staging
```

## Quick Reference

**Required in GitHub:**
- [ ] Variables: `STAGING_VM_IP`, `PRODUCTION_VM_IP`
- [ ] Secret: `GHCR_TOKEN`
- [ ] Branch protection: `main` and `dev`
- [ ] Environment: `production` with reviewers
- [ ] Self-hosted runner: Online and idle

**On Self-Hosted Runner VM:**
- [ ] Runner service running
- [ ] Docker installed
- [ ] SSH keys configured for staging/production access
- [ ] Network access to staging and production VMs

## Next Steps

1. ✅ Configure GitHub variables (VM IPs)
2. ✅ Add GHCR_TOKEN secret
3. ✅ Set up branch protection rules
4. ✅ Create production environment
5. ✅ Install self-hosted runner (see [SELF_HOSTED_RUNNER.md](./SELF_HOSTED_RUNNER.md))
6. ✅ Test deployment to staging
7. ✅ Create first production release
