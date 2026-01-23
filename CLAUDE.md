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
pytest tests/
ruff check . && ruff format .

# Frontend
cd frontend && npm run dev
npm run lint
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

## Recent Changes
- 028-exploration-summary: Added Python 3.13+ + FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK, Arize Phoenix

## Design and mechanics
  - Document Storage: Uses existing experiment_documents table with exploration.experiment_id as FK
  - Phoenix Tracing: All LLM calls wrapped with _tracer.start_as_current_span()

Database migration must be always done via Alembic. Tests use an isolated container (make test) which auto-applies migrations.

## CI/CD Pipeline (Local Pre-Push + Auto Deploy)

### Setup (First Time Only)

Configure o Git para usar os hooks locais:
```bash
# Configurar diretório de hooks
git config core.hooksPath .githooks

# Verificar configuração
git config core.hooksPath

# Login no GHCR (necessário para push de imagens)
podman login ghcr.io
# ou
docker login ghcr.io
# Fornecer: username=seu-github-username, password=seu-github-PAT-com-scope-write:packages
```

**Criar GitHub Personal Access Token**:
1. Acesse: https://github.com/settings/tokens
2. "Generate new token (classic)"
3. Selecione scope: `write:packages` e `read:packages`
4. Use o token como senha no `docker login`

### Overview
O pipeline de CI/CD é dividido em duas fases principais:
1. **Pre-Push Hook (Local)**: Build + testes completos + push de imagens para GHCR
2. **Deploy Staging (GitHub Actions)**: Deploy automático de imagens pré-testadas para staging

### Fase 1: Pre-Push Hook (Local)

**Trigger**: `git push` para branch `main`

**Localização**: `.githooks/pre-push`

**Fluxo**:
```
1. Build Docker Images (Local)
   ├─> Build backend image (synth-lab-api:commit-sha)
   └─> Build frontend image (synth-lab-frontend:commit-sha)

2. Run Full Test Suite (Local)
   └─> make test (todos os testes pytest)

3. Run E2E Tests (Local)
   └─> make test-e2e (Playwright E2E tests)

4. Push Images to GHCR
   ├─> Tag images com commit SHA
   ├─> Push backend image para GHCR
   └─> Push frontend image para GHCR

5. Allow Push to Main
   └─> Se todas as etapas passarem, permite o push
```

**Benefícios**:
- ✅ Validação completa antes do push
- 🚀 Deploy mais rápido (imagens já prontas)
- 🔒 Garante que apenas código testado chegue ao remote
- 💾 Imagens pré-construídas reutilizadas no deploy

**Como usar**:
```bash
# Push normal para main (hook executa automaticamente)
git push origin main

# Bypass do hook (não recomendado)
git push origin main --no-verify
```

**Requisitos**:
- Autenticação no GHCR (GitHub Personal Access Token com scope `write:packages`)
- Login no GHCR: `podman login ghcr.io` ou `docker login ghcr.io`

### Fase 2: Deploy Staging (GitHub Actions)

**Trigger**: Push para `main` (após pre-push hook completar)

**Fluxo**:
```
1. Reset Staging DB
   └─> DROP SCHEMA public CASCADE (limpa tudo)

2. Migrate Staging DB
   └─> alembic upgrade head (aplica migrations)

3. Seed Staging DB (Conditional)
   └─> Executa APENAS se synth_groups estiver vazia
   └─> Preserva dados existentes se houver

4. Deploy Backend
   └─> Railway deploy com imagem GHCR:commit-sha

5. Deploy Frontend
   └─> Railway deploy com imagem GHCR:commit-sha

6. Smoke Tests
   └─> Playwright tests críticos (não dependem de dados específicos)

7. Tag Verified
   └─> Tag images como "staging-verified" se smoke tests passaram
```

**Características**:
- 🔄 Usa imagens pré-buildadas e pré-testadas
- 🗄️ Seed condicional: não recria dados se já existirem
- ✅ Smoke tests não dependem de dados específicos do seed
- 🏷️ Images são tagadas como "staging-verified" para promoção

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

# Forçar deploy para staging (usa últimas imagens do GHCR)
gh workflow run deploy-staging.yml

# Rodar smoke tests localmente contra staging
make test-smoke-staging

# Rodar smoke tests localmente contra production
make test-smoke-production

# Ver status dos hooks
git config core.hooksPath

# Temporariamente desabilitar pre-push hook
git push origin main --no-verify
```

### Promoção para Produção (Futuro)

As imagens tagadas como `staging-verified` podem ser promovidas para produção:
```bash
# Exemplo de promoção (quando workflow de prod estiver pronto)
docker pull ghcr.io/owner/synth-lab-api:staging-verified
docker tag ghcr.io/owner/synth-lab-api:staging-verified ghcr.io/owner/synth-lab-api:production
docker push ghcr.io/owner/synth-lab-api:production
```
