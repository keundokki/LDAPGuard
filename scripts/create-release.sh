#!/bin/bash
# Create and push a new release tag

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== LDAPGuard Release Script ===${NC}\n"

# Check if we're on main branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${RED}Error: You must be on the 'main' branch to create a release${NC}"
    echo "Current branch: $CURRENT_BRANCH"
    exit 1
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${RED}Error: Working directory is not clean${NC}"
    git status --short
    exit 1
fi

# Get current version from last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
echo -e "Last release: ${YELLOW}$LAST_TAG${NC}"

# Ask for new version
echo -e "\nEnter new version (format: v1.0.0):"
read -r NEW_VERSION

# Validate version format
if [[ ! "$NEW_VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}Error: Invalid version format. Use vX.Y.Z (e.g., v1.0.0)${NC}"
    exit 1
fi

# Check if tag already exists
if git rev-parse "$NEW_VERSION" >/dev/null 2>&1; then
    echo -e "${RED}Error: Tag $NEW_VERSION already exists${NC}"
    exit 1
fi

# Get release notes
echo -e "\nEnter release notes (press Ctrl+D when done):"
RELEASE_NOTES=$(cat)

# Confirm
echo -e "\n${YELLOW}Ready to create release:${NC}"
echo "  Version: $NEW_VERSION"
echo "  Branch: main"
echo "  Notes: ${RELEASE_NOTES:0:50}..."
echo -e "\nProceed? (y/n)"
read -r CONFIRM

if [ "$CONFIRM" != "y" ]; then
    echo "Aborted."
    exit 0
fi

# Pull latest from main
echo -e "\n${GREEN}Pulling latest changes from origin/main...${NC}"
git pull origin main

# Create annotated tag
echo -e "\n${GREEN}Creating tag $NEW_VERSION...${NC}"
git tag -a "$NEW_VERSION" -m "$RELEASE_NOTES"

# Push tag
echo -e "\n${GREEN}Pushing tag to origin...${NC}"
git push origin "$NEW_VERSION"

echo -e "\n${GREEN}✓ Release $NEW_VERSION created successfully!${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Go to GitHub Actions → Deploy to Production"
echo "2. Click 'Run workflow'"
echo "3. Enter Image Tag: $NEW_VERSION"
echo "4. Click 'Run workflow' button"
echo "5. Wait for approval request"
echo "6. Approve deployment"
