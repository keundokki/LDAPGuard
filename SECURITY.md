# Security Policy

## Supported Versions

Currently supported versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within LDAPGuard, please send an email to security@example.com. All security vulnerabilities will be promptly addressed.

Please do not disclose security vulnerabilities publicly until they have been addressed.

## Security Features

LDAPGuard implements several security measures:

1. **Encryption**: AES-256-CBC encryption for all backup files
2. **Authentication**: JWT-based authentication with configurable expiration
3. **RBAC**: Role-Based Access Control with three levels (Admin, Operator, Viewer)
4. **Password Hashing**: Bcrypt with configurable work factor
5. **LDAP Integration**: Secure LDAP/LDAPS support
6. **Audit Logging**: Comprehensive audit trail for all operations

## Best Practices

When deploying LDAPGuard:

1. **Change default credentials**: Always update SECRET_KEY and ENCRYPTION_KEY
2. **Use strong passwords**: Minimum 32 characters for encryption keys
3. **Enable SSL/TLS**: Use LDAPS for LDAP connections
4. **Network isolation**: Run services on isolated networks
5. **Regular updates**: Keep all dependencies up to date
6. **Backup encryption**: Always enable backup encryption
7. **Access control**: Implement network-level access controls
8. **Monitoring**: Enable audit logging and monitor for suspicious activity

## Known Security Considerations

1. **Backup files**: Encrypted backups should be stored with appropriate access controls
2. **Database credentials**: PostgreSQL credentials should be strong and rotated regularly
3. **Redis access**: Redis should not be exposed to untrusted networks
4. **API access**: Use HTTPS in production environments
5. **LDAP credentials**: Bind DN credentials are stored encrypted in the database
