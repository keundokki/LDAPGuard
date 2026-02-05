# Testing Staging + Production LDAPGuard

Just 6 simple tests to verify everything works.

---

## Test 1: Manual Backup

### Steps
```bash
# Get API token
TOKEN=$(curl -X POST http://staging-vm:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  | jq -r '.access_token')

# Create backup
curl -X POST http://staging-vm:8001/api/backups \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ldap_server_id": 1}'

# List backups
curl http://staging-vm:8001/api/backups \
  -H "Authorization: Bearer $TOKEN"
```

### Success
✅ Backup created with timestamp
✅ Status shows "completed"

---

## Test 2: List Backups

### Steps
```bash
curl http://staging-vm:8001/api/backups \
  -H "Authorization: Bearer $TOKEN"
```

### Success
✅ All backups listed
✅ Metadata shows size, date, status

---

## Test 3: Restore Backup

### Steps
```bash
# Get backup ID from previous test
BACKUP_ID=1

# Initiate restore
curl -X POST http://staging-vm:8001/api/restores \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"backup_id": '$BACKUP_ID', "target_ldap_server_id": 2}'

# Check status
curl http://staging-vm:8001/api/restores \
  -H "Authorization: Bearer $TOKEN"
```

### Success
✅ Restore initiated (status: pending → running → completed)
✅ No errors in logs

---

## Test 4: Rate Limiting

### Steps
```bash
# Try 6 rapid login attempts
for i in {1..6}; do
  curl -X POST http://staging-vm:8001/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"wrong"}' \
    -w "\nAttempt $i: HTTP %{http_code}\n"
done
```

### Success
✅ First 5 return 200/401 (normal)
✅ 6th returns 429 (rate limited)

---

## Test 5: Check Encryption

### Steps
```bash
# Backup files should be .enc (encrypted)
docker exec ldapguard-api ls -la /backups/

# Verify raw file is binary (not readable LDIF)
docker exec ldapguard-api file /backups/backup_*.enc
# Should show: "data" (binary)

# Verify restore still works (decryption working)
# Run Test 3 above - should succeed
```

### Success
✅ Backup files are `.enc` (encrypted)
✅ File content is binary/gibberish
✅ Restore decrypts successfully

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

### Can't connect to API?
```bash
docker-compose -f docker-compose.staging.yml ps
# Make sure containers are "Up"
```

### Restore fails?
```bash
# Check database for errors
docker exec ldapguard-db psql -U postgres -d ldapguard_staging -c \
  "SELECT * FROM restores ORDER BY created_at DESC LIMIT 1;"
```

### Rate limiting too strict?
Edit [api/core/config.py](api/core/config.py) and adjust:
```python
LOGIN_RATE_LIMIT = "5/minute"  # Change this number
```

---

## Done = Ready for Production

Once all 6 tests pass:
✅ Staging works
✅ Production works
✅ Backups created
✅ Restores work
✅ Encryption active
✅ Rate limiting active

You're ready to use real LDAP servers!
