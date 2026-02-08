# OpenLDAP Development Setup

This folder contains Docker Compose configuration for running OpenLDAP locally for development and testing purposes.

## Getting Started

### Start the LDAP services with test data

```bash
cd LDAP
podman-compose up -d
# or with docker
docker-compose up -d
```

The initialization will:
1. Start the OpenLDAP server
2. Automatically wait for the server to be ready
3. Load test data with sample users, groups, and organizational units

Check initialization logs:
```bash
podman-compose logs ldap-init
# or
docker-compose logs ldap-init
```

### Stop the LDAP services

```bash
cd LDAP
podman-compose down
# or with docker
docker-compose down
```

## Services

### OpenLDAP
- **Port:** 3389 (LDAP), 6363 (LDAPS)
- **Admin DN:** `cn=admin,dc=example,dc=com`
- **Admin Password:** `admin_password`
- **Base DN:** `dc=example,dc=com`
- **Readonly User:** `cn=readonly,dc=example,dc=com` / `readonly_password`

### PHPLDAPAdmin (Web UI)
- **URL:** http://localhost:6680
- **Login DN:** `cn=admin,dc=example,dc=com`
- **Password:** `admin_password`

### LDAP Init Service
- Automatically initializes test data on first run
- Runs after OpenLDAP is healthy
- Skips if data already exists (prevent duplicates)

## Test Data Included

The following structure is automatically created:

### Organizational Units
- `ou=users` - User accounts (10 test users)
- `ou=groups` - Group definitions
- `ou=services` - Service accounts
- `ou=it` - IT Department
- `ou=hr` - Human Resources
- `ou=finance` - Finance Department

### Groups
- **admin** - Administrator group
- **developers** - Developer team
- **managers** - Management team
- **support** - Support team

### Test Users

| UID | Name | Password | Role | Email |
|-----|------|----------|------|-------|
| admin | Administrator | password123 | System Admin | admin@example.com |
| john.doe | John Doe | password123 | Senior Developer | john.doe@example.com |
| jane.smith | Jane Smith | password123 | DevOps Engineer | jane.smith@example.com |
| bob.wilson | Bob Wilson | password123 | Junior Developer | bob.wilson@example.com |
| alice.johnson | Alice Johnson | password123 | IT Manager | alice.johnson@example.com |
| charlie.brown | Charlie Brown | password123 | Project Manager | charlie.brown@example.com |
| david.lee | David Lee | password123 | Support Engineer | david.lee@example.com |
| emma.davis | Emma Davis | password123 | Support Specialist | emma.davis@example.com |
| frank.miller | Frank Miller | password123 | QA Engineer | frank.miller@example.com |
| grace.taylor | Grace Taylor | password123 | Product Manager | grace.taylor@example.com |

### Service Accounts
- **ldap-sync** - For LDAP synchronization
- **backup-service** - For backup operations

**All test passwords are:** `password123`

## Configuration in LDAPGuard

### Add LDAP Server

In the LDAPGuard web interface, add an LDAP server with these settings:

| Field | Value |
|-------|-------|
| Server Name | Development LDAP |
| Host | localhost |
| Port | 3389 |
| Base DN | dc=example,dc=com |
| Bind DN | cn=admin,dc=example,dc=com |
| Bind Password | admin_password |

### Test Authentication

Try logging in with any test user:
- **Username:** `john.doe` or any UID from test users table
- **Password:** `password123`

## Testing Different Users

Use PHPLDAPAdmin or command line to test different users:

```bash
# Test with a specific user (Linux/Mac)
ldapwhoami -x -D "uid=john.doe,ou=users,dc=example,dc=com" -w password123 -h localhost -p 389

# Or from container
podman exec ldapguard-openldap ldapwhoami -x -D "uid=john.doe,ou=users,dc=example,dc=com" -w password123
```

## Customizing

Edit `docker-compose.yml` to change:
- `LDAP_DOMAIN` - Your domain (changes base DN)
- `LDAP_ORGANISATION` - Your organization name
- `LDAP_ADMIN_PASSWORD` - Admin password
- Port mappings (389, 636, 6680) if conflicts exist

## Modifying Test Data

### Option 1: Edit the LDIF file and reinitialize

1. Edit `init-test-data.ldif`
2. Delete existing data: `podman-compose down -v`
3. Restart: `podman-compose up -d`

### Option 2: Use PHPLDAPAdmin

1. Access http://localhost:6680
2. Log in with `cn=admin,dc=example,dc=com` / `admin_password`
3. Add/edit entries through the web interface

### Option 3: Use command line

```bash
# Add a new user
ldapadd -x -D "cn=admin,dc=example,dc=com" -w admin_password -h localhost -p 3389 << EOF
dn: uid=newuser,ou=users,dc=example,dc=com
objectClass: inetOrgPerson
uid: newuser
cn: New User
sn: User
userPassword: password123
mail: newuser@example.com
EOF

# Modify existing entry
ldapmodify -x -D "cn=admin,dc=example,dc=com" -w admin_password -h localhost -p 3389 << EOF
dn: uid=john.doe,ou=users,dc=example,dc=com
changetype: modify
replace: mail
mail: newemail@example.com
EOF

# Delete an entry
ldapdelete -x -D "cn=admin,dc=example,dc=com" -w admin_password -h localhost -p 3389 \
  "uid=newuser,ou=users,dc=example,dc=com"
```

## Data Persistence

LDAP data is stored in:
- `./ldap-data/` - LDAP database (git-ignored)
- `./ldap-config/` - LDAP configuration (git-ignored)

These folders are created automatically on first run.

## Troubleshooting

**Can't connect to LDAP?**
```bash
podman-compose ps
podman-compose logs openldap
```

**Test data not loaded?**
```bash
podman-compose logs ldap-init
```

**Port already in use?**
- Change ports in `docker-compose.yml`
- Example: change `389:389` to `3389:389` (then use port 3389)

**Need to reinitialize?**
```bash
podman-compose down -v  # Remove volumes
podman-compose up -d     # Restart fresh
```

**Reset to clean state:**
```bash
podman-compose down -v
rm -rf ldap-data ldap-config
podman-compose up -d
```

## Integration with LDAPGuard

Once running, LDAPGuard can:
- **Backup** all test LDAP data
- **Restore** backups to verify recovery
- **Monitor** LDAP structure and changes
- **Test** different user authentication scenarios
- **Verify** LDAP connectivity and permissions

Perfect for development, testing, and demonstrations!

