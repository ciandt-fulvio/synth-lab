# 🔐 Guia de Configuração de Secrets

Este documento descreve todas as secrets necessárias para GitHub Actions e Railway, com comandos prontos para configurá-las.

## 📋 Índice
- [GitHub Actions Secrets](#github-actions-secrets)
- [GitHub Actions Variables](#github-actions-variables)
- [Railway Environment Variables](#railway-environment-variables)
- [Comandos de Setup](#comandos-de-setup)
- [Gerando Secrets Seguras](#gerando-secrets-seguras)

---

## GitHub Actions Secrets

Usados nos workflows de CI/CD (`.github/workflows/*.yml`)

| Secret | Descrição | Onde Obter | Usado Em |
|--------|-----------|------------|----------|
| `OPENAI_API_KEY` | Chave da API OpenAI para testes | https://platform.openai.com/api-keys | tests-pr.yml, tests-e2e.yml, deploy-staging.yml |
| `RAILWAY_API_TOKEN` | Token de acesso à API Railway | https://railway.app/account/tokens | deploy.yml, deploy-staging.yml |
| `RAILWAY_PROJECT_ID` | ID do projeto Railway | `railway status` ou Railway Dashboard | deploy.yml, deploy-staging.yml |
| `DATABASE_STAGING_URL` | URL do PostgreSQL staging | Railway Dashboard > Staging > PostgreSQL > Variables | deploy-staging.yml |
| `DATABASE_PRODUCTION_URL` | URL do PostgreSQL production | Railway Dashboard > Production > PostgreSQL > Variables | deploy.yml |

### Comandos para configurar GitHub Secrets

```bash
# 1. OpenAI API Key
gh secret set OPENAI_API_KEY --body "sk-proj-..."

# 2. Railway API Token
gh secret set RAILWAY_API_TOKEN --body "YOUR_RAILWAY_TOKEN"

# 3. Railway Project ID
gh secret set RAILWAY_PROJECT_ID --body "YOUR_PROJECT_ID"

# 4. Database URLs
gh secret set DATABASE_STAGING_URL --body "postgresql://..."
gh secret set DATABASE_PRODUCTION_URL --body "postgresql://..."
```

---

## GitHub Actions Variables

Configurações públicas (não-sensíveis)

| Variable | Valor | Descrição |
|----------|-------|-----------|
| `STAGING_FRONTEND_URL` | https://YOUR-FRONTEND-STAGING.railway.app | URL do frontend staging |
| `STAGING_BACKEND_URL` | https://YOUR-BACKEND-STAGING.railway.app | URL do backend staging |

### Comandos para configurar GitHub Variables

```bash
gh variable set STAGING_FRONTEND_URL --body "https://front..."
gh variable set STAGING_BACKEND_URL --body "https://back..."
```

---

## Railway Environment Variables

Configuradas por ambiente (staging/production)

### Secrets Críticas (DEVEM ser diferentes em produção)

| Variável | Valor Dev | Produção | Como Gerar |
|----------|-----------|----------|------------|
| `JWT_SECRET_KEY` | ⚠️ GERAR | ⚠️ GERAR NOVO | `openssl rand -hex 32` |
| `SESSION_SECRET_KEY` | ⚠️ GERAR | ⚠️ GERAR NOVO | `openssl rand -hex 32` |
| `GOOGLE_CLIENT_SECRET` | ⚠️ GERAR | ⚠️ USAR PROD | Google Cloud Console |

### OAuth & Authentication

| Variável | Staging | Production |
|----------|---------|------------|
| `GOOGLE_CLIENT_ID` | YOUR-GOOGLE-CLIENT-ID.apps.googleusercontent.com | (mesmo ou específico para prod) |
| `OAUTH_REDIRECT_URI` | https://YOUR-BACKEND-STAGING.railway.app/auth/callback | https://YOUR-BACKEND-PRODUCTION.railway.app/auth/callback |
| `JWT_ALGORITHM` | HS256 | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 10080 (7 dias) | 10080 (7 dias) |
| `WHITELIST` | user@example.com,@example.com | (ajustar conforme necessário) |

### CORS & Environment

| Variável | Staging | Production |
|----------|---------|------------|
| `CORS_ORIGINS` | https://YOUR-FRONTEND-STAGING.railway.app | https://YOUR-FRONTEND-PRODUCTION.railway.app |
| `ENVIRONMENT` | staging | production |

### S3 Storage (Railway Buckets)

| Variável | Valor |
|----------|-------|
| `ENDPOINT` | https://storage.railway.app |
| `BUCKET` | YOUR-BUCKET-NAME |
| `BUCKET_ACCESS_KEY_ID` | YOUR-BUCKET-ACCESS-KEY-ID |
| `BUCKET_SECRET_ACCESS_KEY` | YOUR-BUCKET-SECRET-ACCESS-KEY |
| `REGION` | auto |

### Observability (Phoenix)

| Variável | Staging | Production |
|----------|---------|------------|
| `PHOENIX_ENABLED` | false | true |
| `PHOENIX_COLLECTOR_ENDPOINT` | - | http://localhost:6006 |

### Database

| Variável | Descrição |
|----------|-----------|
| `DATABASE_URL` | ✅ Provisionado automaticamente pelo Railway quando você adiciona PostgreSQL |

---

## Comandos de Setup

### Setup Completo GitHub

```bash
# Executar script automatizado
chmod +x scripts/setup-github-secrets.sh
./scripts/setup-github-secrets.sh

# Verificar configuração
gh secret list
gh variable list
```

### Setup Completo Railway

```bash
# Fazer login no Railway
railway login

# Link ao projeto
railway link

# Configurar staging
chmod +x scripts/setup-railway-secrets.sh
./scripts/setup-railway-secrets.sh staging

# Configurar production
./scripts/setup-railway-secrets.sh production

# Verificar configuração
railway variables -e staging
railway variables -e production
```

### Comandos Individuais Railway

```bash
# Configurar uma variável específica
railway variables --set "OPENAI_API_KEY=sk-proj-..." -e staging

# Configurar múltiplas variáveis de uma vez
railway variables \
  --set "OPENAI_API_KEY=sk-proj-..." \
  --set "JWT_SECRET_KEY=abc123..." \
  -e staging

# Listar todas variáveis
railway variables -e staging

# Ver variáveis em formato KV (chave=valor)
railway variables --kv -e staging
```

---

## Gerando Secrets Seguras

### JWT Secret Key
```bash
openssl rand -hex 32
# Output: <64 caracteres hexadecimais>
```

### Session Secret Key
```bash
openssl rand -hex 32
# Output: <64 caracteres hexadecimais>
```

### Railway API Token
1. Acesse: https://railway.app/account/tokens
2. Click "Create Token"
3. Nomeie: "GitHub Actions CI/CD"
4. Copie o token (só é mostrado uma vez!)

### Railway Project ID
```bash
railway status
# ou visite Railway Dashboard > Settings > Project ID
```

### Database URLs
Railway provisiona automaticamente quando você adiciona PostgreSQL:
1. Railway Dashboard > Environment (staging/production)
2. Click "+ New" > "Database" > "PostgreSQL"
3. Aguarde provisionamento
4. Copie `DATABASE_URL` de Variables

---

## Checklist de Segurança

### ✅ Antes de ir para Produção

- [ ] Gerar novo `JWT_SECRET_KEY` para produção
- [ ] Gerar novo `SESSION_SECRET_KEY` para produção
- [ ] Verificar credenciais Google OAuth (usar prod se disponível)
- [ ] Atualizar `WHITELIST` com emails/domínios autorizados
- [ ] Configurar `OPENAI_API_KEY` válida
- [ ] Verificar URLs de CORS corretas
- [ ] Testar `OAUTH_REDIRECT_URI` funciona
- [ ] Validar acesso S3 funciona (upload/download)
- [ ] Confirmar `DATABASE_URL` aponta para prod

### ⚠️ NUNCA

- ❌ Commitar secrets no git
- ❌ Usar secrets de dev em produção
- ❌ Compartilhar secrets em canais públicos
- ❌ Logar secrets no console/arquivos
- ❌ Reusar secrets entre ambientes

---

## Troubleshooting

### GitHub Actions não encontra secret
```bash
# Verificar se existe
gh secret list

# Reconfigurar
gh secret set SECRET_NAME --body "value"
```

### Railway não aplica variáveis
```bash
# Forçar redeploy
railway up -e staging

# Verificar se a variável existe
railway variables -e staging
```

### Database URL inválida
```bash
# Formato correto
postgresql://user:password@host:port/database

# Exemplo Railway
postgresql://postgres:password@containers-us-west-123.railway.app:5432/railway
```

---

## Referências

- [GitHub CLI - Secrets](https://cli.github.com/manual/gh_secret)
- [Railway CLI - Variables](https://docs.railway.app/develop/cli#variables)
- [OpenAI API Keys](https://platform.openai.com/api-keys)
- [Railway Tokens](https://railway.app/account/tokens)
