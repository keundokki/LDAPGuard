#!/bin/bash

# LDAPGuard Kubernetes Update Script
# Updates LDAPGuard deployment in Kubernetes to a specific version

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
NAMESPACE="ldapguard"
VERSION=""
METHOD=""
SKIP_BACKUP=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --version|-v)
            VERSION="$2"
            shift 2
            ;;
        --namespace|-n)
            NAMESPACE="$2"
            shift 2
            ;;
        --method|-m)
            METHOD="$2"
            shift 2
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --version VERSION     Version to update to (required)"
            echo "  -n, --namespace NS        Kubernetes namespace (default: ldapguard)"
            echo "  -m, --method METHOD       Update method: kustomize|argocd (auto-detect if not specified)"
            echo "  --skip-backup             Skip database backup"
            echo "  -h, --help                Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --version 1.0.1                      # Update to version 1.0.1 (auto-detect method)"
            echo "  $0 --version 1.0.1 --method kustomize   # Update using kubectl/kustomize"
            echo "  $0 --version latest --namespace prod    # Update prod namespace to latest"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$VERSION" ]; then
    echo -e "${RED}✗${NC} Error: --version is required"
    echo "Use --help for usage information"
    exit 1
fi

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

# Check required commands
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is required but not installed"
        exit 1
    fi
    log_success "kubectl found"
}

check_argocd() {
    if ! command -v argocd &> /dev/null; then
        return 1
    fi
    return 0
}

# Detect update method
detect_method() {
    # Check if ArgoCD is managing this app
    if kubectl get application ldapguard -n argocd &> /dev/null 2>&1; then
        echo "argocd"
    else
        echo "kustomize"
    fi
}

# Backup database
backup_database() {
    if [ "$SKIP_BACKUP" = true ]; then
        log_warn "Skipping database backup (--skip-backup flag used)"
        return 0
    fi

    log_info "Creating database backup..."
    
    # Create backup directory
    BACKUP_DIR="./backups/k8s-db-backups"
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/pre-update-$(date +%Y%m%d-%H%M%S).sql"
    
    # Find postgres pod
    POSTGRES_POD=$(kubectl get pod -n "$NAMESPACE" -l app.kubernetes.io/name=ldapguard,app.kubernetes.io/component=postgres -o jsonpath='{.items[0].metadata.name}')
    
    if [ -z "$POSTGRES_POD" ]; then
        log_warn "Could not find postgres pod, skipping backup"
        return 0
    fi
    
    # Create backup
    if kubectl exec -n "$NAMESPACE" "$POSTGRES_POD" -- pg_dump -U ldapguard ldapguard > "$BACKUP_FILE" 2>/dev/null; then
        log_success "Database backed up to: $BACKUP_FILE"
        echo "$BACKUP_FILE"
    else
        log_warn "Database backup failed"
        read -p "Continue without backup? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Update cancelled"
            exit 0
        fi
    fi
}

# Update using Kustomize
update_kustomize() {
    log_info "Updating using Kustomize..."
    
    # Create a temporary kustomization overlay for version pinning
    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT
    
    cat > "$TEMP_DIR/kustomization.yaml" <<EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: $NAMESPACE

resources:
  - ../../k8s

images:
  - name: ghcr.io/keundokki/ldapguard-api
    newTag: "$VERSION"
  - name: ghcr.io/keundokki/ldapguard-worker
    newTag: "$VERSION"
  - name: ghcr.io/keundokki/ldapguard-web
    newTag: "$VERSION"
EOF

    log_info "Applying update to namespace: $NAMESPACE"
    
    if kubectl apply -k "$TEMP_DIR"; then
        log_success "Update applied"
    else
        log_error "Failed to apply update"
        exit 1
    fi
}

# Update using ArgoCD
update_argocd() {
    log_info "Updating using ArgoCD..."
    
    if ! check_argocd; then
        log_error "argocd CLI not found"
        log_info "Install from: https://argo-cd.readthedocs.io/en/stable/cli_installation/"
        exit 1
    fi
    
    # Update ArgoCD application with new image tags
    log_info "Updating ArgoCD application with version: $VERSION"
    
    kubectl patch application ldapguard -n argocd --type merge -p "{
      \"spec\": {
        \"source\": {
          \"kustomize\": {
            \"images\": [
              \"ghcr.io/keundokki/ldapguard-api:$VERSION\",
              \"ghcr.io/keundokki/ldapguard-worker:$VERSION\",
              \"ghcr.io/keundokki/ldapguard-web:$VERSION\"
            ]
          }
        }
      }
    }"
    
    log_success "ArgoCD application updated"
    log_info "Triggering ArgoCD sync..."
    
    argocd app sync ldapguard --prune
    
    log_success "ArgoCD sync triggered"
}

# Wait for rollout
wait_for_rollout() {
    log_info "Waiting for deployment rollout..."
    
    DEPLOYMENTS=("api" "worker" "web")
    
    for deployment in "${DEPLOYMENTS[@]}"; do
        log_info "Waiting for $deployment deployment..."
        if kubectl rollout status deployment/$deployment -n "$NAMESPACE" --timeout=5m; then
            log_success "$deployment deployment rolled out successfully"
        else
            log_error "$deployment deployment failed to roll out"
            exit 1
        fi
    done
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check pod status
    READY_PODS=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=ldapguard -o json | jq -r '.items[] | select(.status.phase=="Running") | .metadata.name' | wc -l)
    TOTAL_PODS=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=ldapguard -o json | jq -r '.items | length')
    
    log_info "Pods ready: $READY_PODS/$TOTAL_PODS"
    
    # Check API health
    API_POD=$(kubectl get pod -n "$NAMESPACE" -l app.kubernetes.io/component=api -o jsonpath='{.items[0].metadata.name}')
    
    if [ -n "$API_POD" ]; then
        log_info "Checking API health..."
        if kubectl exec -n "$NAMESPACE" "$API_POD" -- curl -sf http://localhost:8000/docs > /dev/null 2>&1; then
            log_success "API is healthy"
        else
            log_warn "API health check failed"
        fi
    fi
}

# Main function
main() {
    echo ""
    echo "╔════════════════════════════════════════════════╗"
    echo "║   LDAPGuard Kubernetes Update Utility          ║"
    echo "╚════════════════════════════════════════════════╝"
    echo ""
    
    # Check kubectl
    check_kubectl
    
    # Auto-detect method if not specified
    if [ -z "$METHOD" ]; then
        METHOD=$(detect_method)
        log_info "Auto-detected update method: $METHOD"
    fi
    
    log_info "Namespace: $NAMESPACE"
    log_info "Target version: $VERSION"
    log_info "Update method: $METHOD"
    
    # Check namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_error "Namespace '$NAMESPACE' does not exist"
        exit 1
    fi
    
    # Confirmation
    echo ""
    log_warn "This will update LDAPGuard in namespace '$NAMESPACE' to version '$VERSION'"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Update cancelled"
        exit 0
    fi
    
    # Backup database
    BACKUP_FILE=$(backup_database)
    
    # Perform update based on method
    case "$METHOD" in
        kustomize)
            update_kustomize
            ;;
        argocd)
            update_argocd
            ;;
        *)
            log_error "Unknown update method: $METHOD"
            log_info "Supported methods: kustomize, argocd"
            exit 1
            ;;
    esac
    
    # Wait for rollout
    wait_for_rollout
    
    # Verify deployment
    verify_deployment
    
    # Success message
    echo ""
    echo "╔════════════════════════════════════════════════╗"
    echo "║   ✅  Update completed successfully!           ║"
    echo "╚════════════════════════════════════════════════╝"
    echo ""
    echo "🎯 Updated to version: $VERSION"
    echo "📦 Namespace: $NAMESPACE"
    echo "🔧 Method: $METHOD"
    if [ -n "$BACKUP_FILE" ]; then
        echo ""
        echo "💾 Database backup: $BACKUP_FILE"
    fi
    echo ""
    echo "📋 Useful commands:"
    echo "   View pods:         kubectl get pods -n $NAMESPACE"
    echo "   View logs (API):   kubectl logs -n $NAMESPACE -l app.kubernetes.io/component=api -f"
    echo "   Port forward:      kubectl port-forward -n $NAMESPACE svc/web 8080:80"
    echo ""
}

# Handle interruption
trap 'log_error "Update interrupted"; exit 130' INT TERM

# Run main function
main "$@"
