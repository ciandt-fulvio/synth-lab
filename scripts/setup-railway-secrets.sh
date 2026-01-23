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
# Carregar valores do .env.dev (quando disponível)
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/docker/.env.dev"

if [ -f "$ENV_FILE" ]; then
    echo "📂 Carregando valores de docker/.env.dev..."
    # Carregar apenas valores não-secretos ou que podem ser reutilizados
    source <(grep -E '^(GOOGLE_CLIENT_ID|JWT_ALGORITHM|ACCESS_TOKEN_EXPIRE_MINUTES|ENDPOINT|REGION)=' "$ENV_FILE")
else
    echo "⚠️  Arquivo docker/.env.dev não encontrado. Usando placeholders."
fi

# ============================================================================
# Valores padrão (placeholders) para valores não carregados do .env.dev
# ============================================================================

# Google OAuth (ler do .env.dev se disponível, senão usar placeholder)
GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID:-YOUR-GOOGLE-CLIENT-ID.apps.googleusercontent.com}"
GOOGLE_CLIENT_SECRET="${GOOGLE_CLIENT_SECRET:-YOUR_GOOGLE_CLIENT_SECRET}"

# JWT (CRÍTICO: Gere novos valores para produção!)
JWT_SECRET_KEY="${JWT_SECRET_KEY:-YOUR_JWT_SECRET_KEY}"
JWT_ALGORITHM="${JWT_ALGORITHM:-HS256}"
ACCESS_TOKEN_EXPIRE_MINUTES="${ACCESS_TOKEN_EXPIRE_MINUTES:-10080}"

# Session (CRÍTICO: Gere novo valor para produção!)
SESSION_SECRET_KEY="${SESSION_SECRET_KEY:-YOUR_SESSION_SECRET_KEY}"

# S3 Storage (Railway Buckets)
S3_ENDPOINT="${ENDPOINT:-https://storage.railway.app}"
S3_BUCKET="${BUCKET:-YOUR-BUCKET-NAME}"
S3_ACCESS_KEY_ID="${BUCKET_ACCESS_KEY_ID:-YOUR-BUCKET-ACCESS-KEY-ID}"
S3_SECRET_ACCESS_KEY="${BUCKET_SECRET_ACCESS_KEY:-YOUR-BUCKET-SECRET-ACCESS-KEY}"
S3_REGION="${REGION:-auto}"

# Whitelist (ajustar conforme necessário)
WHITELIST="${WHITELIST:-user@example.com,@example.com}"

# ============================================================================
# URLs específicas por ambiente
# ============================================================================

if [ "$ENVIRONMENT" == "staging" ]; then
    OAUTH_REDIRECT_URI="${OAUTH_REDIRECT_URI:-https://YOUR-BACKEND-STAGING.railway.app/auth/callback}"
    CORS_ORIGINS="${CORS_ORIGINS:-https://YOUR-FRONTEND-STAGING.railway.app}"
    ENVIRONMENT_NAME="staging"
else
    OAUTH_REDIRECT_URI="${OAUTH_REDIRECT_URI:-https://YOUR-BACKEND-PRODUCTION.railway.app/auth/callback}"
    CORS_ORIGINS="${CORS_ORIGINS:-https://YOUR-FRONTEND-PRODUCTION.railway.app}"
    ENVIRONMENT_NAME="production"
fi

# ============================================================================
# Configurar secrets no Railway
# ============================================================================

echo "📝 Configurando variáveis para $ENVIRONMENT..."
echo ""

# OpenAI (deve ser passada via env var)
OPENAI_KEY="${OPENAI_API_KEY:-YOUR_OPENAI_API_KEY_HERE}"

# Phoenix (observability) - condicional por ambiente
if [ "$ENVIRONMENT" == "production" ]; then
    PHOENIX_ENABLED="true"
    PHOENIX_ENDPOINT="http://localhost:6006"
else
    PHOENIX_ENABLED="false"
    PHOENIX_ENDPOINT=""
fi

# Configurar todas as variáveis em um único comando (mais rápido)
railway variables \
  --set "OPENAI_API_KEY=$OPENAI_KEY" \
  --set "GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID" \
  --set "GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET" \
  --set "OAUTH_REDIRECT_URI=$OAUTH_REDIRECT_URI" \
  --set "JWT_SECRET_KEY=$JWT_SECRET_KEY" \
  --set "JWT_ALGORITHM=$JWT_ALGORITHM" \
  --set "ACCESS_TOKEN_EXPIRE_MINUTES=$ACCESS_TOKEN_EXPIRE_MINUTES" \
  --set "SESSION_SECRET_KEY=$SESSION_SECRET_KEY" \
  --set "ENVIRONMENT=$ENVIRONMENT_NAME" \
  --set "WHITELIST=$WHITELIST" \
  --set "CORS_ORIGINS=$CORS_ORIGINS" \
  --set "ENDPOINT=$S3_ENDPOINT" \
  --set "BUCKET=$S3_BUCKET" \
  --set "BUCKET_ACCESS_KEY_ID=$S3_ACCESS_KEY_ID" \
  --set "BUCKET_SECRET_ACCESS_KEY=$S3_SECRET_ACCESS_KEY" \
  --set "REGION=$S3_REGION" \
  --set "PHOENIX_ENABLED=$PHOENIX_ENABLED" \
  -e "$ENVIRONMENT" \
  -s "$SERVICE"

# Phoenix endpoint (apenas para production)
if [ "$ENVIRONMENT" == "production" ]; then
    railway variables --set "PHOENIX_COLLECTOR_ENDPOINT=$PHOENIX_ENDPOINT" -e "$ENVIRONMENT" -s "$SERVICE"
fi

echo ""
echo "✅ Secrets configurados para $ENVIRONMENT!"
echo ""
echo "📊 Resumo dos valores configurados:"
echo "   - Serviço: $SERVICE"
echo "   - Ambiente: $ENVIRONMENT"
echo "   - OPENAI_API_KEY: ${OPENAI_KEY:0:20}..."
echo "   - GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID:0:30}..."
echo "   - JWT_SECRET_KEY: ${JWT_SECRET_KEY:0:20}..."
echo "   - SESSION_SECRET_KEY: ${SESSION_SECRET_KEY:0:20}..."
echo "   - S3 BUCKET: $S3_BUCKET"
echo "   - OAUTH_REDIRECT_URI: $OAUTH_REDIRECT_URI"
echo "   - CORS_ORIGINS: $CORS_ORIGINS"
echo "   - WHITELIST: $WHITELIST"
echo ""
echo "⚠️  IMPORTANTE: Verifique os valores antes de usar em produção!"
if [ "$ENVIRONMENT" == "production" ]; then
    echo ""
    echo "🔴 Para PRODUÇÃO, você DEVE gerar novos valores para:"
    echo "   - JWT_SECRET_KEY: openssl rand -hex 32"
    echo "   - SESSION_SECRET_KEY: openssl rand -hex 32"
    echo "   - GOOGLE_CLIENT_SECRET: Use credenciais de produção do Google Cloud"
    echo ""
    echo "💡 Exemplo de uso com valores reais:"
    echo "   OPENAI_API_KEY=sk-... JWT_SECRET_KEY=\$(openssl rand -hex 32) \\"
    echo "   SESSION_SECRET_KEY=\$(openssl rand -hex 32) \\"
    echo "   GOOGLE_CLIENT_SECRET=GOCSPX-... \\"
    echo "   BUCKET=your-bucket BUCKET_ACCESS_KEY_ID=tid_... \\"
    echo "   BUCKET_SECRET_ACCESS_KEY=tsec_... \\"
    echo "   OAUTH_REDIRECT_URI=https://api.example.com/auth/callback \\"
    echo "   CORS_ORIGINS=https://app.example.com \\"
    echo "   WHITELIST=admin@example.com,@example.com \\"
    echo "   ./scripts/setup-railway-secrets.sh production $SERVICE"
fi
echo ""
echo "📖 Para verificar: railway variables -e $ENVIRONMENT -s $SERVICE"
echo "🔐 Para gerar secrets seguras: openssl rand -hex 32"
