#!/bin/bash
# Generate self-signed certificates for LDAPS

CERT_DIR="./ldap-certs"
mkdir -p "$CERT_DIR"

echo "Generating self-signed certificate for LDAP TLS..."

# Generate private key
openssl genrsa -out "$CERT_DIR/ldap.key" 2048

# Generate certificate
openssl req -new -x509 -key "$CERT_DIR/ldap.key" -out "$CERT_DIR/ldap.crt" -days 365 \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=ldapguard-openldap/CN=localhost/CN=127.0.0.1"

# Generate DH parameters (for stronger TLS)
openssl dhparam -out "$CERT_DIR/dhparam.pem" 2048

# Copy CA cert (can be same as cert for self-signed)
cp "$CERT_DIR/ldap.crt" "$CERT_DIR/ca.crt"

# Set proper permissions
chmod 600 "$CERT_DIR/ldap.key"
chmod 644 "$CERT_DIR/ldap.crt"
chmod 644 "$CERT_DIR/ca.crt"
chmod 644 "$CERT_DIR/dhparam.pem"

echo "✓ Certificates generated in $CERT_DIR/"
ls -la "$CERT_DIR/"
