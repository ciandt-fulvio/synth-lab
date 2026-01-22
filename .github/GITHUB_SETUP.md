# GitHub Actions Setup Guide

Este documento descreve como configurar secrets e variáveis necessárias para os workflows de CI/CD do synth-lab.

## 🔑 Entendendo Railway Tokens

Railway oferece dois tipos de tokens com usos diferentes:

### RAILWAY_API_TOKEN (Account/Team Token) ⭐ **USAMOS ESTE**
**Quando usar:**
- Comandos de gerenciamento: `railway link`, `railway whoami`, `railway list`
- Deploy com `--environment` flag: `railway up --environment staging`
- Acesso a múltiplos projetos e ambientes da conta/equipe

**Variável de ambiente:** `RAILWAY_API_TOKEN`

**Nos nossos workflows:** Usamos este token para todos os comandos porque ele tem acesso amplo e funciona com `railway link` + `railway up`.

### RAILWAY_TOKEN (Project Token) ℹ️ **NÃO USAMOS**
**Quando usar:**
- Deploy direto sem `railway link`: `railway up` (sem flags de environment)
- Escopo específico: um único ambiente dentro de um projeto
- Acesso limitado a variáveis de ambiente de um projeto específico

**Variável de ambiente:** `RAILWAY_TOKEN`

**Por que não usamos:** Precisaríamos de tokens separados para staging e production, tornando a configuração mais complexa.

---

## Secrets (GitHub Settings → Secrets → Actions)

### Required Secrets

| Secret Name | Description | Where to Get | Example/Notes |
|------------|-------------|--------------|---------------|
| `RAILWAY_API_TOKEN` | **Account Token** do Railway (acesso a todos os ambientes) | Railway Dashboard → Settings → Tokens | Use o token "API_TOKEN" ou "github20JAN26" existente |
| `RAILWAY_PROJECT_ID` | ID do projeto Railway | Railway Dashboard → Project Settings → Project ID | Mesmo ID para staging e production |
| `DATABASE_STAGING_URL` | PostgreSQL connection string para staging | Railway Dashboard → staging → PostgreSQL → Variables → DATABASE_URL | `postgresql://postgres:***@host:port/database` |
| `DATABASE_PRODUCTION_URL` | PostgreSQL connection string para produção | Railway Dashboard → production → PostgreSQL → Variables → DATABASE_URL | Similar ao staging, mas para produção |
| `OPENAI_API_KEY` | OpenAI API key (shared entre todos os ambientes) | OpenAI Dashboard → API Keys | Usado para testes, staging e produção |

**⚠️ IMPORTANTE:**
- Usamos `RAILWAY_API_TOKEN` (Account Token) para ter acesso a múltiplos ambientes
- NÃO usamos `RAILWAY_TOKEN` (Project Token) porque ele é específico para um único ambiente
- O controle de ambiente é feito via flags: `--environment staging` ou `--environment production`

## Variables (GitHub Settings → Variables → Actions)

### Staging URLs

| Variable Name | Description | Value | Where to Get |
|--------------|-------------|-------|--------------|
| `STAGING_FRONTEND_URL` | URL pública do frontend em staging | `https://synth-lab-frontend-staging.up.railway.app` | Railway Dashboard → staging → synth-lab-frontend → Settings → Domains |
| `STAGING_BACKEND_URL` | URL pública do backend em staging | `https://synth-lab-api-staging.up.railway.app` | Railway Dashboard → staging → synth-lab-api → Settings → Domains |

**NOTA**: As URLs acima NÃO incluem `https://` - apenas o domínio. O protocolo é adicionado automaticamente nos testes E2E.

### Production URLs (opcional - para documentação)

| Variable Name | Description | Example Value |
|--------------|-------------|---------------|
| `PRODUCTION_FRONTEND_URL` | URL pública do frontend em produção | `https://synth-lab-frontend-production.up.railway.app` |
| `PRODUCTION_BACKEND_URL` | URL pública do backend em produção | `https://synth-lab-api-production.up.railway.app` |

## Como Configurar

### 1. Acessar GitHub Settings
1. Vá para o repositório: https://github.com/[seu-usuario]/synth-lab
2. Clique em **Settings** (canto superior direito)
3. No menu lateral esquerdo, clique em **Secrets and variables** → **Actions**

### 2. Adicionar Secrets
1. Clique na aba **Secrets**
2. Clique em **New repository secret**
3. Insira o nome (ex: `RAILWAY_STAGING_TOKEN`)
4. Cole o valor do secret
5. Clique em **Add secret**
6. Repita para todos os secrets listados acima

### 3. Adicionar Variables
1. Clique na aba **Variables**
2. Clique em **New repository variable**
3. Insira o nome (ex: `STAGING_FRONTEND_URL`)
4. Cole o valor da variável
5. Clique em **Add variable**
6. Repita para todas as variáveis listadas acima

## Como Obter Railway Token

**IMPORTANTE**: Railway usa um único token de API que funciona para todos os ambientes. Não é necessário criar tokens separados para staging e production.

### Obter Token Existente
1. Acesse Railway Dashboard → Account Settings → Tokens
2. Você deve ver tokens como "API_TOKEN" ou "github20JAN26"
3. Use um desses tokens como `RAILWAY_TOKEN` no GitHub

### Criar Novo Token (se necessário)
```bash
# Via Railway Dashboard:
# 1. Railway Dashboard → Account Settings → Tokens
# 2. Click "Create New Token"
# 3. Name: "github-actions" (ou qualquer nome descritivo)
# 4. Workspace: Selecione "ciandt-fulvio's Projects" ou "No workspace"
# 5. Copie o token e adicione como RAILWAY_TOKEN no GitHub
```

**NOTA**: O mesmo token `RAILWAY_TOKEN` é usado para staging e production. O Railway CLI determina o ambiente via flag `--environment staging` ou `--environment production`.

## Validação

### Verificar Secrets Configurados
1. GitHub → Settings → Secrets and variables → Actions → Secrets
2. Deve listar:
   - `RAILWAY_API_TOKEN` ✅ (Account Token para todos os ambientes)
   - `RAILWAY_PROJECT_ID` ✅
   - `DATABASE_STAGING_URL` ✅
   - `DATABASE_PRODUCTION_URL` ✅
   - `OPENAI_API_KEY` ✅

### Verificar Variables Configuradas
1. GitHub → Settings → Secrets and variables → Actions → Variables
2. Deve listar:
   - `STAGING_FRONTEND_URL` ✅
   - `STAGING_BACKEND_URL` ✅

### Testar Workflows

#### 1. Testar Fast Tests (automático em push)
```bash
git checkout -b test-ci-setup
git commit --allow-empty -m "test: trigger fast tests"
git push origin test-ci-setup

# Verificar: GitHub Actions → Fast Tests deve rodar e passar
```

#### 2. Testar Deploy Staging (manual)
```bash
# GitHub → Actions → Deploy Staging → Run workflow
# Selecione branch "main"
# Click "Run workflow"

# Verificar:
# - Reset DB ✅
# - Migrate DB ✅
# - Seed DB ✅
# - Deploy Backend ✅
# - Deploy Frontend ✅
# - E2E Tests ✅
```

#### 3. Testar Deploy Production (manual)
```bash
# GitHub → Actions → Deploy Production → Run workflow
# Digite "deploy" no campo de confirmação
# Click "Run workflow"

# Verificar:
# - Validate Confirmation ✅
# - Migrate DB ✅
# - Deploy Backend ✅
# - Deploy Frontend ✅
# - Smoke Tests ✅
```

## Troubleshooting

### Erro: "RAILWAY_API_TOKEN not found"
- Verifique se o secret foi adicionado corretamente no GitHub
- Verifique se o nome está exatamente `RAILWAY_API_TOKEN` (case-sensitive)
- Certifique-se de usar um **Account Token** (não Project Token)
- Token deve ser visível em Railway Dashboard → Settings → Tokens

### Erro: "Failed to connect to Railway"
- Verifique se o token tem permissões corretas (staging ou production)
- Verifique se o `RAILWAY_PROJECT_ID` está correto

### Erro: "Database connection failed"
- Verifique se `DATABASE_STAGING_URL` ou `DATABASE_PRODUCTION_URL` estão corretos
- Verifique se o banco de dados está rodando no Railway
- Formato correto: `postgresql://user:password@host:port/database`

### Erro: "E2E tests failed on staging"
- Verifique se `STAGING_FRONTEND_URL` e `STAGING_BACKEND_URL` estão corretos
- Verifique se os serviços foram deployados com sucesso
- Verifique logs de deploy: GitHub Actions → Deploy Staging → Upload artifacts

## Próximos Passos

Após configurar todos os secrets e variáveis:

1. ✅ Testar push para qualquer branch (fast tests)
2. ✅ Criar PR para main (full tests + E2E)
3. ✅ Merge para main (deploy staging automático)
4. ✅ Deploy manual para produção (confirmar "deploy")

## Referências

- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [GitHub Actions Variables](https://docs.github.com/en/actions/learn-github-actions/variables)
- [Railway CLI Documentation](https://docs.railway.app/develop/cli)
- [Railway API Tokens](https://docs.railway.app/develop/tokens)
