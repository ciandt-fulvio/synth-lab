#!/bin/bash
# Install Git hooks for synth-lab

set -e

HOOKS_DIR=".git/hooks"
HOOK_SRC="scripts/pre-push-hook.sh"
HOOK_DST="${HOOKS_DIR}/pre-push"

echo ""
echo "==================================="
echo "Installing Git Hooks for synth-lab"
echo "==================================="
echo ""

# Verify we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: This directory is not a git repository"
    echo "   Please run this script from the project root"
    exit 1
fi

# Verify source hook exists
if [ ! -f "${HOOK_SRC}" ]; then
    echo "❌ Error: Hook source not found: ${HOOK_SRC}"
    exit 1
fi

# Copy and make executable
echo "Installing pre-push hook..."
cp "${HOOK_SRC}" "${HOOK_DST}"
chmod +x "${HOOK_DST}"

echo ""
echo "✅ Git hooks installed successfully!"
echo ""
echo "Installed hooks:"
echo "  - pre-push: Runs E2E tests via Docker before each push"
echo ""
echo "How it works:"
echo "  - Before every 'git push', E2E tests will run automatically"
echo "  - If tests pass, push proceeds normally"
echo "  - If tests fail, push is blocked"
echo ""
echo "To bypass hook (NOT RECOMMENDED):"
echo "  git push --no-verify"
echo ""
echo "To uninstall:"
echo "  rm .git/hooks/pre-push"
echo ""
