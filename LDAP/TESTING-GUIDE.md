# Using LDAP with LDAPGuard for Testing

This guide explains how to use the LDAP test environment with LDAPGuard to develop, test, and demonstrate backup/restore functionality.

## Initial Setup

### 1. Start the LDAP Environment

```bash
cd LDAP
chmod +x init-ldap.sh ldap-manage.sh
./ldap-manage.sh start
```

Wait for initialization (check with `./ldap-manage.sh init-logs`)

### 2. Configure LDAPGuard

In the LDAPGuard web interface (http://localhost:5000 or your dev URL):

**Add LDAP Server:**
- Name: "Development LDAP"
- Host: `localhost`
- Port: `3389`
- Base DN: `dc=example,dc=com`
- Connection: LDAP (not LDAPS)
- Bind DN: `cn=admin,dc=example,dc=com`
- Bind Password: `admin_password`

Click "Test Connection" - should succeed!

### 3. Verify Test Data

List LDAP servers and check:
- Status: Connected ✓
- Users: Should show the 12 test entries
- Base DN: `dc=example,dc=com`

## Testing Scenarios

### Scenario 1: Basic Backup & Restore

**Goal:** Test full backup and restore cycle

1. **Authenticate** in LDAPGuard with test data present
2. **Create a backup:**
   - Name: "Initial Full Backup"
   - Select your Development LDAP server
   - Type: Full
   - Click Create Backup
3. **Verify backup:**
   - Check Backups tab
   - Should see "Initial Full Backup" with status "Completed"
   - Should contain all 12+ entries
4. **Create backup again:**
   - Add a new test user in LDAP (via PHPLDAPAdmin at http://localhost:6680)
   - Create another backup named "After New User"
   - Compare sizes (second should be larger)
5. **Restore backup:**
   - Go to Restores tab
   - Select the first backup
   - Restore to Development LDAP
   - Verify recovery
   - New user should be gone (back to original state)

### Scenario 2: Test Data Validation

**Goal:** Verify backup includes all test data

1. **Create a backup** of Development LDAP
2. **View backup details:**
   - Entries count should be ~23+ (depends on any manual additions)
   - Should include all 10 users
   - Should include all 4 groups
   - Should include all 6 organizational units
3. **Export and inspect** if available:
   - Search for expected users: john.doe, jane.smith, admin
   - Verify group memberships preserved
   - Verify all organizational units present

### Scenario 3: User Authentication Testing

**Goal:** Test LDAP authentication with different users

1. **Test admin authentication:**
   - User: admin
   - Password: admin_password (if supported)
   - Should work

2. **Test regular user:**
   - User: john.doe
   - Password: password123
   - Should work

3. **Test service account:**
   - User: ldap-sync
   - Password: password123
   - Should work

4. **Test readonly user:**
   - User: readonly
   - Password: readonly_password
   - Verify permissions (read-only, cannot modify)

### Scenario 4: Incremental Backups

**Goal:** Test incremental backup functionality (if supported)

1. Create initial full backup: "Baseline"
2. Add new users to LDAP:
   ```bash
   # Use PHPLDAPAdmin or ldapadd command
   # Add 2-3 test users
   ```
3. Create incremental backup: "After Additions"
4. Create another full backup: "Full Snapshot 2"
5. Compare:
   - Incremental should be much smaller
   - Full should contain all entries

### Scenario 5: Load Testing

**Goal:** Test performance with multiple backups

1. Create 5 backups of same LDAP server
2. Monitor:
   - Storage usage
   - Backup duration
   - Restore accuracy
3. Create 2-3 different LDAP servers (duplicate configuration)
4. Create backups of multiple servers
5. Verify independent management

### Scenario 6: Data Integrity Testing

**Goal:** Verify no data loss during backup/restore

**Before:**
```bash
# List all entries
ldapsearch -x -h localhost -p 389 \
  -b "dc=example,dc=com" \
  > /tmp/ldap-before.ldif
```

**After restore:**
```bash
# List all entries again
ldapsearch -x -h localhost -p 389 \
  -b "dc=example,dc=com" \
  > /tmp/ldap-after.ldif

# Compare
diff /tmp/ldap-before.ldif /tmp/ldap-after.ldif
# Should be identical
```

### Scenario 7: Permissions & RBAC Testing

**Goal:** Test role-based access in LDAPGuard

If LDAPGuard has user roles:

1. **Create admin user in LDAP** (or promote test user)
   ```bash
   # Via PHPLDAPAdmin or:
   ldapmodify -x -D "cn=admin,dc=example,dc=com" \
     -w admin_password -h localhost << EOF
   dn: uid=john.doe,ou=users,dc=example,dc=com
   changetype: modify
   add: ldapguardRole
   ldapguardRole: admin
   EOF
   ```

2. Test different users:
   - Admin user: Should see all operations
   - Operator: Should see backups but not admin functions
   - Viewer: Should see backups but not create/delete

3. Verify ACLs work correctly

### Scenario 8: Scheduled Backups

**Goal:** Test scheduled backup functionality

1. Create a scheduled backup:
   - Server: Development LDAP
   - Schedule: Every day at specific time
   - Name: "Nightly Full Backup"
   - Retention: 30 days

2. Trigger it (if admin function available)

3. Verify:
   - Backup created on schedule
   - Named correctly
   - Contains expected data
   - Old backups deleted after retention period

### Scenario 9: Disaster Recovery Simulation

**Goal:** Test complete data loss and recovery

**Simulate disaster:**
```bash
# Delete LDAP data
podman-compose down -v
rm -rf ldap-data ldap-config

# Recreate empty LDAP
podman-compose up -d
./ldap-manage.sh init-logs  # Wait for new init
```

**Recover:**
1. Go to LDAPGuard Restores
2. Select a backup from Development LDAP
3. Restore to the (now empty) LDAP server
4. Verify all data restored:
   ```bash
   ldapsearch -x -h localhost -p 3389 \
     -b "ou=users,dc=example,dc=com" | grep ^dn:
   # Should list all 10+ users
   ```

## Test Users by Role

Use different users to test different scenarios:

| User | Role | Use For |
|------|------|---------|
| admin | System Admin | Full backup permissions, admin functions |
| john.doe | Developer | Regular user backup, group testing |
| alice.johnson | Manager | Accessing team backups, read operations |
| ldap-sync | Service | Automated backup testing, integrations |
| readonly | Readonly | Verify limited permissions |

## Automation Testing

### Command Line Testing

```bash
# Test connectivity to LDAP
ldapsearch -x -h localhost -p 3389 \
  -b "dc=example,dc=com" \
  "(cn=*)" | head -20

# Count users
ldapsearch -x -h localhost -p 3389 \
  -b "ou=users,dc=example,dc=com" \
  "(objectClass=inetOrgPerson)" | \
  grep "^dn:" | wc -l

# Get total entry count
ldapsearch -x -h localhost -p 3389 \
  -b "dc=example,dc=com" | \
  grep "^dn:" | wc -l

# Export for comparison
ldapsearch -x -h localhost -p 3389 \
  -b "dc=example,dc=com" \
  -L > /tmp/ldap-export.ldif
```

### Backup Verification Script

```bash
#!/bin/bash

echo "LDAP Backup Verification"
echo "========================"

echo ""
echo "1. Connectivity:"
ldapsearch -x -h localhost -p 3389 \
  -b "dc=example,dc=com" -s base \
  "(objectclass=*)" > /dev/null && echo "✓ LDAP is online"

echo ""
echo "2. User Count:"
USER_COUNT=$(ldapsearch -x -h localhost -p 3389 \
  -b "ou=users,dc=example,dc=com" \
  "(objectClass=inetOrgPerson)" | grep "^dn:" | wc -l)
echo "✓ Found $USER_COUNT users"

echo ""
echo "3. Group Count:"
GROUP_COUNT=$(ldapsearch -x -h localhost -p 3389 \
  -b "ou=groups,dc=example,dc=com" \
  "(objectClass=groupOfNames)" | grep "^dn:" | wc -l)
echo "✓ Found $GROUP_COUNT groups"

echo ""
echo "4. Total Entries:"
TOTAL=$(ldapsearch -x -h localhost -p 3389 \
  -b "dc=example,dc=com" | grep "^dn:" | wc -l)
echo "✓ Total entries: $TOTAL"

echo ""
echo "Results: Users=$USER_COUNT Groups=$GROUP_COUNT Total=$TOTAL"
```

## Development Tips

1. **Keep multiple backups:**
   - Before major changes
   - At different stages
   - For comparison testing

2. **Reset LDAP for clean testing:**
   ```bash
   ./ldap-manage.sh reset
   ```

3. **Monitor backup operations:**
   - Check LDAPGuard logs
   - Watch LDAP server logs
   - Monitor disk space

4. **Test edge cases:**
   - Large entry sizes
   - Many small backups
   - Long-running restores
   - Concurrent operations

5. **Document results:**
   - Keep notes on test results
   - Save export files for comparison
   - Track performance metrics

## Troubleshooting Test Issues

**Backup fails with "Connection error"**
```bash
./ldap-manage.sh test
```

**Test data missing**
```bash
./ldap-manage.sh init-logs
./ldap-manage.sh reset
```

**Can't authenticate test user**
```bash
ldapwhoami -x -D "uid=john.doe,ou=users,dc=example,dc=com" \
  -w password123 -h localhost
```

**Different data after restore**
```bash
# Export before
ldapsearch -x -h localhost -p 389 \
  -b "dc=example,dc=com" > /tmp/before.ldif

# Restore
# (via LDAPGuard)

# Export after
ldapsearch -x -h localhost -p 389 \
  -b "dc=example,dc=com" > /tmp/after.ldif

# Compare
diff /tmp/before.ldif /tmp/after.ldif
```

## Success Criteria

Your LDAP + LDAPGuard testing is complete when:

✅ LDAP server starts with test data  
✅ LDAPGuard connects successfully  
✅ Full backup includes all 12+ entries  
✅ Restore recovers all data exactly  
✅ Different users can be tested  
✅ Multiple backups can be created  
✅ Scheduled backups work (if supported)  
✅ No data loss confirmed  
✅ Performance acceptable  
✅ All test scenarios pass  

Good luck with testing!
