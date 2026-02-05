# Staging Environment Setup Guide

This document explains how to set up and use the staging environment for LDAPGuard.

---

## Overview

The staging environment is a production-like environment that automatically deploys from the `dev` branch. It serves as:
- Integration testing platform
- Pre-release validation
- Demo environment
- Performance testing

---

## Quick Start

### Local Staging Setup

1. **Start staging environment**
   ```bash
   docker-compose -f docker-compose.staging.yml up -d
   ```

2. **Access staging**
   - Web UI: http://localhost:8081
   - API: http://localhost:8001
   - API Docs: http://localhost:8001/api/docs

3. **Run migrations**
   ```bash
   docker-compose -f docker-compose.staging.yml exec api alembic upgrade head
   ```

4. **Create admin user**
   ```bash
   docker-compose -f docker-compose.staging.yml exec api python -c "
   from api.core.database import get_db
   from api.core.security import get_password_hash
   from api.models.models import User
   import asyncio
   
   async def create_admin():
       async for db in get_db():
           user = User(
               username='admin',
               email='admin@staging.local',
               password_hash=get_password_hash('admin123'),
               is_admin=True
           )
           db.add(user)
           await db.commit()
           print('Admin user created')
   
   asyncio.run(create_admin())
   "
   ```

5. **Stop staging**
   ```bash
   docker-compose -f docker-compose.staging.yml down
   ```

---

## Remote Staging Server Setup

### Prerequisites

- Ubuntu/Debian server (2 CPU, 4GB RAM minimum)
- Docker and Docker Compose installed
- GitHub access (for pulling code)
- Domain name (optional): staging.ldapguard.yourdomain.com

### Installation Steps

1. **Install Docker**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Install Docker Compose
   sudo apt install docker-compose -y
   
   # Add user to docker group
   sudo usermod -aG docker $USER
   newgrp docker
   ```

2. **Clone repository**
   ```bash
   cd /opt
   sudo git clone https://github.com/keundokki/LDAPGuard.git ldapguard-staging
   sudo chown -R $USER:$USER ldapguard-staging
   cd ldapguard-staging
   git checkout dev
   ```

3. **Configure environment**
   ```bash
   # Create .env.staging file
   cat > .env.staging << 'EOF'
   # Application
   SECRET_KEY=$(openssl rand -hex 32)
   ENCRYPTION_KEY=$(openssl rand -base64 32)
   ENVIRONMENT=staging
   
   # Database
   DATABASE_URL=postgresql+asyncpg://ldapguard:CHANGE_THIS_PASSWORD@postgres:5432/ldapguard_staging
   
   # Redis
   REDIS_URL=redis://redis:6379/0
   
   # API Settings
   ALLOWED_ORIGINS=http://staging.ldapguard.yourdomain.com,http://YOUR_SERVER_IP:8081
   
   # Security
   JWT_ALGORITHM=HS256
   JWT_EXPIRE_MINUTES=30
   
   # Logging
   LOG_LEVEL=DEBUG
   EOF
   
   # Generate actual secrets
   sed -i "s/$(openssl rand -hex 32)/$(openssl rand -hex 32)/" .env.staging
   sed -i "s/$(openssl rand -base64 32)/$(openssl rand -base64 32)/" .env.staging
   sed -i "s/CHANGE_THIS_PASSWORD/$(openssl rand -base64 24)/" .env.staging
   ```

4. **Start services**
   ```bash
   docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d
   ```

5. **Initialize database**
   ```bash
   # Wait for containers to be healthy
   sleep 30
   
   # Run migrations
   docker-compose -f docker-compose.staging.yml exec api alembic upgrade head
   ```

6. **Configure firewall**
   ```bash
   # Allow HTTP/HTTPS
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   
   # Allow staging ports
   sudo ufw allow 8001/tcp  # API
   sudo ufw allow 8081/tcp  # Web
   
   # Enable firewall
   sudo ufw enable
   ```

---

## Auto-Deployment from Dev Branch

### Option 1: GitHub Actions (Recommended)

Create `.github/workflows/deploy-staging.yml`:

```yaml
name: Deploy to Staging

on:
  push:
    branches:
      - dev

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Deploy to staging server
        uses: appleboy/ssh-action@v0.1.10
        with:
          host: ${{ secrets.STAGING_HOST }}
          username: ${{ secrets.STAGING_USER }}
          key: ${{ secrets.STAGING_SSH_KEY }}
          script: |
            cd /opt/ldapguard-staging
            git fetch origin
            git checkout dev
            git pull origin dev
            docker-compose -f docker-compose.staging.yml --env-file .env.staging pull
            docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d --build
            docker-compose -f docker-compose.staging.yml exec -T api alembic upgrade head
            echo "Staging deployed: $(date)"
```

**Required GitHub Secrets:**
- `STAGING_HOST`: Staging server IP or hostname
- `STAGING_USER`: SSH username
- `STAGING_SSH_KEY`: Private SSH key for authentication

### Option 2: Webhook (Simpler, less secure)

1. **Install webhook on staging server**
   ```bash
   sudo apt install webhook -y
   ```

2. **Create webhook configuration**
   ```bash
   sudo cat > /etc/webhook/hooks.json << 'EOF'
   [
     {
       "id": "deploy-staging",
       "execute-command": "/opt/ldapguard-staging/scripts/deploy-staging.sh",
       "command-working-directory": "/opt/ldapguard-staging",
       "response-message": "Deploying to staging...",
       "trigger-rule": {
         "match": {
           "type": "payload-hash-sha256",
           "secret": "YOUR_WEBHOOK_SECRET_HERE",
           "parameter": {
             "source": "header",
             "name": "X-Hub-Signature-256"
           }
         }
       }
     }
   ]
   EOF
   ```

3. **Create deployment script**
   ```bash
   cat > /opt/ldapguard-staging/scripts/deploy-staging.sh << 'EOF'
   #!/bin/bash
   set -e
   
   echo "$(date): Starting staging deployment"
   
   cd /opt/ldapguard-staging
   
   # Pull latest dev branch
   git fetch origin
   git checkout dev
   git pull origin dev
   
   # Rebuild and restart containers
   docker-compose -f docker-compose.staging.yml --env-file .env.staging pull
   docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d --build
   
   # Run migrations
   docker-compose -f docker-compose.staging.yml exec -T api alembic upgrade head
   
   echo "$(date): Staging deployment complete"
   EOF
   
   chmod +x /opt/ldapguard-staging/scripts/deploy-staging.sh
   ```

4. **Start webhook service**
   ```bash
   sudo webhook -hooks /etc/webhook/hooks.json -verbose -port 9000
   ```

5. **Configure GitHub webhook**
   - Go to: https://github.com/keundokki/LDAPGuard/settings/hooks
   - Click "Add webhook"
   - Payload URL: http://your-staging-server:9000/hooks/deploy-staging
   - Content type: application/json
   - Secret: Same as YOUR_WEBHOOK_SECRET_HERE
   - Events: Just the push event
   - Active: ✅

### Option 3: Cron Job (Scheduled Pull)

```bash
# Add to crontab
crontab -e

# Pull and deploy from dev every hour
0 * * * * cd /opt/ldapguard-staging && git pull origin dev && docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d --build && docker-compose -f docker-compose.staging.yml exec -T api alembic upgrade head
```

---

## Environment Comparison

| Feature | Development | Staging | Production |
|---------|-------------|---------|------------|
| **Purpose** | Local coding | Integration testing | Live users |
| **Branch** | Any | `dev` | `main` |
| **Auto-deploy** | No (manual) | Yes (on push to dev) | No (manual release) |
| **Database** | ldapguard_dev | ldapguard_staging | ldapguard |
| **Ports** | 8000, 5432 | 8001, 5433 | 80, 443 |
| **Data** | Test data | Sample data | Real data |
| **SSL** | No | Optional | Required |
| **Monitoring** | No | Basic | Full |
| **Backups** | No | Daily | Hourly |
| **Debug mode** | Yes | Yes | No |

---

## Testing in Staging

### Automated Testing

```bash
# Run tests against staging API
export STAGING_URL=http://staging.ldapguard.yourdomain.com

# Health check
curl $STAGING_URL:8001/health

# Authentication test
curl -X POST $STAGING_URL:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Create LDAP server test
TOKEN="<token_from_login>"
curl -X POST $STAGING_URL:8001/api/ldap-servers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Server",
    "host": "ldap.test.local",
    "port": 389,
    "base_dn": "dc=test,dc=local",
    "bind_dn": "cn=admin,dc=test,dc=local",
    "bind_password": "testpass"
  }'
```

### Manual Testing Checklist

- [ ] Can log in with admin account
- [ ] Can create new user
- [ ] Can add LDAP server
- [ ] Can create backup
- [ ] Can list backups
- [ ] Can download backup
- [ ] Can initiate restore
- [ ] Can view audit logs
- [ ] Can manage API keys
- [ ] UI responsive on mobile
- [ ] No console errors in browser
- [ ] All API endpoints return correct status codes

---

## Monitoring Staging

### Log Access

```bash
# View all logs
docker-compose -f docker-compose.staging.yml logs -f

# API logs only
docker-compose -f docker-compose.staging.yml logs -f api

# Worker logs only
docker-compose -f docker-compose.staging.yml logs -f worker

# Search for errors
docker-compose -f docker-compose.staging.yml logs | grep ERROR

# Last 100 lines
docker-compose -f docker-compose.staging.yml logs --tail=100
```

### Health Monitoring Script

Create `/opt/ldapguard-staging/scripts/health-check.sh`:

```bash
#!/bin/bash

STAGING_URL="http://localhost:8001"
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Check health endpoint
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" $STAGING_URL/health)

if [ "$HEALTH" != "200" ]; then
    MESSAGE="🚨 Staging environment is DOWN! Health check returned: $HEALTH"
    
    # Send to Slack
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"$MESSAGE\"}" \
        $SLACK_WEBHOOK
    
    # Log locally
    echo "$(date): $MESSAGE" >> /var/log/ldapguard-staging-health.log
    
    # Try to restart
    cd /opt/ldapguard-staging
    docker-compose -f docker-compose.staging.yml restart
fi
```

Add to crontab:
```bash
# Check every 5 minutes
*/5 * * * * /opt/ldapguard-staging/scripts/health-check.sh
```

---

## Troubleshooting

### Staging won't start

```bash
# Check if ports are in use
sudo lsof -i :8001
sudo lsof -i :8081
sudo lsof -i :5433

# Check Docker resources
docker system df
docker system prune -a  # Free up space

# Rebuild from scratch
docker-compose -f docker-compose.staging.yml down -v
docker-compose -f docker-compose.staging.yml up -d --build --force-recreate
```

### Database migration fails

```bash
# Check current migration version
docker-compose -f docker-compose.staging.yml exec api alembic current

# Stamp to specific version
docker-compose -f docker-compose.staging.yml exec api alembic stamp head

# Retry migration
docker-compose -f docker-compose.staging.yml exec api alembic upgrade head
```

### Auto-deployment not working

```bash
# Check webhook logs
sudo journalctl -u webhook -f

# Test deployment script manually
/opt/ldapguard-staging/scripts/deploy-staging.sh

# Check GitHub webhook deliveries
# Go to: Settings → Webhooks → Recent Deliveries

# Verify SSH key for GitHub Actions
ssh -T git@github.com
```

---

## Best Practices

### Data Management

1. **Reset staging data weekly**
   ```bash
   docker-compose -f docker-compose.staging.yml down -v
   docker-compose -f docker-compose.staging.yml up -d
   docker-compose -f docker-compose.staging.yml exec api alembic upgrade head
   ```

2. **Use test data fixtures**
   ```bash
   docker-compose -f docker-compose.staging.yml exec api python scripts/seed_test_data.py
   ```

3. **Never use production data**
   - Use anonymized/synthetic data
   - GDPR compliance

### Security

1. **Keep staging isolated**
   - Don't connect to production LDAP servers
   - Use test credentials only
   - Different encryption keys

2. **Limit access**
   - IP whitelist if possible
   - HTTP Basic Auth for public staging
   - Disable user registration

3. **Regular updates**
   - Update dependencies monthly
   - Apply security patches immediately

### Performance

1. **Monitor resource usage**
   ```bash
   docker stats
   ```

2. **Scale if needed**
   ```bash
   docker-compose -f docker-compose.staging.yml up -d --scale worker=3
   ```

---

## Maintenance

### Weekly Tasks

- [ ] Review staging logs for errors
- [ ] Test latest dev branch changes
- [ ] Verify auto-deployment working
- [ ] Check disk space usage
- [ ] Update dependencies if needed

### Monthly Tasks

- [ ] Full staging environment rebuild
- [ ] Review and update staging documentation
- [ ] Audit staging access logs
- [ ] Performance testing
- [ ] Backup retention cleanup

---

**Last Updated:** February 5, 2026  
**Maintained By:** GitHub Copilot
