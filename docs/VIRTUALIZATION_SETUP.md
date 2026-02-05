# Virtualization Setup for LDAPGuard - 3 VM Architecture

## Your Infrastructure

**Hardware**: 24 cores, 64GB RAM, 1TB storage (KVM)

---

## VM Layout (3 Separate VMs)

```
Physical Host (24 CPU, 64GB RAM, 1TB storage)
│
├── VM1: Staging LDAPGuard (4 CPU, 8GB RAM, 50GB storage)
│   ├── PostgreSQL (staging)
│   ├── Redis
│   ├── API + Worker + Web UI
│   └── Mock OpenLDAP (Docker)
│
├── VM2: Production LDAPGuard (6 CPU, 16GB RAM, 150GB storage)
│   ├── PostgreSQL (production)
│   ├── Redis
│   ├── API + Worker + Web UI
│   └── Nginx reverse proxy
│
└── VM3: Production LDAP (2 CPU, 4GB RAM, 20GB storage)
    └── OpenLDAP installed directly on the VM (no containers)
```

**Resource Allocation**:
- CPU: 12 of 24 cores (50%)
- RAM: 28GB of 64GB (44%)
- Storage: 220GB of 1TB (22%)

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

### 2. Install LDAPGuard (VM1 + VM2)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
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

# Start mock LDAP first
docker-compose -f docker-compose.ldap.yml up -d

# Copy staging config
cp .env.example .env.staging
nano .env.staging

# Start staging LDAPGuard
docker-compose -f docker-compose.staging.yml up -d

# Verify
docker-compose -f docker-compose.ldap.yml ps
docker-compose -f docker-compose.staging.yml ps
```

### 4. Install OpenLDAP on VM3 (Production LDAP)

```bash
sudo apt update && sudo apt install -y slapd ldap-utils

# Reconfigure (optional)
sudo dpkg-reconfigure slapd

# Verify
ldapwhoami -H ldap://localhost -D cn=admin,dc=production,dc=local -W
```

### 5. Deploy Production LDAPGuard (VM2)

```bash
git checkout main
git pull origin main

cp .env.example .env
nano .env

# Point LDAPGuard to VM3 IP (example: LDAP_HOST=192.168.x.50)

docker-compose up -d
docker-compose ps
```

---

## Configuration

### Staging `.env.staging`
```
SECRET_KEY=staging-secret
ENCRYPTION_KEY=staging-key-base64==
LDAP_HOST=openldap
LDAP_PORT=389
LDAP_BIND_DN=cn=admin,dc=test,dc=local
LDAP_PASSWORD=admin
POSTGRES_PASSWORD=staging-pass
```

### Production `.env`
```
SECRET_KEY=prod-secret-key
ENCRYPTION_KEY=prod-key-base64==
LDAP_HOST=192.168.x.50      # VM3 IP address
LDAP_PORT=389
LDAP_BIND_DN=cn=admin,dc=production,dc=local
LDAP_PASSWORD=prod-admin-password
POSTGRES_PASSWORD=prod-pass
```

---

## Access Points

| Component | URL | VM |
|---|---|---|
| Staging Web UI | http://staging-vm:8081 | VM1 |
| Staging API | http://staging-vm:8001 | VM1 |
| Staging LDAP | openldap:389 (internal) | VM1 |
| Production Web UI | http://prod-vm | VM2 |
| Production API | http://prod-vm:8000 | VM2 |
| Production LDAP | prod-ldap-vm:389 | VM3 |

---

## Next Steps

1. Create 3 VMs with specified resources
2. Deploy Staging (VM1) with mock LDAP
3. Install OpenLDAP on VM3
4. Deploy Production LDAPGuard (VM2) pointing to VM3
5. Run tests: See [TEST_SCENARIOS_SIMPLE.md](TEST_SCENARIOS_SIMPLE.md)
# Virtualization Setup for LDAPGuard - 3 VM Architecture

## Your Infrastructure

**Hardware**: 24 cores, 64GB RAM, 1TB storage (KVM)

---

## VM Layout (3 Separate VMs)

```
Physical Host (24 CPU, 64GB RAM, 1TB storage)
│
├── VM1: Staging LDAPGuard (4 CPU, 8GB RAM, 50GB storage)
│   ├── PostgreSQL (staging)
│   ├── Redis
│   ├── API + Worker + Web UI
│   └── Mock OpenLDAP (included)
│
├── VM2: Production LDAPGuard (6 CPU, 16GB RAM, 150GB storage)
│   ├── PostgreSQL (production)
│   ├── Redis
│   ├── API + Worker + Web UI
│   └── Nginx reverse proxy
│
└── VM3: Production LDAP (2 CPU, 4GB RAM, 20GB storage)
    └── OpenLDAP (real data, separate)
```

**Resource Allocation**:
- CPU: 12 of 24 cores (50%)
- RAM: 28GB of 64GB (44%)
- Storage: 220GB of 1TB (22%)
- Remaining: Headroom for host, snapshots, expansion

---

## Set## Set## Set## Set## Set## Set## Set## Set## Set## Set## Set## Set## Set## Set## Set## Set## Set l## Set## Set## Set## Set## Set## Set## Set## Set## Sisk si## Set## Set## Set## t u## Set## Set## Set## Set## Set## Set## Set## Set## none --## Set## Set## Set## Set## S

**VM2**VM2**VM2**VM2**VM2**VM2**VM2**VM2**VM2**VMas*
virt-install --name ldapguard-prod \
  --memory 16384 --vcpus 6 \
  --disk size=150 \
  --os-variant ub  --os-variant ub  -or  --os-variant ub  --os-variant ub  er  --os-variant ub  --os-variant ub  -or*    C  --os-variant ub  --os-variant ub  -or  --os-variant ub  --os-vari-m  --os-variant ub  --os-variisk size=20   --os-variant ub  -nt  --os-variant ub  --os-variant ub  --graphics none --serial pty --console pty  --os-variant ub  --os-variant ub  -or  --os-variant ub  --o   --os-variant ub  --os-variant ub  -or  --l Docke  --os-variant ub  //get.  --os-variant ub  --os-vah
  --os-variant ub  --os- I  --os-variant ub  --os- I  pt  --os-variant ub  --os- I  --os-variant ub  --os- do   t c  --os-variant ub  --os- I  --os-variPGuard.git
sudo chown -R $USER:$USER LDAPGuard
cd LDAPGuard
```

### 3. Deploy Staging (VM1)

```bash
git checkout dev
git pull origin dev

# Start mock LDAP first
docker-compose -f docker-compose.ldap.yml up -d

# Copy staging config
cpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcrtcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcf cpcpcpcpcpcpcpcpcpcpcpcpcp upcpcpcpcpcpcpcpcpcprucpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcrtcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcf cpcpcpcpcpcpcpcpcpcpcpcpcp upcpcpcpcpcpcpcpcpcprucpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcrtcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcf cpcpcpcpcpcpcpcpcpcpcpcpcp upcpcpcpcpcpcpcpcpcprucpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcrtcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcf cpcpcpcpcpcpcpcpcpcpcpcpcp upcpcpcpcpcpcpcpcpcprucpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcrtcpcpcpcpcpcpcpcponcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcrtcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcf cpcpcpcpcpcpcpcpcpcpcpcpcp upcpcpcpcpcpcpcpcpcprucpcpcpcpcpcpcpcpcpcpomcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcpcp


pcpcpcpcpc `.env.pcpcpcp`
```
SECRET_KEY=stagiSECRETreSECRET_KEY=stagY=SECRET_KEY=stagiSE==
SECRET_KEY=stagiSECRET      # Local docker hostname
LDAP_PORT=389
LDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BILDAP_BstLDAP_BILDAP_BILDAP_BIdge=LDAP_BILDAP_BILDAP_BILDAhes LDAP via local docker network
- Production → reaches LDAP via - Production → reaches LDAP via - Production →--- ProductioSteps

1. Create 3 VMs with specified resources
2. Deploy Staging (VM1) with mock LDAP
3. Deploy Production LDAP (VM3)
4. Deploy Production LDAPGuard (VM2) pointing to VM3
5. Run tests: See [TEST_SCENARIOS_SIMPLE.md](TEST_SCENARIOS_SIMPLE.md)

