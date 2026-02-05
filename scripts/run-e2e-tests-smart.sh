#!/bin/bash
#
# Smart test runner for E2E tests (Playwright)
#
# Strategy:
# 1. Run previously failed tests first with fail-fast (--max-failures=1)
# 2. If all pass, run full suite without fail-fast
#
# This provides quick feedback during development while ensuring
# full test coverage before considering the run complete.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Playwright last-run info
PLAYWRIGHT_STATE="frontend/.last-run.json"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🎭 Smart Test Runner (E2E)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if there are previously failed tests
if [ -f "$PLAYWRIGHT_STATE" ]; then
    # Playwright tracks failed tests in .last-run.json
    # Extract failed test count if file exists and has content
    if grep -q '"status".*:.*"failed"' "$PLAYWRIGHT_STATE" 2>/dev/null; then
        FAILED_COUNT=$(grep -o '"status".*:.*"failed"' "$PLAYWRIGHT_STATE" | wc -l | tr -d ' ')

        if [ "$FAILED_COUNT" -gt 0 ]; then
            echo -e "${YELLOW}📋 Found $FAILED_COUNT previously failed test(s)${NC}"
            echo -e "${YELLOW}   Running failed tests first (fail-fast mode)...${NC}"
            echo ""

            # Run only failed tests with fail-fast
            if ! cd frontend && TEST_ENV="${TEST_ENV:-docker}" npm run test:e2e -- --last-failed --max-failures=1; then
                cd ..
                echo ""
                echo -e "${RED}❌ Previously failed test(s) still failing!${NC}"
                echo -e "${RED}   Fix these tests before running full suite.${NC}"
                echo ""
                exit 1
            fi

            cd ..
            echo ""
            echo -e "${GREEN}✅ All previously failed tests now pass!${NC}"
            echo -e "${BLUE}   Running full test suite...${NC}"
            echo ""
        fi
    fi
fi

# Run full test suite (without stopping on first failure)
echo -e "${BLUE}🔄 Running full E2E test suite (no fail-fast)...${NC}"
echo ""

if ! cd frontend && TEST_ENV="${TEST_ENV:-docker}" npm run test:e2e; then
    cd ..
    echo ""
    echo -e "${RED}❌ Some tests failed in full suite!${NC}"
    echo -e "${YELLOW}   Next run will prioritize these failed tests.${NC}"
    echo ""
    exit 1
fi

cd ..
echo ""
echo -e "${GREEN}✅ All E2E tests passed!${NC}"
echo ""
