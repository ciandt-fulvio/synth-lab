# Implementation Plan: Causal Simulation System for Decision Making

**Branch**: `035-causal-simulation` | **Date**: 2026-01-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/035-causal-simulation/spec.md`

## Summary

Implement a complete causal simulation system that transforms natural language business questions into actionable forecasts through a 6-stage pipeline: (1) Question Parsing - extract intervention, outcomes, time horizon from natural language; (2) Causal Model Construction - generate and validate directed acyclic graphs (DAGs) with variable classification; (3) Hypothesis Parametrization - quantify variables with distributions, ranges, and correlations; (4) Simulation Engine - generate 500+ synthetic worlds with seeded randomness; (5) Evidence Calculation - aggregate results into percentile distributions, sensitivity analysis, failure modes, and behavioral clusters; (6) Insight Generation - produce traceable, actionable recommendations. The system supports human editing at each stage, maintains complete audit trails for reproducibility, and enables hypothesis versioning for scenario planning.

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5.5+ (frontend), React 18
**Primary Dependencies**:
- **Backend**: FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic 2.5+, OpenAI SDK 2.8.0+, Arize Phoenix 5.0+
- **Graph/DAG**: NetworkX 3.0+ (Python standard for graph operations, cycle detection, topological sort)
- **Probabilistic Simulation**: NumPy 1.26+ (distributions), SciPy 1.11+ (statistical functions), Python's random module (seeded randomness)
- **Statistical Analysis**: scikit-learn 1.4+ (clustering, PCA), NumPy (percentiles, correlations)
- **Frontend**: TanStack Query 5.56+, shadcn/ui (Radix), React Flow 11.0+ (interactive DAG visualization), Recharts 2.12+ (charts)

**Storage**: PostgreSQL 14+ with JSONB for DAG structures, hypothesis parameters, and simulation metadata
**Testing**: pytest 8.0+ (backend), React Testing Library + Playwright (frontend E2E)
**Target Platform**: Web application (FastAPI backend + React frontend)
**Project Type**: Web (backend + frontend)

**Performance Goals**:
- Question parsing: < 10 seconds (LLM call)
- DAG generation: < 15 seconds (LLM call with structured output)
- Hypothesis parametrization: < 20 seconds (parallel LLM calls per variable)
- Simulation of 500 worlds: < 2 minutes (for DAGs with ≤ 20 variables)
- Evidence calculation: < 30 seconds (statistical aggregation)
- Insight generation: < 45 seconds (LLM synthesis with tracing)
- Total end-to-end for first forecast: < 5 minutes

**Constraints**:
- LLM context window: ~128K tokens (GPT-4.1 or Claude 3.5 Sonnet)
- DAG complexity: 8-20 variables per typical business question
- Simulation determinism: Must support exact replay via random seed
- No cycles in DAG: Must validate and reject circular dependencies
- Hypothesis versioning: Must preserve complete snapshots for comparison
- Audit trail: Every insight must trace back to exact variables, assumptions, and simulation worlds

**Scale/Scope**:
- 6 core workflows (Parse → DAG → Hypotheses → Simulate → Evidence → Insights)
- 13 domain entities (BusinessQuestion, ProblemDecomposition, CausalDAG, Variable, Hypothesis, HypothesisVersion, SimulatedWorld, SyntheticIndividual, Evidence, FailureMode, BehavioralCluster, Insight, AuditTrail)
- 8 database tables (simulations, causal_dags, variables, hypotheses, hypothesis_versions, simulated_worlds, insights, audit_trails)
- 47 functional requirements across 6 capability areas
- 6 user stories (priority P1-P3)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Principle I (TDD/BDD)**: ✅ PASS
- All 6 user stories have explicit Given-When-Then acceptance criteria
- Unit tests for each service method (question parser, DAG validator, hypothesis generator, simulation engine, evidence calculator, insight generator)
- Integration tests for end-to-end workflow with test database
- Contract tests for API endpoints and frontend hooks

**Principle II (Fast Test Battery)**: ✅ PASS
- Unit tests with mocked LLM responses (< 1s each)
- DAG validation tests with fixture graphs (< 0.5s)
- Hypothesis parametrization tests with sample distributions (< 0.5s)
- Mini-simulations (10 worlds) for testing logic without full compute (< 2s)
- Frontend component tests without API calls (< 1s)

**Principle III (Complete Test Battery)**: ✅ PASS
- Integration tests for complete simulation pipeline with PostgreSQL test container
- API tests for all CRUD operations (simulations, DAGs, hypotheses, insights)
- E2E tests for UI workflows (question input → DAG editing → hypothesis adjustment → results visualization)
- Regression tests for deterministic simulation replay (same seed = same results)

**Principle IV (Frequent Commits)**: ✅ PASS
- Commit after each Phase 0 research question answered
- Commit after each entity model defined (Phase 1)
- Commit after each service method implemented
- Commit after each API endpoint added
- Commit after each frontend component/hook completed
- Commit after migration scripts

**Principle V (Simplicity & Code Quality)**: ✅ PASS
- Files under 500 lines:
  - QuestionParserService (~200 lines)
  - DAGConstructorService (~300 lines)
  - HypothesisParametrizerService (~250 lines)
  - SimulationEngineService (~400 lines - largest, handles world generation)
  - EvidenceCalculatorService (~300 lines)
  - InsightGeneratorService (~250 lines)
- Functions under 30 lines (decompose simulation loop, DAG traversal, statistical calculations)
- No premature optimization - focus on correctness first, then performance
- Dependencies well-justified (NetworkX for graph algorithms, NumPy for distributions, React Flow for DAG UI)

**Principle VI (Language)**: ✅ PASS
- Code in English (CausalDAGService, SimulatedWorld, HypothesisVersion, etc.)
- Documentation in Portuguese (spec.md, plan.md, comments)
- User-facing strings externalized (UI labels, insight messages)

**Principle VII (Architecture)**: ✅ PASS
- **Backend**: Router → Service → Repository pattern maintained
  - `/api/routers/simulations.py`: Thin router (request → service → response)
  - Services:
    - `services/simulation/question_parser_service.py`: Parse natural language to structured problem
    - `services/simulation/dag_constructor_service.py`: Generate and validate causal DAGs
    - `services/simulation/hypothesis_parametrizer_service.py`: Quantify variables with distributions
    - `services/simulation/simulation_engine_service.py`: Generate synthetic worlds and compute outcomes
    - `services/simulation/evidence_calculator_service.py`: Aggregate statistics, detect patterns
    - `services/simulation/insight_generator_service.py`: Synthesize actionable insights with tracing
  - Repositories:
    - `repositories/simulation_repository.py`: CRUD for simulation records
    - `repositories/causal_dag_repository.py`: CRUD for DAG structures (JSONB)
    - `repositories/hypothesis_repository.py`: CRUD for hypotheses and versions
    - `repositories/insight_repository.py`: CRUD for generated insights
  - All LLM calls use `_tracer.start_as_current_span()` with Phoenix
  - All SQL queries parametrized in repositories
- **Frontend**:
  - Pages: `SimulationCreate.tsx`, `SimulationResults.tsx`, `DAGEditor.tsx`, `HypothesisEditor.tsx`
  - Components (pure, props → JSX):
    - `components/simulation/QuestionInput.tsx`
    - `components/simulation/DAGVisualization.tsx` (React Flow integration)
    - `components/simulation/HypothesisTable.tsx`
    - `components/simulation/PercentileChart.tsx`
    - `components/simulation/SensitivityChart.tsx`
    - `components/simulation/FailureModeCard.tsx`
    - `components/simulation/ClusterComparison.tsx`
    - `components/simulation/InsightCard.tsx`
  - Hooks: `use-simulations.ts`, `use-dag.ts`, `use-hypotheses.ts`, `use-insights.ts` (React Query wrappers)
  - Services: `simulations-api.ts` (fetchAPI calls)
  - Query keys: `lib/query-keys.ts` (centralized cache keys)

**Principle VIII (Other)**: ✅ PASS
- Phoenix tracing: ALL LLM calls wrapped (question parsing, DAG generation, hypothesis generation, insight synthesis)
- DRY: Shared utilities for DAG traversal, distribution sampling, percentile calculation
- SOLID: Single responsibility (one service per pipeline stage)
- KISS/YAGNI: Start with basic distributions (uniform, normal), no exotic models initially
- Separation of concerns: DAG logic separate from simulation logic, evidence separate from insights

**Violations Requiring Justification**: None

**Gate Result**: ✅ PASS - Proceed to Phase 0 research

## Project Structure

### Documentation (this feature)

```text
specs/035-causal-simulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── api-simulation.yaml
│   ├── api-dag.yaml
│   ├── api-hypothesis.yaml
│   └── api-insight.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
# Backend (Python)
src/synth_lab/
├── api/
│   ├── routers/
│   │   ├── simulations.py               # NEW: Simulation lifecycle endpoints
│   │   ├── causal_dag.py                # NEW: DAG CRUD and validation endpoints
│   │   ├── hypotheses.py                # NEW: Hypothesis CRUD and versioning endpoints
│   │   └── simulation_insights.py       # NEW: Insight retrieval and tracing endpoints
│   └── schemas/
│       ├── simulation.py                # NEW: Pydantic schemas for simulation requests/responses
│       ├── causal_dag.py                # NEW: DAG node/edge schemas
│       ├── hypothesis.py                # NEW: Hypothesis and version schemas
│       └── simulation_insight.py        # NEW: Insight and evidence schemas
├── domain/
│   └── entities/
│       ├── simulation.py                # NEW: Simulation aggregate root
│       ├── causal_dag.py                # NEW: CausalDAG, Variable entities
│       ├── hypothesis.py                # NEW: Hypothesis, HypothesisVersion entities
│       ├── simulated_world.py           # NEW: SimulatedWorld, SyntheticIndividual entities
│       ├── evidence.py                  # NEW: Evidence, FailureMode, BehavioralCluster entities
│       ├── simulation_insight.py        # NEW: Insight entity
│       └── audit_trail.py               # NEW: AuditTrail entity
├── repositories/
│   ├── simulation_repository.py         # NEW: Simulation CRUD
│   ├── causal_dag_repository.py         # NEW: DAG CRUD (JSONB storage)
│   ├── hypothesis_repository.py         # NEW: Hypothesis CRUD with versioning
│   └── simulation_insight_repository.py # NEW: Insight CRUD with traceability
├── services/
│   └── simulation/
│       ├── question_parser_service.py           # NEW: NL → structured problem
│       ├── dag_constructor_service.py           # NEW: Generate/validate DAG
│       ├── hypothesis_parametrizer_service.py   # NEW: Quantify variables
│       ├── simulation_engine_service.py         # NEW: Generate synthetic worlds
│       ├── evidence_calculator_service.py       # NEW: Aggregate statistics
│       ├── insight_generator_service.py         # NEW: Synthesize insights
│       ├── dag_validator.py                     # NEW: Cycle detection, orphan nodes
│       ├── distribution_sampler.py              # NEW: Sample from distributions
│       ├── sensitivity_analyzer.py              # NEW: Variance decomposition
│       ├── cluster_detector.py                  # NEW: k-means clustering
│       └── failure_mode_detector.py             # NEW: Threshold-based pattern detection
└── infrastructure/
    ├── llm_client.py                    # EXISTING: Reused for all LLM calls
    └── phoenix_tracing.py               # EXISTING: Reused for tracing

# Frontend (TypeScript/React)
frontend/src/
├── pages/
│   ├── SimulationCreate.tsx             # NEW: Create simulation from question
│   ├── SimulationResults.tsx            # NEW: View results with insights
│   ├── DAGEditor.tsx                    # NEW: Interactive DAG editing
│   └── HypothesisEditor.tsx             # NEW: Edit hypothesis parameters
├── components/
│   └── simulation/
│       ├── QuestionInput.tsx            # NEW: NL question textarea
│       ├── DAGVisualization.tsx         # NEW: React Flow DAG renderer
│       ├── DAGNodeCard.tsx              # NEW: Variable node display
│       ├── DAGEdgeControls.tsx          # NEW: Add/remove edges
│       ├── HypothesisTable.tsx          # NEW: Editable hypothesis table
│       ├── DistributionPicker.tsx       # NEW: Select distribution type
│       ├── PercentileChart.tsx          # NEW: Box plot with p5/p50/p95
│       ├── SensitivityChart.tsx         # NEW: Bar chart of variance explained
│       ├── FailureModeCard.tsx          # NEW: Display failure patterns
│       ├── ClusterComparison.tsx        # NEW: Side-by-side cluster stats
│       ├── InsightCard.tsx              # NEW: Insight display with tracing
│       ├── VersionSelector.tsx          # NEW: Hypothesis version dropdown
│       └── AuditTrailModal.tsx          # NEW: Reproducibility details
├── hooks/
│   ├── use-simulations.ts               # NEW: Simulation CRUD hooks
│   ├── use-dag.ts                       # NEW: DAG editing hooks
│   ├── use-hypotheses.ts                # NEW: Hypothesis CRUD with versioning
│   ├── use-simulation-insights.ts       # NEW: Insight retrieval hooks
│   └── use-evidence.ts                  # NEW: Evidence fetching hooks
├── services/
│   ├── simulations-api.ts               # NEW: Simulation API client
│   ├── dag-api.ts                       # NEW: DAG API client
│   ├── hypotheses-api.ts                # NEW: Hypothesis API client
│   └── simulation-insights-api.ts       # NEW: Insight API client
├── types/
│   ├── simulation.ts                    # NEW: TypeScript types for simulation
│   ├── causal-dag.ts                    # NEW: DAG types (nodes, edges)
│   ├── hypothesis.ts                    # NEW: Hypothesis types
│   └── simulation-insight.ts            # NEW: Insight and evidence types
└── lib/
    └── query-keys.ts                    # MODIFIED: Add simulation query keys

# Database Migrations
src/synth_lab/alembic/versions/
└── 20260126_0001_add_causal_simulation_tables.py  # NEW: Create 8 tables

# Tests
tests/
├── unit/
│   ├── services/simulation/
│   │   ├── test_question_parser_service.py
│   │   ├── test_dag_constructor_service.py
│   │   ├── test_hypothesis_parametrizer_service.py
│   │   ├── test_simulation_engine_service.py
│   │   ├── test_evidence_calculator_service.py
│   │   └── test_insight_generator_service.py
│   ├── domain/entities/
│   │   ├── test_causal_dag.py
│   │   ├── test_hypothesis.py
│   │   └── test_simulation_insight.py
│   └── infrastructure/
│       ├── test_dag_validator.py
│       ├── test_distribution_sampler.py
│       └── test_cluster_detector.py
├── integration/
│   ├── api/
│   │   ├── test_simulations_router.py
│   │   ├── test_causal_dag_router.py
│   │   ├── test_hypotheses_router.py
│   │   └── test_simulation_insights_router.py
│   └── repositories/
│       ├── test_simulation_repository.py
│       ├── test_causal_dag_repository.py
│       └── test_hypothesis_repository.py
└── e2e/
    ├── test_simulation_workflow.py
    └── test_hypothesis_versioning.py
```

**Structure Decision**: Web application structure. This feature introduces a new capability domain (causal simulation) with 6 tightly-coupled services forming a pipeline. Backend follows Router → Service → Repository pattern. Frontend adds new pages for simulation creation and results, with React Flow for interactive DAG editing. Database uses JSONB columns for flexible DAG/hypothesis storage while maintaining relational integrity for simulations, versions, and audit trails.

## Complexity Tracking

**No violations.** Constitution Check passed all principles. No complexity tracking required.
