# Test LDAP Data & Scenarios

## Overview

This guide provides LDIF (LDAP Data Interchange Format) files to populate your test LDAP servers with realistic data mirroring a production environment.

---

## Test Data Structure

### Corporate LDAP (5,000 users)
```
dc=corporate,dc=test
├── ou=departments
│   ├── ou=engineering (800 users)
│   ├── ou=sales (600 users)
│   ├── ou=marketing (400 users)
│   ├── ou=finance (300 users)
│   ├── ou=hr (200 users)
│   └── ou=operations (700 users)
├── ou=groups
│   ├── cn=admin-group (50 members)
│   ├── cn=dev-team (200 members)
│   ├── cn=sales-team (150 members)
│   └── [196 more groups]
└── ou=users (5,000 users total)
```

**Total Size**: ~2GB

---

### Finance LDAP (1,500 users)
```
dc=finance,dc=test
├── ou=departments
│   ├── ou=accounting (400 users)
│   ├── ou=audit (200 users)
│   ├── ou=treasury (300 users)
│   ├── ou=payroll (300 users)
│   └── ou=compliance (300 users)
├── ou=groups
│   ├── cn=cfo-office (25 members)
│   ├── cn=accountants (100 members)
│   └── [48 more groups]
└── ou=users (1,500 users total)
```

**Total Size**: ~800MB

---

### HR LDAP (1,000 users)
```
dc=hr,dc=test
├── ou=departments
│   ├── ou=recruitment (150 users)
│   ├── ou=benefits (100 users)
│   ├── ou=payroll-admin (150 users)
│   ├── ou=employee-relations (300 users)
│   └── ou=training (300 users)
├── ou=groups
│   ├── cn=hr-managers (30 members)
│   ├── cn=recruiters (50 members)
│   └── [18 more groups]
└── ou=users (1,000 users total)
```

**Total Size**: ~400MB

---

## Setup Procedure

### 1. Create Base LDAP Entries

**File: corporate.ldif**
```ldif
version: 1

# Corporate DC
dn: dc=corporate,dc=test
objectClass: dcObject
objectClass: organization
dc: corporate
o: Corporate Directory

# Engineering Department
dn: ou=departments,dc=corporate,dc=test
objectClass: organizationalUnit
ou: departments

dn: ou=engineering,ou=departments,dc=corporate,dc=test
objectClass: organizationalUnit
ou: engineering
description: Engineering Department

# Sample Users (create 800 for engineering)
dn: uid=eng001,ou=engineering,ou=departments,dc=corporate,dc=test
objectClass: inetOrgPerson
objectClass: posixAccount
uid: eng001
cn: John Engineer
sn: Engineer
givenName: John
mail: john.engineer@corporate.test
userPassword: {SSHA}password_hash_here
uidNumber: 10001
gidNumber: 1000
homeDirectory: /home/eng001
```

### 2. Bulk Load Data

```bash
# Load corporate LDAP
ldapadd -x -D "cn=admin,dc=corporate,dc=test" \
  -w admin_password -f corporate.ldif

# Load finance LDAP
ldapadd -x -D "cn=admin,dc=finance,dc=test" \
  -w admin_password -f finance.ldif

# Load HR LDAP
ldapadd -x -D "cn=admin,dc=hr,dc=test" \
  -w admin_password -f hr.ldif
```

---

## Test Scenarios

### Scenario 1: Daily Backup Testing (Week 1-2)

**Objective**: Establish baseline backup procedures

```
Day 1: Initial full backup
  - Corporate: 2.0GB (5000 users)
  - Finance: 0.8GB (1500 users)
  - HR: 0.4GB (1000 users)
  Total: 3.2GB

Days 2-7: Daily backups
  Incremental changes simulated:
  - Add 50 users per day to Corporate
  - Add 20 users per day to Finance
  - Add 10 users per day to HR
  Daily incremental: 50-100MB
```

**Validation**:
- ✅ All 3 directories backup successfully
- ✅ Backup files created in correct location
- ✅ Backup metadata recorded in PostgreSQL
- ✅ Backup files encrypted

### Scenario 2: Point-in-Time Recovery (Week 2-3)

**Objective**: Verify ability to recover to specific point in time

```
Setup:
  - Create backups for 7 consecutive days
  - On Day 8: Delete 500 users from Corporate
  - Request: Restore Corporate to Day 7 state

Test Steps:
  1. Create manual restore point
  2. Select Corporate LDAP directory
  3. Choose Day 7 backup
  4. Perform selective restore
  5. Verify 500 deleted users restored
  6. Verify no data loss
```

**Success Criteria**:
- ✅ Restore completes in < 3 minutes
- ✅ All 500 users present after restore
- ✅ User attributes match backup
- ✅ Groups/memberships correct

### Scenario 3: Selective Restore (Week 3-4)

**Objective**: Restore only specific data (users, departments, groups)

```
Test 3a: Single User Restore
  - Delete: uid=eng001,ou=engineering...
  - Restore just this user
  - Verify user restored with all attributes

Test 3b: Department Restore
  - Delete: ou=finance,ou=departments...
  - Restore entire Finance department (300 users)
  - Verify structure and all users

Test 3c: Group Restore
  - Delete: cn=admin-group...
  - Restore just this group
  - Verify members intact
```

**Success Criteria**:
- ✅ Single user restore works
- ✅ Department restore works
- ✅ Group restore works
- ✅ Relationships maintained

### Scenario 4: Disaster Recovery (Week 5)

**Objective**: Simulate complete LDAP server failure

```
Setup:
  - Run normal backups for 30 days
  - Simulate VM1 failure (all LDAP data lost)

Recovery Steps:
  1. Create new test LDAP servers
  2. For each directory (Corporate, Finance, HR):
     - Initiate full restore from latest backup
     - Verify all entries present
     - Verify all groups present
     - Verify all user attributes
  3. Measure recovery time

Expected Recovery Time:
  - Corporate: 3-5 minutes (2GB)
  - Finance: 1-2 minutes (800MB)
  - HR: < 1 minute (400MB)
  Total: < 10 minutes
```

**Success Criteria**:
- ✅ All 3 directories fully recovered
- ✅ Zero data loss
- ✅ Recovery time < 10 minutes
- ✅ No manual intervention needed

### Scenario 5: Encryption Verification (Week 4)

**Objective**: Verify backup encryption

```
Test 5a: Encrypted File Check
  - Check backup file content
  - File should be unreadable (binary/encrypted)
  - Should not contain readable LDIF content

Test 5b: Restore from Encrypted Backup
  - Perform restore from encrypted backup
  - Restore should work normally
  - Decryption should be transparent
  - Data integrity verified

Test 5c: Key Rotation (Advanced)
  - Change encryption key in config
  - Attempt restore with old backup
  - Should fail with "unable to decrypt"
  - Switch back to original key
  - Restore should work
```

**Success Criteria**:
- ✅ Backups are encrypted
- ✅ Encrypted backups not readable
- ✅ Restore from encrypted works
- ✅ Key rotation verified

### Scenario 6: Retention Policy (Week 5-6)

**Objective**: Verify backup retention and cleanup

```
Setup:
  - Create backups for 60 days
  - Configure 30-day retention policy
  - Apply retention policy

Verification:
  - Backups 1-30: Should be DELETED
  - Backups 31-60: Should be RETAINED
  - Verify correct backups removed
  - Verify storage space freed (~96GB)
```

**Success Criteria**:
- ✅ Old backups deleted
- ✅ New backups retained
- ✅ Storage space freed
- ✅ No valid backups deleted by mistake

---

## Test Data Generation Script

```bash
#!/bin/bash
# generate_test_data.sh

# Install prerequisites
sudo apt install -y slapd ldap-utils

# Create corporate.ldif (5000 users)
cat > corporate.ldif << 'LDIF'
version: 1
dn: dc=corporate,dc=test
objectClass: dcObject
objectClass: organization
dc: corporate
o: Corporate Directory
LDIF

# Generate 5000 user entries
for i in {1..5000}; do
  printf -v uid "user%05d" $i
  cat >> corporate.ldif << LDIF

dn: uid=$uid,ou=users,dc=corporate,dc=test
objectClass: inetOrgPerson
uid: $uid
cn: Test User $i
sn: User
givenName: Test
mail: $uid@corporate.test
userPassword: {SSHA}W2K0MKssfbwCXvNW9PmXIUyadPc=
LDIF
done

# Similar for finance.ldif (1500 users) and hr.ldif (1000 users)
```

---

## Monitoring Test Progress

```bash
# Count entries in each directory
ldapsearch -x -b "dc=corporate,dc=test" -D "cn=admin,dc=corporate,dc=test" \
  -w password | grep "^dn:" | wc -l

# Check backup status in LDAPGuard
curl http://localhost:8001/api/backups

# Monitor backup storage
du -sh /opt/ldapguard/backups/

# Check database for backup metadata
psql ldapguard -c "SELECT directory, created_at, status, size FROM backups;"
```

---

## Success Metrics

After 6 weeks, document:
- ✅ Total backups created: _____
- ✅ Total data backed up: _____ GB
- ✅ Restore success rate: _____%
- ✅ Average backup time: _____ minutes
- ✅ Average restore time: _____ minutes
- ✅ Zero data loss incidents: Yes/No
- ✅ Encryption verification: Passed/Failed
- ✅ Retention policy working: Yes/No

---

## Next: Automation Scripts

Ready for me to create:
1. **Automatic backup scheduling** (cron jobs)
2. **Restore automation** (test scripts)
3. **Data generation** (LDIF generators)
4. **Monitoring dashboards** (Prometheus/Grafana)
