#!/bin/bash

# Helper script to manage OpenLDAP development environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_CMD="${DOCKER_CMD:-podman-compose}"

# Check if we're using docker or podman
if ! command -v "$COMPOSE_CMD" &> /dev/null; then
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif command -v podman-compose &> /dev/null; then
        COMPOSE_CMD="podman-compose"
    else
        echo "Error: Neither docker-compose nor podman-compose found"
        exit 1
    fi
fi

function show_help() {
    cat << EOF
OpenLDAP Development Environment Manager

Usage: ./ldap-manage.sh [command]

Commands:
    start       - Start OpenLDAP, PHPLDAPAdmin, and initialize test data
    stop        - Stop all LDAP services
    restart     - Restart all services
    logs        - Show logs (use Ctrl+C to exit)
    init-logs   - Show initialization logs only
    clean       - Stop services and remove volumes (WARNING: deletes data)
    reset       - Clean and start fresh
    status      - Show service status
    test        - Run LDAP connectivity tests
    help        - Show this help message

Examples:
    ./ldap-manage.sh start
    ./ldap-manage.sh logs
    ./ldap-manage.sh clean
    ./ldap-manage.sh reset

Environment Variables:
    DOCKER_CMD  - Use 'docker-compose' instead of default 'podman-compose'

Examples:
    DOCKER_CMD=docker-compose ./ldap-manage.sh start
EOF
}

function start_services() {
    echo "Starting OpenLDAP services..."
    cd "$SCRIPT_DIR"
    $COMPOSE_CMD up -d
    echo ""
    echo "✓ Services started!"
    echo ""
    echo "Access points:"
    echo "  LDAP:                  localhost:3389"
    echo "  PHPLDAPAdmin:          http://localhost:6680"
    echo "  Admin DN:              cn=admin,dc=example,dc=com"
    echo "  Admin Password:        admin_password"
    echo ""
    echo "Waiting for initialization..."
    sleep 3
    show_init_status
}

function stop_services() {
    echo "Stopping OpenLDAP services..."
    cd "$SCRIPT_DIR"
    $COMPOSE_CMD down
    echo "✓ Services stopped"
}

function restart_services() {
    stop_services
    sleep 1
    start_services
}

function show_logs() {
    cd "$SCRIPT_DIR"
    $COMPOSE_CMD logs -f
}

function show_init_logs() {
    cd "$SCRIPT_DIR"
    echo "LDAP Initialization logs:"
    echo "------------------------"
    $COMPOSE_CMD logs ldap-init
}

function show_init_status() {
    cd "$SCRIPT_DIR"
    echo "Initialization status:"
    if $COMPOSE_CMD logs ldap-init | grep -q "✓"; then
        echo "✓ Test data loaded successfully"
        echo ""
        echo "Available test users: See TEST-USERS.md"
        echo "All passwords: password123"
    else
        echo "⏳ Still initializing or waiting for logs..."
        echo "Run: ./ldap-manage.sh init-logs"
    fi
}

function clean_services() {
    echo "WARNING: This will delete all LDAP data!"
    read -p "Continue? (type 'yes' to confirm): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Cancelled"
        return
    fi
    
    cd "$SCRIPT_DIR"
    echo "Removing services and volumes..."
    $COMPOSE_CMD down -v
    rm -rf ldap-data ldap-config
    echo "✓ Cleaned"
}

function reset_services() {
    clean_services
    start_services
}

function show_status() {
    cd "$SCRIPT_DIR"
    echo "Service Status:"
    echo "---------------"
    $COMPOSE_CMD ps
}

function test_ldap() {
    cd "$SCRIPT_DIR"
    echo "Testing LDAP connectivity..."
    echo ""
    
    # Test if LDAP is responding
    if command -v ldapsearch &> /dev/null; then
        echo "✓ Testing with ldapsearch..."
        if ldapsearch -x -h localhost -p 3389 -b "dc=example,dc=com" -s base "(objectclass=*)" > /dev/null 2>&1; then
            echo "  ✓ LDAP responding on localhost:3389"
        else
            echo "  ✗ Cannot connect to localhost:3389"
            return 1
        fi
        
        # Test authentication
        echo ""
        echo "✓ Testing user authentication..."
        if ldapwhoami -x -D "cn=admin,dc=example,dc=com" -w admin_password -h localhost -p 3389 > /dev/null 2>&1; then
            echo "  ✓ Admin can authenticate"
        else
            echo "  ✗ Admin authentication failed"
            return 1
        fi
        
        # Test user count
        echo ""
        echo "✓ Checking test data..."
        USER_COUNT=$(ldapsearch -x -h localhost -p 3389 \
            -b "ou=users,dc=example,dc=com" \
            "(objectClass=inetOrgPerson)" | grep "^dn:" | wc -l)
        echo "  ✓ Found $USER_COUNT user accounts"
        
        echo ""
        echo "✓ All tests passed!"
    else
        echo "ldapsearch not installed. Install ldap-utils:"
        echo "  Ubuntu/Debian: sudo apt-get install ldap-utils"
        echo "  macOS:         brew install openldap"
        echo "  Fedora:        sudo dnf install openldap-clients"
    fi
}

# Main
case "${1:-help}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        show_logs
        ;;
    init-logs)
        show_init_logs
        ;;
    clean)
        clean_services
        ;;
    reset)
        reset_services
        ;;
    status)
        show_status
        ;;
    test)
        test_ldap
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo "Run './ldap-manage.sh help' for usage"
        exit 1
        ;;
esac
