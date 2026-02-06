# Deployment - synth-lab

## Pipeline CI/CD (Build Once, Deploy Everywhere)

```
git push origin main
       ↓
┌─ PRE-PUSH HOOK (local, ARM64) ──────────────────────────────────┐
│  Build images (ARM64, para testes locais)                        │
│  make test (unitários) + make test-e2e (Playwright)              │
│  Smart mode: detecta mudanças e pula builds/testes irrelevantes  │
└──────────────────────────────────────────────────────────────────┘
       ↓
┌─ BUILD IMAGES (GitHub Actions, AMD64 nativo) ────────────────────┐
│  Build backend + frontend em paralelo (~5 min)                    │
│  Push GHCR: :staging, :commit-sha, :latest                       │
└──────────────────────────────────────────────────────────────────┘
       ↓
┌─ DEPLOY STAGING (GitHub Actions) ────────────────────────────────┐
│  Gate: build-images passou?                                       │
│  Migrate DB (alembic upgrade head) + Seed condicional             │
│  Deploy backend + frontend → Railway                              │
│  Smoke tests (com auth via test-login)                            │
│  Tag :staging-verified                                            │
└──────────────────────────────────────────────────────────────────┘
       ↓
┌─ DEPLOY PRODUCTION (GitHub Actions) ─────────────────────────────┐
│  Gate: staging smoke tests passaram?                              │
│  Migrate DB (seguro, não dropa)                                   │
│  Retag :staging-verified → :production no GHCR                    │
│  Deploy backend + frontend → Railway                              │
│  Smoke tests (sem auth, apenas health checks)                     │
└──────────────────────────────────────────────────────────────────┘
```

**Tempo total**: ~20-30 min (push → production)

## Setup Inicial

```bash
git config core.hooksPath .githooks
```

## Railway

### Ambientes e URLs

| Ambiente | Frontend | Backend |
|----------|----------|---------|
| **Production** | https://synth-lab-frontend-production.up.railway.app | https://synth-lab-api-production.up.railway.app |
| **Staging** | https://synth-lab-frontend-staging.up.railway.app | https://synth-lab-api-staging.up.railway.app |

### Serviços por Ambiente

| Serviço | Tecnologia |
|---------|------------|
| synth-lab-frontend | React 18 + Vite |
| synth-lab-api | Python 3.13 + FastAPI |
| Postgres | PostgreSQL 17 |

### Verificar Deploy

```bash
curl -s https://synth-lab-api-production.up.railway.app/health | jq .version
# Comparar com: git rev-parse HEAD
```

## Docker (Desenvolvimento Local)

### Profiles

| Profile | Propósito | Portas |
|---------|-----------|--------|
| `dev` | Desenvolvimento com hot reload | frontend: 8080, backend: 8000, postgres: 5432 |
| `test` | Testes E2E isolados | frontend: 8091, backend: 8001, postgres: 5433 |

### Comandos

```bash
make dev-up           # Iniciar dev
make dev-down         # Parar dev
make dev-logs         # Ver logs dev

make test-e2e         # Build + start + test + cleanup
make test-e2e-docker-up    # Iniciar ambiente teste (para debug)
make test-e2e-docker-down  # Parar ambiente teste
```

### Estrutura Docker

```
docker/
├── docker-compose.yml       # Compose unificado com profiles
├── .env.dev                 # Variáveis dev
├── .env.test                # Variáveis test
├── backend/Dockerfile.dev   # Dev (volume mounts)
├── frontend/Dockerfile.dev  # Dev (HMR)
└── postgres/init-scripts/

Dockerfile                   # Produção backend
frontend/Dockerfile          # Produção frontend
```

## Secrets e Variáveis

### GitHub Actions Secrets

| Secret | Descrição |
|--------|-----------|
| `OPENAI_API_KEY` | Chave OpenAI para testes |
| `RAILWAY_API_TOKEN` | Token API Railway |
| `RAILWAY_PROJECT_ID` | ID do projeto Railway |
| `DATABASE_STAGING_URL` | URL Postgres staging |
| `DATABASE_PRODUCTION_URL` | URL Postgres production |

### GitHub Actions Variables

| Variable | Descrição |
|----------|-----------|
| `STAGING_BACKEND_URL` | URL backend staging |
| `STAGING_FRONTEND_URL` | URL frontend staging |
| `PRODUCTION_BACKEND_URL` | URL backend production |
| `PRODUCTION_FRONTEND_URL` | URL frontend production |

### Railway Variables (Backend)

```bash
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...
ENVIRONMENT=staging|production
JWT_SECRET_KEY=...          # Gerar: openssl rand -hex 32
SESSION_SECRET_KEY=...      # Gerar: openssl rand -hex 32
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
CORS_ORIGINS=https://frontend-url
```

### Comandos para Setup

```bash
# GitHub Secrets
gh secret set OPENAI_API_KEY --body "sk-..."
gh secret set RAILWAY_API_TOKEN --body "..."

# GitHub Variables
gh variable set STAGING_BACKEND_URL --body "https://..."
```

## Decisões Arquiteturais

1. **Build local é ARM64 nativo** (sem QEMU) — imagens locais servem apenas para testes. AMD64 para Railway é buildado no GitHub Actions.
2. **Railway usa Docker Image source** — deploy via GraphQL API (`serviceInstanceUpdate`).
3. **Production retag** — staging-verified → production no GHCR, depois redeploy no Railway.
4. **Smoke tests diferem por ambiente**: staging com auth, production apenas health checks.
5. **Seed condicional** — `scripts/seed_database.py` verifica se `synth_groups` tem dados antes de executar.

## Comandos Úteis

```bash
# Acompanhar pipeline
gh run list --limit 10
gh run watch
gh run view <run-id> --log-failed

# Smoke tests contra ambientes remotos
make test-smoke-staging
make test-smoke-production

# Deploy manual
gh workflow run deploy-staging.yml
gh workflow run deploy-production.yml

# Deploy production com fresh start (DESTROI DADOS)
gh workflow run deploy-production.yml -f fresh_start=true

# Rollback
railway rollback --environment production
```

## Emergência: Desabilitar Auto-Deploy

Editar `.github/workflows/deploy-production.yml`, comentar trigger `workflow_run`. Production passa a usar apenas `workflow_dispatch` (manual).
