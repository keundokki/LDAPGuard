# Infrastructure Requirements for LDAPGuard Environments

## Environment Architecture

```
Developer Machine (Local)
    ↓ git push
GitHub (Code + CI/CD)
    ↓ on push to dev (auto-deploy)
Staging Server
    ↓ manual PR/merge
    ↓ on push to main (manual deploy)
Production Server
```

---

## 1. Development Environment (LOCAL)

### Current Setup
- ✅ docker-compose.dev.yml with volume mounts
- ✅ Live code reload
- ✅ Local PostgreSQL (port 5433)
- ✅ Local Redis (port 6380)
- ✅ Pre-push git hook for tests

### Requirements
- **Machine**: Any laptop/desktop
- **Software**: 
  - Podman/Docker
  - Git
  - Python 3.11+
  - Optional: pytest, black, flake8 for local testing
- **Resources**:
  - 2+ CPU cores
  - 4GB+ RAM
  - 10GB disk space

### Cost: $0 (your machine)

---

## 2. Staging Environment (TESTING)

### Current Setup
- ✅ docker-compose.staging.yml
- ✅ GitHub Actions auto-deployment
- ✅ Separate database/redis
- ✅ Health checks

### Requirements
- **Machine Type**: Small Linux server
  - Ubuntu 20.04+ or similar
  - 2 CPU cores
  - 4GB RAM
  - 20GB disk space (includes backup test data)

### Network Setup
```
Internet
    ↓
Firewall (Port 80/443)
    ↓
Nginx/Reverse Proxy
    ↓
Docker Services (API on 8001, Web on 8081)
```

### Services Running
- PostgreSQL 15 (separate from production)
- Redis 7 (separate from production)
- API (8001)
- Worker (background tasks)
- Web UI (8081)

### Cost Examples
- **AWS EC2 t3.medium**: ~$30/month
- **Digital Ocean**: ~$12-24/month
- **Linode**: ~$12-24/month
- **On-premises**: ~$100-300 hardware + electricity

---

## 3. Production Environment (LIVE)

### Requirements
- **Machine Type**: Medium Linux server
  - Ubuntu 20.04+ or similar
  - 4+ CPU cores
  - 8GB+ RAM
  - 50GB+ disk space (includes backups)
  - SSD recommended

### Network Setup
```
Internet
    ↓
Firewall (Port 80/443 ONLY)
    ↓
Nginx/Reverse Proxy (SSL/TLS)
    ↓
Docker Services (API on 127.0.0.1:8000)
    ↓
PostgreSQL (127.0.0.1 only)
    ↓
Redis (127.0.0.1 only)
```

### Services Running
- PostgreSQL 15 (production data)
- Redis 7 (production task queue)
- API (internal only)
- Worker (background tasks)
- Web UI (internal only)
- Nginx reverse proxy (external)

### Additional Components
- SSL/TLS certificates (Let's Encrypt)
- Firewall configuration
- Backup automation
- Log aggregation (optional)
- Monitoring/alerting (optional)

### Cost Examples
- **AWS EC2 t3.large**: ~$60/month
- **Digital Ocean**: ~$24-48/month
- **Linode**: ~$24-48/month
- **On-premises**: ~$500-1000 hardware + electricity

---

## Database Strategy

### Development
```
Local PostgreSQL (ldapguard_dev)
↓
Test data only
↓
Reset frequently
```

### Staging
```
Staging PostgreSQL (ldapguard_staging)
↓
Sample/synthetic data
↓
Can be reset between test cycles
```

### Production
```
Production PostgreSQL (ldapguard)
↓
Real LDAP backup data
↓
CRITICAL - backed up hourly
↓
Encrypted and isolated
```

---

## Minimum Setup (Small Deployment)

### Option 1: All-in-One (Cheapest)
```
Single Server (4 CPU, 8GB RAM, 50GB disk)
├── PostgreSQL
├── Redis
├── API
├── Worker
├── Web UI
└── Nginx

Cost: $30-50/month
Pros: Simple, cheap
Cons: Single point of failure
```

### Option 2: Separate Staging + Production (Recommended)
```
Staging Server (2 CPU, 4GB RAM, 20GB)    Cost: $12-24/month
├── PostgreSQL (test data)
├── Redis
├── API
├── Worker
└── Web UI

Production Server (4 CPU, 8GB RAM, 50GB) Cost: $30-50/month
├── PostgreSQL (real data, backups)
├── Redis
├── API
├── Worker
├── Web UI
└── Nginx (SSL/TLS)

Total: $50-75/month
Pros: Isolated testing, production stability
Cons: Double the cost
```

### Option 3: Highly Available Production (Enterprise)
```
Staging (2 CPU, 4GB, 20GB)                $12-24/month

Production Primary (4 CPU, 8GB, 50GB)     $30-50/month
├── PostgreSQL + replication
├── Redis + sentinel
├── API + Load Balancer
└── Worker

Production Backup (4 CPU, 8GB, 50GB)      $30-50/month
├── PostgreSQL replica
├── Redis replica
└── Standby services

Total: $75-150/month
Pros: High availability, disaster recovery
Cons: Complex, expensive
```

---

## Current Status

| Component | Dev | Staging | Production |
|-----------|-----|---------|------------|
| Docker config | ✅ dev.yml | ✅ staging.yml | ✅ docker-compose.yml |
| Auto-deploy | Manual | ✅ GitHub Actions | Manual (SSH) |
| CI/CD tests | ✅ Pre-push hook | ✅ GitHub Actions | ✅ GitHub Actions |
| Database | Local | Separate | Separate |
| Backup script | ❌ | ⏳ Needed | ✅ Required |
| Monitoring | No | Optional | Recommended |
| SSL/TLS | No | Optional | Required |

---

## Recommended Next Steps

### Immediate (This week)
1. Set up staging server (smallest option)
2. Configure GitHub Actions secrets
3. Test auto-deployment workflow

### Short-term (This month)
1. Finalize production server specs
2. Configure backups (PostgreSQL → S3 or similar)
3. Set up SSL certificates
4. Configure monitoring/alerts

### Medium-term (This quarter)
1. Add log aggregation (optional)
2. Set up health monitoring
3. Document runbooks
4. Train ops team

---

## Cost Breakdown (Recommended Setup)

| Component | Cost/Month |
|-----------|-----------|
| Staging server | $18 |
| Production server | $40 |
| SSL cert | $0 (Let's Encrypt) |
| Backups (optional S3) | $2-5 |
| Monitoring (optional) | $5-10 |
| **Total** | **$65-75** |

---

## Questions for You

1. **Do you have existing servers?** (On-premises or cloud)
2. **What's your hosting provider preference?** (AWS, DigitalOcean, Linode, on-prem)
3. **How many users will staging need to support?** (Affects sizing)
4. **Do you need high availability?** (Affects production architecture)
5. **Budget constraints?** (Affects choices)

Based on your answers, I can create:
- Staging server setup guide
- Production deployment guide
- Backup/disaster recovery plan
- Monitoring configuration
