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

## Environment (.env)
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

## Recent Changes
- 028-exploration-summary: Added Python 3.13+ + FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK, Arize Phoenix

## Design and mechanics
  - Document Storage: Uses existing experiment_documents table with exploration.experiment_id as FK
  - Phoenix Tracing: All LLM calls wrapped with _tracer.start_as_current_span()

Database migration must be alway done via Alembic. and applyed to DATABASE_URL and DATABASE_TEST_URL as well.
