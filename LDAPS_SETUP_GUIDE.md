# LDAP & LDAPS Connection Guide

## ✅ Status: FULLY OPERATIONAL

Both LDAP and LDAPS connections are now working correctly.

## Connection Details

### LDAP (Unencrypted)
- **Host**: `localhost` or `127.0.0.1`
- **Port**: `3389`
- **Example**: `ldap://localhost:3389`
- **Status**: ✅ **WORKING**

### LDAPS (Encrypted with TLS)
- **Host**: `localhost` or `127.0.0.1`
- **Port**: `6363`
- **Example**: `ldaps://localhost:6363`
- **Status**: ✅ **WORKING**

### Authentication
- **Bind DN**: `cn=admin,dc=example,dc=com`
- **Password**: `admin_password`

## Important Notes

### Host Resolution
- ❌ **`host.containers.internal:6363` does NOT work from the host machine**
  - This hostname is only for containers to reach the host
  - From the host, use `localhost` or `127.0.0.1`
- ✅ **Use `localhost` or `127.0.0.1` for LDAPS on the host**

### Container Environment
- If the API is running in a **Docker/Podman container**, use:
  - `ldap://host.containers.internal:3389` (LDAP)
  - `ldaps://host.containers.internal:6363` (LDAPS with proper hostname resolution in container)

## TLS Certificate Configuration

### Self-Signed Certificate Details
- **CN**: `ldapguard-openldap`, `localhost`, `127.0.0.1`
- **Location**: `/Users/raphaeldubois-liski/Documents/LDAPGuard/LDAP/ldap-certs/`
- **Files**:
  - `ldap.crt` - Certificate
  - `ldap.key` - Private key
  - `ca.crt` - CA certificate
  - `dhparam.pem` - Diffie-Hellman parameters

### Python-LDAP Configuration
```python
import ldap

# Disable certificate verification for self-signed certificates
ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
ldap.set_option(ldap.OPT_X_TLS_NEWCTX, 0)

# Now connect normally
conn = ldap.initialize('ldaps://localhost:6363')
conn.simple_bind_s('cn=admin,dc=example,dc=com', 'admin_password')
```

## Verified Functionality

### LDAP Tests Passed
- ✅ Anonymous bind
- ✅ Admin authentication
- ✅ Search operations
- ✅ Directory traversal

### LDAPS Tests Passed
- ✅ TLS connection establishment
- ✅ Certificate negotiation (with verification disabled for self-signed)
- ✅ Admin authentication over encrypted connection
- ✅ Search operations over encrypted connection

## API Usage

When configuring LDAPGuard API for LDAPS:
```python
# For running on the host
LDAP_SERVER = "localhost"
LDAP_PORT = 6363
LDAP_USE_SSL = True

# Or alternatively
LDAP_SERVER = "127.0.0.1"
LDAP_PORT = 6363
LDAP_USE_SSL = True
```

## Docker/Podman Services

### Active Containers
1. **ldapguard-openldap** (OpenLDAP server)
   - LDAP: `0.0.0.0:3389->389`
   - LDAPS: `0.0.0.0:6363->636`

2. **ldapguard-phpldapadmin** (Web UI)
   - HTTP: `0.0.0.0:6680->80`

3. **ldapguard-ldap-init** (Initialization container)
   - Runs data import on startup

### Services Management
```bash
# Start services
cd /Users/raphaeldubois-liski/Documents/LDAPGuard/LDAP
podman-compose up -d

# Stop services
podman-compose down

# View logs
podman-compose logs -f openldap

# Direct LDAPS test
/opt/homebrew/anaconda3/bin/python /Users/raphaeldubois-liski/Documents/LDAPGuard/test_ldap_ldaps_comprehensive.py
```

## Troubleshooting

### LDAPS Connection Failed
1. Verify containers are running: `podman-compose ps`
2. Test with localhost instead of host.containers.internal
3. Ensure python-ldap has TLS certificate verification disabled:
   ```python
   ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
   ```

### Port Already in Use
- LDAP (3389) or LDAPS (6363) might be already bound
- Check with: `lsof -i :3389` or `lsof -i :6363`
- Restart podman-compose: `podman-compose down && podman-compose up -d`

## Additional Resources

- [python-ldap Documentation](https://www.python-ldap.org/)
- [OpenLDAP TLS Configuration](https://www.openldap.org/doc/admin24/tls.html)
- Test scripts in repository:
  - `test_ldap_ldaps_comprehensive.py` - Full functionality test
  - `test_ldaps_hosts.py` - Host resolution test
