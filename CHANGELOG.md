# Changelog

All notable changes to LDAPGuard will be documented in this file.

## [0.0.5] - 2026-02-05

### Security
- **CRITICAL**: Added startup validation for hardcoded secrets (SECRET_KEY, ENCRYPTION_KEY)
- **CRITICAL**: Implemented AES-256 encryption for LDAP bind passwords in database
- Added rate limiting to authentication endpoints (5 login attempts/min, 3 registrations/hour)
- Fixed XSS vulnerabilities by sanitizing all HTML output with escapeHtml()
- Restricted CORS to specific origins in production mode
- Added password_encrypted flag to track encryption status

### Fixed
- Implemented backup file deletion from disk (completed TODO)
- Implemented restore task scheduling with background tasks (completed TODO)
- Added proper error handling for password decryption failures
- Fixed potential integer injection in onclick handlers

### Changed
- LDAP passwords now automatically encrypted on create/update operations
- Backup and restore tasks now decrypt passwords before LDAP operations
- Added slowapi dependency for rate limiting
- Updated database schema (migration 003)

## [0.0.4] - 2026-02-05

### Added
- Audit logging system with filtering by action, resource type, and user
- API key management with secure bcrypt hashing and revocation capabilities
- System settings storage with key-value pairs and batch update support
- Configuration import/export functionality for servers, schedules, and users
- LDAP connection testing endpoint before server creation
- Batch delete operations for backups with multi-select UI
- Advanced filtering for backups (by server, status, type, and search)
- Dark mode support with localStorage persistence and theme toggle
- Multi-section admin panel (Users, Audit Logs, API Keys, Notifications, Settings)
- Notification settings for email and webhook alerts
- `/auth/me` endpoint for current user information
- Database migration for new tables (api_keys, system_settings)

### Changed
- Enhanced admin navigation with tabbed interface
- Improved authentication flow with proper token verification
- Updated UI with theme toggle button in header
- Reorganized admin features into dedicated sections

### Fixed
- Fixed missing authentication initialization in app.js
- Fixed white screen issue by adding auth check on page load
- Added missing toast notification styles (toast-info)
- Fixed API endpoint routing for all new admin features

### Security
- Enhanced JWT authentication with role-based access control
- Secure API key storage with bcrypt hashing
- Admin-only access restrictions for sensitive operations

## [0.0.3] - 2026-02-04

### Fixed
- Fixed web UI displaying incorrect version (now fetches dynamically from API)
- Web footer now shows correct version matching the API

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
