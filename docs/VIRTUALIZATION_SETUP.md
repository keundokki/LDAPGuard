# Virtualization Setup for LDAPGuard - Production Test Scenario

## Your Infrastructure

**Hardware**: 24 cores, 64GB RAM, 1TB storage (KVM)

---

## Recommended VM Layout

### Test Environment Architecture

```
Physical Host (24 CPU, 64GB RAM, 1TB storage)
│
├── VM1: LDAP Test Servers (8 CPU, 16GB RAM, 100GB storage)
│   ├── OpenLDAP-1 (Corporate AD sync)
│   ├── OpenLDAP-2 (Finance AD sync)
│   └── OpenLDAP-3 (HR AD sync)
│
├── VM2: Staging LDAPGuard (4 CPU, 8GB RAM, 50GB storage)
│   ├── PostgreSQL (ldapguard_staging)
│   ├── Redis
│   ├── API (port 8001)
│   ├── Worker
│   └── Web UI (port 8081)
│
└── VM3: Production LDAPGuard (6 CPU, 16GB RAM, 150GB storage)
    ├── PostgreSQL (ldapguard + backups)
    ├── Redis (with sentinel)
    ├── API (port 8000)
    ├── Worker
    ├── Web UI
    └── Nginx reverse proxy
```

**Total Resource Allocation**:
- CPU: 18 of 24 cores (75%)
- RAM: 40GB of 64GB (62.5%)
- Storage: 300GB of 1TB (30%)
- Remaining: Headroom for snapshots, temp storage, host OS

---

## Use Case Scenario: Production Test

### Scenario Overview

**Organization**: Multi-department company with 3 LDAP directories
- **Corporate LDAP**: 5,000 users, 2GB data
- **Finance LDAP**: 1,500 users, 800MB data
- **HR LDAP**: 1,000 users, 400MB data

### Test Objectives

1. ✅ Backup all 3 directories daily
2. ✅ Test point-in-time recovery
3. ✅ Validate selective restore
4. ✅ Simulate disaster recovery
5. ✅ Test backup retention policies
6. ✅ Verify data encryption

---

## VM 1: LDAP Test Servers (8 CPU, 16GB RAM, 100GB)

### Setup Script

```bash
#!/bin/bash
# Create 3 test OpenLDAP servers

# VM1-LDAP Base Configuration
sudo apt update && sudo apt install -y slapd ldap-utils

# Create test organizational structure for each directory
# See: docs/TEST_LDAP_DATA.md for detailed LDIF files
```

### Test Data Structure

**Corporate LDAP** (ou=corporate)
- 5,000 users (cn=user0001 to cn=user5000)
- 50 departments
- 200 groups
- 2GB total data

**Finance LDAP** (ou=finance)
- 1,500 users (cn=user0001 to cn=user1500)
- 10 departments
- 50 groups
- 800MB total data

**HR LDAP** (ou=hr)
- 1,000 users (cn=user0001 to cn=user1000)
- 5 departments
- 20 groups
- 400MB total data

---

## VM 2: Staging LDAPGuard (4 CPU, 8GB RAM, 50GB)

### Purpose
- Testing backup procedures
- Validating restore operations
- Performance testing
- Integration testing with test LDAP servers

### Setup

```bash
# Pull latest dev code
git checkout dev
git pull

# Start staging environment
podman-compose -f docker-compose.staging.yml up -d

# Configure test LDAP connections
# Create 3 LDAP server entries pointing to VM1
```

### Test Workflow

1. **Daily Backups** (automated via scheduler)
   - Corporate: 2GB backup
   - Finance: 800MB backup
   - HR: 400MB backup
   - Total daily: ~3.2GB

2. **Weekly Full Restore Test**
   - Pick random directory
   - Full restore to test environment
   - Validate all entries restored correctly

3. **Monthly Disaster Recovery Test**
   - Simulate VM1 failure
   - Restore all 3 directories
   - Verify data integrity
   - Time recovery process

---

## VM 3: Production LDAPGuard (6 CPU, 16GB RAM, 150GB)

### Purpose
- Production-like environment
- Real deployment testing
- Performance under load
- Backup automation & retention

### Setup

```bash
# Pull from main branch
git checkout main
git pull

# Start production environment
podman-compose up -d

# Configure SSL/TLS with Let's Encrypt (optional for test)
# Set backup retention: 30 days
# Enable automated daily backups
```

### Test Scenarios

1. **Incremental Backups**
   - Day 1: Full backup (3.2GB)
   - Days 2-7: Incremental (50-100MB each)
   - Total week 1: ~4GB

2. **Retention Policy Test**
   - Create backups for 60 days
   - Apply 30-day retention
   - Verify old backups deleted
   - Verify recent backups retained

3. **Point-in-Time Recovery Test**
   - Backup directory on Day 10
   - Modify/delete 100 user entries
   - Restore from Day 9 backup
   - Verify users restored

4. **Selective Restore Test**
   - Restore only Finance department (ou=finance,ou=finance)
   - Restore only specific 10 users
   - Merge into existing LDAP

5. **Encryption Test**
   - Verify backups encrypted (AES-256)
   - Attempt to read raw backup file (should be unreadable)
   - Restore encrypted backup (should work)

---

## Test Schedule

### Week 1: Setup & Baseline
- [ ] Day 1: Deploy VMs
- [ ] Day 2: Create test LDAP data
- [ ] Day 3: First backups
- [ ] Day 4-7: Monitor, verify automatic backups

### Week 2-4: Functional Testing
- [ ] Daily backups running (20-30 backups)
- [ ] Weekly full restore tests
- [ ] Selective restore tests
- [ ] Performance monitoring

### Week 5: Production Simulation
- [ ] Disaster recovery drill
- [ ] 30-day retention policy validation
- [ ] Encryption verification
- [ ] Load testing with multiple concurrent backups

### Week 6: Sign-off
- [ ] Document results
- [ ] Finalize configuration
- [ ] Create runbooks
- [ ] Transition to production

---

## Test Success Criteria

✅ All backups complete successfully
✅ Recovery time < 5 minutes for 2GB backup
✅ Selective restore works (single user, department, etc.)
✅ Encrypted backups unreadable without decryption
✅ Retention policies work correctly
✅ 100% data integrity after restore
✅ No data loss scenarios

---

## Next: Create Detailed Test Data

I can create:
1. **TEST_LDAP_DATA.md** - LDIF files for 3 test directories
2. **TEST_SCENARIOS.md** - Step-by-step test procedures
3. **BACKUP_AUTOMATION.md** - Cron jobs and scheduling
4. **TEST_MONITORING.md** - Health checks and validation

Want me to create these now?
