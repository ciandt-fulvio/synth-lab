# Implementation Plan: synth-lab REST API with Database Layer

**Branch**: `010-rest-api` | **Date**: 2025-12-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-rest-api/spec.md`

## Summary

Implement a REST API for synth-lab with proper architectural separation:
- **Entry Layer**: CLI and FastAPI as thin adapters (no business logic)
- **Service Layer**: Business logic, LLM orchestration, and workflow coordination
- **Repository Layer**: Data access abstraction over SQLite
- **Infrastructure Layer**: Centralized LLM client, database connection management

Key architectural goals (per user requirements):
- CLI and API are **entry points only** - they dispatch to services
- **All business logic** (including LLM calls) lives in the service layer
- **Single LLM component** - centralized client with retry/timeout handling
- Follow **DRY** (extract common patterns) and **YAGNI** (no speculative abstractions)

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: FastAPI, uvicorn, SQLite (stdlib), openai>=2.8.0, openai-agents>=0.0.16, typer, rich, pydantic>=2.5.0
**Storage**: SQLite with JSON1 extension (single file: `output/synthlab.db`)
**Testing**: pytest with pytest-asyncio
**Target Platform**: Linux/macOS development server
**Project Type**: Single Python package with layered architecture
**Performance Goals**: <200ms metadata queries, <1s document retrieval, 10 concurrent clients
**Constraints**: Synchronous write operations, no authentication required
**Scale/Scope**: ~79 files, 9 synths, 14 transcripts, 6 reports (small dataset)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. TDD/BDD | ✅ PASS | Tests written before implementation; acceptance scenarios in spec.md |
| II. Fast Tests (<5s) | ✅ PASS | Unit tests for services; integration tests in slow battery |
| III. Complete Tests Before PR | ✅ PASS | All 17 endpoints + service layer tests required |
| IV. Frequent Commits | ✅ PASS | Commit per layer completion, per endpoint group |
| V. Simplicity (<500 lines, <30 line functions) | ✅ PASS | Layered design promotes small, focused modules |
| VI. Language | ✅ PASS | Code in English, docs in Portuguese, i18n ready |

## Project Structure

### Documentation (this feature)

```text
specs/010-rest-api/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI spec)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/synth_lab/
├── __init__.py
├── __main__.py                 # Entry: CLI routing (argparse → Typer apps)
│
├── # === ENTRY LAYER (thin adapters) ===
├── api/                        # NEW: FastAPI entry layer
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, lifespan, CORS
│   ├── dependencies.py         # Dependency injection (services)
│   ├── errors.py               # Exception handlers → API error responses
│   └── routers/
│       ├── __init__.py
│       ├── synths.py           # 5 endpoints → synth_service
│       ├── topics.py           # 3 endpoints → topic_service
│       ├── research.py         # 6 endpoints → research_service
│       └── prfaq.py            # 3 endpoints → prfaq_service
│
├── # === SERVICE LAYER (business logic) ===
├── services/                   # NEW: Business logic layer
│   ├── __init__.py
│   ├── synth_service.py        # Synth CRUD, search, avatar retrieval
│   ├── topic_service.py        # Topic guide management
│   ├── research_service.py     # Interview execution, transcripts, summaries
│   ├── prfaq_service.py        # PR-FAQ generation, export
│   └── errors.py               # Service-level exceptions (domain errors)
│
├── # === REPOSITORY LAYER (data access) ===
├── repositories/               # NEW: Data access abstraction
│   ├── __init__.py
│   ├── base.py                 # Base repository with common patterns
│   ├── synth_repository.py     # Synth data access (SQLite)
│   ├── topic_repository.py     # Topic guide access (filesystem + DB metadata)
│   ├── research_repository.py  # Research executions, transcripts
│   └── prfaq_repository.py     # PR-FAQ storage and retrieval
│
├── # === INFRASTRUCTURE LAYER (cross-cutting concerns) ===
├── infrastructure/             # NEW: Shared infrastructure
│   ├── __init__.py
│   ├── llm_client.py           # SINGLE LLM client (OpenAI + retry + logging)
│   ├── database.py             # SQLite connection manager
│   └── config.py               # Centralized configuration
│
├── # === DOMAIN MODELS ===
├── models/                     # NEW: Shared domain models
│   ├── __init__.py
│   ├── synth.py                # Synth Pydantic models
│   ├── topic.py                # TopicGuide models
│   ├── research.py             # Execution, Transcript models
│   ├── prfaq.py                # PR-FAQ models
│   └── pagination.py           # Pagination request/response models
│
├── # === EXISTING MODULES (to refactor) ===
├── gen_synth/                  # REFACTOR: Extract LLM calls → services
├── query/                      # KEEP: Will be absorbed into repositories
├── research_agentic/           # REFACTOR: CLI thin, logic → research_service
├── research_prfaq/             # REFACTOR: CLI thin, logic → prfaq_service
├── topic_guides/               # REFACTOR: CLI thin, logic → topic_service
└── trace_visualizer/           # KEEP: Standalone utility

tests/
├── unit/                       # Fast battery (<5s total)
│   ├── services/
│   ├── repositories/
│   └── infrastructure/
├── integration/                # Slow battery
│   ├── api/
│   └── services/
└── contract/                   # API contract tests
```

**Structure Decision**: Single project with clear layer separation. The new layered architecture (`api/`, `services/`, `repositories/`, `infrastructure/`, `models/`) is added alongside existing modules to enable gradual refactoring while maintaining backward compatibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Repository pattern | Abstracts SQLite + filesystem access for topic guides | Direct DB access would scatter SQL and file I/O across services, violating DRY |
| Service layer | Centralizes business logic for CLI and API reuse | Putting logic in CLI/API would duplicate code and make testing harder |

## Architectural Principles

### Layer Responsibilities

```
┌─────────────────────────────────────────────────────────────────┐
│                      ENTRY LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │    CLI       │  │   FastAPI    │                             │
│  │  (Typer)     │  │   Routers    │                             │
│  └──────┬───────┘  └──────┬───────┘                             │
│         │  Input parsing, │  Request validation                  │
│         │  output format  │  Response serialization              │
│         └────────┬────────┘                                      │
└──────────────────┼──────────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  synth_service │ topic_service │ research_service │ prfaq │   │
│  │                                                          │   │
│  │  • Business logic & validation                           │   │
│  │  • Orchestrates LLM calls via llm_client                │   │
│  │  • Coordinates multiple repositories                     │   │
│  │  • Returns domain models                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────┬──────────────────────────────────────────────┘
                   │
┌──────────────────┼──────────────────────────────────────────────┐
│                  ▼            INFRASTRUCTURE                     │
│  ┌─────────────────────┐  ┌─────────────────────────────────┐   │
│  │   llm_client.py     │  │       database.py               │   │
│  │  (SINGLE OpenAI)    │  │    (SQLite connection)          │   │
│  │  • Retry logic      │  │    • Connection pool            │   │
│  │  • Timeout handling │  │    • WAL mode                   │   │
│  │  • Model selection  │  │    • Transaction management     │   │
│  │  • Token tracking   │  │                                 │   │
│  └─────────────────────┘  └─────────────────────────────────┘   │
└──────────────────┬──────────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    REPOSITORY LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  synth_repo │ topic_repo │ research_repo │ prfaq_repo    │   │
│  │                                                          │   │
│  │  • Data access abstraction                               │   │
│  │  • SQLite queries                                        │   │
│  │  • Filesystem operations (topic guides, avatars)         │   │
│  │  • Maps DB rows → domain models                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   SQLite     │  │  Filesystem  │  │   OpenAI     │          │
│  │  synthlab.db │  │  (avatars,   │  │    API       │          │
│  │              │  │  transcripts)│  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### DRY Principles Applied

1. **Single LLM Client**: All OpenAI calls go through `infrastructure/llm_client.py`
   - Centralizes API key management
   - Unified retry logic with exponential backoff (using tenacity)
   - Model selection via configuration
   - Token usage tracking

2. **Shared Domain Models**: `models/` contains Pydantic models used by all layers
   - No duplicate model definitions
   - Consistent validation rules

3. **Common Repository Base**: `repositories/base.py` provides:
   - Pagination helpers
   - Error handling patterns
   - Connection management

### YAGNI Principles Applied

1. **No ORM**: SQLite with raw SQL is sufficient for current scale
2. **No Caching Layer**: Current dataset is small; add only if performance issues arise
3. **No Async for SQLite**: Synchronous operations are adequate for current load
4. **No Authentication**: Internal/development use only (per spec assumptions)
5. **No Event System**: Direct function calls; add pub/sub only if needed

## Migration Strategy

### Phase 1: Infrastructure Foundation
1. Create `infrastructure/` with `llm_client.py` and `database.py`
2. Create `models/` with shared Pydantic models
3. Migrate SQLite schema from DuckDB patterns

### Phase 2: Repository Layer
1. Create `repositories/` with data access abstraction
2. Migrate existing query patterns from `query/database.py`
3. Add filesystem operations for topic guides and avatars

### Phase 3: Service Layer
1. Create `services/` extracting logic from existing CLIs
2. Each service calls repositories and `llm_client`
3. Update existing CLIs to use services (backward compatibility)

### Phase 4: API Layer
1. Create `api/` with FastAPI routers
2. Routers call services (same as CLI)
3. Add error handlers and dependency injection

### Backward Compatibility

During migration, existing CLI commands continue to work:
1. CLI modules (`research_agentic/cli.py`, etc.) are updated to call services
2. Old direct function calls are replaced with service calls
3. Same user-facing behavior, different internal implementation

## Key Design Decisions

### LLM Client Centralization

```python
# infrastructure/llm_client.py
class LLMClient:
    """Single source of truth for all LLM operations."""

    def __init__(self, api_key: str | None = None, default_model: str = "gpt-5-mini"):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.default_model = default_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def complete(self, messages: list[dict], model: str | None = None, **kwargs) -> str:
        """Unified completion with retry logic."""
        ...

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def generate_image(self, prompt: str, model: str = "dall-e-3") -> bytes:
        """Unified image generation with retry logic."""
        ...
```

### Service Pattern

```python
# services/research_service.py
class ResearchService:
    def __init__(
        self,
        synth_repo: SynthRepository,
        topic_repo: TopicRepository,
        research_repo: ResearchRepository,
        llm_client: LLMClient,
    ):
        self.synth_repo = synth_repo
        self.topic_repo = topic_repo
        self.research_repo = research_repo
        self.llm_client = llm_client

    def execute_research(self, request: ResearchExecuteRequest) -> ResearchExecution:
        """Executes research interviews - business logic lives here."""
        # Validate inputs
        topic = self.topic_repo.get_by_name(request.topic_name)
        if not topic:
            raise TopicNotFoundError(request.topic_name)

        # Select synths
        synths = self._select_synths(request)

        # Execute interviews (uses llm_client internally)
        execution = self._run_interviews(topic, synths, request)

        # Save results
        self.research_repo.save_execution(execution)

        return execution
```

### Thin CLI Pattern

```python
# research_agentic/cli.py (refactored)
from synth_lab.services import get_research_service

@app.command()
def batch(topic_name: str, synth_count: int, ...):
    """Execute batch research - thin wrapper around service."""
    service = get_research_service()

    try:
        result = service.execute_research(ResearchExecuteRequest(
            topic_name=topic_name,
            synth_count=synth_count,
            ...
        ))
        console.print(f"[green]Execution complete: {result.exec_id}[/green]")
    except TopicNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
```

### Thin API Router Pattern

```python
# api/routers/research.py
from synth_lab.services import get_research_service

@router.post("/execute", status_code=201)
async def execute_research(request: ResearchExecuteRequest):
    """Execute research - thin wrapper around service."""
    service = get_research_service()

    try:
        result = service.execute_research(request)
        return ResearchExecuteResponse.from_execution(result)
    except TopicNotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": "TOPIC_NOT_FOUND", "message": str(e)})
```

## Database Schema Summary

See `data-model.md` for full schema. Key tables:

| Table | Purpose |
|-------|---------|
| `synths` | Synth profiles with JSON columns for nested data |
| `research_executions` | Execution metadata and status |
| `transcripts` | Interview transcripts (JSON messages) |
| `prfaq_metadata` | PR-FAQ metadata and validation status |
| `schema_migrations` | Schema version tracking |

Note: Topic guides remain filesystem-based with optional DB metadata caching.

## Next Steps

1. **Phase 0**: Generate `research.md` with technology decisions
2. **Phase 1**: Generate `data-model.md`, `contracts/`, `quickstart.md`
3. **Phase 2**: Generate `tasks.md` via `/speckit.tasks` command
