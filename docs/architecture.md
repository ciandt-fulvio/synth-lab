# Arquitetura - synth-lab

## Backend

### Camadas

```
API Layer (api/)           → Endpoints HTTP, schemas Pydantic, error handlers
       ↓
Service Layer (services/)  → Lógica de negócio, prompts LLM, orquestração
       ↓
Repository Layer (repos/)  → Acesso a dados, queries SQL parametrizadas
       ↓
Infrastructure (infra/)    → Config, DB, LLM client, tracing, storage
       ↓
Domain (domain/entities/)  → Entidades de negócio (Pydantic models)
```

### Estrutura de Diretórios

```
src/synth_lab/
├── api/
│   ├── main.py                   # FastAPI app, lifespan, CORS
│   ├── errors.py                 # Exception handlers → HTTP responses
│   ├── routers/                  # Endpoints agrupados por domínio
│   └── schemas/                  # Request/Response Pydantic models
├── services/
│   ├── errors.py                 # Exceções de domínio
│   ├── experiment_service.py
│   ├── synth_service.py
│   ├── material_service.py       # Upload S3, thumbnails, descrição IA
│   ├── quantitative_analysis_service.py  # Modelo causal, simulação, relatório
│   ├── simulation_engine.py      # Motor de simulação DAG
│   ├── research_agentic/         # Subdomínio: entrevistas
│   └── research_prfaq/           # Subdomínio: PR-FAQ
├── repositories/
│   ├── base.py                   # BaseRepository com paginação
│   └── *_repository.py
├── infrastructure/
│   ├── config.py                 # Env vars, constantes
│   ├── database_v2.py            # SQLAlchemy engine/session (PostgreSQL)
│   ├── llm_client.py             # OpenAI chat completions (retry, timeout)
│   ├── image_generator.py        # OpenAI gpt-image-1.5
│   ├── storage_client.py         # S3-compatible (presigned URLs, upload/download)
│   ├── phoenix_tracing.py        # Phoenix/OTEL tracing
│   └── migrations/               # Alembic
├── domain/entities/               # Entidades Pydantic
└── models/orm/                    # SQLAlchemy ORM models
```

### Regras por Camada

**API Layer** — Router só faz: `request → service.method() → response`
- Schemas Pydantic em `api/schemas/`
- Sem lógica de negócio, SQL, ou chamadas LLM

**Service Layer** — Toda lógica de negócio
- Validações de domínio
- Chamadas LLM via `LLMClient` (sempre com `_tracer.start_as_current_span()`)
- Prompts em `services/*/prompts.py` ou como métodos privados
- Logging via `loguru`

**Repository Layer** — Todo acesso a dados
- Queries SQL parametrizadas (`?` placeholders, NUNCA string interpolation)
- Conversão row → entity

**Infrastructure Layer**
- `database_v2.py`: SQLAlchemy engine + session factory
- `llm_client.py`: `get_llm_client()` → singleton com retry + timeout
- `image_generator.py`: `get_image_generator()` → gpt-image-1.5
- `storage_client.py`: `generate_upload_url()`, `generate_view_url()`, `upload_object()`, etc.
- `phoenix_tracing.py`: `get_tracer("name")` → spans customizados

**Domain Layer** — Entidades Pydantic com validação e geração de IDs

### Dependency Injection

```python
class ExperimentService:
    def __init__(self, repository=None, llm_client=None):
        self.repository = repository or ExperimentRepository()
        self.llm = llm_client or get_llm_client()

def get_experiment_service() -> ExperimentService:
    return ExperimentService()
```

### Error Handling

```
SynthLabError (base)
├── NotFoundError (→ HTTP 404)
├── ValidationError (→ HTTP 422)
├── GenerationFailedError (→ HTTP 422)
└── DatabaseError (→ HTTP 503)
```

Service lança exceção de domínio → Router deixa subir → `api/errors.py` converte em HTTP response.

### Migrações (Alembic)

```bash
make db-migrate MSG="add column"  # Criar nova migração (e aplicar)
```

Migrações ficam em `src/synth_lab/infrastructure/migrations/versions/`. Testes usam container isolado que aplica migrações automaticamente.

---

## Frontend

### Camadas

```
UI Layer (pages/, components/)  → Páginas, componentes puros (props → JSX)
       ↓
State Layer (hooks/)            → React Query (useQuery, useMutation)
       ↓
Service Layer (services/)       → Funções fetchAPI para API REST
       ↓
Data Layer (types/, data/)      → TypeScript interfaces, constantes
```

### Estrutura de Diretórios

```
frontend/src/
├── App.tsx                    # Rotas (React Router)
├── pages/                     # Uma página por rota
├── components/
│   ├── ui/                    # shadcn/ui (NÃO EDITAR)
│   ├── shared/                # Componentes genéricos
│   ├── experiments/           # Componentes de experiments
│   ├── quantitative/          # Análise quantitativa (DAG, simulação, perfis)
│   └── synths/                # Componentes de synths
├── hooks/                     # useExperiments, useSynths, useTags, etc.
├── services/
│   ├── api.ts                 # fetchAPI base
│   └── *-api.ts               # Funções por domínio
├── types/                     # TypeScript interfaces
└── lib/
    ├── utils.ts               # cn() helper
    └── query-keys.ts          # Chaves React Query centralizadas
```

### Regras por Camada

**Pages** — Compõem componentes + usam hooks. Sem fetch direto.

**Components** — Puros: recebem props, retornam JSX. Sem fetch, sem mutations.

**Hooks** — Encapsulam React Query. Invalidam cache após mutations.
- Query keys sempre de `lib/query-keys.ts`

**Services** — Funções com `fetchAPI`. Uma função por operação API.

### Rotas

| Path | Componente |
|------|------------|
| `/` | Index (lista de experimentos) |
| `/experiments/:id` | ExperimentDetail |
| `/experiments/:expId/interviews/:execId` | InterviewDetail |
| `/synths` | Synths (catálogo) |

### Tech Stack

- React 18, TypeScript 5.5+, Vite
- TanStack Query 5 (server state)
- shadcn/ui + Tailwind CSS (UI)
- React Hook Form + Zod (formulários)
- Sonner (toast notifications)
- React Router (routing)

---

## Referências

- **Backend**: FastAPI, Pydantic, Loguru, Phoenix/Arize, OpenTelemetry
- **Frontend**: React, TanStack Query, shadcn/ui, Tailwind CSS, React Hook Form, Zod
