# synth-lab Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-22

## Active Technologies
- Python 3.13+ (backend), TypeScript 5.5+ (frontend) + FastAPI, OpenAI SDK, React 18, TanStack Query, shadcn/ui (015-synth-chat)
- SQLite (leitura apenas - sem persistência de chat) (015-synth-chat)
- SQLite 3 com JSON1 extension (output/synthlab.db) - WAL mode (016-feature-impact-simulation)
- Python 3.13+ (backend), TypeScript 5.5.3 (frontend) (018-experiment-hub)
- Python 3.13+ (backend), TypeScript 5.5+ (frontend) + FastAPI 0.109+, Pydantic 2.5+, React 18, TanStack Query 5.56+, shadcn/ui (019-experiment-refactor)
- SQLite 3 com JSON1 extension e WAL mode (`output/synthlab.db`) (019-experiment-refactor)
- TypeScript 5.5.3 (frontend) + React 18.3.1, TanStack React Query 5.56+, Recharts 2.12.7+, shadcn/ui (Radix UI), Tailwind CSS 3.4+ (020-experiment-results-frontend)
- N/A (data from backend API) (020-experiment-results-frontend)
- SQLite 3 with JSON1 extension (output/synthlab.db) (001-analysis-tabs-refactor)
- Python 3.13+ (backend), TypeScript 5.5+ (frontend) + FastAPI 0.109+, Pydantic 2.5+, React 18, TanStack Query, shadcn/ui (022-observable-latent-traits)
- Python 3.13+ (backend) + FastAPI 0.109+, Pydantic 2.5+, OpenAI SDK, asyncio (024-llm-scenario-exploration)
- SQLite 3 com JSON1 extension (`output/synthlab.db`) (024-llm-scenario-exploration)
- Python 3.13+ (backend), TypeScript 5.5+ (frontend) + FastAPI, Pydantic, React 18, Recharts, TanStack Query (025-sankey-diagram)
- Python 3.13 (backend), TypeScript 5.5 (frontend) + FastAPI 0.109+, Pydantic 2.5+, SQLite 3 with JSON1, React 18, TanStack Query 5.56+ (026-experiment-documents)
- SQLite 3 with WAL mode (`output/synthlab.db`) (026-experiment-documents)
- Python 3.13+ + SQLAlchemy 2.0+, Alembic 1.12+, psycopg2-binary (PostgreSQL driver) (027-postgresql-migration)
- PostgreSQL 14+ (production), SQLite 3 with JSON1 (development/fallback) (027-postgresql-migration)

### Backend
- **Python**: 3.13+
- **Framework**: FastAPI 0.109.0+, Uvicorn 0.27.0+, Pydantic 2.5.0+
- **Database**: SQLite 3 with JSON1 extension and WAL mode (`output/synthlab.db`)
- **AI/LLM**:
  - OpenAI SDK 2.8.0+
  - OpenAI Agents 0.0.16+
- **Core Libraries**:
  - Data generation: Faker 21.0.0+
  - Schema validation: jsonschema 4.20.0+
  - CLI: Typer 0.9.0+, Rich 13.0.0+
  - Logging: Loguru 0.7.0+
  - Image processing: Pillow 10.0.0+
  - HTTP client: Requests 2.31.0+
  - PDF processing: pdfplumber 0.11.0+
  - Retry logic: Tenacity 8.0.0+
  - PDF generation: ReportLab 4.0.0+
  - Templates: Jinja2 3.1.0+
- **Data Science**:
  - Numerical: NumPy 1.26.0+, Numba 0.61.0+
  - ML: scikit-learn 1.4.0+
  - Explainability: SHAP 0.46.0+
- **Observability**:
  - Arize Phoenix 5.0.0+, Phoenix OTEL 0.6.0+
  - OpenTelemetry SDK 1.20.0+, OTLP Exporter 1.20.0+
  - OpenInference instrumentation for OpenAI and Agents
- **Dev Dependencies**:
  - Linting/Formatting: Ruff 0.1.0+
  - Testing: pytest 8.0.0+, pytest-cov 4.1.0+, pytest-asyncio 0.23.0+
  - HTTP testing: httpx 0.27.0+

### Frontend
- **Runtime**: TypeScript 5.5.3, React 18.3.1, React DOM 18.3.1
- **Build**: Vite 6.3.4, @vitejs/plugin-react-swc 3.9.0+
- **UI Framework**:
  - shadcn/ui (Radix UI primitives)
  - Tailwind CSS 3.4.11+, Tailwind Merge 2.5.2+
  - Tailwind Animate 1.0.7+, @tailwindcss/typography 0.5.15+
  - Lucide React 0.462.0+ (icons)
  - class-variance-authority 0.7.1+, clsx 2.1.1+
- **Radix UI Components**:
  - Accordion, Alert Dialog, Aspect Ratio, Avatar, Checkbox
  - Collapsible, Context Menu, Dialog, Dropdown Menu, Hover Card
  - Label, Menubar, Navigation Menu, Popover, Progress
  - Radio Group, Scroll Area, Select, Separator, Slider
  - Slot, Switch, Tabs, Toast, Toggle, Toggle Group, Tooltip
- **Data Fetching**: TanStack React Query 5.56.2+
- **Routing**: React Router DOM 6.26.2+
- **Forms**: React Hook Form 7.53.0+, @hookform/resolvers 3.9.0+, Zod 3.23.8+
- **UI Libraries**:
  - cmdk 1.0.0+ (command palette)
  - Sonner 1.5.0+ (toast notifications)
  - Vaul 0.9.3+ (drawer component)
  - next-themes 0.3.0+ (theme management)
  - embla-carousel-react 8.3.0+ (carousel)
  - react-resizable-panels 2.1.3+
  - input-otp 1.2.4+
- **Utilities**:
  - Date handling: date-fns 3.6.0+, react-day-picker 8.10.1+
  - Markdown: react-markdown 10.1.0+, remark-gfm 4.0.1+
  - Charts: recharts 2.12.7+
- **Dev Dependencies**:
  - Linting: ESLint 9.9.0+, TypeScript ESLint 8.0.1+
  - Type definitions: @types/react, @types/react-dom, @types/node
  - PostCSS 8.4.47+, Autoprefixer 10.4.20+
  - @dyad-sh/react-vite-component-tagger 0.8.0+

## When debuging issues
See BACKEND_LOG at /tmp/synth-lab-backend.log
See FRONTEND_LOG at /tmp/synth-lab-frontend.log

## Project Structure

```text
synth-lab/
├── src/synth_lab/          # Backend Python package
│   ├── api/                # FastAPI REST API
│   ├── domain/             # Business logic models
│   ├── gen_synth/          # Synth generation
│   ├── infrastructure/     # Database, config
│   ├── repositories/       # Data access layer
│   └── services/           # Business services
├── frontend/               # React TypeScript app
│   └── src/
│       ├── components/     # React components
│       ├── hooks/          # Custom React hooks
│       ├── pages/          # Page components
│       ├── services/       # API clients
│       └── types/          # TypeScript types
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── output/                 # Runtime data
│   └── synthlab.db        # SQLite database
└── data/                   # Static data files
```

## Commands

### Package Management

**Backend (Python with uv):**
```bash
# Install all dependencies
uv pip install -e ".[dev]"

# Add a new dependency
# 1. Add to pyproject.toml dependencies or optional-dependencies
# 2. Sync: uv pip install -e ".[dev]"

# Update dependencies
uv pip install --upgrade -e ".[dev]"
```

**Frontend (Node with npm):**
```bash
cd frontend

# Install dependencies
npm install

# Add a new dependency
npm install <package-name>

# Add a dev dependency
npm install -D <package-name>

# Update dependencies
npm update
```

### Development

**Backend:**
```bash
# Start API server (with auto-reload)
uv run uvicorn synth_lab.api.main:app --reload

# Start with specific host/port
uv run uvicorn synth_lab.api.main:app --host 0.0.0.0 --port 8000 --reload

# Run CLI
uv run python -m synth_lab

# Run specific module
uv run python -m synth_lab.services.research_agentic.batch_runner
```

**Frontend:**
```bash
cd frontend

# Start dev server (default: http://localhost:5173)
npm run dev

# Build for production
npm run build

# Build for development
npm run build:dev

# Preview production build
npm run preview
```

### Testing & Quality

**Backend:**
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=synth_lab --cov-report=html

# Run specific test file
pytest tests/unit/test_specific.py

# Run with verbose output
pytest tests/ -v

# Run async tests
pytest tests/ -v --asyncio-mode=auto

# Linting
ruff check .

# Format code
ruff format .

# Check and fix
ruff check --fix .
```

**Frontend:**
```bash
cd frontend

# Lint code
npm run lint

# Type check (TypeScript)
npx tsc --noEmit
```

## Code Style & Conventions

### Backend (Python)
- **Python Version**: 3.13+
- **Style Guide**: PEP 8 via Ruff
- **Line Length**: 100 characters (configured in pyproject.toml)
- **Type Hints**: Use native Python type hints (e.g., `list[str]` not `List[str]`)
- **Imports**: Organized by Ruff (stdlib, third-party, local)
- **Docstrings**: Google-style for all modules, classes, functions
- **Error Handling**: Specific exceptions with context and proper logging (Loguru)
- **Async**: Never use `asyncio.run()` inside functions - only in main blocks
- **File Size**: Maximum 500 lines per file
- **Validation**: Every module must have `if __name__ == "__main__":` block for testing

### Frontend (TypeScript/React)
- **TypeScript**: Strict mode enabled (tsconfig.json)
- **React**: Functional components with hooks
- **Styling**: Tailwind CSS classes (no CSS files unless necessary)
- **Component Organization**:
  - Pages in `frontend/src/pages/`
  - Reusable components in `frontend/src/components/`
  - Types in `frontend/src/types/`
  - API clients in `frontend/src/services/`
  - Custom hooks in `frontend/src/hooks/`
- **State Management**: React Query for server state, React hooks for local state
- **Forms**: React Hook Form + Zod for validation
- **Routing**: React Router DOM (routes defined in `App.tsx`)
- **UI Components**: Prefer shadcn/ui components (already installed)
- **Icons**: Use Lucide React

### API Design
- **Style**: RESTful conventions
- **Documentation**: Auto-generated OpenAPI/Swagger (FastAPI)
- **Response Format**: JSON with consistent structure
- **Error Handling**: Proper HTTP status codes and error messages
- **Versioning**: URL-based versioning when needed (`/api/v1/...`)

### Database
- **Engine**: SQLite 3 with JSON1 extension
- **Mode**: WAL (Write-Ahead Logging) for better concurrency
- **Location**: `output/synthlab.db`
- **Migrations**: Manual migrations when needed (document in code)
- **Schema**: Use Pydantic models for validation

## Architecture

**IMPORTANTE**: Documentação detalhada de arquitetura em:
- **Backend**: [`docs/arquitetura.md`](docs/arquitetura.md)
- **Frontend**: [`docs/arquitetura_front.md`](docs/arquitetura_front.md)

### Backend Layers
- **API Layer** (`src/synth_lab/api/`): FastAPI endpoints, request/response handling
- **Domain Layer** (`src/synth_lab/domain/`): Business logic models, core entities
- **Service Layer** (`src/synth_lab/services/`): Business logic implementation
- **Repository Layer** (`src/synth_lab/repositories/`): Data access, database operations
- **Infrastructure** (`src/synth_lab/infrastructure/`): Database connection, config, external services

### Backend Rules (NON-NEGOTIABLE)
- **Router só faz**: `request → service.method() → response`
- **Lógica de negócio**: SEMPRE em services, NUNCA em routers
- **Acesso a dados**: SEMPRE em repositories, NUNCA em services ou routers
- **Prompts de LLM**: SEMPRE em services, NUNCA em routers
- **Chamadas LLM**: DEVEM usar tracing Phoenix (`_tracer.start_as_current_span()`)
- **Queries SQL**: DEVEM ser parametrizadas (`?` placeholders), NUNCA string interpolation

### Frontend Patterns
- **Component-Based**: Reusable, composable React components
- **Composition**: Prefer composition over prop drilling
- **Custom Hooks**: Extract reusable logic into hooks
- **API Integration**: React Query for data fetching and caching
- **Type Safety**: TypeScript interfaces for all API responses and props

### Frontend Rules (NON-NEGOTIABLE)
- **Pages**: Apenas compõem componentes e usam hooks
- **Componentes**: São puros (recebem props, retornam JSX), SEM fetch direto
- **Hooks**: Encapsulam React Query (useQuery, useMutation)
- **Services**: Contêm funções de chamada à API usando `fetchAPI`
- **Query Keys**: Centralizadas em `lib/query-keys.ts`

### Development Best Practices
- **Function-First**: Prefer functions over classes (unless maintaining state or validation)
- **Real Data Testing**: Always test with actual data, never mocks for core functionality
- **Results Before Linting**: Get functionality working before addressing style issues
- **DRY Principle**: Avoid code duplication, reuse existing functionality
- **Modular Design**: Create small, focused modules (max 500 lines)
- **Documentation**: Include usage examples and expected outputs in docstrings
- **Error Handling**: Specific exceptions with clear error messages
- **Logging**: Use Loguru with appropriate log levels (debug, info, error)

## Data Storage

- **Database**: `output/synthlab.db` (SQLite with JSON1 extension, WAL mode)
- **Avatars**: `output/synths/avatar/*.png` (local) or fallback to `link_photo` URL
- **Reports**: `output/reports/`

## Environment Variables

Configure via `.env` file in project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...

# Database
DATABASE_PATH=output/synthlab.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Observability (optional)
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006

# Development
DEBUG=true
LOG_LEVEL=INFO
```



## Recent Changes
- 027-postgresql-migration: Added Python 3.13+ + SQLAlchemy 2.0+, Alembic 1.12+, psycopg2-binary (PostgreSQL driver)
- 026-experiment-documents: Added Python 3.13 (backend), TypeScript 5.5 (frontend) + FastAPI 0.109+, Pydantic 2.5+, SQLite 3 with JSON1, React 18, TanStack Query 5.56+
- 025-sankey-diagram: Added Python 3.13+ (backend), TypeScript 5.5+ (frontend) + FastAPI, Pydantic, React 18, Recharts, TanStack Query


<!-- MANUAL ADDITIONS START -->

## Code Review Checklist (Architecture Compliance)

**IMPORTANTE**: Todo code review DEVE verificar conformidade com a arquitetura documentada.

### Backend Checklist
- [ ] Router só faz `request → service → response`?
- [ ] Validações de negócio estão em services (não em routers)?
- [ ] Prompts de LLM estão em services (não em routers)?
- [ ] Chamadas LLM usam tracing Phoenix?
- [ ] SQL está em repositories (não em services ou routers)?
- [ ] Queries SQL usam parametrização (`?` placeholders)?
- [ ] Não há string interpolation em queries SQL?

### Frontend Checklist
- [ ] Pages usam hooks para dados (não fetch direto)?
- [ ] Componentes são puros (props → JSX)?
- [ ] Hooks usam React Query (useQuery, useMutation)?
- [ ] Query keys estão em `lib/query-keys.ts`?
- [ ] Services usam `fetchAPI` base?

### Padrões LLM (Critical)
Operações LLM DEVEM seguir este padrão:

```python
class MyLLMService:
    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or get_llm_client()
        self.logger = logger.bind(component="my_llm_service")

    def generate(self, data) -> Result:
        with _tracer.start_as_current_span("generate"):
            prompt = self._build_prompt(data)
            response = self.llm.complete_json(messages=[...])
            self.logger.info(f"Generated for {data.id}")
            return self._parse_response(response)

    def _build_prompt(self, data) -> str:
        return f"""..."""  # Prompt como método privado

```

### Referências de Arquitetura
- Backend: [`docs/arquitetura.md`](docs/arquitetura.md)
- Frontend: [`docs/arquitetura_front.md`](docs/arquitetura_front.md)
- Constitution: [`.specify/memory/constitution.md`](.specify/memory/constitution.md)

<!-- MANUAL ADDITIONS END -->
