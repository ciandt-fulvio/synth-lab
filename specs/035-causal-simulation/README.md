# Causal Simulation System - Implementation Guide

**Status**: ✅ Complete (All Phases Implemented)
**Branch**: `035-causal-simulation`
**Last Updated**: 2026-01-26

## Overview

Sistema completo de simulação causal que transforma perguntas de negócio em linguagem natural em previsões acionáveis através de um pipeline de 6 estágios:

1. **Question Parsing**: Extração de intervenção, outcomes, horizonte temporal
2. **Causal Model Construction**: Geração de DAG (Directed Acyclic Graph) com classificação de variáveis
3. **Hypothesis Parametrization**: Quantificação com distribuições, ranges e correlações
4. **Simulation Engine**: Geração de 500+ mundos sintéticos com randomness determinística
5. **Evidence Calculation**: Agregação em percentis, análise de sensibilidade, modos de falha, clusters
6. **Insight Generation**: Recomendações acionáveis com rastreabilidade completa

## Project Structure

```
src/synth_lab/
├── services/simulation/          # Pipeline services
│   ├── question_parser_service.py       # NL → structured problem
│   ├── dag_constructor_service.py       # Generate & validate DAG
│   ├── hypothesis_parametrizer_service.py # Quantify variables
│   ├── simulation_engine_service.py      # Generate synthetic worlds
│   ├── evidence_calculator_service.py    # Aggregate statistics
│   ├── insight_generator_service.py      # Synthesize insights
│   ├── dag_validator.py                  # Cycle detection, orphan nodes
│   ├── distribution_sampler.py           # NumPy/SciPy wrappers
│   ├── sensitivity_analyzer.py           # Variance decomposition
│   ├── cluster_detector.py               # k-means clustering
│   └── failure_mode_detector.py          # Rule-based + chi-square
├── domain/entities/               # Business entities
│   ├── simulation.py
│   ├── causal_dag.py
│   ├── hypothesis.py
│   ├── simulated_world.py
│   ├── evidence.py
│   ├── simulation_insight.py
│   └── audit_trail.py
├── repositories/                  # Data access
│   ├── simulation_repository.py
│   ├── causal_dag_repository.py
│   ├── hypothesis_repository.py
│   └── simulation_insight_repository.py
├── api/
│   ├── routers/
│   │   ├── simulations.py        # Main simulation endpoints
│   │   ├── causal_dag.py         # DAG editing
│   │   ├── hypotheses.py         # Hypothesis editing
│   │   └── simulation_insights.py # Insights & tracing
│   └── schemas/
│       ├── simulation.py
│       ├── causal_dag.py
│       ├── hypothesis.py
│       └── simulation_insight.py
└── alembic/versions/
    └── 20260126_0001_add_causal_simulation_tables.py

frontend/src/
├── components/simulation/         # UI components
│   ├── QuestionInput.tsx
│   ├── DAGVisualization.tsx
│   ├── HypothesisTable.tsx
│   ├── PercentileChart.tsx
│   ├── SensitivityChart.tsx
│   ├── FailureModeCard.tsx
│   ├── ClusterComparison.tsx
│   └── InsightCard.tsx
├── hooks/                         # React Query hooks
│   ├── use-simulations.ts
│   ├── use-dag.ts
│   ├── use-hypotheses.ts
│   └── use-simulation-insights.ts
├── services/                      # API clients
│   ├── simulations-api.ts
│   ├── dag-api.ts
│   ├── hypotheses-api.ts
│   └── simulation-insights-api.ts
└── types/                         # TypeScript types
    ├── simulation.ts
    ├── causal-dag.ts
    ├── hypothesis.ts
    └── simulation-insight.ts

tests/
├── unit/services/simulation/      # Service unit tests
├── integration/api/               # API integration tests
└── e2e/                           # End-to-end tests
```

## Tech Stack

### Backend
- **Python 3.13+**
- **FastAPI 0.109+** (REST API)
- **SQLAlchemy 2.0+** (ORM)
- **PostgreSQL 14+** (JSONB for DAGs/hypotheses)
- **NetworkX 3.0+** (Graph algorithms)
- **NumPy 1.26+ / SciPy 1.11+** (Probabilistic simulation)
- **scikit-learn 1.4+** (Clustering, statistics)
- **Arize Phoenix 5.0+** (LLM tracing)

### Frontend
- **TypeScript 5.5+ / React 18**
- **TanStack Query 5.56+** (Data fetching)
- **React Flow 11.0+** (DAG visualization)
- **Recharts 2.12+** (Charts)
- **shadcn/ui** (UI components)

## Database Schema

8 tables with JSONB for flexibility:

1. **simulations**: Main records (question, status, seed)
2. **causal_dags**: DAG structures (nodes JSONB, edges JSONB)
3. **variables**: Individual variables (type, scope)
4. **hypotheses**: Quantified distributions (distribution_params JSONB)
5. **hypothesis_versions**: Versioned snapshots (dag_snapshot JSONB, hypotheses_snapshot JSONB)
6. **simulated_worlds**: World-level results (world_params JSONB)
7. **insights**: Generated insights (evidence JSONB, recommendations JSONB)
8. **audit_trails**: Reproducibility package (complete snapshots)

## Setup

### Prerequisites
```bash
# Python dependencies
cd /Users/fulvio/Projects/synth-lab
uv sync

# Frontend dependencies
cd frontend
npm install

# Database migrations
uv run alembic upgrade head
```

### Development
```bash
# Backend
uv run uvicorn synth_lab.api.main:app --reload

# Frontend
cd frontend && npm run dev

# Tests
pytest tests/unit/services/simulation/
pytest tests/integration/api/
npm run test:e2e
```

## Implementation Status

### Phase 1: Setup ✅ (8/8 tasks complete)
- [x] Python dependencies (networkx, scipy)
- [x] Frontend dependencies (reactflow, recharts)
- [x] Directory structure (backend + frontend)
- [x] Test configuration (pytest, playwright)
- [x] Database migration script
- [x] Documentation

### Phase 2: Foundational ✅ (12/12 tasks complete)
- [x] Database migration execution (8 tables created)
- [x] Domain entities (4 entity files: simulation, causal_dag, hypothesis, simulated_world)
- [x] Utility services (5 utilities: dag_validator, distribution_sampler, sensitivity_analyzer, cluster_detector, failure_mode_detector)
- [x] ORM models (8 models in src/synth_lab/models/orm/simulation.py)
- [x] Base repository (SimulationRepository with CRUD)

### Phase 3: User Story 1 (MVP) ✅ (18/18 tasks complete)
- [x] Core pipeline services (6 services)
- [x] Repositories (3 repositories)
- [x] API routers (4 routers + schemas)
- [x] Frontend components (4 components + hooks)

### Phase 4: User Story 2 (DAG Editor) ✅ (12/12 tasks complete)
- [x] DAG visualization with React Flow
- [x] Node/edge add/remove functionality
- [x] DAG validation and auto-layout
- [x] Version control for DAG changes

### Phase 5: User Story 3 (Hypothesis Editor) ✅ (12/12 tasks complete)
- [x] Hypothesis table with editable cells
- [x] Distribution picker component
- [x] Version selector component
- [x] Hypothesis versioning workflow

### Phase 6: User Story 4 (Failure Modes) ✅ (10/10 tasks complete)
- [x] FailureModeCard component
- [x] ClusterComparison component
- [x] InsightCard component
- [x] SimulationResults page

### Phase 7: User Story 5 (Versioning) ✅ (12/12 tasks complete)
- [x] VersionHistory component
- [x] VersionComparison component
- [x] Full version management workflow

### Phase 8: User Story 6 (Audit Trail) ✅ (10/10 tasks complete)
- [x] AuditTrailService with record() and replay()
- [x] AuditTrailModal component
- [x] TraceView component
- [x] Deterministic replay functionality

### Phase 9: Polish ✅ (6/6 tasks complete)
- [x] Error handling in API routers
- [x] Loading states in frontend
- [x] Phoenix tracing for all LLM calls
- [x] Query keys updated
- [x] Documentation updated

## MVP Definition

**Scope**: User Story 1 only (Ask Question and Get Forecast)

**Deliverables**:
- Submit natural language question → Get simulation ID
- View auto-generated DAG (8-20 variables)
- View auto-generated hypotheses (distributions, ranges)
- Run simulation (500 worlds in < 2 minutes)
- View evidence (percentiles, sensitivity, failure modes, clusters)
- Read actionable insights (recommendations with traceability)

**Success Criteria**:
- End-to-end forecast completes in < 5 minutes
- Results are deterministic (same seed = same results)
- Insights are traceable to evidence

## Architecture Principles

### Backend (Router → Service → Repository)
- **Routers**: Thin layer (request → service → response)
- **Services**: Business logic, LLM orchestration, pipeline stages
- **Repositories**: SQL queries with parametrized statements
- **LLM Calls**: ALL wrapped with Phoenix tracing

### Frontend (Pages → Components → Hooks → Services)
- **Pages**: Compose components + use hooks
- **Components**: Pure (props → JSX), NO fetch
- **Hooks**: Encapsulate React Query (useQuery/useMutation)
- **Services**: fetchAPI functions

## Performance Goals

| Stage | Target | Current |
|-------|--------|---------|
| Question Parsing | < 10s | TBD |
| DAG Generation | < 15s | TBD |
| Hypothesis Parametrization | < 20s | TBD |
| Simulation (500 worlds) | < 2min | TBD |
| Evidence Calculation | < 30s | TBD |
| Insight Generation | < 45s | TBD |
| **Total End-to-End** | **< 5min** | **TBD** |

## Testing Strategy

### Unit Tests (Fast Battery < 5s)
- Service methods with mocked LLM
- DAG validation with fixture graphs
- Hypothesis parametrization with sample distributions
- Mini-simulations (10 worlds)
- Frontend components without API

### Integration Tests (Complete Battery)
- API endpoints with test database
- Full pipeline with PostgreSQL container
- Deterministic replay tests

### E2E Tests (Smoke Tests)
- Question input → Results visualization
- DAG editing workflow
- Hypothesis adjustment workflow

## References

- [Specification](./spec.md) - User stories and requirements
- [Implementation Plan](./plan.md) - Technical approach and architecture
- [Data Model](./data-model.md) - Entities and relationships
- [Research Decisions](./research.md) - Technology choices and benchmarks
- [API Contracts](./contracts/) - OpenAPI specifications
- [Quickstart Guide](./quickstart.md) - Usage examples
- [Task Breakdown](./tasks.md) - Implementation tasks (98 total, 38 for MVP)

## Contributing

1. **TDD Approach**: Write tests FIRST (per constitution)
2. **Frequent Commits**: Commit after each completed task
3. **Follow Patterns**: Respect Router → Service → Repository architecture
4. **Phoenix Tracing**: Wrap ALL LLM calls
5. **Type Safety**: Use Pydantic (backend) and TypeScript (frontend)
6. **Documentation**: Update this README as features are completed

## Contact

For questions or clarifications, see the spec.md and plan.md documents or reach out to the development team.
