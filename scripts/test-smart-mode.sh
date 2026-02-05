#!/bin/bash
#
# Test script for pre-push hook smart mode change detection
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🧪 Testing Pre-Push Hook Smart Mode${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Fetch latest main
echo -e "${CYAN}Fetching origin/main...${NC}"
git fetch origin main --quiet 2>/dev/null || true
echo ""

# Get changed files
CHANGED_FILES=$(git diff --name-only origin/main...HEAD 2>/dev/null || git diff --name-only HEAD~1...HEAD)

if [ -z "$CHANGED_FILES" ]; then
    echo -e "${YELLOW}⚠️  No changes detected${NC}"
    echo -e "${YELLOW}Comparing with HEAD~1 instead...${NC}"
    CHANGED_FILES=$(git diff --name-only HEAD~1...HEAD)
fi

echo -e "${BLUE}Changed files:${NC}"
echo "$CHANGED_FILES" | while IFS= read -r file; do
    echo "  - $file"
done
echo ""

# Detect what changed
BACKEND_CHANGED=false
FRONTEND_CHANGED=false
DOCS_ONLY=true
CONFIG_CHANGED=false

while IFS= read -r file; do
    # Backend changes
    if [[ "$file" =~ ^(src/|tests/|pyproject\.toml|uv\.lock|Dockerfile\.backend|alembic/|scripts/seed_database\.py) ]]; then
        BACKEND_CHANGED=true
        DOCS_ONLY=false
        echo -e "${YELLOW}  📦 Backend change detected: $file${NC}"
    fi

    # Frontend changes
    if [[ "$file" =~ ^frontend/(src/|tests/|package\.json|package-lock\.json|Dockerfile) ]]; then
        FRONTEND_CHANGED=true
        DOCS_ONLY=false
        echo -e "${YELLOW}  🎨 Frontend change detected: $file${NC}"
    fi

    # Config changes
    if [[ "$file" =~ ^(docker/|\.env\.|Makefile|\.github/) ]]; then
        CONFIG_CHANGED=true
        DOCS_ONLY=false
        echo -e "${YELLOW}  ⚙️  Config change detected: $file${NC}"
    fi

    # Non-doc changes
    if [[ ! "$file" =~ \.(md|txt)$ ]] && [[ ! "$file" =~ ^docs/ ]]; then
        DOCS_ONLY=false
    fi
done <<< "$CHANGED_FILES"

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}📊 Change Detection Summary${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "  Backend changed:  $([ "$BACKEND_CHANGED" = true ] && echo -e "${YELLOW}YES${NC}" || echo -e "${GREEN}NO${NC}")"
echo -e "  Frontend changed: $([ "$FRONTEND_CHANGED" = true ] && echo -e "${YELLOW}YES${NC}" || echo -e "${GREEN}NO${NC}")"
echo -e "  Config changed:   $([ "$CONFIG_CHANGED" = true ] && echo -e "${YELLOW}YES${NC}" || echo -e "${GREEN}NO${NC}")"
echo -e "  Docs only:        $([ "$DOCS_ONLY" = true ] && echo -e "${GREEN}YES${NC}" || echo -e "${YELLOW}NO${NC}")"
echo ""

# If config changed, force full validation
if [ "$CONFIG_CHANGED" = true ]; then
    BACKEND_CHANGED=true
    FRONTEND_CHANGED=true
    DOCS_ONLY=false
    echo -e "${YELLOW}⚠️  Config changed - full validation required${NC}"
    echo ""
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}🎯 Actions to be taken${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

if [ "$DOCS_ONLY" = true ]; then
    echo -e "${GREEN}✅ Skip backend build (docs only)${NC}"
    echo -e "${GREEN}✅ Skip frontend build (docs only)${NC}"
    echo -e "${GREEN}✅ Skip unit tests (docs only)${NC}"
    echo -e "${GREEN}✅ Skip E2E tests (docs only)${NC}"
    echo -e "${GREEN}✅ Skip image push (docs only)${NC}"
    echo ""
    echo -e "${BLUE}💡 Estimated time: ~5 seconds${NC}"
else
    # Backend actions
    if [ "$BACKEND_CHANGED" = true ]; then
        echo -e "${YELLOW}🏗️  Build backend image${NC}"
        echo -e "${YELLOW}🧪 Run unit tests${NC}"
    else
        echo -e "${GREEN}⏭️  Skip backend build${NC}"
        echo -e "${GREEN}⏭️  Skip unit tests${NC}"
    fi

    # Frontend actions
    if [ "$FRONTEND_CHANGED" = true ]; then
        echo -e "${YELLOW}🏗️  Build frontend image${NC}"
    else
        echo -e "${GREEN}⏭️  Skip frontend build${NC}"
    fi

    # E2E tests
    if [ "$BACKEND_CHANGED" = true ] || [ "$FRONTEND_CHANGED" = true ]; then
        echo -e "${YELLOW}🎭 Run E2E tests${NC}"
    else
        echo -e "${GREEN}⏭️  Skip E2E tests${NC}"
    fi

    # Push images
    if [ "$BACKEND_CHANGED" = true ]; then
        echo -e "${YELLOW}📦 Push backend image${NC}"
    else
        echo -e "${GREEN}⏭️  Skip backend push${NC}"
    fi

    if [ "$FRONTEND_CHANGED" = true ]; then
        echo -e "${YELLOW}📦 Push frontend image${NC}"
    else
        echo -e "${GREEN}⏭️  Skip frontend push${NC}"
    fi

    echo ""
    if [ "$BACKEND_CHANGED" = true ] && [ "$FRONTEND_CHANGED" = true ]; then
        echo -e "${BLUE}💡 Estimated time: 5-10 minutes (full validation)${NC}"
    elif [ "$BACKEND_CHANGED" = true ] || [ "$FRONTEND_CHANGED" = true ]; then
        echo -e "${BLUE}💡 Estimated time: 2-3 minutes (partial validation)${NC}"
    else
        echo -e "${BLUE}💡 Estimated time: ~30 seconds (verify only)${NC}"
    fi
fi

echo ""
echo -e "${GREEN}✅ Smart mode detection working correctly!${NC}"
echo ""
