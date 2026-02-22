#!/bin/bash

# LDAPGuard Update Script
# Updates an existing LDAPGuard installation to the latest or specific version
# Supports Docker Compose, Podman Compose, and Docker Compose v2

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
UPDATE_TO_VERSION=""
SKIP_BACKUP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --version|-v)
            UPDATE_TO_VERSION="$2"
            shift 2
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "LDAPGuard update script for Docker and Podman installations."
            echo ""
            echo "Options:"
            echo "  -v, --version VERSION   Update to specific version (e.g., 1.0.1)"
            echo "  --skip-backup           Skip database backup"
            echo "  -h, --help              Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                      # Update to latest version"
            echo "  $0 --version 1.0.1      # Update to version 1.0.1"
            echo ""
            echo "Supports: docker-compose, podman-compose, Docker Compose v2"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is required but not installed"
        return 1
    fi
    return 0
}

# Detect compose command
detect_compose() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif command -v podman-compose &> /dev/null; then
        echo "podman-compose"
    elif docker compose version &> /dev/null 2>&1; then
        echo "docker compose"
    else
        echo ""
    fi
}

# Main script
main() {
    echo ""
    echo "╔════════════════════════════════════════════════╗"
    echo "║   LDAPGuard Update Utility (Docker/Podman)    ║"
    echo "╚════════════════════════════════════════════════╝"
    echo ""

    # Check if we're in LDAPGuard directory
    if [ ! -f "docker-compose.yml" ] && [ ! -f ".env" ]; then
        log_error "This doesn't appear to be an LDAPGuard installation directory"
        log_info "Please run this script from your LDAPGuard installation folder"
        exit 1
    fi

    # Detect compose command
    COMPOSE_CMD=$(detect_compose)
    if [ -z "$COMPOSE_CMD" ]; then
        log_error "Docker Compose or Podman Compose not found"
        log_info "Please install docker-compose, podman-compose, or Docker Compose v2"
        exit 1
    fi
    log_info "Container runtime: ${COMPOSE_CMD}"

    # Check if services are running
    log_info "Checking current installation..."
    if ! $COMPOSE_CMD ps | grep -q "Up"; then
        log_warn "LDAPGuard services don't appear to be running"
        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Update cancelled"
            exit 0
        fi
    fi

    # Determine target version
    if [ -z "$UPDATE_TO_VERSION" ]; then
        TARGET_VERSION="latest"
        log_info "Target version: latest (most recent release)"
    else
        TARGET_VERSION="$UPDATE_TO_VERSION"
        log_info "Target version: $TARGET_VERSION"
    fi

    # Show current version if available
    if [ -f "VERSION" ]; then
        CURRENT_VERSION=$(cat VERSION | tr -d '[:space:]')
        log_info "Current version: $CURRENT_VERSION"
    fi

    # Ask for update confirmation
    echo ""
    log_warn "This will update LDAPGuard to version: $TARGET_VERSION"
    log_info "The update process will:"
    echo "  1. Create a backup of your database (unless --skip-backup)"
    echo "  2. Pull Docker images for version $TARGET_VERSION"
    echo "  3. Stop current services"
    echo "  4. Run database migrations"
    echo "  5. Restart services with new version"
    echo ""
    read -p "Continue with update? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Update cancelled"
        exit 0
    fi

    # Create backup directory if it doesn't exist
    BACKUP_DIR="./backups/db-backups"
    mkdir -p "$BACKUP_DIR"

    # Backup database
    if [ "$SKIP_BACKUP" = false ]; then
        echo ""
        log_info "Creating database backup..."
        BACKUP_FILE="$BACKUP_DIR/pre-update-$(date +%Y%m%d-%H%M%S).sql"
        
        if $COMPOSE_CMD exec -T db pg_dump -U ldapguard ldapguard > "$BACKUP_FILE" 2>/dev/null; then
            log_success "Database backed up to: $BACKUP_FILE"
        else
            log_warn "Database backup failed (services might not be running)"
            read -p "Continue without backup? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "Update cancelled"
                exit 0
            fi
        fi
    else
        log_warn "Skipping database backup (--skip-backup flag used)"
    fi

    # Pull latest changes from git (if this is a git repo)
    if [ -d ".git" ]; then
        echo ""
        log_info "Pulling latest code from repository..."
        git fetch origin
        
        CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
        LOCAL_HASH=$(git rev-parse HEAD)
        REMOTE_HASH=$(git rev-parse origin/$CURRENT_BRANCH)
        
        if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
            log_info "Updates available on branch: $CURRENT_BRANCH"
            
            # Check for local changes
            if ! git diff-index --quiet HEAD --; then
                log_warn "You have uncommitted local changes"
                log_info "Stashing local changes..."
                git stash push -m "Auto-stash before update $(date +%Y%m%d-%H%M%S)"
            fi
            
            git pull origin "$CURRENT_BRANCH"
            log_success "Code updated from repository"
        else
            log_success "Already on latest commit"
        fi
    fi

    # Pull latest Docker images
    echo ""
    log_info "Pulling Docker images for version: $TARGET_VERSION..."
    
    # Set IMAGE_TAG environment variable for docker-compose
    export IMAGE_TAG="$TARGET_VERSION"
    
    if $COMPOSE_CMD pull; then
        log_success "Images updated to version: $TARGET_VERSION"
    else
        log_error "Failed to pull images"
        exit 1
    fi
    
    # Update .env file with new IMAGE_TAG if it exists
    if [ -f ".env" ]; then
        if grep -q "^IMAGE_TAG=" .env; then
            # Update existing IMAGE_TAG
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s/^IMAGE_TAG=.*/IMAGE_TAG=$TARGET_VERSION/" .env
            else
                sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=$TARGET_VERSION/" .env
            fi
            log_success "Updated IMAGE_TAG in .env to: $TARGET_VERSION"
        else
            # Add IMAGE_TAG if not present
            echo "IMAGE_TAG=$TARGET_VERSION" >> .env
            log_success "Added IMAGE_TAG=$TARGET_VERSION to .env"
        fi
    fi

    # Stop services gracefully
    echo ""
    log_info "Stopping services..."
    if $COMPOSE_CMD stop; then
        log_success "Services stopped"
    else
        log_warn "Some services may not have stopped cleanly"
    fi

    # Run database migrations
    echo ""
    log_info "Running database migrations..."
    
    # Start only the database temporarily
    $COMPOSE_CMD up -d db redis
    sleep 5
    
    # Run migrations using the API container
    if $COMPOSE_CMD run --rm api alembic upgrade head 2>/dev/null; then
        log_success "Database migrations completed"
    else
        log_warn "Migration command returned non-zero (may be normal if no migrations needed)"
    fi

    # Start all services
    echo ""
    log_info "Starting all services with new version..."
    if $COMPOSE_CMD up -d; then
        log_success "Services started"
    else
        log_error "Failed to start services"
        log_info "You can try manually with: $COMPOSE_CMD up -d"
        exit 1
    fi

    # Wait for services to be healthy
    echo ""
    log_info "Waiting for services to become healthy..."
    MAX_RETRIES=12
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        sleep 5
        RETRY_COUNT=$((RETRY_COUNT + 1))
        
        # Check if API is responding
        if curl -sf http://localhost:8000/docs > /dev/null 2>&1; then
            log_success "API is healthy"
            break
        fi
        
        if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
            log_error "Services failed to become healthy"
            log_info "Check logs with: $COMPOSE_CMD logs"
            exit 1
        fi
        
        echo -n "."
    done
    echo ""

    # Verify services
    echo ""
    log_info "Verifying services..."
    
    # Check if all containers are running
    RUNNING_COUNT=$($COMPOSE_CMD ps | grep -c "Up" || true)
    if [ "$RUNNING_COUNT" -ge 4 ]; then
        log_success "All services running"
    else
        log_warn "Some services may not be running. Check with: $COMPOSE_CMD ps"
    fi

    # Show version info
    echo ""
    log_info "Version updated to: $TARGET_VERSION"
    if [ -f "VERSION" ] && [ "$TARGET_VERSION" != "latest" ]; then
        log_warn "Note: VERSION file still shows: $(cat VERSION)"
        log_info "The VERSION file tracks git tags, not Docker image tags"
    fi

    # Show service status
    echo ""
    log_info "Service status:"
    $COMPOSE_CMD ps

    # Final success message
    echo ""
    echo "╔════════════════════════════════════════════════╗"
    echo "║   ✅  Update completed successfully!           ║"
    echo "╚════════════════════════════════════════════════╝"
    echo ""
    echo "📍 Access Points:"
    echo "   Web UI:  http://localhost:3000"
    echo "   API:     http://localhost:8000"
    echo "   Docs:    http://localhost:8000/docs"
    echo ""
    echo "🎯 Updated to version: $TARGET_VERSION"
    if [ "$SKIP_BACKUP" = false ] && [ -n "$BACKUP_FILE" ]; then
        echo ""
        echo "💾 Database backup saved to:"
        echo "   $BACKUP_FILE"
    fi
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs:     $COMPOSE_CMD logs -f"
    echo "   Check status:  $COMPOSE_CMD ps"
    echo "   Restart:       $COMPOSE_CMD restart"
    echo ""
}

# Handle interruption
trap 'log_error "Update interrupted"; exit 130' INT TERM

# Run main function
main "$@"
