#!/bin/bash
#
# Smart test runner for E2E tests (Playwright)
#
# Strategy:
# 1. Run previously failed tests first with fail-fast
# 2. If all pass, run full suite
#
# Strips ANSI cursor-movement codes from Playwright output so results
# are visible when running through Make (non-TTY).
#
# Usage:
#   ./scripts/run-e2e-tests-smart.sh              # Smart mode
#   FORCE_ALL=1 ./scripts/run-e2e-tests-smart.sh  # Run all, skip smart

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
DIM='\033[2m'
NC='\033[0m'

PLAYWRIGHT_STATE="frontend/.last-run.json"
TEST_ENV="${TEST_ENV:-docker}"

# Strip ANSI cursor-movement escape codes that eat output in non-TTY.
# Keeps color codes (so output stays colorful) but removes:
#   \e[nA (cursor up), \e[nB (cursor down),
#   \e[nK (erase line), \e[nJ (erase display),
#   \e[?25l/h (hide/show cursor), \r (carriage return for overwrite)
strip_cursor_codes() {
    sed -E \
        -e 's/\x1b\[[0-9]*[ABCDJK]//g' \
        -e 's/\x1b\[\?25[lh]//g' \
        -e 's/\r//g'
}

# Run playwright and filter output for non-TTY visibility
run_playwright() {
    local extra_args="$*"
    local pw_exit=0
    cd frontend
    # Disable errexit for the pipe so we can capture PIPESTATUS
    set +e
    # shellcheck disable=SC2086
    TEST_ENV="$TEST_ENV" npx playwright test $extra_args 2>&1 | strip_cursor_codes
    pw_exit=${PIPESTATUS[0]}
    set -e
    cd ..
    return $pw_exit
}

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🎭 Playwright E2E Tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Count spec files
SPEC_COUNT=$(find frontend/tests/e2e -name '*.spec.ts' ! -path '*/smoke/*' 2>/dev/null | wc -l | tr -d ' ')
echo -e "${BLUE}📋 Test files: ${NC}${SPEC_COUNT} spec files (excluding smoke)"
echo ""

# ── Smart mode: run previously failed tests first ──────────────
if [ -z "$FORCE_ALL" ] && [ -f "$PLAYWRIGHT_STATE" ]; then
    if grep -q '"status".*:.*"failed"' "$PLAYWRIGHT_STATE" 2>/dev/null; then
        FAILED_COUNT=$(grep -o '"status".*:.*"failed"' "$PLAYWRIGHT_STATE" | wc -l | tr -d ' ')

        if [ "$FAILED_COUNT" -gt 0 ]; then
            echo -e "${YELLOW}⚡ Found $FAILED_COUNT previously failed test(s) — running those first...${NC}"
            echo ""

            if ! run_playwright --last-failed --max-failures=1; then
                echo ""
                echo -e "${RED}❌ Previously failed test(s) still failing.${NC}"
                echo -e "${YELLOW}   View report: cd frontend && npx playwright show-report${NC}"
                exit 1
            fi

            echo ""
            echo -e "${GREEN}✅ Previously failed tests now pass.${NC}"
            echo -e "${BLUE}   Running full suite...${NC}"
            echo ""
        fi
    fi
fi

# ── Full test suite ────────────────────────────────────────────
echo -e "${BLUE}🔄 Running full E2E test suite...${NC}"
echo ""

if ! run_playwright; then
    echo ""
    echo -e "${RED}❌ Some E2E tests failed.${NC}"
    echo -e "${YELLOW}   Next run will prioritize failed tests.${NC}"
    echo -e "${YELLOW}   View report: cd frontend && npx playwright show-report${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ All E2E tests passed!${NC}"
