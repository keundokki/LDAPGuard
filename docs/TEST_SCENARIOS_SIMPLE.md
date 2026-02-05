# Testing LDAPGuard - Staging with Mock LDAP, Production Ready

## Environment Setup

**Staging**: Mock OpenLDAP + LDAPGuard (dev/testing)
**Production**: LDAPGuard only (add real LDAP servers via UI)

---

## Staging: Add Mock LDAP Server via Web UI

### Access Staging
```
Web UI: http://staging-vm:8081
API: http://staging-vm:8001
```

### Add Test LDAP Server

1. Login (admin/admin)
2. LDAP Servers → Add Server
3. Fill in:
   - **Name**: Test LDAP
   - **Host**: openldap (docker container name on staging)
   - **Port**: 389
   - **Bind DN**: cn=admin,dc=test,dc=local
   - **Bind Password**: admin
   - **Base DN**: dc=test,dc=local

4. Click "Test Connection"
   - Should succeed ✅

---

## Test 1: Connection Test

### Verify Mock LDAP is accessible

```bash
# From inside staging network
docker exec ldapguard-staging-ldap ldapwhoami \
  -H ldap://localhost \
  -D cn=admin,dc=test,dc=local \
  -w admin

# Should show: dn:cn=admin,dc=test,dc=local
```

### Success
✅ Connection successful from LDAPGuard

---

## Test 2: Manual Backup

## Test 2: Manual Backup

### Create backup of mock LDAP

```bash
# Get token
TOKEN=$(curl -X POST http://staging-vm:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  | jq -r '.access_token')

# Create backup
curl -X POST http://staging-vm:8001/api/backups \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ldap_server_id": 1, "backup_name": "test-backup-1"}'

# List backups
curl http://staging-vm:8001/api/backups \
  -H "Authorization: Bearer $TOKEN"
```

### Success
✅ Backup created (encrypted .enc file)
✅ Status shows "completed"
✅ Timestamp recorded

---

## Test 3: List Users from LDAP

### Query test data in LDAPGuard

```bash
# Get users from LDAP (via LDAPGuard)
curl http://staging-vm:8001/api/ldap-servers/1/users \
  -H "Authorization: Bearer $TOKEN"

# Expected: 8 users (alice, bob, charlie, diana, eve, frank, grace, testadmin)
```

### Success
✅ Users listed from mock LDAP
✅ All 8 test users visible

---

## Test 4: Restore Backup

## Test 4: Restore Backup

### Test restoration

```bash
# Get backup ID (from Test 2)
BACKUP_ID=1

# Initiate restore
curl -X POST http://staging-vm:8001/api/restores \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"backup_id": '$BACKUP_ID', "target_ldap_server_id": 1}'

# Check restore status
curl http://staging-vm:8001/api/restores \
  -H "Authorization: Bearer $TOKEN"
```

### Success
✅ Restore initiated
✅ Status shows "completed"
✅ No errors in logs

---

## Test 5: Rate Limiting

## Test 5: Rate Limiting

### Verify rate limiting works

```bash
# Try 6 rapid login attempts
for i in {1..6}; do
  curl -X POST http://staging-vm:8001/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"wrong"}' \
    -w "\nAttempt $i: HTTP %{http_code}\n" \
    -s -o /dev/null
done

# Expected: 200/401 on first 5, then 429 on 6th
```

### Success
✅ First 5 requests: 200 or 401 (normal)
✅ 6th request: 429 (rate limited)

---

## Test 6: Check Encryption

## Test 6: Check Encryption

### Verify backups are encrypted

```bash
# List backup files
docker exec ldapguard-staging-api ls -la /backups/

# File should be .enc (encrypted)
# Attempt to read raw file (should be gibberish)
docker exec ldapguard-staging-api file /backups/backup_*.enc
# Expected: "data" (binary, not LDIF)

# Verify restore still works (decryption works)
# Re-run Test 4 above
```

### Success
✅ Backup files are .enc
✅ Raw file is binary/unreadable
✅ Restore successfully decrypts

---

## Production: Add OpenLDAP Server via Web UI

### Connect Production to OpenLDAP

1. SSH to production VM
2. Access web UI: http://prod-vm
3. Add OpenLDAP server:
   - **Name**: Production LDAP
   - **Host**: openldap (docker container name on production)
   - **Port**: 389
   - **Bind DN**: cn=admin,dc=production,dc=local
   - **Bind Password**: (value from LDAP_ADMIN_PASSWORD env var, default: admin)
   - **Base DN**: dc=production,dc=local

4. Click "Test Connection"
   - Should succeed ✅

### Test with Production Data

Once connected, all tests (1-6 above) work identically on production:
- Backups of production LDAP data
- Restores to production LDAP servers
- Encryption of production data
- Rate limiting active
- All security features working

---

## Quick Setup Reference

### Start LDAP (once)
```bash
docker-compose -f docker-compose.ldap.yml up -d
```

### Staging VM
```bash
# Deploy
git checkout dev
docker-compose -f docker-compose.staging.yml up -d

# Access
API: http://staging-vm:8001
Web: http://staging-vm:8081
Mock LDAP: localhost:389 (internal hostname: openldap)
```

### Production VM
```bash
# Deploy
git checkout main
docker-compose up -d

# Access
API: http://prod-vm:8000
Web: http://prod-vm:80
OpenLDAP: localhost:389 (internal hostname: openldap)
```

---

## Test 6: Production Environment

### Steps
```bash
# SSH to prod VM
ssh user@prod-vm

# Check services
docker-compose ps
# All containers should show "Up"

# Test API (like Test 1-5 on production)
curl http://prod-vm:8000/api/backups -H "Authorization: Bearer $TOKEN"
```

### Success
✅ All containers running
✅ API responds
✅ Tests 1-5 work identically

---

## Quick Setup Reference

### Staging VM
```bash
# Deploy
git checkout dev
docker-compose -f docker-compose.staging.yml up -d

# Access
API: http://staging-vm:8001
Web: http://staging-vm:8081
DB: localhost:5433
```

### Production VM
```bash
# Deploy
git checkout main
docker-compose up -d

# Access
API: http://prod-vm:8000
Web: http://prod-vm:80
```

---

## If Something Fails

### Staging containers won't start?
```bash
docker-compose -f docker-compose.staging.yml logs api
```

### Can't connect to LDAP (Staging)?
```bash
# Check LDAP container
docker-compose -f docker-compose.ldap.yml ps
docker exec ldapguard-ldap ldapwhoami -H ldap://localhost -D cn=admin,dc=test,dc=local -w admin
```

### Can't connect to LDAP (Production)?
```bash
# Check LDAP container
docker-compose ps | grep ldap
docker exec ldapguard-openldap ldapwhoami -H ldap://localhost -D cn=admin,dc=production,dc=local -w admin
```

### Restore fails?
```bash
# Check database for errors
docker exec ldapguard-staging-db psql -U ldapguard -d ldapguard_staging -c \
  "SELECT * FROM restores ORDER BY created_at DESC LIMIT 1;"
```

### Rate limiting too strict?
Edit [api/core/config.py](api/core/config.py) and adjust:
```python
LOGIN_RATE_LIMIT = "5/minute"  # Change this number
```

---

## Test Data Available in Staging

**Mock LDAP Users** (8 test users):
- alice, bob, charlie (Engineering)
- diana, eve (Finance)
- frank, grace (HR)
- testadmin (Admin account)

**Base DN**: dc=test,dc=local
**Admin**: cn=admin,dc=test,dc=local / password: admin

---

## Done = Ready for Production

Once all 6 tests pass on staging:
✅ Staging works
✅ Production works
✅ Backups created
✅ Restores work
✅ Encryption active
✅ Rate limiting active

You're ready to use real LDAP servers!
