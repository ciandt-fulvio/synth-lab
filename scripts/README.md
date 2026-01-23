# 🔐 Scripts de Configuração de Secrets

Guia rápido para configurar secrets no GitHub e Railway.

## 📋 Pré-requisitos

### GitHub CLI
```bash
# Verificar se está instalado
gh --version

# Fazer login
gh auth login

# Verificar autenticação
gh auth status
```

### Railway CLI
```bash
# Verificar se está instalado
railway --version

# Fazer login
railway login

# Verificar autenticação
railway whoami
```

## 🚀 Uso Rápido

### 1️⃣ GitHub Secrets

```bash
# Opção A: Passar valores via variáveis de ambiente (RECOMENDADO)
OPENAI_API_KEY=sk-proj-xxx \
RAILWAY_API_TOKEN=your-token \
RAILWAY_PROJECT_ID=your-project-id \
DATABASE_STAGING_URL=postgresql://... \
DATABASE_PRODUCTION_URL=postgresql://... \
STAGING_FRONTEND_URL=https://your-frontend-staging.railway.app \
STAGING_BACKEND_URL=https://your-backend-staging.railway.app \
./scripts/setup-github-secrets.sh

# Opção B: Exportar variáveis e executar
export OPENAI_API_KEY=sk-proj-xxx
export RAILWAY_API_TOKEN=your-token
# ... outras variáveis
./scripts/setup-github-secrets.sh

# Opção C: Editar o script diretamente (NÃO RECOMENDADO)
# Substitua os placeholders e execute
./scripts/setup-github-secrets.sh
```

**Verificar:**
```bash
gh secret list
gh variable list
```

---

### 2️⃣ Railway Secrets

**IMPORTANTE:** Primeiro você precisa linkar o projeto Railway.

```bash
# Linkar ao projeto
railway link

# Verificar status e ver serviços disponíveis
railway status
# Output exemplo:
#   Project: sunny-caring
#   Environment: staging
#   Service: None
```

Depois de linkado, você precisa especificar o **serviço** onde as variáveis serão configuradas:

```bash
# Para STAGING (pode usar valores do docker/.env.dev)
./scripts/setup-railway-secrets.sh staging synth-lab-api

# Para PRODUCTION (DEVE passar valores novos e seguros)
OPENAI_API_KEY=sk-proj-xxx \
JWT_SECRET_KEY=$(openssl rand -hex 32) \
SESSION_SECRET_KEY=$(openssl rand -hex 32) \
GOOGLE_CLIENT_SECRET=GOCSPX-xxx \
BUCKET=your-production-bucket \
BUCKET_ACCESS_KEY_ID=tid_xxx \
BUCKET_SECRET_ACCESS_KEY=tsec_xxx \
OAUTH_REDIRECT_URI=https://api.yourapp.com/auth/callback \
CORS_ORIGINS=https://yourapp.com \
WHITELIST=admin@yourcompany.com,@yourcompany.com \
./scripts/setup-railway-secrets.sh production synth-lab-api
```

**Verificar:**
```bash
railway variables -e staging
railway variables -e production

# Ver em formato KV (chave=valor)
railway variables --kv -e staging
```

---

## 🔑 Gerando Secrets Seguras

### JWT e Session Keys
```bash
# Gerar JWT Secret Key
openssl rand -hex 32

# Gerar Session Secret Key
openssl rand -hex 32
```

### Railway API Token
1. Acesse: https://railway.app/account/tokens
2. Click "Create Token"
3. Nomeie: "GitHub Actions CI/CD"
4. Copie o token (mostrado apenas uma vez!)

### Railway Project ID
```bash
# Ver informações do projeto
railway status

# Ou visite Railway Dashboard > Settings > Project ID
```

### Database URLs
Railway provisiona automaticamente:
1. Railway Dashboard > Environment (staging/production)
2. Click "+ New" > "Database" > "PostgreSQL"
3. Aguarde provisionamento
4. Copie `DATABASE_URL` de Variables

---

## 🐛 Troubleshooting

### GitHub: "gh: command not found"
```bash
# macOS
brew install gh

# Ubuntu/Debian
sudo apt install gh

# Ver outros: https://github.com/cli/cli#installation
```

### GitHub: "authentication required"
```bash
gh auth login
# Siga as instruções no terminal
```

### Railway: "command not found"
```bash
# macOS
brew install railway

# npm (qualquer SO)
npm install -g @railway/cli

# Ver outros: https://docs.railway.app/develop/cli#installation
```

### Railway: "No service linked"
```bash
# Linkar ao projeto
railway link

# Selecionar/criar serviço
railway service

# Verificar status
railway status
```

### Railway: "environment not found"
```bash
# Listar ambientes disponíveis
railway environment

# Criar novo ambiente (via Dashboard)
# Railway Dashboard > Environments > New Environment
```

### Railway: Variáveis não aparecem após configurar
```bash
# Forçar redeploy para aplicar variáveis
railway up -e staging

# Verificar variáveis configuradas
railway variables -e staging
```

---

## 📖 Documentação Completa

Para documentação detalhada, veja:
- [docs/SECRETS_SETUP.md](../docs/SECRETS_SETUP.md) - Guia completo de secrets

## ⚠️ Segurança

### ✅ Fazer
- Usar variáveis de ambiente para passar secrets
- Gerar novos JWT/Session keys para produção
- Usar credenciais OAuth específicas para produção
- Verificar valores antes de aplicar em produção
- Manter `.env.dev` no `.gitignore`

### ❌ Nunca
- Commitar secrets no git
- Reusar secrets de dev em produção
- Compartilhar secrets em canais públicos
- Logar secrets no console
- Editar scripts com valores reais e commitar

---

## 📝 Checklist Rápido

### GitHub Actions
- [ ] `OPENAI_API_KEY` configurada
- [ ] `RAILWAY_API_TOKEN` configurada
- [ ] `RAILWAY_PROJECT_ID` configurada
- [ ] `DATABASE_STAGING_URL` configurada
- [ ] `DATABASE_PRODUCTION_URL` configurada
- [ ] `STAGING_FRONTEND_URL` configurada (variable)
- [ ] `STAGING_BACKEND_URL` configurada (variable)

### Railway Staging
- [ ] Projeto linkado (`railway link`)
- [ ] Serviço selecionado (se necessário)
- [ ] Script executado (`./scripts/setup-railway-secrets.sh staging`)
- [ ] Variáveis verificadas (`railway variables -e staging`)

### Railway Production
- [ ] Gerado novo `JWT_SECRET_KEY` (`openssl rand -hex 32`)
- [ ] Gerado novo `SESSION_SECRET_KEY` (`openssl rand -hex 32`)
- [ ] Configurado `GOOGLE_CLIENT_SECRET` de produção
- [ ] Configurado bucket S3 de produção
- [ ] Ajustado `WHITELIST` para usuários autorizados
- [ ] Configurado URLs corretas (OAUTH_REDIRECT_URI, CORS_ORIGINS)
- [ ] Script executado com valores de produção
- [ ] Variáveis verificadas (`railway variables -e production`)
- [ ] Deploy testado

---

## 🔗 Links Úteis

- [GitHub CLI Docs](https://cli.github.com/manual/)
- [Railway CLI Docs](https://docs.railway.app/develop/cli)
- [Railway API Tokens](https://railway.app/account/tokens)
- [OpenAI API Keys](https://platform.openai.com/api-keys)
- [Google Cloud Console](https://console.cloud.google.com/)
