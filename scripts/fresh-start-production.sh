#!/bin/bash
#
# Fresh Start - Production Database
#
# ⚠️⚠️⚠️ DANGER: THIS WILL DESTROY ALL PRODUCTION DATA ⚠️⚠️⚠️
#
# This script triggers a complete reset of the production database:
# 1. DROP all tables (DESTROYS ALL DATA)
# 2. Run all migrations from scratch
# 3. Deploy latest staging-verified images
#
# Usage:
#   ./scripts/fresh-start-production.sh
#
# ⚠️ ONLY USE THIS FOR:
#   - Initial production deployment
#   - Complete system reset (with backup and user communication)
#
# ⚠️ BEFORE RUNNING:
#   - Create database backup
#   - Communicate with users about downtime
#   - Verify staging is working correctly

set -e

echo "============================================"
echo "⚠️  Fresh Start - Production Database ⚠️"
echo "============================================"
echo ""
echo "⚠️⚠️⚠️ DANGER ⚠️⚠️⚠️"
echo ""
echo "This will DESTROY ALL PRODUCTION DATA:"
echo "  - All user accounts"
echo "  - All experiments"
echo "  - All synth groups"
echo "  - All simulation results"
echo "  - Everything in the database"
echo ""
echo "⚠️⚠️⚠️ DANGER ⚠️⚠️⚠️"
echo ""

# Triple confirmation for production
echo "Type 'DELETE ALL PRODUCTION DATA' to continue:"
read -r CONFIRM1
if [[ "$CONFIRM1" != "DELETE ALL PRODUCTION DATA" ]]; then
    echo "❌ Aborted (confirmation failed)"
    exit 1
fi

echo ""
echo "Type 'I have a backup' to continue:"
read -r CONFIRM2
if [[ "$CONFIRM2" != "I have a backup" ]]; then
    echo "❌ Aborted (backup confirmation failed)"
    exit 1
fi

echo ""
echo "Type 'Users are notified' to continue:"
read -r CONFIRM3
if [[ "$CONFIRM3" != "Users are notified" ]]; then
    echo "❌ Aborted (user notification confirmation failed)"
    exit 1
fi

echo ""
echo "🚀 Triggering PRODUCTION fresh start workflow..."
echo ""

# Trigger workflow with fresh_start=true and staging-verified images
gh workflow run deploy-production.yml \
    -f fresh_start=true \
    -f use_staging_verified=true

echo ""
echo "✅ Workflow triggered!"
echo ""
echo "⚠️  PRODUCTION DATABASE RESET IN PROGRESS ⚠️"
echo ""
echo "Monitor progress:"
echo "  gh run watch"
echo ""
echo "Or visit:"
echo "  https://github.com/$(gh repo view --json owner,name -q '.owner.login + "/" + .name')/actions"
