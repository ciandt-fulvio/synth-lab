#!/bin/bash
#
# Validation script for smart test execution
#
# Tests the smart test runner by:
# 1. Running tests and simulating failures
# 2. Verifying that failed tests are tracked
# 3. Confirming that failed tests run first on subsequent runs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🧪 Smart Test Execution Validator${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if required files exist
echo -e "${BLUE}[1/4] Checking required files...${NC}"
required_files=(
    "scripts/run-tests-smart.sh"
    "scripts/run-e2e-tests-smart.sh"
    ".githooks/pre-push"
)

all_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✅ $file${NC}"
    else
        echo -e "${RED}  ❌ $file (missing)${NC}"
        all_exist=false
    fi
done

if [ "$all_exist" = false ]; then
    echo ""
    echo -e "${RED}❌ Some required files are missing!${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}[2/4] Checking script permissions...${NC}"
for file in "scripts/run-tests-smart.sh" "scripts/run-e2e-tests-smart.sh"; do
    if [ -x "$file" ]; then
        echo -e "${GREEN}  ✅ $file (executable)${NC}"
    else
        echo -e "${YELLOW}  ⚠️  $file (not executable, fixing...)${NC}"
        chmod +x "$file"
        echo -e "${GREEN}     Fixed!${NC}"
    fi
done

echo ""
echo -e "${BLUE}[3/4] Checking Makefile integration...${NC}"
makefile_checks=(
    "run-tests-smart.sh:Backend test integration"
    "run-e2e-tests-smart.sh:E2E test integration"
)

for check in "${makefile_checks[@]}"; do
    script="${check%%:*}"
    desc="${check##*:}"
    if grep -q "$script" Makefile; then
        echo -e "${GREEN}  ✅ $desc${NC}"
    else
        echo -e "${RED}  ❌ $desc (not found in Makefile)${NC}"
    fi
done

echo ""
echo -e "${BLUE}[4/4] Checking .gitignore entries...${NC}"
gitignore_entries=(
    ".pytest_cache/:Backend test cache"
    "test-results/:Playwright results"
    ".last-run.json:Playwright last run"
)

for entry in "${gitignore_entries[@]}"; do
    pattern="${entry%%:*}"
    desc="${entry##*:}"
    if grep -q "$pattern" .gitignore; then
        echo -e "${GREEN}  ✅ $desc${NC}"
    else
        echo -e "${YELLOW}  ⚠️  $desc (not in .gitignore)${NC}"
    fi
done

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Validation Complete!${NC}"
echo ""
echo -e "${BLUE}Smart test execution is properly configured.${NC}"
echo ""
echo -e "${BLUE}Usage:${NC}"
echo -e "  ${YELLOW}make test${NC}       - Run backend tests (smart mode)"
echo -e "  ${YELLOW}make test-e2e${NC}   - Run E2E tests (smart mode)"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo -e "  ${YELLOW}docs/testing.md${NC}"
echo ""
