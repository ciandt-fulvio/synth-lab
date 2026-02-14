#!/bin/bash
#
# Smart test runner for backend tests (pytest)
#
# Strategy:
# 1. Run previously failed tests first with fail-fast (--maxfail=1)
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

# Pytest cache file that tracks last failed tests
PYTEST_CACHE=".pytest_cache/v/cache/lastfailed"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🧪 Smart Test Runner (Backend)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if there are previously failed tests
if [ -f "$PYTEST_CACHE" ] && [ -s "$PYTEST_CACHE" ]; then
    # Count failed tests (JSON file with test paths as keys)
    FAILED_COUNT=$(cat "$PYTEST_CACHE" | grep -o '": true' | wc -l | tr -d ' ')

    if [ "$FAILED_COUNT" -gt 0 ]; then
        echo -e "${YELLOW}📋 Found $FAILED_COUNT previously failed test(s)${NC}"
        echo -e "${YELLOW}   Running failed tests first (fail-fast mode)...${NC}"
        echo ""

        # Run only failed tests with fail-fast (skip real API tests by default)
        if ! DATABASE_URL="${DATABASE_URL}" uv run pytest --last-failed --maxfail=1 -v -m "not real_api"; then
            echo ""
            echo -e "${RED}❌ Previously failed test(s) still failing!${NC}"
            echo -e "${RED}   Fix these tests before running full suite.${NC}"
            echo ""
            exit 1
        fi

        echo ""
        echo -e "${GREEN}✅ All previously failed tests now pass!${NC}"
        echo -e "${BLUE}   Running full test suite...${NC}"
        echo ""
    fi
fi

# Run full test suite (without stopping on first failure)
# Skip real_api tests by default (they're slow and cost money)
echo -e "${BLUE}🔄 Running full test suite (no fail-fast, skipping real API tests)...${NC}"
echo ""

if ! DATABASE_URL="${DATABASE_URL}" uv run pytest -v -m "not real_api"; then
    echo ""
    echo -e "${RED}❌ Some tests failed in full suite!${NC}"
    echo -e "${YELLOW}   Next run will prioritize these failed tests.${NC}"
    echo ""
    exit 1
fi

echo ""
echo -e "${GREEN}✅ All tests passed!${NC}"
echo ""
