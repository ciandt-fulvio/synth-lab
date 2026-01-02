# Implementation Plan: AI-Generated Insights for Quantitative Analysis

**Branch**: `023-quantitative-ai-insights` | **Date**: 2025-12-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/023-quantitative-ai-insights/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement automatic AI-generated insights for quantitative analysis results. The system will generate two types of reports: (1) individual chart insights displayed within each chart card (7 chart types: Try vs Success, SHAP Summary, PDP, PCA Scatter, Radar Comparison, Extreme Cases, Outliers), and (2) an executive summary synthesizing all insights. Insights are triggered automatically after chart data is cached, run in parallel via async background tasks, and stored in analysis_cache table. UI changes include removing the "Insights" tab, adding collapsible insight sections per chart card, and adding a "View Summary" button at the top of results page.

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5.5.3 (frontend), React 18.3.1
**Primary Dependencies**: FastAPI 0.109+, Pydantic 2.5+, OpenAI SDK 2.8.0+, TanStack Query 5.56+, Recharts 2.12.7+, shadcn/ui (Radix UI)
**Storage**: PostgreSQL 3 with JSON1 extension and WAL mode (`output/synthlab.db`)
**Testing**: pytest 8.0+ (backend), React Testing Library (frontend)
**Target Platform**: Web application (FastAPI backend + React frontend)
**Project Type**: Web (backend + frontend)
**Performance Goals**:
  - Individual insights generated within 2 minutes of chart data caching
  - Executive summary generated within 30 seconds after last individual insight
  - Insight generation succeeds for 90%+ of chart types
  - Users save 40% time interpreting results
**Constraints**:
  - LLM context window limit (~10K tokens per chart)
  - UI must remain responsive during background insight generation
  - Insights stored in existing analysis_cache table (no schema migrations)
  - Must integrate with existing async task patterns (daemon threads + asyncio)
**Scale/Scope**:
  - 7 chart types for individual insights
  - 1 executive summary per experiment
  - Typical experiment: 50-1000 synths, 7-9 charts pre-computed

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Principle I (TDD/BDD)**: ✅ PASS
- Tests will be written before implementation
- Each user story has clear Given-When-Then acceptance criteria
- Unit tests for insight generation services
- Integration tests for API endpoints
- Contract tests for frontend hooks and services

**Principle II (Fast Test Battery)**: ✅ PASS
- Unit tests for prompt building and response parsing (< 0.5s each)
- Fast tests use mocked LLM responses (no actual API calls)
- Backend unit tests: insight service logic, data extraction, prompt assembly
- Frontend unit tests: hooks, component rendering without API calls

**Principle III (Complete Test Battery)**: ✅ PASS
- Integration tests with test database for repository layer
- API tests for insight endpoints (with mocked LLM)
- E2E tests for complete workflow (chart data → insight generation → UI display)

**Principle IV (Frequent Commits)**: ✅ PASS
- Commits after each service method (backend)
- Commits after each component/hook (frontend)
- Commits at each task phase completion

**Principle V (Simplicity & Code Quality)**: ✅ PASS
- Files under 500 lines (services split by concern: InsightService, ExecutiveSummaryService)
- Functions under 30 lines (prompt builders as separate methods)
- No premature optimization - focus on working insights first
- Dependencies well-justified (04-mini for reasoning, existing LLMClient)

**Principle VI (Language)**: ✅ PASS
- Code in English (InsightService, ChartInsight, etc.)
- Documentation in Portuguese
- User-facing strings externalized (insight UI labels)

**Principle VII (Architecture)**: ✅ PASS
- **Backend**: Router → Service → Repository pattern maintained
  - `/api/routers/insights.py`: Thin router (request → service → response)
  - `services/insight_service.py`: Business logic (LLM prompts, insight generation)
  - `repositories/analysis_repository.py`: Data access (existing - read/write analysis_cache)
  - LLM calls use Phoenix tracing (`_tracer.start_as_current_span()`)
  - SQL queries parametrized in repositories
- **Frontend**:
  - Pages compose components and use hooks
  - Components pure (props → JSX)
  - Hooks use React Query (useQuery for fetching insights)
  - Services call API via fetchAPI
  - Query keys in `lib/query-keys.ts`

**Principle VIII (Other)**: ✅ PASS
- Phoenix tracing for all LLM calls (first-class concern)
- DRY: Shared prompt utilities, reusable insight display components
- SOLID: Single responsibility (InsightService per chart type)
- KISS/YAGNI: No over-engineering - start with basic insight structure

**Violations Requiring Justification**: None

**Gate Result**: ✅ PASS - Proceed to Phase 0 research

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Backend (Python)
src/synth_lab/
├── api/
│   └── routers/
│       └── insights.py                    # NEW: API endpoints for insights
├── domain/
│   └── entities/
│       ├── chart_insight.py               # NEW: ChartInsight entity
│       └── executive_summary.py           # NEW: ExecutiveSummary entity
├── repositories/
│   └── analysis_repository.py             # MODIFIED: Add insight read/write methods
├── services/
│   ├── insight_service.py                 # NEW: Individual chart insight generation
│   └── executive_summary_service.py       # NEW: Aggregated summary generation
└── infrastructure/
    └── llm_client.py                      # EXISTING: Reused for LLM calls

# Frontend (TypeScript/React)
frontend/src/
├── components/
│   └── experiments/
│       └── results/
│           ├── InsightSection.tsx         # NEW: Collapsible insight display
│           ├── ExecutiveSummaryModal.tsx  # NEW: Summary modal/panel
│           ├── DendrogramSection.tsx      # MODIFIED: Add InsightSection
│           ├── ExtremeCasesSection.tsx    # MODIFIED: Add InsightSection
│           ├── OutliersSection.tsx        # MODIFIED: Add InsightSection
│           ├── PDPSection.tsx             # MODIFIED: Add InsightSection
│           ├── PCAScatterSection.tsx      # MODIFIED: Add InsightSection
│           ├── PhaseOverview.tsx          # MODIFIED: Add InsightSection
│           └── RadarSection.tsx           # MODIFIED: Add InsightSection
├── hooks/
│   ├── use-chart-insight.ts               # NEW: Hook for chart insights
│   └── use-executive-summary.ts           # NEW: Hook for summary
├── services/
│   └── insights-api.ts                    # NEW: API client for insights
├── types/
│   └── insights.ts                        # NEW: TypeScript types
└── lib/
    └── query-keys.ts                      # MODIFIED: Add insight query keys

# Tests
tests/
├── unit/
│   ├── services/
│   │   ├── test_insight_service.py        # NEW: Unit tests for InsightService
│   │   └── test_executive_summary_service.py  # NEW: Unit tests for summary
│   └── domain/
│       └── entities/
│           ├── test_chart_insight.py      # NEW: ChartInsight entity tests
│           └── test_executive_summary.py  # NEW: ExecutiveSummary entity tests
├── integration/
│   ├── api/
│   │   └── test_insights_router.py        # NEW: API integration tests
│   └── repositories/
│       └── test_analysis_repository_insights.py  # NEW: Repository tests for insights
└── contract/
    └── test_insights_contracts.py         # NEW: Frontend-backend contract tests
```

**Structure Decision**: Web application structure (Option 2). This feature extends the existing analysis system with new backend services for AI insight generation and frontend components for display. Backend follows the established Router → Service → Repository pattern. Frontend extends existing chart section components with collapsible insight sections. No new tables needed - insights stored in existing `analysis_cache` table using new cache keys.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations.** Constitution Check passed all principles. No complexity tracking required.
