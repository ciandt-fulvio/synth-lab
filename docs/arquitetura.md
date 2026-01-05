# Arquitetura do Backend - synth-lab

## Visão Geral

O **synth-lab** implementa uma arquitetura em **camadas** com separação clara de responsabilidades. Este documento define as regras obrigatórias que devem ser seguidas em todo código novo.

```
┌─────────────────────────────────────────────────────────────────┐
│                        API LAYER                                 │
│  api/routers/     - Endpoints HTTP (recebe request, retorna     │
│                     response)                                    │
│  api/schemas/     - Pydantic models para request/response       │
│  api/errors.py    - Exception handlers HTTP                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                               │
│  services/        - Lógica de negócio                           │
│  services/errors.py - Exceções de domínio                       │
│  services/*/prompts.py - Prompts de LLM                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    REPOSITORY LAYER                              │
│  repositories/    - Acesso a dados (SQL encapsulado)            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                           │
│  infrastructure/database_v2.py   - SQLAlchemy engine/session    │
│  infrastructure/database.py      - DatabaseManager (legacy)     │
│  infrastructure/llm_client.py    - Cliente OpenAI               │
│  infrastructure/phoenix_tracing.py - Observabilidade            │
│  infrastructure/config.py        - Configurações                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                                │
│  domain/entities/ - Entidades de negócio (Pydantic)             │
│  models/          - Models compartilhados (pagination, events)  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Estrutura de Diretórios

```
src/synth_lab/
├── api/                          # Camada de Interface HTTP
│   ├── main.py                   # FastAPI app, lifespan, CORS
│   ├── errors.py                 # Exception handlers → HTTP responses
│   ├── routers/                  # Endpoints agrupados por domínio
│   │   ├── synths.py
│   │   ├── experiments.py
│   │   └── ...
│   └── schemas/                  # Request/Response Pydantic models
│       ├── experiments.py
│       └── ...
│
├── services/                     # Camada de Negócio
│   ├── errors.py                 # Exceções de domínio
│   ├── experiment_service.py     # Serviço de experiments
│   ├── synth_service.py          # Serviço de synths
│   ├── research_service.py       # Serviço de research
│   ├── simulation/               # Subdomínio: simulação
│   │   ├── scorecard_llm.py      # Operações LLM para scorecard
│   │   ├── simulation_service.py
│   │   └── ...
│   ├── research_agentic/         # Subdomínio: entrevistas
│   │   ├── prompts.py            # Prompts de LLM (NUNCA no router!)
│   │   └── ...
│   └── research_prfaq/           # Subdomínio: PR-FAQ
│       ├── prompts.py
│       └── generator.py
│
├── repositories/                 # Camada de Dados
│   ├── base.py                   # BaseRepository com paginação
│   ├── experiment_repository.py
│   ├── synth_repository.py
│   └── ...
│
├── infrastructure/               # Camada de Infraestrutura
│   ├── config.py                 # Configurações (env vars)
│   ├── database_v2.py            # Database (PostgreSQL + SQLAlchemy)
│   ├── llm_client.py             # LLMClient (OpenAI)
│   ├── phoenix_tracing.py        # Tracing (Phoenix/OTEL)
│   └── migrations/               # Migrações Alembic
│
├── domain/                       # Camada de Domínio
│   └── entities/                 # Entidades de negócio
│       ├── experiment.py
│       ├── synth_group.py
│       └── ...
│
└── models/                       # Models Compartilhados
    ├── pagination.py             # PaginationParams, PaginatedResponse
    ├── events.py                 # SSE events
    └── ...
```

---

## Regras por Camada

### 1. API Layer (`api/`)

**Responsabilidades:**
- Receber requests HTTP
- Validar input com Pydantic schemas
- Chamar services
- Converter exceções em HTTP responses
- Retornar responses JSON

**PERMITIDO:**
```python
# Router chama service
@router.post("", response_model=ExperimentResponse)
async def create_experiment(data: ExperimentCreate):
    service = get_experiment_service()
    try:
        experiment = service.create_experiment(
            name=data.name,
            hypothesis=data.hypothesis,
        )
        return ExperimentResponse.from_entity(experiment)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
```

**PROIBIDO:**
```python
# ❌ Lógica de negócio no router
@router.post("")
async def create_experiment(data: ExperimentCreate):
    if len(data.name) > 100:  # ❌ Validação de negócio
        raise HTTPException(422, "Name too long")

    # ❌ SQL direto no router
    db.execute("INSERT INTO experiments...")

    # ❌ Chamada LLM no router
    llm = get_llm_client()
    response = llm.complete(...)

# ❌ Prompts de LLM no router
SCORECARD_PROMPT = """Você é um especialista..."""
```

**Regra de Ouro:** Router só faz: `request → service.method() → response`

---

### 2. Service Layer (`services/`)

**Responsabilidades:**
- Toda lógica de negócio
- Validações de domínio
- Orquestração de repositories
- Chamadas LLM (via LLMClient ou classes dedicadas)
- Logging (via loguru)

**PERMITIDO:**
```python
class ExperimentService:
    def __init__(self, repository: ExperimentRepository | None = None):
        self.repository = repository or ExperimentRepository()
        self.logger = logger.bind(component="experiment_service")

    def create_experiment(self, name: str, hypothesis: str) -> Experiment:
        # ✅ Validação de negócio no service
        if not name or not name.strip():
            raise ValueError("name is required")
        if len(name) > 100:
            raise ValueError("name must not exceed 100 characters")

        # ✅ Criação de entidade
        experiment = Experiment(name=name, hypothesis=hypothesis)

        # ✅ Persistência via repository
        return self.repository.create(experiment)
```

**Para operações LLM, criar classe dedicada:**
```python
# services/experiment/scorecard_estimator.py
class ScorecardEstimator:
    """Estimativa de scorecard via LLM."""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or get_llm_client()
        self.logger = logger.bind(component="scorecard_estimator")

    def estimate_from_experiment(self, experiment: Experiment) -> ScorecardEstimate:
        with _tracer.start_as_current_span("estimate_scorecard"):
            prompt = self._build_prompt(experiment)
            response = self.llm.complete_json(messages=[...])
            self.logger.info(f"Estimated scorecard for {experiment.id}")
            return self._parse_response(response)

    def _build_prompt(self, experiment: Experiment) -> str:
        """Prompt encapsulado como método privado."""
        return f"""Você é um especialista..."""
```

**PROIBIDO:**
```python
# ❌ SQL direto no service
class ExperimentService:
    def get_experiment(self, exp_id: str):
        db.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,))

# ❌ Constantes de prompt fora de services
# (prompts devem estar em services/*/prompts.py ou como métodos privados)
```

---

### 3. Repository Layer (`repositories/`)

**Responsabilidades:**
- Todo acesso a dados
- Queries SQL
- Conversão row → entity
- Paginação

**PERMITIDO:**
```python
class ExperimentRepository(BaseRepository):
    def __init__(self, db: DatabaseManager | None = None):
        super().__init__(db)

    def create(self, experiment: Experiment) -> Experiment:
        self.db.execute(
            """
            INSERT INTO experiments (id, name, hypothesis, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (experiment.id, experiment.name, experiment.hypothesis, experiment.created_at),
        )
        return experiment

    def get_by_id(self, exp_id: str) -> Experiment | None:
        row = self.db.fetchone(
            "SELECT * FROM experiments WHERE id = ?",
            (exp_id,),
        )
        return self._row_to_entity(row) if row else None
```

**OBRIGATÓRIO:** Usar queries parametrizadas (prevenção SQL injection)
```python
# ✅ CORRETO - Parametrizado
self.db.execute("SELECT * FROM synths WHERE id = ?", (synth_id,))

# ❌ ERRADO - String interpolation
self.db.execute(f"SELECT * FROM synths WHERE id = '{synth_id}'")
```

---

### 4. Infrastructure Layer (`infrastructure/`)

**Responsabilidades:**
- Conexões externas (DB, APIs)
- Configuração
- Tracing/Observabilidade

**Componentes:**

| Arquivo | Responsabilidade |
|---------|------------------|
| `config.py` | Variáveis de ambiente, constantes, paths |
| `database_v2.py` | SQLAlchemy engine, session factory, PostgreSQL |
| `llm_client.py` | `LLMClient` (OpenAI chat/completions com retry, timeout, logging) |
| `image_generator.py` | `ImageGenerator` (OpenAI gpt-image-1.5, geração de imagens) |
| `phoenix_tracing.py` | Setup Phoenix/OTEL, instrumentação automática |

#### Database Layer (SQLAlchemy + PostgreSQL)

O sistema utiliza **PostgreSQL** como banco de dados principal.

**Configuração via ambiente:**
```bash
# PostgreSQL (produção e desenvolvimento)
DATABASE_URL="postgresql://user:pass@localhost:5432/synthlab"

# Docker Compose (local)
DATABASE_URL="postgresql://synthlab:synthlab_dev@localhost:5432/synthlab"
```

**Padrão de uso (SQLAlchemy Session):**
```python
from synth_lab.infrastructure.database_v2 import get_session

with get_session() as session:
    experiment = session.query(Experiment).filter_by(id=exp_id).first()
    experiment.name = "Updated"
    # Auto-commits on exit
```

**FastAPI Dependency:**
```python
from synth_lab.infrastructure.database_v2 import get_db_session

@router.get("/{id}")
def get_experiment(id: str, db: Session = Depends(get_db_session)):
    return db.query(Experiment).filter_by(id=id).first()
```

**ORM Models:**
Os modelos SQLAlchemy estão em `models/orm/`:
```
models/orm/
├── base.py          # Base, JSONVariant, mixins
├── experiment.py    # Experiment, InterviewGuide
├── synth.py         # Synth, SynthGroup
├── analysis.py      # AnalysisRun, SynthOutcome, AnalysisCache
├── research.py      # ResearchExecution, Transcript
├── exploration.py   # Exploration, ScenarioNode
├── insight.py       # ChartInsight, SensitivityResult, RegionAnalysis
├── document.py      # ExperimentDocument
└── legacy.py        # FeatureScorecard, SimulationRun
```

**Migrações (Alembic):**
```bash
# Aplicar migrações
make alembic-upgrade

# Rollback
make alembic-downgrade

# Criar nova migração
make alembic-revision MSG="add column"
```

#### LLMClient (Chat/Completions)

Cliente centralizado para operações de texto com OpenAI (chat completions).

**Padrão de uso:**
```python
from synth_lab.infrastructure.llm_client import get_llm_client, LLMClient

class MyService:
    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or get_llm_client()  # ✅ Injeção de dependência

    def generate_text(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        return self.llm.complete(messages)

    def generate_json(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        return self.llm.complete_json(messages)  # ✅ Força response_format=json

    def stream_response(self, prompt: str):
        messages = [{"role": "user", "content": prompt}]
        for chunk in self.llm.complete_stream(messages):
            yield chunk
```

**Características:**
- Retry automático com backoff exponencial
- Timeout configurável via `SYNTHLAB_LLM_TIMEOUT`
- Tracking de tokens consumidos
- Tracing automático no Phoenix

---

#### ImageGenerator (Geração de Imagens)

Cliente para geração de imagens via OpenAI `gpt-image-1.5`.

**Padrão de uso:**
```python
from synth_lab.infrastructure.image_generator import get_image_generator, ImageGenerator

class AvatarService:
    def __init__(self, image_generator: ImageGenerator | None = None):
        self.img_gen = image_generator or get_image_generator()  # ✅ Singleton

    def generate_avatar(self, description: str) -> str:
        # Retorna base64 da imagem
        return self.img_gen.generate(prompt=description)

    def generate_avatar_bytes(self, description: str) -> bytes:
        # Retorna bytes para salvar em arquivo
        return self.img_gen.generate_bytes(prompt=description)
```

**Parâmetros disponíveis:**
```python
base64_img = generator.generate(
    prompt="Descrição da imagem",        # Obrigatório
    model="gpt-image-1.5",               # Default
    n=1,                                 # Default (1-10)
    size="1536x1024",                    # Default ("1024x1024", "1024x1536", "1536x1024", "auto")
    quality="auto",                      # Default ("auto", "hd")
    output_format="png",                 # Default ("png", "jpeg", "webp")
)
```

**Características:**
- Modelo padrão: `gpt-image-1.5`
- Retorno sempre em **base64**
- Retry automático com backoff exponencial
- Tracing no Phoenix com atributos:
  - `operation_type: "image_generation"`
  - `prompt_preview`: primeiros 100 caracteres do prompt
  - `llm.model_name`, `size`, `quality`, `output_format`

---

#### Config (Configuração Centralizada)

Variáveis de ambiente e constantes do sistema.

**Variáveis de ambiente principais:**
```bash
# Database (obrigatório)
DATABASE_URL="postgresql://user:pass@localhost:5432/synthlab"

# LLM
OPENAI_API_KEY="sk-..."
SYNTHLAB_DEFAULT_MODEL="gpt-4o-mini"    # Modelo padrão para completions
SYNTHLAB_LLM_TIMEOUT="120.0"            # Timeout em segundos
SYNTHLAB_LLM_MAX_RETRIES="3"            # Máximo de retries

# Tracing
PHOENIX_COLLECTOR_ENDPOINT="http://127.0.0.1:6006/v1/traces"
PHOENIX_ENABLED="true"                  # Habilita tracing

# Logging
LOG_LEVEL="INFO"                        # DEBUG, INFO, WARNING, ERROR
```

**Padrão de uso:**
```python
from synth_lab.infrastructure.config import (
    DATABASE_URL,
    DEFAULT_MODEL,
    OPENAI_API_KEY,
    OUTPUT_DIR,
    ensure_directories,
)

# Garantir que diretórios existem
ensure_directories()
```

---

#### Phoenix Tracing (Observabilidade)

Instrumentação automática de chamadas OpenAI para observabilidade.

**Setup (uma vez no startup):**
```python
from synth_lab.infrastructure.phoenix_tracing import setup_phoenix_tracing

# No startup da aplicação (api/main.py)
setup_phoenix_tracing(project_name="synth-lab")
```

**Spans customizados (para operações não-LLM):**
```python
from synth_lab.infrastructure.phoenix_tracing import get_tracer

_tracer = get_tracer("my-service")

class MyService:
    def complex_operation(self, data: dict) -> Result:
        with _tracer.start_as_current_span(
            "MyService: complex_operation",
            attributes={
                "operation_type": "data_processing",
                "input.value": str(data)[:100],
                "data_size": len(data),
            },
        ) as span:
            result = self._process(data)
            span.set_attribute("success", True)
            span.set_attribute("output.value", str(result)[:100])
            return result
```

**Atributos recomendados para spans:**
- `openinference.span.kind`: "LLM", "CHAIN", "TOOL", "RETRIEVER"
- `operation_type`: Tipo da operação (ex: "image_generation", "text_completion")
- `input.value`: Preview do input (primeiros 100 chars)
- `output.value`: Preview do output (primeiros 100 chars)
- `llm.model_name`: Nome do modelo usado
- `success`: Boolean indicando sucesso

**Dashboard:** http://localhost:6006

---

### 5. Domain Layer (`domain/entities/`)

**Responsabilidades:**
- Entidades de negócio
- Validação de dados
- Geração de IDs

**Padrão:**
```python
from pydantic import BaseModel, Field, field_validator
import secrets

def generate_experiment_id() -> str:
    return f"exp_{secrets.token_hex(4)}"

class Experiment(BaseModel):
    id: str = Field(default_factory=generate_experiment_id)
    name: str = Field(max_length=100)
    hypothesis: str = Field(max_length=500)

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v
```

---

## Mecanismos Transversais

### 1. Logging (Loguru)

**Padrão obrigatório:**
```python
from loguru import logger

class MyService:
    def __init__(self):
        self.logger = logger.bind(component="my_service")

    def do_something(self):
        self.logger.info("Starting operation")
        self.logger.debug(f"Details: {details}")
        self.logger.error(f"Failed: {error}")
```

**Níveis:**
- `debug`: Detalhes técnicos para troubleshooting
- `info`: Operações normais importantes
- `warning`: Situações anormais mas não críticas
- `error`: Erros que precisam de atenção

---

### 2. Tracing (Phoenix/OpenTelemetry)

**Para operações LLM, usar spans:**
```python
from synth_lab.infrastructure.phoenix_tracing import get_tracer

_tracer = get_tracer("my-component")

class MyLLMService:
    def generate(self, input: str) -> str:
        with _tracer.start_as_current_span(
            "MyLLMService: generate",
            attributes={"input_length": len(input)},
        ):
            response = self.llm.complete(...)
            return response
```

---

### 3. Error Handling

**Hierarquia de exceções:**
```
SynthLabError (base)
├── NotFoundError
│   ├── SynthNotFoundError
│   ├── ExperimentNotFoundError
│   └── ...
├── ValidationError
│   ├── InvalidQueryError
│   └── InvalidRequestError
├── GenerationFailedError
└── DatabaseError
```

**Fluxo:**
1. Service lança exceção de domínio (`SynthNotFoundError`)
2. Router deixa exceção subir (não precisa capturar)
3. `api/errors.py` converte em HTTP response

**No service:**
```python
from synth_lab.services.errors import SynthNotFoundError

def get_synth(self, synth_id: str) -> Synth:
    synth = self.repository.get_by_id(synth_id)
    if not synth:
        raise SynthNotFoundError(synth_id)  # ✅ Exceção de domínio
    return synth
```

**No router:**
```python
@router.get("/{synth_id}")
async def get_synth(synth_id: str):
    service = get_synth_service()
    return service.get_synth(synth_id)  # ✅ Deixa exceção subir
    # api/errors.py converte SynthNotFoundError → HTTP 404
```

---

### 4. Dependency Injection

**Padrão:**
```python
# Service recebe dependencies via constructor
class ExperimentService:
    def __init__(
        self,
        repository: ExperimentRepository | None = None,
        llm_client: LLMClient | None = None,
    ):
        self.repository = repository or ExperimentRepository()
        self.llm = llm_client or get_llm_client()

# Factory function para API
def get_experiment_service() -> ExperimentService:
    return ExperimentService()

# Uso no router
@router.post("")
async def create_experiment(data: ExperimentCreate):
    service = get_experiment_service()
    return service.create_experiment(...)
```

---

## Checklist de Code Review

### Para cada novo endpoint de API:
- [ ] Router só faz request → service → response?
- [ ] Validações de negócio estão no service (não no router)?
- [ ] Schemas Pydantic em `api/schemas/`?

### Para operações LLM:
- [ ] Prompt está em service (não no router)?
- [ ] Usa classe dedicada (ex: `ScorecardEstimator`) ou service method?
- [ ] Tem tracing com `_tracer.start_as_current_span()`?
- [ ] Tem logging adequado?

### Para acesso a dados:
- [ ] SQL está em repository (não em service ou router)?
- [ ] Usa queries parametrizadas (`?` placeholders)?
- [ ] Não usa string interpolation para valores de usuário?

### Para novas entidades:
- [ ] Entity em `domain/entities/`?
- [ ] Repository correspondente?
- [ ] Service correspondente?
- [ ] Schemas de request/response em `api/schemas/`?

---

## Exemplos de Violações Comuns

### 1. LLM no Router (ERRADO)
```python
# ❌ ERRADO - Prompt e chamada LLM no router
PROMPT = """Você é um especialista..."""

@router.post("/estimate")
async def estimate(data: Request):
    llm = get_llm_client()
    response = llm.complete(messages=[{"role": "user", "content": PROMPT}])
    return response
```

**CORRETO:**
```python
# services/estimation_service.py
class EstimationService:
    def estimate(self, data) -> EstimationResult:
        prompt = self._build_prompt(data)
        response = self.llm.complete_json(messages=[...])
        return EstimationResult(...)

    def _build_prompt(self, data) -> str:
        return f"""Você é um especialista..."""

# routers/estimation.py
@router.post("/estimate")
async def estimate(data: Request):
    service = EstimationService()
    return service.estimate(data)
```

### 2. SQL no Router (ERRADO)
```python
# ❌ ERRADO - SQL direto no router
@router.get("/check")
async def check_exists(ids: list[str]):
    db = get_db()
    rows = db.fetchall(f"SELECT id FROM items WHERE id IN ({','.join(ids)})")
    return {"exists": [r["id"] for r in rows]}
```

**CORRETO:**
```python
# repositories/item_repository.py
class ItemRepository:
    def check_exists_batch(self, ids: list[str]) -> dict[str, bool]:
        placeholders = ",".join("?" * len(ids))
        rows = self.db.fetchall(
            f"SELECT id FROM items WHERE id IN ({placeholders})",
            tuple(ids),
        )
        return {r["id"]: True for r in rows}

# routers/items.py
@router.get("/check")
async def check_exists(ids: list[str]):
    repo = ItemRepository()
    return repo.check_exists_batch(ids)
```

### 3. Validação no Router (ERRADO)
```python
# ❌ ERRADO - Validação de negócio no router
@router.post("")
async def create(data: CreateRequest):
    if len(data.name) > 100:
        raise HTTPException(422, "Name too long")
    if data.name in RESERVED_NAMES:
        raise HTTPException(422, "Reserved name")
```

**CORRETO:**
```python
# services/my_service.py
class MyService:
    RESERVED_NAMES = {"admin", "system"}

    def create(self, name: str) -> Entity:
        if len(name) > 100:
            raise ValueError("Name must not exceed 100 characters")
        if name in self.RESERVED_NAMES:
            raise ValueError(f"Name '{name}' is reserved")
        ...

# routers/my_router.py
@router.post("")
async def create(data: CreateRequest):
    service = MyService()
    try:
        return service.create(data.name)
    except ValueError as e:
        raise HTTPException(422, str(e))
```

---

## Referências

- **FastAPI**: https://fastapi.tiangolo.com/
- **Pydantic**: https://docs.pydantic.dev/
- **Loguru**: https://loguru.readthedocs.io/
- **Phoenix/Arize**: https://docs.arize.com/phoenix
- **OpenTelemetry**: https://opentelemetry.io/docs/languages/python/
