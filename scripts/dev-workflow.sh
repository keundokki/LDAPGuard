#!/bin/bash
# Helper script for development workflow

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=== LDAPGuard Development Workflow ===${NC}\n"

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "Current branch: ${YELLOW}$CURRENT_BRANCH${NC}\n"

# Menu
echo "What would you like to do?"
echo "1) Start new feature (create branch from dev)"
echo "2) Commit and push current changes"
echo "3) Create PR from dev to main"
echo "4) Update dev from main"
echo "5) Exit"
echo
read -r -p "Choose [1-5]: " CHOICE

case $CHOICE in
    1)
        # Start new feature
        if [ "$CURRENT_BRANCH" != "dev" ]; then
            echo -e "${YELLOW}Switching to dev branch...${NC}"
            git checkout dev
            git pull origin dev
        fi
        
        echo -e "\nEnter feature name (e.g., 'backup-encryption'):"
        read -r FEATURE_NAME
        
        BRANCH_NAME="feature/$FEATURE_NAME"
        git checkout -b "$BRANCH_NAME"
        echo -e "${GREEN}✓ Created and switched to $BRANCH_NAME${NC}"
        echo "Make your changes, then run this script again to commit and push."
        ;;
        
    2)
        # Commit and push
        echo -e "\n${YELLOW}Current status:${NC}"
        git status --short
        
        if [ -z "$(git status --porcelain)" ]; then
            echo -e "${GREEN}No changes to commit${NC}"
            exit 0
        fi
        
        echo -e "\nEnter commit message (e.g., 'feat: add backup encryption'):"
        read -r COMMIT_MSG
        
        git add .
        git commit -m "$COMMIT_MSG"
        git push origin "$CURRENT_BRANCH"
        
        echo -e "${GREEN}✓ Changes committed and pushed to $CURRENT_BRANCH${NC}"
        
        if [[ "$CURRENT_BRANCH" == feature/* ]] || [[ "$CURRENT_BRANCH" == dev ]]; then
            echo -e "\n${YELLOW}Ready to create PR?${NC}"
            echo "Run option 3 to create a PR"
        fi
        ;;
        
    3)
        # Create PR
        if ! command -v gh &> /dev/null; then
            echo -e "${RED}GitHub CLI (gh) is not installed${NC}"
            echo "Install: brew install gh"
            echo "Then authenticate: gh auth login"
            echo
            echo "Manual PR creation:"
            echo "1. Go to: https://github.com/keundokki/LDAPGuard/compare"
            echo "2. Select: base: main <- compare: $CURRENT_BRANCH"
            echo "3. Click 'Create pull request'"
            exit 1
        fi
        
        echo -e "\nEnter PR title:"
        read -r PR_TITLE
        
        echo -e "\nEnter PR description (or press Enter to skip):"
        read -r PR_DESCRIPTION
        
        TARGET_BRANCH="main"
        if [[ "$CURRENT_BRANCH" == feature/* ]]; then
            echo -e "\nTarget branch (main/dev) [default: dev]:"
            read -r TARGET
            TARGET_BRANCH=${TARGET:-dev}
        fi
        
        gh pr create --base "$TARGET_BRANCH" --head "$CURRENT_BRANCH" --title "$PR_TITLE" --body "$PR_DESCRIPTION"
        
        echo -e "${GREEN}✓ PR created successfully!${NC}"
        echo "Check status with: ./scripts/check-pr-status.sh"
        ;;
        
    4)
        # Update dev from main
        if [ "$CURRENT_BRANCH" != "dev" ]; then
            echo -e "${YELLOW}Switching to dev...${NC}"
            git checkout dev
        fi
        
        echo -e "${YELLOW}Pulling latest from origin/dev...${NC}"
        git pull origin dev
        
        echo -e "${YELLOW}Merging changes from origin/main...${NC}"
        git pull origin main
        
        echo -e "${YELLOW}Pushing updated dev...${NC}"
        git push origin dev
        
        echo -e "${GREEN}✓ Dev branch updated with main${NC}"
        ;;
        
    5)
        echo "Goodbye!"
        exit 0
        ;;
        
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac
