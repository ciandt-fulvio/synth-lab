# Research: synth-lab REST API with Database Layer

**Feature**: 010-rest-api | **Date**: 2025-12-19

## Technology Decisions

### 1. Database: PostgreSQL with JSON1

**Decision**: Use PostgreSQL (Python stdlib) with JSON1 extension

**Rationale**:
- Zero dependencies - built into Python 3.13
- JSON1 extension enables querying nested JSON fields (e.g., `json_extract(demografia, '$.idade')`)
- WAL mode supports concurrent reads (10 clients per spec)
- Single file deployment (`output/synthlab.db`)
- ACID compliance with transaction support

**Alternatives Considered**:
| Alternative | Rejected Because |
|-------------|------------------|
| DuckDB (current) | Analytical focus overkill for CRUD API; recreates DB from JSON on each init |
| PostgreSQL | External dependency; overkill for ~100 records |
| File-based JSON | No query support; concurrent access issues |

**Key Configuration**:
```sql
PRAGMA journal_mode=WAL;      -- Concurrent reads
PRAGMA foreign_keys=ON;       -- Referential integrity
PRAGMA synchronous=NORMAL;    -- Balance safety/performance
```

---

### 2. API Framework: FastAPI

**Decision**: Use FastAPI with uvicorn

**Rationale**:
- Auto-generated OpenAPI/Swagger documentation (SC-008)
- Pydantic integration for request/response validation
- High performance with uvicorn
- Excellent Python 3.13 support
- Async support for future scaling (but sync operations for PostgreSQL)

**Alternatives Considered**:
| Alternative | Rejected Because |
|-------------|------------------|
| Flask | Manual OpenAPI generation; less Pydantic integration |
| Django REST | Heavyweight for simple API; ORM unnecessary |
| Litestar | Less mature ecosystem |

**Dependencies**:
```toml
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0  # Already a FastAPI dependency
```

---

### 3. LLM Client: Centralized OpenAI Wrapper

**Decision**: Single `LLMClient` class in `infrastructure/llm_client.py`

**Rationale**:
- Currently LLM calls are scattered across 7+ files
- Each module instantiates its own `OpenAI()` client
- No unified retry logic or error handling
- Model names hardcoded in multiple places

**Implementation**:
```python
# infrastructure/llm_client.py
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class LLMClient:
    """Centralized LLM operations with retry and logging."""

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "gpt-xxxx",
        default_timeout: float = 120.0,
    ):
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            timeout=default_timeout,
        )
        self.default_model = default_model
        self.logger = logger.bind(component="llm_client")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        before_sleep=lambda rs: logger.warning(f"LLM retry {rs.attempt_number}")
    )
    def complete(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 1.0,
        **kwargs
    ) -> str:
        """Chat completion with retry logic."""
        response = self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
            **kwargs
        )
        return response.choices[0].message.content

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    def generate_image(self, prompt: str, size: str = "1024x1024") -> bytes:
        """Image generation with retry logic."""
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="hd",
            n=1,
            response_format="b64_json"
        )
        return base64.b64decode(response.data[0].b64_json)
```

**Migration Path**:
1. Create `LLMClient` class
2. Update services to inject `LLMClient`
3. Refactor existing modules to use injected client
4. Remove direct `OpenAI()` instantiation from:
   - `gen_synth/avatar_generator.py`
   - `research_prfaq/generator.py`
   - `research/interview.py`
   - `topic_guides/file_processor.py`

---

### 4. Layered Architecture Pattern

**Decision**: 4-layer architecture (Entry → Service → Repository → Infrastructure)

**Rationale**:
- Current CLIs contain business logic, making it hard to add API
- LLM calls scattered across modules
- No separation between data access and business logic
- Difficult to test in isolation

**Layer Responsibilities**:

| Layer | Purpose | Contains | Calls |
|-------|---------|----------|-------|
| Entry | Input/output adapters | CLI (Typer), API (FastAPI routers) | Services |
| Service | Business logic | Validation, orchestration, LLM workflows | Repositories, LLMClient |
| Repository | Data access | SQL queries, file I/O, JSON parsing | Database, Filesystem |
| Infrastructure | Cross-cutting | LLMClient, DB connection, Config | External systems |

**Dependency Rules**:
- Entry → Service (allowed)
- Service → Repository (allowed)
- Service → Infrastructure (allowed)
- Repository → Infrastructure (allowed)
- NO: Entry → Repository (must go through Service)
- NO: Service → Entry (no callbacks)
- NO: Repository → Service (no business logic in repos)

---

### 5. Data Model Strategy

**Decision**: PostgreSQL tables + filesystem for large files

**Rationale**:
- Synth JSON is ~1KB per record - fits well in PostgreSQL JSON columns
- Transcripts are ~50KB - JSON column is fine
- Avatar images are ~500KB - filesystem is better (PostgreSQL BLOB overhead)
- Topic guides have file references - keep in filesystem

**Storage Mapping**:

| Entity | Storage | Reason |
|--------|---------|--------|
| Synths | PostgreSQL (JSON columns) | Small, needs querying |
| Research Executions | PostgreSQL | Metadata queries |
| Transcripts | PostgreSQL (JSON column) | Query by exec_id, synth_id |
| Summaries | Filesystem (Markdown) | Large text, served as-is |
| PR-FAQs | PostgreSQL (metadata) + Filesystem (content) | Metadata queries + large content |
| Avatars | Filesystem (PNG) | Binary data, served directly |
| Topic Guides | Filesystem + PostgreSQL (metadata cache) | Directory structure + quick listing |

---

### 6. Error Handling Strategy

**Decision**: Domain exceptions mapped to HTTP errors at Entry layer

**Rationale**:
- Services throw domain-specific exceptions (e.g., `SynthNotFoundError`)
- Entry layer (API/CLI) maps exceptions to appropriate responses
- Consistent error format across API endpoints
- CLI can format errors differently than API

**Exception Hierarchy**:
```python
# services/errors.py
class SynthLabError(Exception):
    """Base exception for synth-lab domain errors."""
    code: str = "INTERNAL_ERROR"

class NotFoundError(SynthLabError):
    """Base for not-found errors."""
    pass

class SynthNotFoundError(NotFoundError):
    code = "SYNTH_NOT_FOUND"

class TopicNotFoundError(NotFoundError):
    code = "TOPIC_NOT_FOUND"

class ExecutionNotFoundError(NotFoundError):
    code = "EXECUTION_NOT_FOUND"

class PRFAQNotFoundError(NotFoundError):
    code = "PRFAQ_NOT_FOUND"

class ValidationError(SynthLabError):
    code = "VALIDATION_ERROR"

class InvalidQueryError(ValidationError):
    code = "INVALID_QUERY"

class GenerationFailedError(SynthLabError):
    code = "GENERATION_FAILED"

class DatabaseError(SynthLabError):
    code = "DATABASE_ERROR"
```

**API Error Handler**:
```python
# api/errors.py
@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"error": {"code": exc.code, "message": str(exc)}}
    )

@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": exc.code, "message": str(exc)}}
    )
```

---

### 7. Pagination Strategy

**Decision**: Offset-based pagination with `limit` + `offset`

**Rationale**:
- Simple implementation for current dataset size (~100 records)
- Cursor-based pagination is overkill for static data
- Matches existing DuckDB query patterns
- Easy to implement with PostgreSQL `LIMIT` + `OFFSET`

**Implementation**:
```python
# models/pagination.py
class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)

class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    pagination: PaginationMeta

class PaginationMeta(BaseModel):
    total: int
    limit: int
    offset: int
    has_next: bool

    @classmethod
    def from_params(cls, total: int, params: PaginationParams) -> "PaginationMeta":
        return cls(
            total=total,
            limit=params.limit,
            offset=params.offset,
            has_next=(params.offset + params.limit) < total
        )
```

---

### 8. Testing Strategy

**Decision**: Layered testing with fast/slow separation

**Fast Battery (<5s)**:
- Unit tests for services (mocked repositories, mocked LLM)
- Unit tests for repositories (in-memory PostgreSQL)
- Unit tests for infrastructure (mocked external calls)

**Slow Battery**:
- Integration tests with real PostgreSQL database
- API contract tests with TestClient
- End-to-end tests with actual LLM calls (optional, CI-gated)

**Test Structure**:
```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── services/
│   │   ├── test_synth_service.py
│   │   ├── test_topic_service.py
│   │   ├── test_research_service.py
│   │   └── test_prfaq_service.py
│   ├── repositories/
│   │   └── test_*.py
│   └── infrastructure/
│       ├── test_llm_client.py
│       └── test_database.py
├── integration/
│   ├── api/
│   │   └── test_*.py        # FastAPI TestClient
│   └── services/
│       └── test_*.py        # Real DB + mocked LLM
└── contract/
    └── test_openapi.py      # Validate OpenAPI spec
```

---

### 9. Migration Strategy

**Decision**: Gradual migration with backward compatibility

**Phase 1 - Foundation**:
1. Create `infrastructure/` module
2. Create `models/` module
3. Create PostgreSQL schema and migration script
4. Run migration script to populate initial data

**Phase 2 - Repositories**:
1. Create `repositories/` module
2. Implement data access for each entity
3. Keep existing `query/` module operational

**Phase 3 - Services**:
1. Create `services/` module
2. Extract business logic from CLIs
3. Update CLIs to use services (thin wrappers)

**Phase 4 - API**:
1. Create `api/` module
2. Implement all 17 endpoints
3. Add error handlers and documentation

**Backward Compatibility**:
- Existing CLI commands (`research`, `topic-guide`, `research-prfaq`) continue to work
- Same command-line interface, new internal implementation
- JSON files remain as backup (migration script reads from them)

---

## Dependencies to Add

```toml
# pyproject.toml additions
[project]
dependencies = [
    # Existing
    "openai>=2.8.0",
    "openai-agents>=0.0.16",
    "duckdb>=0.9.0",      # Keep for backward compat during migration
    "typer>=0.9.0",
    "rich>=13.0.0",
    "pydantic>=2.5.0",
    "jsonschema>=4.20.0",
    "faker>=21.0.0",
    "loguru>=0.7.0",
    "tenacity>=8.0.0",    # Already present - used for retry
    "Pillow>=10.0.0",
    "reportlab>=4.0.0",
    "jinja2>=3.1.0",
    "pdfplumber>=0.11.0",

    # NEW for API
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",          # For FastAPI TestClient
    "pytest-cov>=4.1.0",
]
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| PostgreSQL concurrency limits | WAL mode + connection pooling; low traffic expected |
| Migration data loss | Backup JSON before migration; migration is idempotent |
| LLM client breaking existing flows | Gradual rollout; keep old code paths until verified |
| Performance regression | Benchmark before/after; PostgreSQL is fast for small datasets |
| Breaking CLI commands | Integration tests for all CLI commands; same interface |
