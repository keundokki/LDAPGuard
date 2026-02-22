.PHONY: help install start stop restart logs clean rebuild health backup restore test update version update-version update-k8s

# Default target
help:
	@echo "LDAPGuard - Makefile Commands"
	@echo "============================="
	@echo ""
	@echo "Installation & Setup:"
	@echo "  make install        - Run interactive installer"
	@echo "  make quick-install  - Quick install with defaults"
	@echo ""
	@echo "Service Management:"
	@echo "  make start          - Start all services"
	@echo "  make stop           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make rebuild        - Rebuild and restart all services"
	@echo ""
	@echo "Monitoring:"
	@echo "  make logs           - View all logs (follow mode)"
	@echo "  make logs-api       - View API logs only"
	@echo "  make logs-web       - View web logs only"
	@echo "  make logs-worker    - View worker logs only"
	@echo "  make status         - Show container status"
	@echo "  make health         - Check service health"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          - Stop and remove all containers"
	@echo "  make clean-all      - Remove containers, volumes, and images"
	@echo "  make update         - Update LDAPGuard to latest version"
	@echo "  make version        - Show current version"
	@echo "  make check-updates  - Check for available updates"
	@echo ""
	@echo "Database:"
	@echo "  make db-shell       - Open PostgreSQL shell"
	@echo "  make db-backup      - Backup PostgreSQL database"
	@echo "  make db-restore     - Restore PostgreSQL database"
	@echo ""
	@echo "Development:"
	@echo "  make dev            - Start in development mode"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run linters"
	@echo ""

# Detect compose command
COMPOSE := $(shell command -v docker-compose 2> /dev/null || command -v podman-compose 2> /dev/null)

ifndef COMPOSE
$(error Neither docker-compose nor podman-compose found. Please install one.)
endif

# Installation
install:
	@bash install.sh

quick-install:
	@bash scripts/setup.sh

# Service management
start:
	@echo "🚀 Starting LDAPGuard services..."
	@$(COMPOSE) up -d
	@echo "✓ Services started"
	@make -s status

stop:
	@echo "🛑 Stopping services..."
	@$(COMPOSE) stop
	@echo "✓ Services stopped"

restart:
	@echo "🔄 Restarting services..."
	@$(COMPOSE) restart
	@echo "✓ Services restarted"

rebuild:
	@echo "🔨 Rebuilding services..."
	@$(COMPOSE) up -d --build
	@echo "✓ Services rebuilt"

# Monitoring
logs:
	@$(COMPOSE) logs -f

logs-api:
	@$(COMPOSE) logs -f api

logs-web:
	@$(COMPOSE) logs -f web

logs-worker:
	@$(COMPOSE) logs -f worker

status:
	@echo "📊 Container Status:"
	@$(COMPOSE) ps

health:
	@echo "🏥 Checking service health..."
	@curl -sf http://localhost:8000/docs > /dev/null && echo "✓ API is healthy" || echo "✗ API is not responding"
	@curl -sf http://localhost:3000 > /dev/null && echo "✓ Web UI is healthy" || echo "✗ Web UI is not responding"

# Maintenance
clean:
	@echo "🧹 Cleaning up..."
	@$(COMPOSE) down
	@echo "✓ Containers removed"

clean-all:
	@echo "🧹 Removing everything..."
	@$(COMPOSE) down -v --rmi all
	@echo "✓ Containers, volumes, and images removed"

update:
	@bash update.sh
update-version:
\t@read -p \"Enter version to update to (e.g., 1.0.1): \" VERSION; \\
\tbash update.sh --version $$VERSION

update-k8s:
\t@read -p \"Enter version to update to (e.g., 1.0.1): \" VERSION; \\
\tread -p \"Enter namespace [ldapguard]: \" NAMESPACE; \\
\tNAMESPACE=$${NAMESPACE:-ldapguard}; \\
\tbash update-k8s.sh --version $$VERSION --namespace $$NAMESPACE
version:
	@if [ -f VERSION ]; then \
		echo "LDAPGuard Version: $$(cat VERSION)"; \
	else \
		echo "Version file not found"; \
	fi
	@if [ -f api/__init__.py ]; then \
		grep "__version__" api/__init__.py; \
	fi

check-updates:
	@echo "🔍 Checking for updates..."
	@if [ -d .git ]; then \
		git fetch origin; \
		LOCAL=$$(git rev-parse @); \
		REMOTE=$$(git rev-parse @{u}); \
		if [ "$$LOCAL" = "$$REMOTE" ]; then \
			echo "✓ Already up to date"; \
		else \
			echo "⚠️  Updates available. Run 'make update' to install."; \
			git log --oneline $$LOCAL..$$REMOTE; \
		fi; \
	else \
		echo "⚠️  Not a git repository. Cannot check for updates."; \
	fi

# Database
db-shell:
	@$(COMPOSE) exec postgres psql -U ldapguard -d ldapguard

db-backup:
	@echo "💾 Backing up database..."
	@mkdir -p backups/db
	@$(COMPOSE) exec postgres pg_dump -U ldapguard ldapguard > backups/db/backup-$(shell date +%Y%m%d-%H%M%S).sql
	@echo "✓ Database backed up to backups/db/"

db-restore:
	@echo "⚠️  This will restore the most recent database backup"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		LATEST=$$(ls -t backups/db/*.sql | head -1); \
		echo "Restoring $$LATEST..."; \
		$(COMPOSE) exec -T postgres psql -U ldapguard -d ldapguard < $$LATEST; \
		echo "✓ Database restored"; \
	fi

# Development
dev:
	@echo "🔧 Starting in development mode..."
	@cp docker-compose.dev.yml docker-compose.override.yml
	@$(COMPOSE) up -d
	@echo "✓ Development environment started"

test:
	@echo "🧪 Running tests..."
	@$(COMPOSE) exec api pytest
	@echo "✓ Tests complete"

lint:
	@echo "🔍 Running linters..."
	@$(COMPOSE) exec api black --check api/
	@$(COMPOSE) exec api flake8 api/
	@echo "✓ Linting complete"

# Quick access targets
shell-api:
	@$(COMPOSE) exec api bash

shell-web:
	@$(COMPOSE) exec web sh

shell-db:
	@$(COMPOSE) exec postgres bash
