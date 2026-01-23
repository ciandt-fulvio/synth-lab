#!/bin/bash
# Setup Railway Environment Variables (Secrets)
#
# Este script:
# 1. Carrega credenciais do docker/.env.dev (secrets, API keys, etc.)
# 2. Inspeciona o Railway para descobrir URLs dos serviços automaticamente
# 3. Configura todas as variáveis no ambiente especificado
# 4. Informa o que ainda precisa ser configurado manualmente
#
# Usage: ./scripts/setup-railway-secrets.sh <staging|production> <service-name>
# Example: ./scripts/setup-railway-secrets.sh staging synth-lab-api

set -e

ENVIRONMENT=${1:-}
SERVICE=${2:-}

# ============================================================================
# Validação de argumentos
# ============================================================================

if [ -z "$ENVIRONMENT" ]; then
    echo "❌ Erro: Ambiente é obrigatório"
    echo ""
    echo "Usage: $0 <staging|production> <service-name>"
    echo ""
    echo "Examples:"
    echo "  $0 staging synth-lab-api"
    echo "  $0 production synth-lab-api"
    exit 1
fi

if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    echo "❌ Erro: Ambiente deve ser 'staging' ou 'production'"
    exit 1
fi

if [ -z "$SERVICE" ]; then
    echo "❌ Erro: Nome do serviço é obrigatório"
    echo ""
    echo "Usage: $0 $ENVIRONMENT <service-name>"
    echo ""
    echo "Para ver serviços disponíveis: railway status"
    exit 1
fi

# ============================================================================
# Verificações do Railway CLI
# ============================================================================

if ! command -v railway &> /dev/null; then
    echo "❌ Erro: Railway CLI não instalado"
    echo "Instale com: npm install -g @railway/cli"
    exit 1
fi

if ! railway whoami &> /dev/null; then
    echo "❌ Erro: Você precisa estar logado no Railway CLI"
    echo "Execute: railway login"
    exit 1
fi

if ! railway status &> /dev/null; then
    echo "❌ Erro: Você precisa estar linkado a um projeto Railway"
    echo "Execute: railway link"
    exit 1
fi

echo "🚂 Configurando Railway Secrets"
echo "   Ambiente: $ENVIRONMENT"
echo "   Serviço: $SERVICE"
echo ""

# ============================================================================
# Carregar credenciais do .env.dev (NÃO URLs)
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/docker/.env.dev"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Erro: Arquivo docker/.env.dev não encontrado!"
    exit 1
fi

echo "📂 Carregando credenciais de docker/.env.dev..."

# Carregar APENAS credenciais (não URLs) do .env.dev
while IFS='=' read -r key value; do
    # Ignorar comentários e linhas vazias
    [[ "$key" =~ ^#.*$ ]] && continue
    [[ -z "$key" ]] && continue

    # Ignorar variáveis de URL/endereço - serão descobertas via Railway
    case "$key" in
        DATABASE_URL|BACKEND_URL|FRONTEND_URL|OAUTH_REDIRECT_URI|CORS_ORIGINS|\
        PHOENIX_COLLECTOR_ENDPOINT|API_HOST|API_PORT|VITE_*|POSTGRES_*)
            continue
            ;;
    esac

    # Exportar a variável
    export "$key=$value"
done < <(grep -v '^#' "$ENV_FILE" | grep -v '^$' | grep '=')

# ============================================================================
# Inspecionar Railway para descobrir URLs dos serviços
# ============================================================================

echo "🔍 Inspecionando serviços no Railway..."

# Função para obter domínio de um serviço
get_service_domain() {
    local svc_name="$1"
    local env="$2"

    # Tentar obter domínio via railway domain
    local domain
    domain=$(railway domain -s "$svc_name" -e "$env" 2>/dev/null | grep -oE 'https?://[^ ]+' | head -1) || true

    if [ -n "$domain" ]; then
        echo "$domain"
        return 0
    fi

    # Fallback: construir URL padrão do Railway
    # Formato: https://<service>-<environment>.up.railway.app
    if [ "$env" == "production" ]; then
        echo "https://${svc_name}.up.railway.app"
    else
        echo "https://${svc_name}-${env}.up.railway.app"
    fi
}

# Descobrir URLs dos serviços
BACKEND_SERVICE="synth-lab-api"
FRONTEND_SERVICE="synth-lab-frontend"
POSTGRES_SERVICE="synthlab-postgres"

echo "   Buscando URL do backend ($BACKEND_SERVICE)..."
BACKEND_URL=$(get_service_domain "$BACKEND_SERVICE" "$ENVIRONMENT")
echo "   ✓ Backend: $BACKEND_URL"

echo "   Buscando URL do frontend ($FRONTEND_SERVICE)..."
FRONTEND_URL=$(get_service_domain "$FRONTEND_SERVICE" "$ENVIRONMENT")
echo "   ✓ Frontend: $FRONTEND_URL"

# Descobrir DATABASE_URL do PostgreSQL no Railway
echo "   Buscando DATABASE_URL..."
DATABASE_URL=""

# Tentar obter DATABASE_URL das variáveis existentes do serviço PostgreSQL
DB_VAR=$(railway variables -e "$ENVIRONMENT" -s "$POSTGRES_SERVICE" 2>/dev/null | grep -E "^DATABASE_URL=" | cut -d'=' -f2- || true)
if [ -n "$DB_VAR" ]; then
    DATABASE_URL="$DB_VAR"
    echo "   ✓ DATABASE_URL: encontrada no serviço $POSTGRES_SERVICE"
else
    # Tentar obter do serviço de backend (pode já estar linkado)
    DB_VAR=$(railway variables -e "$ENVIRONMENT" -s "$SERVICE" 2>/dev/null | grep -E "^DATABASE_URL=" | cut -d'=' -f2- || true)
    if [ -n "$DB_VAR" ]; then
        DATABASE_URL="$DB_VAR"
        echo "   ✓ DATABASE_URL: já configurada no $SERVICE"
    else
        echo "   ⚠ DATABASE_URL: não encontrada (será adicionada aos pendentes)"
    fi
fi

# Construir URLs derivadas
OAUTH_REDIRECT_URI="${BACKEND_URL}/auth/callback"
CORS_ORIGINS="$FRONTEND_URL"

echo ""
echo "📋 URLs descobertas automaticamente:"
echo "   - BACKEND_URL: $BACKEND_URL"
echo "   - FRONTEND_URL: $FRONTEND_URL"
echo "   - OAUTH_REDIRECT_URI: $OAUTH_REDIRECT_URI"
echo "   - CORS_ORIGINS: $CORS_ORIGINS"
if [ -n "$DATABASE_URL" ]; then
    # Mostrar URL mascarada (esconder senha)
    DB_MASKED=$(echo "$DATABASE_URL" | sed 's/:[^:@]*@/:****@/')
    echo "   - DATABASE_URL: $DB_MASKED"
fi
echo ""

# ============================================================================
# Validar variáveis obrigatórias
# ============================================================================

echo "🔍 Validando variáveis obrigatórias..."

MISSING_VARS=()
MISSING_MANUAL=()

# Credenciais que devem vir do .env.dev
[ -z "$GOOGLE_CLIENT_ID" ] && MISSING_VARS+=("GOOGLE_CLIENT_ID")
[ -z "$GOOGLE_CLIENT_SECRET" ] && MISSING_VARS+=("GOOGLE_CLIENT_SECRET")
[ -z "$JWT_SECRET_KEY" ] && MISSING_VARS+=("JWT_SECRET_KEY")
[ -z "$SESSION_SECRET_KEY" ] && MISSING_VARS+=("SESSION_SECRET_KEY")
[ -z "$BUCKET" ] && MISSING_VARS+=("BUCKET")
[ -z "$BUCKET_ACCESS_KEY_ID" ] && MISSING_VARS+=("BUCKET_ACCESS_KEY_ID")
[ -z "$BUCKET_SECRET_ACCESS_KEY" ] && MISSING_VARS+=("BUCKET_SECRET_ACCESS_KEY")

# OpenAI key - usar do ambiente local se disponível
OPENAI_KEY="${OPENAI_API_KEY:-}"
if [ -n "$OPENAI_KEY" ]; then
    echo "   ✓ OPENAI_API_KEY encontrada no ambiente local"
fi

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "❌ Erro: Variáveis não encontradas no docker/.env.dev:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Adicione essas variáveis ao arquivo docker/.env.dev"
    exit 1
fi

echo "✅ Todas as credenciais encontradas"
echo ""

# ============================================================================
# Configurar variáveis no Railway
# ============================================================================

echo "📝 Configurando variáveis no Railway ($ENVIRONMENT / $SERVICE)..."
echo ""

# Definir ENVIRONMENT_NAME baseado no ambiente
if [ "$ENVIRONMENT" == "staging" ]; then
    ENVIRONMENT_NAME="staging"
    PHOENIX_ENABLED="false"
else
    ENVIRONMENT_NAME="production"
    PHOENIX_ENABLED="true"
fi

railway variables \
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
  --set "LOG_LEVEL=INFO" \
  -e "$ENVIRONMENT" \
  -s "$SERVICE"

# Configurar OPENAI_API_KEY se disponível no ambiente local
if [ -n "$OPENAI_KEY" ]; then
    railway variables --set "OPENAI_API_KEY=$OPENAI_KEY" -e "$ENVIRONMENT" -s "$SERVICE"
    echo "   ✓ OPENAI_API_KEY configurada"
else
    MISSING_MANUAL+=("OPENAI_API_KEY (defina no ambiente local: export OPENAI_API_KEY=sk-... e rode novamente)")
fi

# Configurar DATABASE_URL se descoberta
if [ -n "$DATABASE_URL" ]; then
    railway variables --set "DATABASE_URL=$DATABASE_URL" -e "$ENVIRONMENT" -s "$SERVICE"
    echo "   ✓ DATABASE_URL configurada"
else
    MISSING_MANUAL+=("DATABASE_URL (link o PostgreSQL ao serviço no Railway Dashboard)")
fi

# Phoenix endpoint apenas para production
if [ "$ENVIRONMENT" == "production" ]; then
    railway variables --set "PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006" -e "$ENVIRONMENT" -s "$SERVICE"
fi

echo ""
echo "✅ Variáveis configuradas com sucesso!"
echo ""

# ============================================================================
# Resumo e itens pendentes
# ============================================================================

echo "📊 Resumo da configuração:"
echo "   ┌─────────────────────────────────────────────────────────────────┐"
echo "   │ Serviço:        $SERVICE"
echo "   │ Ambiente:       $ENVIRONMENT_NAME"
echo "   │ Backend URL:    $BACKEND_URL"
echo "   │ Frontend URL:   $FRONTEND_URL"
echo "   │ CORS Origins:   $CORS_ORIGINS"
echo "   │ OAuth Redirect: $OAUTH_REDIRECT_URI"
if [ -n "$DATABASE_URL" ]; then
echo "   │ Database:       ✓ Configurada"
else
echo "   │ Database:       ❌ Pendente"
fi
if [ -n "$OPENAI_KEY" ]; then
echo "   │ OpenAI API:     ✓ Configurada"
else
echo "   │ OpenAI API:     ❌ Pendente"
fi
echo "   └─────────────────────────────────────────────────────────────────┘"
echo ""

# Listar itens que precisam de configuração manual
if [ ${#MISSING_MANUAL[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  AÇÃO NECESSÁRIA - Configure manualmente no Railway Dashboard:"
    echo ""
    for item in "${MISSING_MANUAL[@]}"; do
        echo "   ❌ $item"
    done
    echo ""
    echo "   Dashboard: https://railway.app"
fi

echo ""
echo "📖 Para verificar todas as variáveis:"
echo "   railway variables -e $ENVIRONMENT -s $SERVICE"
echo ""

if [ "$ENVIRONMENT" == "production" ]; then
    echo "🔴 ATENÇÃO: Ambiente de PRODUÇÃO!"
    echo "   Considere gerar novos valores de segurança:"
    echo "   - JWT_SECRET_KEY: openssl rand -hex 32"
    echo "   - SESSION_SECRET_KEY: openssl rand -hex 32"
    echo ""
fi
