# synth-lab Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-22

## Active Technologies

### Backend
- **Python**: 3.13+
- **Framework**: FastAPI 0.109.0+, Uvicorn, Pydantic 2.5.0+
- **Database**: SQLite 3 with JSON1 extension and WAL mode (`output/synthlab.db`)
- **AI/LLM**: OpenAI SDK 2.8.0+, OpenAI Agents 0.0.16+
- **Core Libraries**:
  - Data generation: Faker 21.0.0+
  - Schema validation: jsonschema 4.20.0+
  - CLI: Typer 0.9.0+
  - Logging: Loguru 0.7.0+
  - Image processing: Pillow 10.0.0+
- **Observability**: Arize Phoenix 5.0.0+, OpenTelemetry

### Frontend
- **Runtime**: TypeScript 5.5.3, React 18.3.1
- **Build**: Vite 6.3.4
- **UI Framework**: shadcn/ui, Tailwind CSS 3.4
- **Data Fetching**: TanStack React Query 5.56
- **Routing**: React Router DOM 6.26

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

### Backend
```bash
# Start API server
uv run uvicorn synth_lab.api.main:app --reload

# Run tests
pytest tests/

# Run linter
ruff check .

# Format code
ruff format .
```

### Frontend
```bash
cd frontend

# Start dev server
npm run dev

# Build for production
npm run build

# Run type check
npm run type-check
```

## Code Style

- **Backend**: Python 3.13+, follow PEP 8, use Ruff for linting/formatting
- **Frontend**: TypeScript strict mode, ESLint + Prettier
- **API**: RESTful conventions, OpenAPI/Swagger documentation
- **Database**: SQLite with proper migrations and WAL mode

## Data Storage

- **Database**: `output/synthlab.db` (SQLite with JSON1 extension)
- **Avatars**: `output/synths/avatar/*.png` (local) or fallback to `link_photo` URL
- **Reports**: `output/reports/`

## Recent Changes

- **2025-12-22**: Removed DuckDB dependency, migrated fully to SQLite
- **2025-12-22**: Added avatar fallback to `link_photo` when local file missing
- **2025-12-22**: Added pagination to synth list (45 items per page)
- **014-live-interview-cards**: Live interview features with SSE
- **013-summary-prfaq-states**: Summary generation and PR-FAQ artifact states
- **012-frontend-dashboard**: React frontend dashboard with shadcn/ui

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
