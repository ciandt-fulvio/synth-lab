#!/bin/bash
#
# Full E2E test orchestrator
#
# Handles: docker compose up → health check → playwright tests → compose down
# All output is visible — no silent redirects.
#
# Usage:
#   ./scripts/run-e2e-full.sh              # Normal run
#   FORCE_ALL=1 ./scripts/run-e2e-full.sh  # Skip smart mode (failed-first)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
DIM='\033[2m'
NC='\033[0m'

BACKEND_URL="http://localhost:8001"
FRONTEND_URL="http://localhost:8091"

# Cleanup on exit (always tear down containers)
cleanup() {
    echo ""
    echo -e "${BLUE}🧹 Cleaning up E2E environment...${NC}"
    ./scripts/compose-e2e.sh down > /tmp/e2e-down.log 2>&1 || true
    echo -e "${DIM}   Logs: /tmp/e2e-up.log, /tmp/e2e-down.log${NC}"
}
trap cleanup EXIT

# ─────────────────────────────────────────────────────────────
# Phase 1: Start Docker environment
# ─────────────────────────────────────────────────────────────
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🎭 E2E Test Runner${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "   Frontend: ${FRONTEND_URL}"
echo -e "   Backend:  ${BACKEND_URL}"
echo -e "   Database: localhost:5433"
echo ""

echo -e "${BLUE}🐳 Starting E2E environment...${NC}"
echo ""

# Show compose output directly (tee to log for later reference)
set +e
./scripts/compose-e2e.sh up-detached 2>&1 | tee /tmp/e2e-up.log
COMPOSE_EXIT=${PIPESTATUS[0]}
set -e

echo ""
if [ $COMPOSE_EXIT -ne 0 ]; then
    echo -e "${RED}❌ Failed to start E2E environment (exit: $COMPOSE_EXIT)${NC}"
    echo -e "${YELLOW}   Full log: cat /tmp/e2e-up.log${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Containers started${NC}"
echo ""

# ─────────────────────────────────────────────────────────────
# Phase 2: Wait for services to be healthy
# ─────────────────────────────────────────────────────────────
echo -e "${BLUE}⏳ Waiting for services...${NC}"

MAX_WAIT=180
WAITED=0
BACKEND_READY=false
FRONTEND_READY=false

while [ $WAITED -lt $MAX_WAIT ]; do
    if [ "$BACKEND_READY" = false ] && curl -sf "${BACKEND_URL}/health" > /dev/null 2>&1; then
        BACKEND_READY=true
        echo -e "${GREEN}   ✅ Backend ready ${DIM}(${WAITED}s)${NC}"
    fi

    if [ "$FRONTEND_READY" = false ] && curl -sf "${FRONTEND_URL}" > /dev/null 2>&1; then
        FRONTEND_READY=true
        echo -e "${GREEN}   ✅ Frontend ready ${DIM}(${WAITED}s)${NC}"
    fi

    if [ "$BACKEND_READY" = true ] && [ "$FRONTEND_READY" = true ]; then
        break
    fi

    sleep 2
    WAITED=$((WAITED + 2))

    if [ $((WAITED % 10)) -eq 0 ]; then
        STATUS=""
        [ "$BACKEND_READY" = false ] && STATUS="${STATUS} backend"
        [ "$FRONTEND_READY" = false ] && STATUS="${STATUS} frontend"
        echo -e "${DIM}   ... waiting for${STATUS} (${WAITED}s)${NC}"
    fi
done

if [ "$BACKEND_READY" = false ] || [ "$FRONTEND_READY" = false ]; then
    echo -e "${RED}❌ Services not ready after ${MAX_WAIT}s${NC}"
    [ "$BACKEND_READY" = false ] && echo -e "${RED}   Backend: ${BACKEND_URL}/health not responding${NC}"
    [ "$FRONTEND_READY" = false ] && echo -e "${RED}   Frontend: ${FRONTEND_URL} not responding${NC}"
    echo -e "${YELLOW}   Check: cat /tmp/e2e-up.log${NC}"
    exit 1
fi
echo ""

# ─────────────────────────────────────────────────────────────
# Phase 3: Run Playwright tests
# ─────────────────────────────────────────────────────────────
# Note: don't use exec here — cleanup trap needs to run after tests
./scripts/run-e2e-tests-smart.sh
