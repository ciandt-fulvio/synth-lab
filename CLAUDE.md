# synth-lab Development Guidelines

## Tech Stack
- **Backend**: Python 3.13+, FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK, NumPy
- **Frontend**: TypeScript 5.5+, React 18, TanStack Query, shadcn/ui, Tailwind CSS, Recharts
- **Database**: PostgreSQL 14+ (Alembic migrations)
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

## Chrome DevTools / Browser Login (CRITICAL)

**NUNCA** navegar para `/api/auth/test-login` como GET — retorna 405.

**SEMPRE** fazer login via POST:
```javascript
await fetch('/api/auth/test-login', { method: 'POST', credentials: 'include' });
// Depois navigate para http://localhost:8080
```

Ou com o MCP chrome-devtools:
```
1. navigate_page → http://localhost:8080/login
2. evaluate_script: async () => { await fetch('/api/auth/test-login', { method: 'POST', credentials: 'include' }); return 'ok'; }
3. navigate_page → http://localhost:8080
```

## Git Workflow & Merge (CRITICAL)

**SEMPRE use o script helper para merge:**
```bash
./scripts/merge-to-main.sh <branch-name>
```

`git merge` é LOCAL (não envia nada). `git push` é REMOTO — o pre-push hook (testes E2E) SÓ roda no push.

Se "fiz merge mas os testes não rodaram" → faltou fazer `git push origin main`.

## Container Management (CRITICAL)

⚠️ **NUNCA execute comandos destrutivos em massa:**
```bash
# ❌ PROIBIDO
podman stop -a / podman rm -a / docker stop $(docker ps -aq)
```

✅ **Use comandos específicos:**
```bash
make dev-down                    # Parar ambiente de dev
make test-e2e-docker-down        # Parar ambiente de teste
podman stop <name> && podman rm <name>  # Container específico
```

**Dados persistentes:**
- `synthlab-postgres-dev`: Banco de desenvolvimento (porta 5432) — **NÃO APAGAR**
- `synthlab-postgres-test`: Banco de teste (porta 5433) — efêmero

## Architecture Rules (NON-NEGOTIABLE)

### Backend
- **Router**: `request → service.method() → response` (NADA mais)
- **Service**: Lógica de negócio, prompts LLM, orquestração
- **Repository**: Queries SQL parametrizadas
- **LLM calls**: DEVEM usar `_tracer.start_as_current_span()`
- **Migrations**: SEMPRE via Alembic (`make db-migrate MSG='description'`)

### Testing
- **Default**: SEMPRE mock LLM calls em testes (fast, free, deterministic)
- **Integration tests**: Mock OpenAI/S3/HTTP, real database only
- **Markers**: `integration`, `real_api`, `slow`
- **Fixtures**: `tests/fixtures/llm_mocks.py`
- **Docs**: `docs/testing.md`

### Frontend
- **Pages**: Compõem componentes + usam hooks
- **Components**: Puros (props → JSX), SEM fetch
- **Hooks**: Encapsulam useQuery/useMutation
- **Services**: Funções com `fetchAPI`

## Environment
Sempre use `.env.dev` ou `.env.test` em `./docker`:
```bash
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:pass@localhost/synthlab
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006
```

## Tracing (Phoenix / OpenInference)
- `from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes`
- Use `SpanAttributes.OPENINFERENCE_SPAN_KIND` + `OpenInferenceSpanKindValues.*.value` (nunca raw strings)
- **CHAIN**: orquestração de serviço | **LLM**: chamada real à API | **AGENT**: agente autônomo | **TOOL**: ferramenta dentro de agente

## Debug Logs
```bash
make dev-logs-back   # logs do backend
make dev-logs-front  # logs do frontend
```

## CI/CD
`git push origin main` dispara automaticamente: pre-push hook (testes locais) → build AMD64 no GitHub Actions → deploy staging → deploy production (~20-30 min total).

Comandos úteis:
```bash
gh run list --limit 10
gh run watch
make test-smoke-staging
make test-smoke-production
```

## Makefile (USE SEMPRE QUE POSSÍVEL)

```
Setup:
  make install            Install dependencies
  make setup-hooks        Configure Git hooks

Development (Docker):
  make dev-up             Start full stack (frontend:8080, backend:8000, postgres:5432)
  make dev-down           Stop Docker environment
  make dev-logs-back      View backend logs
  make dev-logs-front     View frontend logs

Testing:
  make test               Run unit/integration tests
  make test-fast          Run fast anti-regression tests (~30s)
  make test-e2e           Run E2E tests
  make test-smoke-staging Run smoke tests against Staging
  make test-smoke-production Run smoke tests against Production

Observability:
  make phoenix            Start Phoenix tracing UI (http://localhost:6006)
  make phoenix-ui         Open Phoenix UI in browser

Database:
  make db-migrate         Create migration: make db-migrate MSG='description'

Other:
  make gensynth           Generate synths: make gensynth ARGS='-n 3'
  make lint-format        Run ruff linter and formatter
  make kill               Kill processes on ports 8000, 8080, 6006
  make clean              Remove cache files
```

## Architecture Docs
- `docs/architecture.md` — arquitetura geral
- `docs/api.md` — API
- `docs/database.md` — banco de dados
- `docs/deployment.md` — deploy e CI/CD
- `docs/testing.md` — testes
