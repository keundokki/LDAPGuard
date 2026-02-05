#!/bin/bash
# Check status of PR checks using GitHub CLI

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=== PR Status Checker ===${NC}\n"

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
    echo "Install it with: brew install gh"
    echo "Then authenticate: gh auth login"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}Not authenticated with GitHub CLI${NC}"
    echo "Run: gh auth login"
    exit 1
fi

# Get PR number from argument or find open PRs
if [ -n "$1" ]; then
    PR_NUMBER=$1
else
    echo "Looking for open PRs..."
    gh pr list --state open --limit 5
    echo -e "\nEnter PR number to check:"
    read -r PR_NUMBER
fi

if [ -z "$PR_NUMBER" ]; then
    echo -e "${RED}No PR number provided${NC}"
    exit 1
fi

echo -e "\n${BLUE}Checking PR #$PR_NUMBER...${NC}\n"

# Get PR status
gh pr view "$PR_NUMBER" --json title,state,isDraft,statusCheckRollup,reviewDecision

echo -e "\n${YELLOW}Detailed checks:${NC}"
gh pr checks "$PR_NUMBER"

# Check if ready to merge
echo -e "\n${YELLOW}Checking merge status...${NC}"
MERGEABLE=$(gh pr view "$PR_NUMBER" --json mergeable --jq '.mergeable')

if [ "$MERGEABLE" == "MERGEABLE" ]; then
    echo -e "${GREEN}✓ PR is ready to merge!${NC}"
else
    echo -e "${RED}✗ PR is not ready to merge${NC}"
    echo "Reasons could be:"
    echo "  - Status checks are failing"
    echo "  - Merge conflicts exist"
    echo "  - Required reviews are missing"
fi
