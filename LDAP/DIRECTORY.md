# LDAP Folder Contents

## Overview
Complete OpenLDAP development environment with automatic test data initialization for testing LDAPGuard.

## Files

### Configuration
- **docker-compose.yml** - Service definitions for OpenLDAP, PHPLDAPAdmin, and initialization

### Initialization
- **init-ldap.sh** - Initialization script that:
  - Waits for OpenLDAP to be ready
  - Loads test data automatically
  - Detects if data already exists (prevents duplicates)
  - Provides status feedback

- **init-test-data.ldif** - LDAP Data Interchange Format file containing:
  - 6 organizational units
  - 4 security groups
  - 10 test user accounts
  - 2 service accounts
  - All organizational structure and memberships

### Management & Documentation
- **ldap-manage.sh** - Helper script for easy management:
  - `./ldap-manage.sh start` - Start all services
  - `./ldap-manage.sh stop` - Stop services
  - `./ldap-manage.sh logs` - View all logs
  - `./ldap-manage.sh test` - Run connectivity tests
  - `./ldap-manage.sh reset` - Clean start

- **README.md** - Complete documentation:
  - Getting started guide
  - Service information
  - Test data details
  - Configuration instructions
  - Customization options
  - Troubleshooting

- **TEST-USERS.md** - Quick reference:
  - All 10 test user credentials
  - Group memberships
  - Test commands
  - Testing scenarios
  - Database statistics

- **QUICKSTART.md** - Fast setup guide:
  - Step-by-step instructions
  - Quick access information
  - Common commands
  - What's included
  - Troubleshooting

- **DIRECTORY.md** - This file

### Generated at Runtime (git-ignored)
- **ldap-data/** - LDAP database files
- **ldap-config/** - LDAP configuration

## Quick Execution

```bash
# Prepare
cd LDAP
chmod +x init-ldap.sh ldap-manage.sh

# Start
./ldap-manage.sh start

# Test
./ldap-manage.sh test

# View logs
./ldap-manage.sh logs

# Stop
./ldap-manage.sh stop
```

## Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Docker Compose Network (ldapguard-network)                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────┐    ┌──────────────────────────┐    │
│  │   OpenLDAP         │    │   PHPLDAPAdmin           │    │
│  │  (openldap)        │───▶│   (phpldapadmin)         │    │
│  │  Port: 389, 636    │    │   Port: 6680             │    │
│  │  DB: ldap-data     │    │   Web UI for management  │    │
│  │  Config: ldap-cfg  │    │                          │    │
│  └────────────────────┘    └──────────────────────────┘    │
│         ▲                                                     │
│         │ (waits for healthy)                               │
│  ┌──────┴──────────────────────────────────────────┐        │
│  │  LDAP Initialization (ldap-init)                │        │
│  │  - Runs: init-ldap.sh                           │        │
│  │  - Loads: init-test-data.ldif                   │        │
│  │  - Status: One-time initialization              │        │
│  └───────────────────────────────────────────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Access Points

| Service | URL/Connection | Credentials |
|---------|---|---|
| LDAP Direct | `localhost:3389` | `cn=admin,dc=example,dc=com` / `admin_password` |
| LDAPS (TLS) | `localhost:6363` | Same as above |
| PHPLDAPAdmin | http://localhost:6680 | Same as above |
| Readonly User | `localhost:3389` | `cn=readonly,dc=example,dc=com` / `readonly_password` |

## Test Data Structure

```
dc=example,dc=com (root)
├── ou=users (10 users + 2 service accounts)
│   ├── uid=admin
│   ├── uid=john.doe (Senior Developer)
│   ├── uid=jane.smith (DevOps Engineer)
│   ├── uid=bob.wilson (Junior Developer)
│   ├── uid=alice.johnson (IT Manager)
│   ├── uid=charlie.brown (Project Manager)
│   ├── uid=david.lee (Support Engineer)
│   ├── uid=emma.davis (Support Specialist)
│   ├── uid=frank.miller (QA Engineer)
│   ├── uid=grace.taylor (Product Manager)
│   ├── uid=ldap-sync (service account)
│   └── uid=backup-service (service account)
├── ou=groups (4 groups)
│   ├── cn=admin
│   ├── cn=developers
│   ├── cn=managers
│   └── cn=support
├── ou=services (service accounts container)
├── ou=it (IT department)
├── ou=hr (HR department)
└── ou=finance (Finance department)
```

## Integration with LDAPGuard

1. Start LDAP: `./ldap-manage.sh start`
2. In LDAPGuard, add LDAP server:
   - Host: `localhost`
   - Port: `389`
   - Base DN: `dc=example,dc=com`
   - Bind DN: `cn=admin,dc=example,dc=com`
   - Password: `admin_password`

3. Test user login: `john.doe` / `password123`

4. Create backups of the test LDAP data
5. Restore and verify recovery

## Maintenance

### View Logs
```bash
./ldap-manage.sh logs           # All services
./ldap-manage.sh init-logs      # Just initialization
podman-compose logs -f          # Raw logs
```

### Check Status
```bash
./ldap-manage.sh status
podman-compose ps
```

### Run Tests
```bash
./ldap-manage.sh test           # Connectivity tests
ldapsearch -x -h localhost ...  # Manual queries
```

### Clean Up
```bash
./ldap-manage.sh stop           # Stop containers
./ldap-manage.sh clean          # Remove volumes
./ldap-manage.sh reset          # Clean + restart
```

## Advanced Usage

### Modify Test Data
Edit `init-test-data.ldif`, then:
```bash
./ldap-manage.sh clean
./ldap-manage.sh start
```

### Add Users After Startup
```bash
ldapadd -x -D "cn=admin,dc=example,dc=com" -w admin_password \
  -h localhost -p 389 -f /path/to/new-users.ldif
```

### Use Docker Instead of Podman
```bash
DOCKER_CMD=docker-compose ./ldap-manage.sh start
```

### Change Port Mappings
Edit `docker-compose.yml`:
- LDAP: Change `389:389` to `3389:389`
- LDAPS: Change `636:636` to `6363:636`
- Web UI: Change `6680:80` to `8080:80`

## File Size Reference

- `docker-compose.yml` - ~1.5 KB
- `init-ldap.sh` - ~2 KB
- `init-test-data.ldif` - ~7 KB
- `ldap-manage.sh` - ~9 KB
- `README.md` - ~12 KB
- `TEST-USERS.md` - ~6 KB
- `QUICKSTART.md` - ~4 KB

**Total: ~41 KB configuration + data**

Runtime data (ignored by git):
- `ldap-data/` - Variable size (typically 5-50 MB depending on backups)
- `ldap-config/` - ~1 MB

## Compatibility

✅ Works with podman-compose  
✅ Works with docker-compose  
✅ Works on Linux, macOS, Windows (with WSL/Docker Desktop)  
✅ Uses standard osixia/openldap image  
✅ Portable across different machines  
✅ Git-safe (data directories ignored)  

## Security Note

⚠️ This is a **development setup only**

- All passwords are hardcoded (intentional for development)
- No SSL/TLS validation
- No production security measures
- Not suitable for sensitive data
- Perfect for testing and development

## Support

For issues, see:
1. `QUICKSTART.md` - Quick troubleshooting
2. `README.md` - Detailed documentation  
3. Logs: `./ldap-manage.sh logs`
4. Status: `./ldap-manage.sh status`
