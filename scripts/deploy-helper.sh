#!/bin/bash
# Helper to trigger GitHub Actions deployment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=== Deployment Helper ===${NC}\n"

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
    echo "Install it with: brew install gh"
    echo "Then authenticate: gh auth login"
    echo
    echo "Manual deployment:"
    echo "1. Go to: https://github.com/keundokki/LDAPGuard/actions/workflows/deploy-production.yml"
    echo "2. Click 'Run workflow'"
    echo "3. Select branch: main"
    echo "4. Enter Image Tag (e.g., v1.0.0)"
    echo "5. Click 'Run workflow'"
    exit 1
fi

# Menu
echo "What would you like to deploy?"
echo "1) Deploy to Production (requires approval)"
echo "2) Rollback Production"
echo "3) Check deployment status"
echo "4) Exit"
echo
read -r -p "Choose [1-4]: " CHOICE

case $CHOICE in
    1)
        # Deploy to production
        echo -e "\n${YELLOW}Available tags:${NC}"
        git tag -l "v*" | tail -5
        
        echo -e "\nEnter image tag to deploy (e.g., v1.0.0):"
        read -r IMAGE_TAG
        
        if [[ ! "$IMAGE_TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo -e "${RED}Error: Invalid tag format. Use vX.Y.Z${NC}"
            exit 1
        fi
        
        if ! git rev-parse "$IMAGE_TAG" >/dev/null 2>&1; then
            echo -e "${RED}Error: Tag $IMAGE_TAG does not exist${NC}"
            exit 1
        fi
        
        echo -e "\n${YELLOW}Triggering production deployment...${NC}"
        gh workflow run deploy-production.yml --ref main --field image_tag="$IMAGE_TAG"
        
        echo -e "${GREEN}✓ Deployment workflow triggered${NC}"
        echo -e "\nMonitor progress:"
        echo "  gh run list --workflow=deploy-production.yml --limit 1"
        echo "  Or visit: https://github.com/keundokki/LDAPGuard/actions"
        ;;
        
    2)
        # Rollback production
        echo -e "\n${YELLOW}Available tags:${NC}"
        git tag -l "v*" | tail -5
        
        echo -e "\nEnter tag to rollback to:"
        read -r ROLLBACK_TAG
        
        if ! git rev-parse "$ROLLBACK_TAG" >/dev/null 2>&1; then
            echo -e "${RED}Error: Tag $ROLLBACK_TAG does not exist${NC}"
            exit 1
        fi
        
        echo -e "${RED}WARNING: This will rollback production to $ROLLBACK_TAG${NC}"
        echo "Are you sure? (yes/no)"
        read -r CONFIRM
        
        if [ "$CONFIRM" != "yes" ]; then
            echo "Aborted."
            exit 0
        fi
        
        echo -e "\n${YELLOW}Triggering rollback...${NC}"
        gh workflow run rollback-production.yml --ref main --field previous_tag="$ROLLBACK_TAG"
        
        echo -e "${GREEN}✓ Rollback workflow triggered${NC}"
        echo "Monitor at: https://github.com/keundokki/LDAPGuard/actions"
        ;;
        
    3)
        # Check status
        echo -e "\n${BLUE}Recent workflow runs:${NC}"
        gh run list --limit 10
        
        echo -e "\n${YELLOW}Enter run ID to view details (or press Enter to skip):${NC}"
        read -r RUN_ID
        
        if [ -n "$RUN_ID" ]; then
            gh run view "$RUN_ID"
        fi
        ;;
        
    4)
        echo "Goodbye!"
        exit 0
        ;;
        
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac
