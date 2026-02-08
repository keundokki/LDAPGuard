#!/bin/bash

# Initialize OpenLDAP with test data
# This script waits for LDAP to be ready and loads the test data

set -e

LDAP_HOST="${LDAP_HOST:-openldap}"
LDAP_PORT="${LDAP_PORT:-389}"
LDAP_ADMIN_DN="cn=admin,dc=example,dc=com"
LDAP_ADMIN_PASSWORD="${LDAP_ADMIN_PASSWORD:-admin_password}"
DATA_FILE="/ldap-data/init-test-data.ldif"

echo "Waiting for LDAP server to be ready..."

# Wait for LDAP to be listening
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if ldapsearch -x -h "$LDAP_HOST" -p "$LDAP_PORT" -b "dc=example,dc=com" -s base "(objectclass=*)" > /dev/null 2>&1; then
        echo "✓ LDAP server is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "  Attempt $attempt/$max_attempts - LDAP not ready yet, retrying in 2 seconds..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "✗ LDAP server failed to start"
    exit 1
fi

# Check if test data already exists (to avoid duplicates)
if ldapsearch -x -D "$LDAP_ADMIN_DN" -w "$LDAP_ADMIN_PASSWORD" -h "$LDAP_HOST" -p "$LDAP_PORT" \
    -b "ou=users,dc=example,dc=com" -s base "(objectclass=*)" > /dev/null 2>&1; then
    echo "ℹ Test data already loaded, skipping initialization"
    exit 0
fi

# Load test data
echo "Loading test data..."
if [ -f "$DATA_FILE" ]; then
    ldapadd -x -D "$LDAP_ADMIN_DN" -w "$LDAP_ADMIN_PASSWORD" \
        -h "$LDAP_HOST" -p "$LDAP_PORT" \
        -f "$DATA_FILE" 2>&1
    echo "✓ Test data loaded successfully!"
else
    echo "⚠ Test data file not found at $DATA_FILE"
    exit 1
fi

exit 0
