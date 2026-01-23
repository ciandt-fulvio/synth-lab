#!/bin/bash
# Setup GitHub Secrets for CI/CD
# Run: chmod +x scripts/setup-github-secrets.sh && ./scripts/setup-github-secrets.sh

set -e

echo "🔐 Configurando GitHub Secrets para CI/CD..."
echo ""

# ============================================================================
# GitHub Secrets (usados nos workflows)
# ============================================================================

# 1. OpenAI API Key (usado em testes)
echo "📝 Configurando OPENAI_API_KEY..."
# IMPORTANTE: Substitua pelo seu valor real ou passe via: OPENAI_API_KEY=sk-... ./setup-github-secrets.sh
OPENAI_KEY="${OPENAI_API_KEY:-YOUR_OPENAI_API_KEY_HERE}"
gh secret set OPENAI_API_KEY --body "$OPENAI_KEY"

# 2. Railway API Token (para deploy)
echo "📝 Configurando RAILWAY_API_TOKEN..."
# Obter em: https://railway.app/account/tokens
RAILWAY_TOKEN="${RAILWAY_API_TOKEN:-YOUR_RAILWAY_API_TOKEN_HERE}"
gh secret set RAILWAY_API_TOKEN --body "$RAILWAY_TOKEN"

# 3. Railway Project ID
echo "📝 Configurando RAILWAY_PROJECT_ID..."
# Obter com: railway status ou em railway.app
RAILWAY_PROJECT="${RAILWAY_PROJECT_ID:-YOUR_RAILWAY_PROJECT_ID_HERE}"
gh secret set RAILWAY_PROJECT_ID --body "$RAILWAY_PROJECT"

# 4. Database URLs (provisionados pelo Railway)
echo "📝 Configurando DATABASE_STAGING_URL..."
# Formato: postgresql://user:pass@host:port/db
# Obter em: Railway Dashboard > Staging Environment > PostgreSQL > Variables > DATABASE_URL
STAGING_DB="${DATABASE_STAGING_URL:-postgresql://user:pass@host:port/db}"
gh secret set DATABASE_STAGING_URL --body "$STAGING_DB"

echo "📝 Configurando DATABASE_PRODUCTION_URL..."
# Obter em: Railway Dashboard > Production Environment > PostgreSQL > Variables > DATABASE_URL
PRODUCTION_DB="${DATABASE_PRODUCTION_URL:-postgresql://user:pass@host:port/db}"
gh secret set DATABASE_PRODUCTION_URL --body "$PRODUCTION_DB"

# ============================================================================
# GitHub Variables (configs públicas)
# ============================================================================

echo ""
echo "🌐 Configurando GitHub Variables (não-secretas)..."

# URLs dos ambientes (ajuste conforme seu projeto Railway)
STAGING_FRONTEND="${STAGING_FRONTEND_URL:-https://YOUR-FRONTEND-STAGING.railway.app}"
STAGING_BACKEND="${STAGING_BACKEND_URL:-https://YOUR-BACKEND-STAGING.railway.app}"

gh variable set STAGING_FRONTEND_URL --body "$STAGING_FRONTEND"
gh variable set STAGING_BACKEND_URL --body "$STAGING_BACKEND"

echo ""
echo "✅ GitHub Secrets e Variables configurados!"
echo ""
echo "⚠️  IMPORTANTE: Verifique se substituiu os valores placeholder:"
echo "   - OPENAI_API_KEY: $OPENAI_KEY"
echo "   - RAILWAY_API_TOKEN: ${RAILWAY_TOKEN:0:20}..."
echo "   - RAILWAY_PROJECT_ID: $RAILWAY_PROJECT"
echo "   - DATABASE_STAGING_URL: ${STAGING_DB:0:30}..."
echo "   - DATABASE_PRODUCTION_URL: ${PRODUCTION_DB:0:30}..."
echo "   - STAGING_FRONTEND_URL: $STAGING_FRONTEND"
echo "   - STAGING_BACKEND_URL: $STAGING_BACKEND"
echo ""
echo "💡 Dica: Passe valores via variáveis de ambiente:"
echo "   OPENAI_API_KEY=sk-... RAILWAY_API_TOKEN=... ./scripts/setup-github-secrets.sh"
echo ""
echo "📖 Para verificar: gh secret list && gh variable list"
