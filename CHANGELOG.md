# Changelog

All notable changes to LDAPGuard will be documented in this file.

## [0.0.2] - 2026-02-04

### Fixed
- Fixed mypy type checking errors in ldap_service.py
- Fixed flake8 linting errors (unused imports, module import ordering)
- Resolved circular import in config.py
- Added proper semantic versioning support

### Changed
- Improved Docker multi-architecture build support (amd64 and arm64)
- Enhanced CI/CD pipeline with version tagging
- Unified version management from single source (api/__init__.py)

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
