# Self-Hosted GitHub Actions Runner Setup

This guide explains how to set up a self-hosted GitHub Actions runner for LDAPGuard deployment.

## Why Self-Hosted Runner?

Since your VMs don't have public IPs, a self-hosted runner on your internal network can:
- Access staging and production VMs directly (no SSH over internet needed)
- Run deployments securely within your network
- **Free** for public repositories (unlimited minutes)
- Faster builds (local network speeds)

## Architecture

```
GitHub (Cloud)
    ↓ (triggers workflow)
Self-Hosted Runner (your network)
    ↓ (direct access)
├── Staging VM (192.168.x.x)
└── Production VM (192.168.x.x)
```

## Prerequisites

- Linux VM or server on your network (can be one of your existing VMs)
- Docker/Podman installed
- Network access to staging and production VMs
- GitHub repository admin access

## Runner Requirements

**Minimum specs:**
- 2 CPU cores
- 4GB RAM
- 20GB disk space
- Ubuntu 20.04+ (or any Linux distro)

**Recommended:**
- 4 CPU cores
- 8GB RAM
- 50GB disk space

## Installation Steps

### 1. Choose Runner Location

You can install the runner on:
- **Dedicated VM** (recommended for production)
- **Staging VM** (simpler, shared resources)
- **Your KVM host** (if it has network access to VMs)

### 2. Get Runner Token from GitHub

1. Go to https://github.com/keundokki/LDAPGuard
2. Click **Settings** → **Actions** → **Runners**
3. Click **New self-hosted runner**
4. Select **Linux** architecture
5. Copy the commands shown (we'll use them below)

### 3. Install Runner Software

SSH to your chosen VM and run:

```bash
# Create a folder for the runner
mkdir -p ~/actions-runner && cd ~/actions-runner

# Download the latest runner package
curl -o actions-runner-linux-x64-2.313.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.313.0/actions-runner-linux-x64-2.313.0.tar.gz

# Extract the installer
tar xzf ./actions-runner-linux-x64-2.313.0.tar.gz

# Create runner configuration
./config.sh --url https://github.com/keundokki/LDAPGuard --token <YOUR_TOKEN_FROM_GITHUB>
```

**During configuration:**
- Runner group: Press Enter (default)
- Runner name: `ldapguard-runner` (or any name)
- Work folder: Press Enter (default: `_work`)
- Labels: `self-hosted,linux,x64` (add `,docker` if you want)

### 4. Install Runner as Service

This ensures the runner starts automatically on boot:

```bash
# Install service (requires sudo)
sudo ./svc.sh install

# Start the service
sudo ./svc.sh start

# Check status
sudo ./svc.sh status
```

### 5. Verify Runner is Online

1. Go to GitHub: Settings → Actions → Runners
2. You should see your runner with a green "Idle" status
3. If offline, check logs: `sudo journalctl -u actions.runner.*`

## Configure Runner Environment

### Install Required Tools

The runner needs tools to deploy:

```bash
# Update system
sudo apt update

# Install Docker (if not already installed)
sudo apt install -y docker.io docker-compose

# Add runner user to docker group
sudo usermod -aG docker $(whoami)

# Install Git
sudo apt install -y git

# Install other tools as needed
sudo apt install -y curl wget jq
```

### Set Up SSH Access to VMs

Since the runner needs to deploy to staging/production:

```bash
# Generate SSH key for runner (if not exists)
ssh-keygen -t ed25519 -C "github-runner" -f ~/.ssh/runner_key -N ""

# Copy public key to staging VM
ssh-copy-id -i ~/.ssh/runner_key.pub ldapguard@STAGING_VM_IP

# Copy public key to production VM
ssh-copy-id -i ~/.ssh/runner_key.pub ldapguard@PRODUCTION_VM_IP

# Test connections
ssh -i ~/.ssh/runner_key ldapguard@STAGING_VM_IP "echo 'Staging OK'"
ssh -i ~/.ssh/runner_key ldapguard@PRODUCTION_VM_IP "echo 'Production OK'"
```

## Update Deployment Scripts

Since the runner is on your network, update the deployment commands in workflows to use direct VM access:

### For Staging Deployment

```bash
# From the runner, deploy to staging:
ssh -i ~/.ssh/runner_key ldapguard@STAGING_VM_IP "cd /opt/ldapguard-staging && \
  git pull && \
  docker-compose -f docker-compose.staging.yml pull && \
  docker-compose -f docker-compose.staging.yml up -d"
```

### For Production Deployment

```bash
# From the runner, deploy to production:
ssh -i ~/.ssh/runner_key ldapguard@PRODUCTION_VM_IP "cd /opt/ldapguard && \
  export IMAGE_TAG=v1.0.0 && \
  docker-compose pull && \
  docker-compose up -d"
```

## GitHub Secrets (Simplified)

With self-hosted runner, you **DON'T NEED** these secrets anymore:
- ~~STAGING_SSH_HOST~~
- ~~STAGING_SSH_USER~~
- ~~STAGING_SSH_KEY~~
- ~~PRODUCTION_SSH_HOST~~
- ~~PRODUCTION_SSH_USER~~
- ~~PRODUCTION_SSH_KEY~~

**Still needed:**
- `GHCR_TOKEN` - For pushing container images to GitHub Container Registry

## Testing the Runner

Create a test workflow to verify:

```yaml
# .github/workflows/test-runner.yml
name: Test Self-Hosted Runner

on:
  workflow_dispatch:

jobs:
  test:
    runs-on: self-hosted
    steps:
      - name: Test runner
        run: |
          echo "Runner hostname: $(hostname)"
          echo "Runner user: $(whoami)"
          echo "Docker version: $(docker --version)"
          echo "Git version: $(git --version)"
          
      - name: Test VM connectivity
        run: |
          ssh -i ~/.ssh/runner_key ldapguard@STAGING_VM_IP "hostname"
          ssh -i ~/.ssh/runner_key ldapguard@PRODUCTION_VM_IP "hostname"
```

## Monitoring and Maintenance

### Check Runner Status

```bash
# On runner VM
sudo systemctl status actions.runner.*

# View logs
sudo journalctl -u actions.runner.* -f
```

### Update Runner

```bash
cd ~/actions-runner
sudo ./svc.sh stop
./config.sh remove --token <REMOVAL_TOKEN>
# Download new version and reconfigure
sudo ./svc.sh install
sudo ./svc.sh start
```

### Restart Runner

```bash
sudo systemctl restart actions.runner.*
```

## Security Best Practices

1. **Dedicated User**: Run runner as dedicated user (not root)
2. **SSH Keys**: Use separate SSH keys for runner (not your personal keys)
3. **Firewall**: Restrict runner VM to only necessary ports
4. **Updates**: Keep runner software updated
5. **Logs**: Monitor runner logs for suspicious activity
6. **Secrets**: Don't store secrets in runner filesystem

## Troubleshooting

### Runner Shows Offline

```bash
# Check service status
sudo systemctl status actions.runner.*

# Restart service
sudo systemctl restart actions.runner.*

# Check network connectivity to GitHub
curl -I https://github.com
```

### Deployment Fails

```bash
# Test SSH from runner to VMs
ssh -i ~/.ssh/runner_key ldapguard@VM_IP "whoami"

# Check Docker access
docker ps

# Verify runner has correct permissions
ls -la ~/actions-runner/_work
```

### Disk Space Issues

```bash
# Clean Docker images
docker system prune -a -f

# Clean old workflow runs
cd ~/actions-runner/_work && rm -rf */

# Check disk usage
df -h
```

## Next Steps

After setting up the runner:

1. ✅ Verify runner shows as "Idle" in GitHub
2. ✅ Test VM connectivity from runner
3. ✅ Run test workflow
4. ✅ Deploy to staging using updated workflow
5. ✅ Monitor logs for any issues

## Reference

- [GitHub Actions Self-Hosted Runner Docs](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Runner Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
