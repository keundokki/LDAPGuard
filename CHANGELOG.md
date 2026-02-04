# Changelog

All notable changes to LDAPGuard will be documented in this file.

## [0.0.1] - 2026-02-04

### Added
- Initial public pre-release of LDAPGuard
- LDAP directory backup to LDIF and JSON formats
- LDAP directory restore functionality
- Scheduled backup support with cron expressions
- REST API with FastAPI
- Web UI for management
- Docker support for amd64 and arm64 architectures
- Prometheus metrics integration
- Webhook notifications
- Multi-user authentication with role-based access control

### Known Issues
- CVE-2024-23342 in ecdsa 0.19.1 (Minerva attack - awaiting upstream patch)

## [1.0.1] - 2024-02-04

### Security
- **CRITICAL**: Updated `cryptography` from 41.0.7 to 42.0.4
  - Fixed NULL pointer dereference with pkcs12.serialize_key_and_certificates
  - Fixed Bleichenbacher timing oracle attack vulnerability
- **HIGH**: Updated `fastapi` from 0.104.1 to 0.109.1
  - Fixed Content-Type Header ReDoS vulnerability
- **HIGH**: Updated `python-multipart` from 0.0.6 to 0.0.22
  - Fixed Arbitrary File Write via Non-Default Configuration
  - Fixed DoS via malformed multipart/form-data boundary
  - Fixed Content-Type Header ReDoS vulnerability

## [1.0.0] - 2024-02-04

### Added
- Initial release of LDAPGuard
- Multi-container architecture (Web UI, API, Workers, PostgreSQL, Redis)
- Full LDAP backup to LDIF/JSON format
- Incremental backup support
- Point-in-time recovery
- Selective restore with LDAP filters
- AES-256-CBC encryption for backups
- JWT-based authentication
- LDAP authentication integration
- Role-Based Access Control (RBAC)
- APScheduler for scheduled backups
- Webhook notifications
- Prometheus metrics
- Comprehensive documentation
- Setup and validation scripts
- Docker/Podman Compose configuration
- Database migrations with Alembic
