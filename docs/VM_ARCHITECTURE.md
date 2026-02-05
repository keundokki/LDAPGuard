# VM Architecture: 3 Separate VMs

## Overview

```
Your Host (24 CPU, 64GB RAM, 1TB storage)
│
├── VM1: Staging (4 CPU, 8GB RAM, 50GB storage)
│   └── docker-compose.staging.yml + docker-compose.ldap.yml
│       ├── PostgreSQL
│       ├── Redis
│       ├── LDAPGuard API/Worker/Web
│       └── Mock OpenLDAP
│
├── VM2: Production (6 CPU, 16GB RAM, 150GB storage)
│   └── docker-compose.yml (no LDAP)
│       ├── PostgreSQL
│       ├── Redis
│       ├── LDAPGuard API/Worker/Web
│       └── Nginx reverse proxy
│
└── VM3: Production LDAP (2 CPU, 4GB RAM, 20GB storage)
    └── docker-compose.ldap.prod.yml
        └── OpenLDAP (real production data)
```

---

## VM Specs

| VM | CPU | RAM | Storage | Purpose |
|---|---|---|---|---|
| VM1 (Staging) | 4 | 8GB | 50GB | Development & testing |
| VM2 (Production) | 6 | 16GB | 150GB | Production LDAPGuard |
| VM3 (LDAP) | 2 | 4GB | 20GB | Production OpenLDAP |
| **Total** | **12** | **28GB** | **220GB** | Uses 50% CPU, 44% RAM, 22% storage |

---

## Setup Steps

### 1. Create VMs

**VM1: Staging** (4 CPU, 8GB RAM, 50GB)
```bash
virt-install --name ldapguard-staging \
  --memory 8192 --vcpus 4 \
  --disk size=50 \
  --os-variant ubuntu22.04 \
  --network bridge=br0 \
  --graphics none --serial pty --console pty
```

**VM2: Production** (6 CPU, 16GB RAM, 150GB)
```bash
virt-install --name ldapguard-prod \
  --memory 16384 --vcpus 6 \
  --disk size=150 \
  --os-variant ubuntu22.04 \
  --network bridge=br0 \
  --graphics none --serial pty --console pty
```

**VM3: LDAP** (2 CPU, 4GB RAM, 20GB)
```bash
virt-install --name ldapguard-ldap \
  --memory 4096 --vcpus 2 \
  --disk size=20 \
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

### 3. Deploy Staging (VM1)

```bash
git checkout dev
git pull origin dev

# Start LDAP first
docker-compose -f docker-compose.ldap.yml up -d

# Copy staging config
cp .env.example .env.staging

# Edit with staging values
nano .env.staging

# Start staging LDAPGuard
docker-compose -f docker-compose.staging.yml up -d

# Verify
docker-compose -f docker-compose.ldap.yml ps
docker-compose -f docker-compose.staging.yml ps
```

### 4. Deploy Production LDAP (VM3)

```bash
git checkout main
git pull origin main

# Copy LDAP config
cp .env.example .env.ldap

# Edit with production LDAP settings
nano .env.ldap

# Start LDAP
docker-compose -f docker-compose.ldap.prod.yml up -d

# Verify
docker-compose -f docker-compose.ldap.prod.yml ps
```

### 5. Deploy Production LDAPGuard (VM2)

```bash
git checkout main
git pull origin main

# Copy production config
cp .env.example .env

# Edit .env with:
# - LDAP host: ldap-vm-ip-or-hostname:389
# - DB password
# - Secret keys
nano .env

# Start production LDAPGuard
docker-compose up -d

# Verify
docker-compose ps
```

---

## Network Configuration

### Staging (VM1)
- API: `http://staging-vm:8001`
- Web: `http://staging-vm:8081`
- Mock LDAP: `localhost:389` (internal)

### Production LDAP (VM3)
- OpenLDAP: `production-ldap-vm:389`
- Bind DN: `cn=admin,dc=production,dc=local`

### Production (VM2)
- Connects to: `production-ldap-vm:389`
- API: `http://prod-vm:8000`
- Web: `http://prod-vm:80`

---

## Connectivity

**VM1 (Staging)** → **Internal LDAP** (same VM)
- All in one docker-compose network
- Direct hostname: `openldap:389`

**VM2 (Production)** → **VM3 (LDAP)**
- Network connection over LAN
- Use VM3 IP or hostname in `.env`
- Example: `LDAP_HOST=192.168.x.50`

---

## Configuration Example

### Staging `.env.staging`
```
SECRET_KEY=staging-secret-key
ENCRYPTION_KEY=staging-encryption-key-base64==
LDAP_HOST=openldap          # Local docker hostname
LDAP_PORT=389
LDAP_BIND_DN=cn=admin,dc=test,dc=local
LDAP_PASSWORD=admin
POSTGRES_PASSWORD=staging-password
ALLOWED_ORIGINS=http://localhost:8081
```

### Production LDAP `.env.ldap`
```
LDAP_ADMIN_PASSWORD=prod-admin-password
LDAP_CONFIG_PASSWORD=prod-config-password
```

### Production `.env`
```
SECRET_KEY=prod-secret-key-change-me
ENCRYPTION_KEY=prod-encryption-key-base64==
LDAP_HOST=192.168.x.50      # VM3 IP address
LDAP_PORT=389
LDAP_BIND_DN=cn=admin,dc=production,dc=local
LDAP_PASSWORD=prod-admin-password
POSTGRES_PASSWORD=prod-password
ALLOWED_ORIGINS=https://ldapguard.example.com
```

---

## Testing

See [TEST_SCENARIOS_SIMPLE.md](TEST_SCENARIOS_SIMPLE.md) for test procedures.

Test on Staging first, then replicate on Production once verified.

---

## Summary

✅ Staging: All-in-one with mock LDAP (easy testing)
✅ Production: Separate LDAPGuard and LDAP (scalability)
✅ Isolation: Each service on dedicated VM
✅ Resources: Total 12 CPU, 28GB RAM (50% utilization)
