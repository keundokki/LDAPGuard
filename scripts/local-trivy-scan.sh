#!/bin/bash

set -e

echo "====================================="
echo "Local Trivy Security Scan Script"
echo "====================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Trivy is installed
if ! command -v trivy &> /dev/null; then
    echo -e "${RED}Trivy is not installed!${NC}"
    echo ""
    echo "Install Trivy using one of the following methods:"
    echo ""
    echo "  macOS:"
    echo "    brew install trivy"
    echo ""
    echo "  Linux (Debian/Ubuntu):"
    echo "    wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -"
    echo "    echo \"deb https://aquasecurity.github.io/trivy-repo/deb \$(lsb_release -sc) main\" | sudo tee -a /etc/apt/sources.list.d/trivy.list"
    echo "    sudo apt-get update && sudo apt-get install trivy"
    echo ""
    echo "  Using install script:"
    echo "    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin"
    exit 1
fi

echo -e "${GREEN}✓ Trivy is installed${NC}"
echo ""

# Define Dockerfiles to scan (matching CI workflow)
DOCKERFILES=("Dockerfile.api" "Dockerfile.worker" "Dockerfile.web")

# Scan settings (matching CI workflow)
SEVERITY="CRITICAL,HIGH"
EXIT_CODE=0  # Don't exit on first failure, scan all images

echo "====================================="
echo "Scanning Docker Images"
echo "====================================="
echo ""

for dockerfile in "${DOCKERFILES[@]}"; do
    if [ ! -f "$dockerfile" ]; then
        echo -e "${YELLOW}⚠ $dockerfile not found, skipping...${NC}"
        continue
    fi
    
    echo -e "${YELLOW}Building image: ldapguard:$dockerfile${NC}"
    docker build -f "$dockerfile" -t "ldapguard:$dockerfile" . || {
        echo -e "${RED}✗ Failed to build $dockerfile${NC}"
        continue
    }
    
    echo ""
    echo -e "${YELLOW}Scanning image: ldapguard:$dockerfile${NC}"
    echo "-------------------------------------"
    
    trivy image \
        --severity "$SEVERITY" \
        --exit-code "$EXIT_CODE" \
        --format table \
        "ldapguard:$dockerfile" || {
        echo -e "${RED}✗ Vulnerabilities found in $dockerfile${NC}"
    }
    
    echo ""
done

echo "====================================="
echo "Scanning Filesystem (Dependencies)"
echo "====================================="
echo ""

trivy fs \
    --severity "$SEVERITY" \
    --exit-code "$EXIT_CODE" \
    --format table \
    . || {
    echo -e "${RED}✗ Vulnerabilities found in filesystem${NC}"
}

echo ""
echo "====================================="
echo "Scan Complete"
echo "====================================="
echo ""
echo -e "${GREEN}Fix for CVE-2025-69421 (OpenSSL vulnerability):${NC}"
echo ""
echo "Update Dockerfile.web to use a newer nginx:alpine base image:"
echo ""
echo -e "${YELLOW}  FROM nginx:alpine${NC} → ${GREEN}FROM nginx:1.27-alpine3.20${NC}"
echo ""
echo "Then rebuild and rescan:"
echo "  docker build -f Dockerfile.web -t ldapguard:Dockerfile.web ."
echo "  trivy image --severity CRITICAL,HIGH ldapguard:Dockerfile.web"