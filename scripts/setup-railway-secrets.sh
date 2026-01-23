#!/bin/bash
# Setup Railway Environment Variables (Secrets)
# Run: chmod +x scripts/setup-railway-secrets.sh && ./scripts/setup-railway-secrets.sh <environment> [service]
# Examples:
#   ./scripts/setup-railway-secrets.sh staging synth-lab-api
#   ./scripts/setup-railway-secrets.sh production synth-lab-api

set -e

ENVIRONMENT=${1:-}
SERVICE=${2:-}

if [ -z "$ENVIRONMENT" ]; then
    echo "❌ Erro: Ambiente é obrigatório"
    echo ""
    echo "Usage: $0 <staging|production> <service-name>"
    echo ""
    echo "Examples:"
    echo "  $0 staging synth-lab-api"
    echo "  $0 production synth-lab-api"
    echo ""
    echo "Para ver serviços disponíveis:"
    echo "  railway status"
    exit 1
fi

if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    echo "❌ Erro: Ambiente deve ser 'staging' ou 'production'"
    echo "Usage: $0 <staging|production> <service-name>"
    exit 1
fi

if [ -z "$SERVICE" ]; then
    echo "❌ Erro: Nome do serviço é obrigatório"
    echo ""
    echo "Usage: $0 $ENVIRONMENT <service-name>"
    echo ""
    echo "Para ver serviços disponíveis:"
    echo "  railway status"
    echo ""
    echo "Exemplo:"
    echo "  $0 $ENVIRONMENT synth-lab-api"
    exit 1
fi

echo "🚂 Configurando Railway Secrets"
echo "   Projeto: $(railway status 2>&1 | grep 'Project:' | cut -d: -f2 | xargs)"
echo "   Ambiente: $ENVIRONMENT"
echo "   Serviço: $SERVICE"
echo ""

# Verificar se está logado no Railway
if ! railway whoami &> /dev/null; then
    echo "❌ Erro: Você precisa estar logado no Railway CLI"
    echo "Execute: railway login"
    exit 1
fi

# Verificar se está linkado a um projeto
if ! railway status &> /dev/null; then
    echo "❌ Erro: Você precisa estar linkado a um projeto Railway"
    echo ""
    echo "Execute um dos seguintes comandos:"
    echo "  railway link                    # Para linkar a um projeto existente"
    echo "  railway init                    # Para criar um novo projeto"
    exit 1
fi

# ============================================================================
# Carregar TODOS os valores do .env.dev
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/docker/.env.dev"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Erro: Arquivo docker/.env.dev não encontrado!"
    echo "   Esperado em: $ENV_FILE"
    exit 1
fi

echo "📂 Carregando valores de docker/.env.dev..."

# Carregar todas as variáveis do .env.dev (exceto comentários e linhas vazias)
set -a  # Automatically export all variables
source <(grep -v '^#' "$ENV_FILE" | grep -v '^$' | grep '=')
set +a

# ============================================================================
# Sobrescrever valores específicos por ambiente
# ============================================================================

# URLs específicas por ambiente (Railway)
if [ "$ENVIRONMENT" == "staging" ]; then
    OAUTH_REDIRECT_URI="https://synth-lab-api-staging.up.railway.app/auth/callback"
    CORS_ORIGINS="https://synth-lab-frontend-staging.up.railway.app"
    FRONTEND_URL="https://synth-lab-frontend-staging.up.railway.app"
    ENVIRONMENT_NAME="staging"
    PHOENIX_ENABLED="false"
else
    OAUTH_REDIRECT_URI="https://synth-lab-api.up.railway.app/auth/callback"
    CORS_ORIGINS="https://synth-lab-frontend.up.railway.app"
    FRONTEND_URL="https://synth-lab-frontend.up.railway.app"
    ENVIRONMENT_NAME="production"
    PHOENIX_ENABLED="true"
fi

# OpenAI key - usar do ambiente se disponível (não está no .env.dev por segurança)
OPENAI_KEY="${OPENAI_API_KEY:-}"
if [ -z "$OPENAI_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY não definida no ambiente."
    echo "   Defina antes de executar: export OPENAI_API_KEY=sk-..."
    echo ""
fi

# ============================================================================
# Validar variáveis críticas
# ============================================================================

echo "🔍 Validando variáveis..."

MISSING_VARS=()

[ -z "$GOOGLE_CLIENT_ID" ] && MISSING_VARS+=("GOOGLE_CLIENT_ID")
[ -z "$GOOGLE_CLIENT_SECRET" ] && MISSING_VARS+=("GOOGLE_CLIENT_SECRET")
[ -z "$JWT_SECRET_KEY" ] && MISSING_VARS+=("JWT_SECRET_KEY")
[ -z "$SESSION_SECRET_KEY" ] && MISSING_VARS+=("SESSION_SECRET_KEY")
[ -z "$BUCKET" ] && MISSING_VARS+=("BUCKET")
[ -z "$BUCKET_ACCESS_KEY_ID" ] && MISSING_VARS+=("BUCKET_ACCESS_KEY_ID")
[ -z "$BUCKET_SECRET_ACCESS_KEY" ] && MISSING_VARS+=("BUCKET_SECRET_ACCESS_KEY")

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "❌ Erro: Variáveis obrigatórias não encontradas no .env.dev:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    exit 1
fi

echo "✅ Todas as variáveis obrigatórias encontradas"
echo ""

# ============================================================================
# Configurar secrets no Railway
# ============================================================================

echo "📝 Configurando variáveis para $ENVIRONMENT..."
echo ""

railway variables \
  --set "OPENAI_API_KEY=$OPENAI_KEY" \
  --set "GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID" \
  --set "GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET" \
  --set "OAUTH_REDIRECT_URI=$OAUTH_REDIRECT_URI" \
  --set "JWT_SECRET_KEY=$JWT_SECRET_KEY" \
  --set "JWT_ALGORITHM=${JWT_ALGORITHM:-HS256}" \
  --set "ACCESS_TOKEN_EXPIRE_MINUTES=${ACCESS_TOKEN_EXPIRE_MINUTES:-10080}" \
  --set "SESSION_SECRET_KEY=$SESSION_SECRET_KEY" \
  --set "ENVIRONMENT=$ENVIRONMENT_NAME" \
  --set "WHITELIST=${WHITELIST:-}" \
  --set "CORS_ORIGINS=$CORS_ORIGINS" \
  --set "FRONTEND_URL=$FRONTEND_URL" \
  --set "ENDPOINT=${ENDPOINT:-https://storage.railway.app}" \
  --set "BUCKET=$BUCKET" \
  --set "BUCKET_ACCESS_KEY_ID=$BUCKET_ACCESS_KEY_ID" \
  --set "BUCKET_SECRET_ACCESS_KEY=$BUCKET_SECRET_ACCESS_KEY" \
  --set "REGION=${REGION:-auto}" \
  --set "PHOENIX_ENABLED=$PHOENIX_ENABLED" \
  --set "LOG_LEVEL=${LOG_LEVEL:-INFO}" \
  -e "$ENVIRONMENT" \
  -s "$SERVICE"

# Phoenix endpoint apenas para production
if [ "$ENVIRONMENT" == "production" ]; then
    railway variables --set "PHOENIX_COLLECTOR_ENDPOINT=${PHOENIX_COLLECTOR_ENDPOINT:-http://localhost:6006}" -e "$ENVIRONMENT" -s "$SERVICE"
fi

echo ""
echo "✅ Secrets configurados para $ENVIRONMENT!"
echo ""
echo "📊 Resumo dos valores configurados:"
echo "   - Serviço: $SERVICE"
echo "   - Ambiente: $ENVIRONMENT_NAME"
echo "   - OPENAI_API_KEY: ${OPENAI_KEY:0:20}..."
echo "   - GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID:0:40}..."
echo "   - JWT_SECRET_KEY: ${JWT_SECRET_KEY:0:20}..."
echo "   - SESSION_SECRET_KEY: ${SESSION_SECRET_KEY:0:20}..."
echo "   - BUCKET: $BUCKET"
echo "   - OAUTH_REDIRECT_URI: $OAUTH_REDIRECT_URI"
echo "   - CORS_ORIGINS: $CORS_ORIGINS"
echo "   - FRONTEND_URL: $FRONTEND_URL"
echo "   - WHITELIST: ${WHITELIST:-<não definida>}"
echo ""

if [ "$ENVIRONMENT" == "production" ]; then
    echo "🔴 ATENÇÃO: Ambiente de PRODUÇÃO!"
    echo ""
    echo "   Considere gerar novos valores para produção:"
    echo "   - JWT_SECRET_KEY: openssl rand -hex 32"
    echo "   - SESSION_SECRET_KEY: openssl rand -hex 32"
    echo ""
fi

echo "📖 Para verificar: railway variables -e $ENVIRONMENT -s $SERVICE"
echo "🔐 Para gerar secrets seguras: openssl rand -hex 32"
