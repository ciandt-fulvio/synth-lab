# synth-lab Development Guidelines

## Tech Stack
- **Backend**: Python 3.13+, FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK
- **Frontend**: TypeScript 5.5+, React 18, TanStack Query, shadcn/ui, Tailwind CSS
- **Database**: PostgreSQL 14+
- **Observability**: Arize Phoenix, OpenTelemetry

## Project Structure
```
src/synth_lab/
├── api/            # FastAPI routers
├── domain/         # Business entities
├── services/       # Business logic
├── repositories/   # Data access (SQL)
└── infrastructure/ # Config, DB, external clients

frontend/src/
├── pages/          # Page components
├── components/     # Reusable UI
├── hooks/          # React Query hooks
├── services/       # API clients (fetchAPI)
└── lib/query-keys.ts
```

## Commands
```bash
# Backend
uv run uvicorn synth_lab.api.main:app --reload

# Testing (see docs/testing.md for details)
pytest                    # Fast tests only (excludes real API calls)
pytest -m "not slow"      # Explicitly exclude slow tests
pytest -m integration     # Only integration tests (mocked APIs)
pytest -m "real_api"      # Only smoke tests with real APIs (costs money!)

# Code quality
ruff check . && ruff format .

# Frontend
cd frontend && npm run dev
npm run lint
```

## Git Workflow & Merge (CRITICAL - ALWAYS FOLLOW)

### 🚨 REGRA FUNDAMENTAL: MERGE = LOCAL, PUSH = REMOTE

**IMPORTANTE**: `git merge` é LOCAL (não envia nada). `git push` é REMOTO (envia para GitHub).
O **pre-push hook** (testes E2E) SÓ roda no `git push`, NÃO no `git merge`.

### 📋 Quando o Usuário Pedir "Merge" ou "Mergear Branch"

**SEMPRE use o script helper**:
```bash
./scripts/merge-to-main.sh <branch-name>
```

**NUNCA** faça merge manual diretamente. O script garante:
- ✅ Verificações de segurança (mudanças não commitadas, branch existe)
- ✅ Atualização da main antes do merge
- ✅ Preview dos commits que serão mergeados
- ✅ Confirmação antes de executar
- ✅ Lembrete para fazer push (onde o pre-push hook rodará)

### 🔄 Fluxo Completo de Merge

```bash
# 1. Usuario pede: "merge a branch 039 na main"
# 2. Claude executa:
./scripts/merge-to-main.sh 039-narrative-mechanism-config

# O script faz:
#   - Checkout main
#   - Pull latest
#   - Mostra preview
#   - Faz merge (LOCAL - nada enviado ainda!)
#   - Pergunta se quer fazer push

# 3. Quando fizer push (manual ou pelo script):
git push origin main
# ↑ PRE-PUSH HOOK RODA AQUI:
#   - Build Docker images
#   - make test (testes unitários)
#   - make test-e2e (testes E2E)
#   - Push de imagens para GHCR
#   - Permite push se tudo passar
```

### 📊 Scripts Disponíveis

1. **scripts/merge-to-main.sh** - Helper para merge (USE SEMPRE)
   ```bash
   ./scripts/merge-to-main.sh <branch-name>
   ```

2. **scripts/test-pre-push-hook.sh** - Diagnóstico do pre-push hook
   ```bash
   ./scripts/test-pre-push-hook.sh
   ```

3. **docs/testing-pre-push-hook.md** - Documentação completa do hook
4. **docs/testing.md** - Documentação de testes e smart mode

### 🚀 Smart Mode (Otimização Automática)

O pre-push hook agora usa **detecção inteligente de mudanças** para otimizar builds e testes:

**Como funciona:**
- Detecta quais arquivos mudaram desde `origin/main`
- Classifica mudanças: backend, frontend, docs, config
- Pula builds/testes desnecessários de forma segura
- Usa cache do GHCR para acelerar builds

**Economia de tempo:**
- Apenas docs: ~5 segundos (antes: 5-10 min) → 98% mais rápido
- Apenas backend: ~2-3 min (antes: 5-10 min) → 60% mais rápido
- Apenas frontend: ~2-3 min (antes: 5-10 min) → 60% mais rápido
- Config mudou: 5-10 min (full validation, sem skip)

**Exemplo de saída:**
```
🔍 Detecting changes since origin/main...
  Changed files:
    - src/synth_lab/services/experiment_service.py
    - tests/services/test_experiment_service.py

📊 Change Summary:
  Backend changed:  YES
  Frontend changed: NO
  Config changed:   NO
  Docs only:        NO

✅ Building backend image (with GHCR cache)
⏭️  Skipping frontend build (no changes)
✅ Running unit tests
✅ Running E2E tests
✅ Pushing backend image to GHCR
⏭️  Skipping frontend push (no changes)
```

**Ver documentação completa:** `docs/testing.md`

### ⚠️ Troubleshooting

Se o usuário disser "fiz merge mas os testes não rodaram":
1. Pergunte: "Você fez push depois do merge?"
2. Explique: "Merge é local, testes só rodam no push"
3. Solução: `git push origin main`

Se precisar verificar status:
```bash
# Ver se há commits locais não enviados
git status
git log origin/main..main --oneline

# Ver branches não mergeadas
git branch --no-merged main
```

## Container Management (CRITICAL)

⚠️ **NUNCA execute comandos destrutivos em massa:**
```bash
# ❌ PROIBIDO - destroi dados de dev/prod
podman stop -a
podman rm -a
podman pod rm -a
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
```

✅ **Use comandos específicos:**
```bash
# Parar ambiente de teste
make test-e2e-docker-down

# Parar ambiente de dev
make dev-down

# Limpar container específico travado
podman stop <container-name> && podman rm <container-name>

# Re-seed banco de dev se necessário
DATABASE_URL="postgresql://synthlab:synthlab@localhost:5432/synthlab" python scripts/seed_database.py
```

**Dados persistentes:**
- `synthlab-postgres-dev`: Banco de desenvolvimento (porta 5432) - **NÃO APAGAR**
- `synthlab-postgres-test`: Banco de teste (porta 5433) - efêmero, pode ser recriado

## Architecture Rules (NON-NEGOTIABLE)

### Backend
- **Router**: `request → service.method() → response` (NADA mais)
- **Service**: Lógica de negócio, prompts LLM, orquestração
- **Repository**: Queries SQL parametrizadas (`?` placeholders)
- **LLM calls**: DEVEM usar `_tracer.start_as_current_span()`

### Testing (CRITICAL)
- **Default**: SEMPRE mock LLM calls em testes (fast, free, deterministic)
- **Integration tests**: Mock OpenAI/S3/HTTP, real database only
- **Smoke tests**: 1 teste "hello world" real por serviço externo (CI only)
- **Markers**: Use pytest markers (`integration`, `real_api`, `slow`)
- **Fixtures**: Use centralized mocks from `tests/fixtures/llm_mocks.py`
- **Documentation**: `docs/testing.md`

### Frontend
- **Pages**: Compõem componentes + usam hooks
- **Components**: Puros (props → JSX), SEM fetch
- **Hooks**: Encapsulam useQuery/useMutation
- **Services**: Funções com `fetchAPI`

## Debug Logs
- Backend: `/tmp/synth-lab-backend.log`
- Frontend: `/tmp/synth-lab-frontend.log`

## Environment (.env.*)
sempre use o .env.dev ou .env.test que está na pasta ./docker
```bash
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:pass@localhost/synthlab
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006
```

## Architecture Docs
- Arquitetura: `docs/architecture.md`
- API: `docs/api.md`
- Banco de dados: `docs/database.md`
- Deploy e CI/CD: `docs/deployment.md`
- Testes: `docs/testing.md`

## Active Technologies
- Python 3.13+ + FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK, Arize Phoenix (028-exploration-summary)
- PostgreSQL 14+ (existing tables: explorations, scenario_nodes, experiments) (028-exploration-summary)
- Python 3.13+ (backend), TypeScript 5.5+ (frontend) + FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK, boto3 (S3), React 18, TanStack Query, shadcn/ui (001-experiment-materials)
- PostgreSQL 14+ (metadata), S3-compatible storage (files) (001-experiment-materials)
- Python 3.13+ + FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK, OpenAI Agents SDK, boto3 (S3), Arize Phoenix (tracing) (029-synth-material-integration)
- PostgreSQL 14+ (metadata via `experiment_materials` table), S3-compatible storage (file content) (029-synth-material-integration)
- Python 3.13+ (backend), TypeScript 5.5+ (frontend) + FastAPI, SQLAlchemy 2.0+, Pydantic, React 18, TanStack Query, shadcn/ui (030-custom-synth-groups)
- PostgreSQL 14+ (JSONB for config), S3-compatible (avatars) (030-custom-synth-groups)
- Python 3.13+ (backend), TypeScript 5.5+ / Node.js 20 (frontend) + FastAPI 0.109+, React 18, Vite 6.3, SQLAlchemy 2.0+, TanStack Query 5.56 (033-docker-containerization)
- PostgreSQL 14+ (local container for dev/test, Railway PostgreSQL for prod) (033-docker-containerization)
- Python 3.13+ (backend), TypeScript 5.5+ (frontend), React 18 (035-causal-simulation)
- PostgreSQL 14+ with JSONB for DAG structures, hypothesis parameters, and simulation metadata (035-causal-simulation)
- Python 3.13+ (backend), TypeScript 5.5+ (frontend) + FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK, React 18, TanStack Query, shadcn/ui (036-simplified-hypothesis-wizard)
- PostgreSQL 14+ (existing tables: simulations, causal_dags, hypotheses, hypothesis_versions - no schema changes needed) (036-simplified-hypothesis-wizard)
- Python 3.13+ (backend), TypeScript 5.5+ (frontend) + FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK, React 18, TanStack Query, shadcn/ui, ReactFlow (037-unified-dag-hypotheses)
- PostgreSQL 14+ (existing tables: hypotheses +1 column, causal_dags unchanged) (037-unified-dag-hypotheses)
- Python 3.13+ (backend), TypeScript 5.5+ (frontend) + FastAPI, SQLAlchemy 2.0+, Pydantic, NumPy (simulation), React 18, TanStack Query (038-mechanism-based-simulation)
- PostgreSQL 14+ (JSONB for scorecard_data, simulation_attributes) (038-mechanism-based-simulation)
- Python 3.13+ (backend), TypeScript 5.5+ (frontend) + FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK (gpt-4o-mini), React 18, TanStack Query, shadcn/ui (039-narrative-mechanism-config)
- PostgreSQL 14+ (novas tabelas para mecanismos/opções, JSONB para narrativa gerada) (039-narrative-mechanism-config)
- Python 3.13+ (backend only — sem mudanças no frontend) + FastAPI, SQLAlchemy 2.0+, Pydantic, NumPy, PyYAML (040-mechanism-sensitivity-update)
- PostgreSQL 14+ (JSONB fields — sem migração de schema) (040-mechanism-sensitivity-update)

## Recent Changes
- 028-exploration-summary: Added Python 3.13+ + FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK, Arize Phoenix

## Design and mechanics
  - Document Storage: Uses existing experiment_documents table with exploration.experiment_id as FK
  - Phoenix Tracing: All LLM calls wrapped with _tracer.start_as_current_span()

Database migration must be always done via Alembic. Tests use an isolated container (make test) which auto-applies migrations.

## CI/CD Pipeline (Build Once, Deploy Everywhere)

### Setup (First Time Only)

```bash
# Configurar diretório de hooks
git config core.hooksPath .githooks
```

**Não é necessário login no GHCR localmente** — build e push de imagens AMD64 acontece no GitHub Actions.

### Arquitetura do Pipeline

O CI/CD separa responsabilidades entre local e cloud:

| Fase | Onde | O que faz | Tempo |
|------|------|-----------|-------|
| **Pre-Push Hook** | Local (Mac ARM64) | Build nativo + testes unitários + E2E | ~2-5 min |
| **Build Images** | GitHub Actions (AMD64) | Build nativo AMD64 + push GHCR | ~3-5 min |
| **Deploy Staging** | GitHub Actions | Migrate + seed + deploy Railway + smoke tests | ~8-10 min |
| **Deploy Production** | GitHub Actions | Migrate + retag + deploy Railway + smoke tests | ~8-10 min |

**Total: ~20-30 min (push → production)**

### Fluxo Completo (AUTOMÁTICO)

```
git push origin main
  ↓
PRE-PUSH HOOK (local, ARM64 nativo):
  ├─ Build images (ARM64, para testes locais apenas)
  ├─ make test (unitários)
  └─ make test-e2e (Playwright)
  ↓
BUILD IMAGES (.github/workflows/build-images.yml):
  ├─ Build backend AMD64 nativo (Docker Buildx + GHCR cache)
  ├─ Build frontend AMD64 nativo (em paralelo)
  └─ Push tags: :staging, :commit-sha, :latest
  ↓
DEPLOY STAGING (.github/workflows/deploy-staging.yml):
  ├─ Migrate DB (alembic upgrade head)
  ├─ Seed DB (condicional — só se synth_groups vazia)
  ├─ Deploy backend → Railway (:staging)
  ├─ Deploy frontend → Railway (:staging)
  ├─ Smoke tests (staging: com auth via test-login)
  └─ Tag images como :staging-verified
  ↓
DEPLOY PRODUCTION (.github/workflows/deploy-production.yml):
  ├─ Gate: só roda se staging smoke tests passaram
  ├─ Migrate DB (seguro, não dropa)
  ├─ Retag :staging-verified → :production no GHCR
  ├─ Deploy backend → Railway (:production)
  ├─ Deploy frontend → Railway (:production)
  └─ Smoke tests (production: sem auth, apenas health checks)
```

### Decisões Importantes de Arquitetura

1. **Build local é ARM64 nativo** (sem `--platform linux/amd64`, sem QEMU)
   - Imagens locais servem APENAS para rodar testes no Mac
   - Imagens AMD64 para Railway são buildadas no GitHub Actions
   - Isso evita crashes de QEMU que aconteciam com emulação ARM→AMD64

2. **Railway usa Docker Image source** (não Dockerfile)
   - Deploy via GraphQL API (`serviceInstanceRedeploy`)
   - Script: `scripts/railway-deploy-image.sh`
   - **Não existe `railway.toml`** — foi removido pois Railway não builda do repo

3. **Production retag** — staging-verified → production
   - Production Railway está configurado com tag `:production`
   - O workflow retag copia `:staging-verified` → `:production` no GHCR
   - Depois dispara `serviceInstanceRedeploy` no Railway

4. **Smoke tests diferem por ambiente**:
   - **Staging**: testes completos com auth (usa `/auth/test-login` backdoor)
   - **Production**: apenas testes públicos sem auth (`public-health.spec.ts`)
   - Configurado em `frontend/playwright.config.ts` via `isProduction`

### Smoke Tests

**Staging** (`frontend/tests/e2e/smoke/critical-flows.spec.ts`):
- Com autenticação via test-login
- Testa navegação, criação de experimentos, etc.
- Não depende de dados específicos (usa `test.skip()` se vazio)

**Production** (`frontend/tests/e2e/smoke/public-health.spec.ts`):
- Sem autenticação (sem backdoor em prod)
- PUB001: Backend health check
- PUB002: Frontend carrega HTML
- PUB004: Sem erros 5xx em endpoints públicos
- PUB005: Backend responde em < 3s
- PUB006: Frontend carrega em < 5s

### Version Tracking

O endpoint `/health` retorna versão e ambiente:
```json
{
  "status": "healthy",
  "service": "synth-lab-api",
  "version": "commit-sha-aqui",
  "environment": "staging|production|local"
}
```

Para verificar que deploy funcionou:
```bash
curl -s https://synth-lab-api-staging.up.railway.app/health | jq
curl -s https://synth-lab-api-production.up.railway.app/health | jq
# Comparar "version" com: git rev-parse HEAD
```

### Seed Condicional

O script `scripts/seed_database.py` verifica se `synth_groups` tem dados:
- **Se vazia**: executa seed completo
- **Se tem dados**: pula seed e preserva dados existentes

### Comandos Úteis

```bash
# Testar localmente
make test && make test-e2e

# Acompanhar pipeline no GitHub
gh run list --limit 10
gh run watch                    # acompanhar workflow atual
gh run view <run-id> --log-failed  # ver logs de falha

# Smoke tests locais contra ambientes remotos
make test-smoke-staging
make test-smoke-production

# Deploy manual (bypass automação)
gh workflow run deploy-staging.yml
gh workflow run deploy-production.yml

# Deploy production com fresh start (DESTROI DADOS)
gh workflow run deploy-production.yml -f fresh_start=true

# Verificar versão deployada
curl -s https://synth-lab-api-production.up.railway.app/health | jq .version
```

### Rollback

```bash
# Opção 1: Re-deploy staging-verified para production
gh workflow run deploy-production.yml -f use_staging_verified=true

# Opção 2: Railway rollback (via Railway CLI)
railway rollback --environment production

# Desabilitar auto-deploy para production (emergência)
# → Remover workflow_run trigger de deploy-production.yml
# → Usar workflow_dispatch para deploys manuais
```

### GitHub Secrets e Variables Necessários

**Secrets**:
- `RAILWAY_API_TOKEN` — Token da API Railway
- `RAILWAY_PROJECT_ID` — ID do projeto Railway
- `DATABASE_STAGING_URL` — URL do Postgres staging
- `DATABASE_PRODUCTION_URL` — URL do Postgres production

**Variables (não secretas)**:
- `STAGING_BACKEND_URL` — `https://synth-lab-api-staging.up.railway.app`
- `STAGING_FRONTEND_URL` — `https://synth-lab-frontend-staging.up.railway.app`
- `PRODUCTION_BACKEND_URL` — `https://synth-lab-api-production.up.railway.app`
- `PRODUCTION_FRONTEND_URL` — `https://synth-lab-frontend-production.up.railway.app`


SEMPRE QUE POSSIVEL, PREFIRA FAZER TAREFAS USANDO O MAKER, VEJA O QUE ELE PODE FAZER:


Setup:
  make install       Install dependencies
  make setup-hooks   Configure Git hooks

Development (Docker):
  make dev-up         Start full stack (frontend:8080, backend:8000, postgres:5432)
  make dev-down       Stop Docker environment
  make dev-logs-back  View backend logs
  make dev-logs-front View frontend logs

Testing (Smart Mode - runs failed tests first):
  make test               Run unit/integration tests (smart mode)
  make test-fast          Run fast anti-regression tests (~30s)
  make test-e2e           Run E2E tests (smart mode, isolated Docker)
  make test-smoke-staging Run smoke tests against Staging (Railway)
  make test-smoke-production Run smoke tests against Production (Railway)

Observability:
  make phoenix       Start Phoenix tracing UI (standalone, http://localhost:6006)
  make phoenix-ui    Open Phoenix UI in browser (for Docker dev environment)

Database:
  make db-migrate    Create migration: make db-migrate MSG='description'

Other:
  make gensynth      Generate synths: make gensynth ARGS='-n 3'
  make lint-format   Run ruff linter and formatter
  make kill          Kill processes on ports 8000, 8080, 6006
  make clean         Remove cache files