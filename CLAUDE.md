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

# Testing (see docs/testing-strategy.md for details)
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
4. **docs/pre-push-hook-smart-mode.md** - Documentação do smart mode

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

**Ver documentação completa:** `docs/pre-push-hook-smart-mode.md`

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
- **Documentation**: `docs/testing-strategy.md`

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
- Backend: `docs/arquitetura.md`
- Frontend: `docs/arquitetura_front.md`

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

## Recent Changes
- 028-exploration-summary: Added Python 3.13+ + FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK, Arize Phoenix

## Design and mechanics
  - Document Storage: Uses existing experiment_documents table with exploration.experiment_id as FK
  - Phoenix Tracing: All LLM calls wrapped with _tracer.start_as_current_span()

Database migration must be always done via Alembic. Tests use an isolated container (make test) which auto-applies migrations.

## CI/CD Pipeline (Build Once, Deploy Everywhere)

### Setup (First Time Only)

Configure o Git para usar os hooks locais:
```bash
# Configurar diretório de hooks
git config core.hooksPath .githooks

# Verificar configuração
git config core.hooksPath
```

**Não é mais necessário login no GHCR localmente** - o build e push de imagens agora acontece no GitHub Actions (AMD64 nativo, sem QEMU).

### Overview
O pipeline de CI/CD é dividido em três fases principais:
1. **Pre-Push Hook (Local)**: Build local (para testes) + testes completos
2. **Build Images (GitHub Actions)**: Build nativo AMD64 + push para GHCR
3. **Deploy Staging → Production (GitHub Actions)**: Deploy automático

### 🚀 Fluxo Completo: Merge → Staging → Production (AUTOMÁTICO)

```
Você: ./scripts/merge-to-main.sh <branch>
  ↓
Merge LOCAL (não envia nada)
  ↓
git push origin main
  ↓
PRE-PUSH HOOK (2-5 min):
  ├─> Build images (local, para testes)
  ├─> Testes unitários
  └─> Testes E2E
  ↓
BUILD IMAGES (5 min):
  ├─> Build AMD64 nativo (backend + frontend em paralelo)
  └─> Push images GHCR (:staging, :sha, :latest)
  ↓
DEPLOY STAGING (10 min):
  ├─> Migrate DB
  ├─> Seed DB (se vazio)
  ├─> Deploy backend → Railway
  ├─> Deploy frontend → Railway
  ├─> Smoke tests
  └─> Tag :staging-verified
  ↓
DEPLOY PRODUCTION (5 min) - AUTO se smoke tests passaram:
  ├─> Migrate DB (seguro, não dropa)
  ├─> Deploy backend → Railway
  ├─> Deploy frontend → Railway
  └─> Smoke tests
  ↓
✅ Deploy completo em staging e production!
```

**IMPORTANTE**:
- Deploy para staging é AUTOMÁTICO após build
- Deploy para production é AUTOMÁTICO se smoke tests staging passarem
- Imagens são buildadas nativamente (AMD64) no GitHub Actions, não localmente

### Fase 1: Pre-Push Hook (Local)

**Trigger**: `git push` para branch `main`

**Localização**: `.githooks/pre-push`

**Fluxo**:
```
1. Build Docker Images (Local - para testes apenas)
   ├─> Build backend image (synth-lab-api:commit-sha)
   └─> Build frontend image (synth-lab-frontend:commit-sha)

2. Run Full Test Suite (Local)
   └─> make test (todos os testes pytest)

3. Run E2E Tests (Local)
   └─> make test-e2e (Playwright E2E tests)

4. Allow Push to Main
   └─> Se todas as etapas passarem, permite o push
```

**Benefícios**:
- ✅ Validação completa antes do push
- 🔒 Garante que apenas código testado chegue ao remote
- ⚡ Rápido (~2-5 min, sem push de imagens)

**Como usar**:
```bash
# Push normal para main (hook executa automaticamente)
git push origin main

# Bypass do hook (não recomendado)
git push origin main --no-verify
```

**Não requer**: Login no GHCR (build local é apenas para testes)

### Fase 2: Build Images (GitHub Actions)

**Trigger**: Push para `main` (após pre-push hook permitir)

**Workflow**: `build-images.yml`

**Fluxo**:
```
1. Build Backend (AMD64 nativo, sem QEMU)
   ├─> Build com Docker Buildx
   ├─> Layer cache do GHCR
   └─> Push: :staging, :commit-sha, :latest

2. Build Frontend (AMD64 nativo, em paralelo)
   ├─> Build com Docker Buildx
   ├─> Layer cache do GHCR
   └─> Push: :staging, :commit-sha, :latest
```

**Benefícios**:
- 🚀 Build nativo AMD64 (GitHub runners, sem QEMU)
- ⚡ Builds em paralelo (backend + frontend)
- 📦 Layer cache para builds mais rápidos
- ✅ Sem crashes (QEMU era instável no Mac ARM)

### Fase 3: Deploy Staging (GitHub Actions)

**Trigger**: Automático após `build-images.yml` completar com sucesso

**Workflow**: `deploy-staging.yml`

**Fluxo**:
```
1. Check Build Status (Gate)
   └─> Só continua se build-images passou

2. Migrate Staging DB
   └─> alembic upgrade head (aplica migrations)

3. Seed Staging DB (Conditional)
   └─> Executa APENAS se synth_groups estiver vazia
   └─> Preserva dados existentes se houver

4. Deploy Backend
   └─> Railway deploy com imagem GHCR:staging

5. Deploy Frontend
   └─> Railway deploy com imagem GHCR:staging

6. Smoke Tests
   └─> Playwright tests críticos (não dependem de dados específicos)

7. Tag Verified
   └─> Tag images como "staging-verified" se smoke tests passaram
```

**Características**:
- 🔄 Usa imagens pré-buildadas nativamente
- 🗄️ Seed condicional: não recria dados se já existirem
- ✅ Smoke tests não dependem de dados específicos do seed
- 🏷️ Images são tagadas como "staging-verified" para produção
- ⚡ Trigger automático (workflow_run)

### Fase 4: Deploy Production (GitHub Actions)

**Trigger**: Automático após `deploy-staging.yml` completar com sucesso (smoke tests passaram)

**Workflow**: `deploy-production.yml`

**Fluxo**:
```
1. Check Staging Status (Gate)
   └─> Só continua se smoke tests staging passaram

2. Migrate Production DB
   └─> alembic upgrade head (SEGURO, não dropa tabelas)

3. Deploy Backend
   └─> Railway deploy com imagem GHCR:staging

4. Deploy Frontend
   └─> Railway deploy com imagem GHCR:staging

5. Smoke Tests Production
   └─> Validação final em produção
```

**Características**:
- 🔒 Gate de qualidade: só deploya se staging passou
- 🗄️ Migrations seguras (não dropa dados)
- ⚡ Trigger automático (workflow_run)
- 🛑 Pode ser desabilitado (remover workflow_run, manter workflow_dispatch)

### Seed Condicional

O script `scripts/seed_database.py` agora verifica se a tabela `synth_groups` tem dados:
- **Se vazia**: executa seed completo
- **Se tem dados**: pula seed e preserva dados existentes

```bash
# Exemplo de uso
DATABASE_URL="postgresql://..." python scripts/seed_database.py

# Saída se dados já existem:
# ℹ️  Database already contains data (synth_groups table not empty)
# ✅ Seed skipped - data already exists
```

### Smoke Tests

Os smoke tests em `frontend/tests/e2e/smoke/` são projetados para:
- ✅ Funcionar com ou sem dados no banco
- ✅ Apenas verificar estrutura e funcionalidade básica
- ❌ **NÃO** criar ou modificar dados
- ❌ **NÃO** depender de IDs ou nomes específicos

**Exemplo**: `ST005 - Experiment detail loads`
- Se não houver experimentos: `test.skip()`
- Se houver experimentos: verifica navegação básica

### Workflow 3: Build and Test (Pull Requests)

**Trigger**: Pull requests para `main`

**Objetivo**: Validar mudanças antes do merge (detecção incremental)

Este workflow roda automaticamente em PRs para validar mudanças antes do merge, com detecção incremental (só reconstrói o que mudou). Uma vez merged para main, o pre-push hook local assume o controle.

### Comandos Úteis

```bash
# Testar localmente antes de fazer push (manual)
make test && make test-e2e

# Ver workflows em execução
gh run list --limit 10
gh run watch  # acompanhar workflow atual

# Rodar smoke tests localmente contra staging
make test-smoke-staging

# Rodar smoke tests localmente contra production
make test-smoke-production

# Ver status dos hooks
git config core.hooksPath

# Temporariamente desabilitar pre-push hook
git push origin main --no-verify

# Deploy manual para staging (bypass build-images)
gh workflow run deploy-staging.yml

# Deploy manual para production (bypass auto-deploy)
gh workflow run deploy-production.yml

# Desabilitar auto-deploy para production (emergência)
# Remover workflow_run trigger de deploy-production.yml
```

### Rollback e Troubleshooting

```bash
# Ver imagens disponíveis no GHCR
docker search ghcr.io/<owner>/synth-lab-api

# Rollback no Railway (via Railway CLI)
railway rollback --environment production

# Rollback manual (re-deploy imagem anterior)
gh workflow run deploy-production.yml

# Verificar logs de build
gh run view <run-id> --log

# Verificar se smoke tests passaram
gh run list --workflow=deploy-staging.yml --limit 5
```
