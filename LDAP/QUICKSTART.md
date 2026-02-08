# Quick Start Guide - LDAP Test Environment

Get a fully functional OpenLDAP development environment running in 2 minutes.

## 1. Start the LDAP environment

```bash
cd LDAP
chmod +x init-ldap.sh ldap-manage.sh
podman-compose up -d  # or: docker-compose up -d
```

**Wait 15 seconds for initialization to complete.**

## 2. Verify everything is working

```bash
# Check all containers are running
podman-compose ps

# Test LDAP connectivity
ldapsearch -x -h localhost -p 3389 -D "cn=admin,dc=example,dc=com" \
  -w admin_password -b "dc=example,dc=com" "(objectClass=*)" | grep "^dn:" | wc -l
# Expected output: 24 (1 base + 1 readonly + 6 OUs + 4 groups + 10 users + 2 service accounts)

# Test PHPLDAPAdmin is accessible
curl -s http://localhost:6680 | grep -o "phpLDAPadmin" | head -1
# Expected output: phpLDAPadmin
```

## 3. Access the services

| Service | URL | Login |
|---------|-----|-------|
| **LDAP** | `ldap://localhost:3389` | `cn=admin,dc=example,dc=com` / `admin_password` |
| **LDAP Secure** | `ldaps://localhost:6363` | Same as LDAP |
| **PHPLDAPAdmin Web UI** | `http://localhost:6680` | Use LDAP credentials |

## 4. Test Data (Automatically Loaded)

✅ **24 LDAP Entries:**
- 1 Base DN: `dc=example,dc=com`
- 1 Readonly user: `cn=readonly,dc=example,dc=com`
- 6 Organizational Units: users, groups, services, it, hr, finance
- 4 Security Groups: admin, developers, managers, support
- 10 Regular Users: admin, john.doe, jane.smith, bob.wilson, alice.johnson, charlie.brown, david.lee, emma.davis, frank.miller, grace.taylor
- 2 Service Accounts: ldap-sync, backup-service

**All test user passwords:** `password123`

See [TEST-USERS.md](TEST-USERS.md) for complete user details.

## 5. Using in LDAPGuard

Configure a new LDAP server with:
```
Host: localhost
Port: 3389
Base DN: dc=example,dc=com
Bind DN: cn=admin,dc=example,dc=com
Bind Password: admin_password
```

Test user login:
- Username: `john.doe` (or any from TEST-USERS.md)
- Password: `password123`

## 6. Management commands

```bash
# Show all logs (live)
./ldap-manage.sh logs

# Show just initialization logs
./ldap-manage.sh init-logs

# Check service status
./ldap-manage.sh status

# Run connectivity tests
./ldap-manage.sh test

# Stop services (preserves data)
./ldap-manage.sh stop

# Restart services
./ldap-manage.sh restart

# Reset to completely fresh state (deletes all data)
./ldap-manage.sh reset
```

## 7. Query test data with command line

If you have `ldap-utils` installed:

```bash
# List all entries
ldapsearch -x -h localhost -p 3389 -D "cn=admin,dc=example,dc=com" \
  -w admin_password -b "dc=example,dc=com" "(objectClass=*)"

# Get specific user details
ldapsearch -x -h localhost -p 3389 -D "cn=admin,dc=example,dc=com" \
  -w admin_password -b "dc=example,dc=com" "uid=john.doe"

# Test user authentication
ldapwhoami -x -D "uid=john.doe,ou=users,dc=example,dc=com" \
  -w password123 -h localhost -p 3389

# List all users in a group
ldapsearch -x -h localhost -p 3389 -D "cn=admin,dc=example,dc=com" \
  -w admin_password -b "dc=example,dc=com" "cn=developers"
```

## 8. Troubleshooting

**Error: Port already in use**
- Edit `docker-compose.yml` and change port mappings
- Example: `3390:389` instead of `3389:389`

**Error: Connection refused**
- Services are still initializing - wait 15 seconds
- Check: `podman-compose logs openldap`

**PHPLDAPAdmin shows 403 Forbidden**
- Use URL: `http://localhost:6680` (not `/index.php`)
- Try hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Linux/Windows)

**To manually add more test data:**
```bash
cat << 'EOF' | podman exec -i ldapguard-openldap ldapadd -x \
  -D "cn=admin,dc=example,dc=com" -w admin_password -h localhost -p 389
dn: uid=newuser,ou=users,dc=example,dc=com
objectClass: inetOrgPerson
objectClass: organizationalPerson
objectClass: person
objectClass: top
uid: newuser
cn: New User
sn: User
mail: newuser@example.com
userPassword: {SSHA}password123
EOF
```

## Next Steps

- See [README.md](README.md) for complete setup documentation
- Read [TESTING-GUIDE.md](TESTING-GUIDE.md) for integration testing examples
- Check [TEST-USERS.md](TEST-USERS.md) for all test user credentials
- Review [PORT-CONFIG.md](PORT-CONFIG.md) for port configuration details
