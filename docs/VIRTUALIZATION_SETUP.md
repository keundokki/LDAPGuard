# Virtualization Setup for LDAPGuard - Staging + Production

## Your Infrastructure

**Hardware**: 24 cores, 64GB RAM, 1TB storage (KVM)

---

## Simple VM Layout

Just 2 VMs - Staging and Production:

```
Physical Host (24 CPU, 64GB RAM, 1TB storage)
│
├── VM1: Staging (4 CPU, 8GB RAM, 50GB storage)
│   ├── PostgreSQL (ldapguard_staging)
│   ├── Redis
│   ├── API (port 8001)
│   ├── Worker
│   └── Web UI (port 8081)
│
└── VM2: Production (6 CPU, 16GB RAM, 150GB storage)
    ├── PostgreSQL (ldapguard + backups)
    ├── Redis
    ├── API (port 8000)
    ├── Worker
    ├── Web UI
    └── Nginx reverse proxy
```

**Resource Allocation**:
- CPU: 10 of 24 cores (42%)
- RAM: 24GB of 64GB (37.5%)
- Storage: 200GB of 1TB (20%)
- Remaining: Headroom for host, snapshots

---

## Quick Start

### 1. Create VMs

**VM1: Staging**
```bash
virt-install --name ldapguard-staging \
  --memory 8192 --vcpus 4 \
  --disk size=50 \
  --os-variant ubuntu22.04 \
  --network bridge=br0 \
  --graphics none --serial pty --console pty
```

**VM2: Production**
```bash
virt-install --name ldapguard-prod \
  --memory 16384 --vcpus 6 \
  --disk size=150 \
  --os-variant ubuntu22.04 \
  --network bridge=br0 \
  --graphics none --serial pty --console pty
```

### 2. Install on Each VM

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker/Podman
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install docker-compose
sudo apt install docker-compose -y

# Clone repo
cd /opt
sudo git clone https://github.com/keundokki/LDAPGuard.git
sudo chown -R $USER:$USER LDAPGuard
cd LDAPGuard
```

### 3. Deploy Staging

```bash
git checkout dev
git pull origin dev

# Copy config
cp .env.example .env.staging

# Edit .env.staging with staging values
nano .env.staging

# Start
docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d
```

### 4. Deploy Production

```bash
git checkout main
git pull origin main

# Copy config
cp .env.example .env

# Edit .env with production values
nano .env

# Start
docker-compose up -d
```

---

## Network Setup

**Staging**: VM accessible on port 8001 (API) and 8081 (Web)
**Production**: VM accessible on port 8000 (API) internally, 80/443 via Nginx

```
Host Network
├── Staging VM: 192.168.x.100:8001 (API)
│                192.168.x.100:8081 (Web UI)
│
└── Production VM: 192.168.x.101:8000 (internal)
                   192.168.x.101:80/443 (Nginx external)
```

---

## Testing

### Add Test LDAP Servers in LDAPGuard UI

You can add dummy LDAP servers for testing:

**Via Web UI (http://staging-vm:8081)**:
1. Login as admin
2. Go to LDAP Servers
3. Add server:
   - Name: "Test LDAP 1"
   - Host: "ldap.test.local" (or any host)
   - Port: 389
   - Bind DN/Password: (test credentials)
4. Click "Test Connection" to verify

### Create Manual Backups

```bash
# Create backup
curl -X POST http://staging-vm:8001/api/backups \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ldap_server_id": 1}'
```

### Test Restore

```bash
# List backups
curl http://staging-vm:8001/api/backups \
  -H "Authorization: Bearer YOUR_TOKEN"

# Initiate restore
curl -X POST http://staging-vm:8001/api/restores \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"backup_id": 1}'
```

---

## What You Get

✅ Staging environment for development & testing
✅ Production-like environment for validation
✅ Both running v0.0.5 with security hardening
✅ Automatic deployments from dev → staging
✅ Manual deployment control for production
✅ All encryption, rate limiting, and security features

---

## Next Steps

1. Create VMs in KVM
2. Deploy Staging
3. Deploy Production
4. Test via web UI and API
5. Ready for real LDAP servers when available
