#!/bin/bash
# Pre-push hook for synth-lab
# Runs E2E tests via Docker before allowing push

set -e

echo ""
echo "==================================="
echo "🎭 Pre-Push Hook: Running E2E Tests"
echo "==================================="
echo ""

# Run E2E tests via Docker (isolated environment)
if make test-e2e-docker; then
    echo ""
    echo "✅ E2E tests passed! Proceeding with push."
    echo ""
    exit 0
else
    echo ""
    echo "❌ E2E tests failed!"
    echo ""
    echo "To bypass this hook (NOT RECOMMENDED):"
    echo "  git push --no-verify"
    echo ""
    echo "To debug:"
    echo "  make test-e2e-docker-up    # Start E2E environment"
    echo "  make test-e2e-docker-logs  # View logs"
    echo "  make test-e2e-docker-down  # Stop environment"
    echo ""
    exit 1
fi
