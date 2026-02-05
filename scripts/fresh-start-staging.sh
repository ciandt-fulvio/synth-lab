#!/bin/bash
#
# Fresh Start - Staging Database
#
# This script triggers a complete reset of the staging database:
# 1. DROP all tables
# 2. Run all migrations from scratch
# 3. Seed with test data
# 4. Deploy latest images
#
# Usage:
#   ./scripts/fresh-start-staging.sh
#
# This is SAFE to run on staging (it's designed to be ephemeral).

set -e

echo "============================================"
echo "Fresh Start - Staging Database"
echo "============================================"
echo ""
echo "This will:"
echo "  1. DROP all tables in staging database"
echo "  2. Run all migrations from scratch"
echo "  3. Seed database with test data"
echo "  4. Deploy latest images to Railway"
echo ""
read -p "Are you sure you want to continue? (yes/no) " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "❌ Aborted"
    exit 1
fi

echo "🚀 Triggering fresh start workflow..."
echo ""

# Trigger workflow with fresh_start=true
gh workflow run deploy-staging.yml \
    -f fresh_start=true

echo ""
echo "✅ Workflow triggered!"
echo ""
echo "Monitor progress:"
echo "  gh run watch"
echo ""
echo "Or visit:"
echo "  https://github.com/$(gh repo view --json owner,name -q '.owner.login + "/" + .name')/actions"
