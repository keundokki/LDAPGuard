#!/bin/bash

# LDAPGuard - One-Command Installer
# Supports Docker and Podman container runtimes
# Usage: curl -fsSL https://raw.githubusercontent.com/keundokki/LDAPGuard/main/install.sh | bash
# Or: bash install.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     OS_TYPE=Linux;;
    Darwin*)    OS_TYPE=Mac;;
    *)          OS_TYPE="UNKNOWN";;
esac

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Banner
clear
echo -e "${BLUE}"
cat << "EOF"
 █████                                       
██   ██                                      
███    ███████  ███  ███  ███████ ██  ██████
███    ███  ██  ███  ███  ███  ██ ███ ███  █
███    ███  ███  ██████   ███  ██ ███ ███  █
██   ██ ███ ███  ██ ██    ███████ ███ ███████
 █████ ███  ███ ███ ███  ███  ██ ███ ███    
                         ███  ██ ███ ███  ██
                         ███████ ███  ██████ 
EOF
echo -e "${NC}"
echo -e "${GREEN}     Centralized LDAP Backup & Restore Solution${NC}"
echo ""

print_header "🔍 System Check"

# Check prerequisites
MISSING_DEPS=0

# Check docker or podman
if command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
    COMPOSE_CMD="docker-compose"
    print_success "Docker found"
elif command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
    COMPOSE_CMD="podman-compose"
    print_success "Podman found"
else
    print_error "Neither Docker nor Podman found"
    MISSING_DEPS=1
fi

# Check compose
if command -v docker-compose &> /dev/null || command -v podman-compose &> /dev/null; then
    print_success "Compose found ($COMPOSE_CMD)"
else
    print_error "Compose not found (need ${CONTAINER_CMD}-compose)"
    MISSING_DEPS=1
fi

# Check git
if command -v git &> /dev/null; then
    print_success "Git found"
else
    print_error "Git not found"
    MISSING_DEPS=1
fi

# Check openssl
if command -v openssl &> /dev/null; then
    print_success "OpenSSL found"
else
    print_warning "OpenSSL not found (will generate simpler keys)"
fi

# Check curl
if command -v curl &> /dev/null; then
    print_success "curl found"
else
    print_warning "curl not found (health checks will be skipped)"
fi

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    print_error "Missing required dependencies. Please install them first."
    echo ""
    echo "Installation guides:"
    echo "  Docker:  https://docs.docker.com/get-docker/"
    echo "  Podman:  https://podman.io/getting-started/installation"
    echo "  Git:     https://git-scm.com/downloads"
    exit 1
fi

# Installation mode
print_header "⚙️  Installation Mode"
echo "Choose installation type:"
echo "  1) Quick Install (recommended for testing)"
echo "     - Uses all defaults"
echo "     - Installs in current directory"
echo "     - Takes ~2 minutes"
echo ""
echo "  2) Custom Install (recommended for production)"
echo "     - Configure installation path"
echo "     - Set custom ports"
echo "     - Configure backup retention"
echo ""
read -p "Enter choice [1-2] (default: 1): " INSTALL_MODE
INSTALL_MODE=${INSTALL_MODE:-1}

# Set defaults
INSTALL_DIR="./ldapguard"
WEB_PORT=3000
API_PORT=8000
DB_PORT=5432
RETENTION_DAYS=30

if [ "$INSTALL_MODE" == "2" ]; then
    echo ""
    read -p "Installation directory (default: ./ldapguard): " CUSTOM_DIR
    INSTALL_DIR=${CUSTOM_DIR:-$INSTALL_DIR}
    
    read -p "Web UI port (default: 3000): " CUSTOM_WEB_PORT
    WEB_PORT=${CUSTOM_WEB_PORT:-$WEB_PORT}
    
    read -p "API port (default: 8000): " CUSTOM_API_PORT
    API_PORT=${CUSTOM_API_PORT:-$API_PORT}
    
    read -p "Database port (default: 5432): " CUSTOM_DB_PORT
    DB_PORT=${CUSTOM_DB_PORT:-$DB_PORT}
    
    read -p "Backup retention days (default: 30): " CUSTOM_RETENTION
    RETENTION_DAYS=${CUSTOM_RETENTION:-$RETENTION_DAYS}
fi

# Clone or use existing
print_header "📦 Getting LDAPGuard"

if [ -d "$INSTALL_DIR/.git" ]; then
    print_info "LDAPGuard directory exists, updating..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    print_info "Cloning LDAPGuard repository..."
    git clone https://github.com/keundokki/LDAPGuard.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

print_success "Repository ready"

# Generate configuration
print_header "🔐 Generating Configuration"

# Generate secure random keys
if command -v openssl &> /dev/null; then
    SECRET_KEY=$(openssl rand -hex 32)
    ENCRYPTION_KEY=$(openssl rand -hex 32)
    POSTGRES_PASSWORD=$(openssl rand -hex 16)
else
    # Fallback for systems without openssl
    SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)
    ENCRYPTION_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)
    POSTGRES_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
fi

# Create .env file
cat > .env << EOF
# LDAPGuard Configuration
# Generated on $(date)

# PostgreSQL
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Application
DEBUG=false

# Application Security
SECRET_KEY=${SECRET_KEY}
ENCRYPTION_KEY=${ENCRYPTION_KEY}

# Database Connection
DATABASE_URL=postgresql+asyncpg://ldapguard:${POSTGRES_PASSWORD}@postgres:5432/ldapguard

# Redis
REDIS_URL=redis://redis:6379

# Backup Settings
BACKUP_DIR=/app/backups
BACKUP_RETENTION_DAYS=${RETENTION_DAYS}
INCREMENTAL_BACKUP_ENABLED=true

# Webhooks
WEBHOOK_ENABLED=false

# Prometheus Metrics
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
EOF

print_success "Configuration generated"
print_info "Secure keys created and stored in .env"

# Update ports if custom
if [ "$INSTALL_MODE" == "2" ]; then
    print_info "Updating ports in docker-compose.yml..."
    # Create a temporary modified compose file
    if [ -f docker-compose.yml ]; then
        # Use appropriate sed syntax for OS
        if [ "$OS_TYPE" == "Mac" ]; then
            sed -i '' "s/3000:80/${WEB_PORT}:80/" docker-compose.yml
            sed -i '' "s/8000:8000/${API_PORT}:8000/" docker-compose.yml
            sed -i '' "s/5432:5432/${DB_PORT}:5432/" docker-compose.yml
        else
            sed -i "s/3000:80/${WEB_PORT}:80/" docker-compose.yml
            sed -i "s/8000:8000/${API_PORT}:8000/" docker-compose.yml
            sed -i "s/5432:5432/${DB_PORT}:5432/" docker-compose.yml
        fi
    fi
fi

# Create directories
print_info "Creating directories..."
mkdir -p logs backups
print_success "Directories created"

# Start services
print_header "🚀 Starting Services"

print_info "Pulling images..."
$COMPOSE_CMD pull

print_info "Starting containers..."
$COMPOSE_CMD up -d

print_success "Containers started"

# Wait for services
print_header "⏳ Waiting for Services"

print_info "Waiting for database to initialize (30 seconds)..."
sleep 30

# Health check
MAX_RETRIES=12
RETRY_COUNT=0
API_HEALTHY=0

if command -v curl &> /dev/null; then
    print_info "Checking API health..."
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -sf http://localhost:${API_PORT}/docs > /dev/null 2>&1; then
            API_HEALTHY=1
            break
        fi
        RETRY_COUNT=$((RETRY_COUNT + 1))
        sleep 5
        echo -n "."
    done
    echo ""
    
    if [ $API_HEALTHY -eq 1 ]; then
        print_success "API is healthy and responding"
    else
        print_warning "API is still starting (this may take a few more moments)"
    fi
fi

# Show container status
print_info "Container status:"
$COMPOSE_CMD ps

# Success message
print_header "✨ Installation Complete!"

echo -e "${GREEN}"
cat << EOF
   ╔════════════════════════════════════════════════════╗
   ║                                                    ║
   ║   🎉  LDAPGuard is now running!                   ║
   ║                                                    ║
   ╚════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo ""
echo -e "${BLUE}📍 Access Points:${NC}"
echo -e "   ${GREEN}Web UI:${NC}      http://localhost:${WEB_PORT}"
echo -e "   ${GREEN}API:${NC}         http://localhost:${API_PORT}"
echo -e "   ${GREEN}API Docs:${NC}    http://localhost:${API_PORT}/docs"
echo -e "   ${GREEN}Metrics:${NC}     http://localhost:${API_PORT}/metrics"
echo ""
echo -e "${BLUE}🔑 Default Login:${NC}"
echo -e "   ${GREEN}Username:${NC}    admin"
echo -e "   ${GREEN}Password:${NC}    admin"
echo -e "   ${RED}⚠ Change this password immediately!${NC}"
echo ""
echo -e "${BLUE}📊 Useful Commands:${NC}"
echo -e "   View logs:       ${YELLOW}cd $INSTALL_DIR && $COMPOSE_CMD logs -f${NC}"
echo -e "   Stop services:   ${YELLOW}cd $INSTALL_DIR && $COMPOSE_CMD stop${NC}"
echo -e "   Start services:  ${YELLOW}cd $INSTALL_DIR && $COMPOSE_CMD start${NC}"
echo -e "   Restart all:     ${YELLOW}cd $INSTALL_DIR && $COMPOSE_CMD restart${NC}"
echo -e "   Remove all:      ${YELLOW}cd $INSTALL_DIR && $COMPOSE_CMD down${NC}"
echo ""
echo -e "${BLUE}📚 Next Steps:${NC}"
echo "   1. Open http://localhost:${WEB_PORT} in your browser"
echo "   2. Login with admin/admin"
echo "   3. Change admin password (Settings → Change Password)"
echo "   4. Add your first LDAP server (Servers → Add Server)"
echo "   5. Create your first backup"
echo ""
echo -e "${BLUE}📖 Documentation:${NC}"
echo "   README:          $INSTALL_DIR/README.md"
echo "   GitHub:          https://github.com/keundokki/LDAPGuard"
echo ""
echo -e "${GREEN}Happy backing up! 🚀${NC}"
echo ""
