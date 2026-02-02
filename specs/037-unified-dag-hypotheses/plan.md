# Implementation Plan: Unified DAG & Hypothesis Generation

**Branch**: `037-unified-dag-hypotheses` | **Date**: 2026-02-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/037-unified-dag-hypotheses/spec.md`

**Note**: This plan merges DAG and hypothesis generation into a single LLM step, adds relevance-driven visualization, and replaces tooltips with drawer-based editing.

## Summary

Unify DAG and hypothesis generation into a single `gpt-4o-mini` structured output call, replacing two separate `gpt-4o` calls. Add relevance (low/medium/high) and range clamping (optional min/max) to hypotheses. Render DAG nodes with HSL saturation proportional to relevance. Replace hover tooltips with a right-side Sheet component for viewing and editing variable details (relevance, range).

**Technical Approach**: Extend `DAGResponse` structured output schema with hypothesis fields (`LLMHypothesis`). Switch model to `gpt-4o-mini`. Add `relevance` column via Alembic migration. Populate existing `range_min`/`range_max` columns. Apply `np.clip()` clamping in `DistributionSampler`. Build `NodeDetailSheet` component using existing Sheet UI. Modify `DAGNodeCard` to use HSL saturation mapping.

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5.5+ (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK, React 18, TanStack Query, shadcn/ui, ReactFlow
**Storage**: PostgreSQL 14+ (existing tables: hypotheses +1 column, causal_dags unchanged)
**Testing**: pytest (backend), Vitest + Playwright (frontend)
**Target Platform**: Web application (containerized for Railway deployment)
**Project Type**: Web application (fullstack)
**Performance Goals**: Unified generation <15s for 8-15 variables, drawer open <200ms, node saturation update instant
**Constraints**: Single LLM call for DAG+hypotheses, backward compatible with existing simulations, range validation min ≤ max
**Scale/Scope**: Extend existing causal simulation feature (035+036), ~5 modified files + ~3 new files per layer

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Backend Architecture Compliance

- ✅ **Router layer**: Modified `confirm-question` endpoint delegates to unified service, new PATCH endpoint for hypothesis updates
- ✅ **Service layer**: New `UnifiedDAGConstructorService` (or extend existing `DAGConstructorService`) merges DAG + hypothesis generation
- ✅ **Repository layer**: Reuse existing `HypothesisRepository` and `CausalDAGRepository` — add `update` method for single hypothesis
- ✅ **LLM calls**: Unified generation wrapped with `_tracer.start_as_current_span()` for Phoenix tracing
- ✅ **SQL**: Reuse existing parameterized queries, one Alembic migration for new column

### Frontend Architecture Compliance

- ✅ **Pages**: Modified `CausalSimulationDetail.tsx` to manage sheet state
- ✅ **Components**: New `NodeDetailSheet` (pure, props → JSX), modified `DAGNodeCard` for saturation
- ✅ **Hooks**: Extended `use-simulations.ts` with hypothesis update mutation
- ✅ **Services**: Extended `simulations-api.ts` with PATCH hypothesis function

### Test-First Development

- ✅ **TDD Required**: Tests written before implementation for unified service and clamping logic
- ✅ **Fast Battery**: Unit tests for clamping, relevance defaults, HSL color computation (<5s)
- ✅ **Slow Battery**: Integration tests for unified endpoint, E2E tests for drawer interaction
- ✅ **Coverage**: Minimum 80% for new code

### Code Quality

- ✅ **Function size**: <30 lines per function
- ✅ **File size**: <500 lines per file (unified service may be split if needed)
- ✅ **Dependencies**: No new external dependencies
- ✅ **Linting**: ruff (backend), ESLint (frontend)

### Language & Documentation

- ✅ **Code**: English (classes, variables, functions)
- ✅ **Comments/Docs**: Portuguese
- ✅ **User-facing strings**: i18n-ready

### Version Control

- ✅ **Atomic commits**: Each logical milestone
- ✅ **Fast tests on commit**: Run fast battery before each commit
- ✅ **Complete tests before PR**: All tests pass before PR

## Project Structure

### Documentation (this feature)

```text
specs/037-unified-dag-hypotheses/
├── plan.md              # This file
├── research.md          # Phase 0: Unified generation, relevance, clamping, drawer decisions
├── data-model.md        # Phase 1: Hypothesis entity changes, migration
├── quickstart.md        # Phase 1: How to use unified generation + drawer editing API
├── contracts/           # Phase 1: OpenAPI for PATCH hypothesis endpoint
└── tasks.md             # Phase 2: Implementation task breakdown (created by /speckit.tasks)
```

### Source Code (repository root)

```text
# Backend (extends existing src/synth_lab/)
src/synth_lab/
├── domain/entities/
│   └── hypothesis.py                    # [MODIFY] Add Relevance enum, range_min/range_max fields
├── services/simulation/
│   ├── dag_constructor_service.py       # [MODIFY] Extend with unified DAG+hypothesis generation
│   ├── distribution_sampler.py          # [MODIFY] Add np.clip() clamping after sampling
│   └── hypothesis_parametrizer_service.py  # [EXISTING] May be partially reused for prompt
├── repositories/
│   └── hypothesis_repository.py         # [MODIFY] Ensure update handles relevance + range
├── models/orm/
│   └── simulation.py                    # [MODIFY] Add relevance column to Hypothesis ORM
├── api/
│   ├── routers/simulations.py           # [MODIFY] confirm-question now generates hypotheses too
│   ├── routers/hypotheses.py            # [MODIFY] Add PATCH endpoint for single hypothesis
│   └── schemas/hypothesis.py            # [MODIFY] Add relevance field, update request schema

# Alembic migration
alembic/versions/
└── xxx_add_relevance_to_hypotheses.py   # [NEW] Add relevance column

# Tests
tests/
├── unit/services/
│   ├── test_dag_constructor_service.py  # [MODIFY] Test unified generation
│   └── test_distribution_sampler.py     # [MODIFY] Test clamping logic
└── integration/api/
    └── test_simulations_api.py          # [MODIFY] Test confirm-question returns hypotheses

# Frontend (extends existing frontend/src/)
frontend/src/
├── components/simulation/
│   ├── DAGNodeCard.tsx                  # [MODIFY] HSL saturation based on relevance
│   ├── DAGVisualization.tsx             # [MODIFY] Manage sheet state, remove tooltip logic
│   └── NodeDetailSheet.tsx              # [NEW] Right-side sheet for variable editing
├── hooks/
│   └── use-simulations.ts              # [MODIFY] Add hypothesis update mutation
├── services/
│   └── simulations-api.ts              # [MODIFY] Add PATCH hypothesis API function
└── types/
    └── simulation.ts                    # [MODIFY] Add relevance to Hypothesis type
```

**Structure Decision**: Web application structure. Extends existing backend/frontend with minimal new files. One new frontend component (`NodeDetailSheet`), one Alembic migration, rest is modifications to existing files.

## Complexity Tracking

No violations detected. All gates pass:
- Architecture follows established patterns (Router → Service → Repository, Page → Component → Hook → Service)
- No new external dependencies
- One simple database migration (add column with default)
- Follows TDD workflow
- Maintains code quality standards

## Phase 0: Research & Design Decisions

### Research Tasks

1. **Unified Structured Output Schema** — How to combine DAG + hypothesis in one LLM response?
   - **Decision**: Extend `DAGResponse` with `hypotheses: list[LLMHypothesis]` field
   - **Output**: [research.md Decision 1](research.md#decision-1-unified-dag--hypothesis-structured-output)

2. **Relevance Attribute Design** — How to store and visualize relevance?
   - **Decision**: Three-level enum (low/medium/high), HSL saturation mapping
   - **Output**: [research.md Decision 2](research.md#decision-2-relevance-attribute-design)

3. **Range Clamping Strategy** — How to apply min/max bounds during simulation?
   - **Decision**: Post-sampling `np.clip()` using existing ORM columns
   - **Output**: [research.md Decision 3](research.md#decision-3-range-clamping-strategy)

4. **Drawer Component Selection** — Sheet vs Drawer for node editing?
   - **Decision**: Use existing Sheet component (right-side, Radix-based)
   - **Output**: [research.md Decision 4](research.md#decision-4-drawer-component-selection)

5. **Node Visual Saturation** — How to implement relevance-driven colors?
   - **Decision**: HSL manipulation on existing scope colors
   - **Output**: [research.md Decision 5](research.md#decision-5-node-visual-saturation-implementation)

6. **Fallback for Incomplete Responses** — What if LLM misses some variables?
   - **Decision**: Uniform distribution default, medium relevance, no range
   - **Output**: [research.md Decision 6](research.md#decision-6-fallback-strategy-for-incomplete-llm-responses)

7. **Tooltip → Drawer Transition** — How to replace hover tooltips?
   - **Decision**: Remove onMouseEnter/Leave, make node clickable → opens sheet
   - **Output**: [research.md Decision 7](research.md#decision-7-tooltip-removal-and-drawer-trigger)

### Research Output

All findings documented in [research.md](research.md).

## Phase 1: Design & Contracts

### Data Model

**One Alembic migration**: Add `relevance VARCHAR(10) NOT NULL DEFAULT 'medium'` to `hypotheses` table.

**Modified entities**:
- `Hypothesis` (domain entity): Add `relevance: Relevance` field
- `Hypothesis` (ORM): Add `relevance` column
- `HypothesisSchema` (API): Add `relevance` field
- `UnifiedDAGResponse` (new): Extended structured output schema for LLM

**Full details**: [data-model.md](data-model.md)

### API Contracts

**Modified Endpoints**:
- `POST /api/simulations/{id}/confirm-question` — Now generates DAG + hypotheses (unified)

**New Endpoints**:
- `PATCH /api/simulations/{id}/hypotheses/{hyp_id}` — Update hypothesis relevance/range

**Reuse Existing**:
- `GET /api/simulations/{id}/hypotheses` — Retrieve hypotheses (now includes relevance, range)
- Wizard endpoints from feature 036 — Still work, apply adjustments AFTER unified generation

**Full details**: [contracts/openapi.yaml](contracts/openapi.yaml)

### Frontend Flow

```
1. User confirms question (existing flow)
   → POST /confirm-question (now unified)
   ↓
2. DAG + hypotheses generated in single step
   ↓
3. DAG displayed with relevance-driven saturation
   → High = full color, Medium = 70%, Low = 40%
   ↓
4. User clicks node → Sheet opens from right
   → Shows: name, description, relevance selector, range inputs
   ↓
5. User edits relevance/range → PATCH /hypotheses/{id}
   → Node saturation updates immediately
   ↓
6. User validates DAG → proceeds to simulation
```

### Integration Points

**Backend**:
- `DAGConstructorService.generate()` extended to produce `UnifiedDAGResponse`
- `DistributionSampler.sample()` adds `np.clip()` for range clamping
- `HypothesisRepository.update()` handles relevance + range fields
- Router `confirm-question` creates hypotheses alongside DAG

**Frontend**:
- `DAGNodeCard` reads hypothesis relevance for color computation
- `DAGVisualization` manages sheet state and passes `onEditNode` callback
- New `NodeDetailSheet` component with relevance selector + range inputs
- `use-simulations.ts` adds `useUpdateHypothesis` mutation

### Agent Context Update

After Phase 1 design, run:
```bash
.specify/scripts/bash/update-agent-context.sh claude
```

## Phase 1 Deliverables

1. **research.md** ✅ — All 7 research questions answered
2. **data-model.md** ✅ — Hypothesis entity changes, migration plan
3. **contracts/** ✅ — OpenAPI for PATCH hypothesis endpoint
4. **quickstart.md** ✅ — Unified generation + drawer editing API guide

## Next Steps (Phase 2 - Not in this command)

After Phase 1 completion, run `/speckit.tasks` to generate implementation task breakdown. Expected task structure:

1. Backend tasks (TDD):
   - Alembic migration for `relevance` column
   - Add `Relevance` enum to domain entity
   - Extend `Hypothesis` entity with relevance field
   - Write tests for unified DAG+hypothesis generation
   - Implement `UnifiedDAGResponse` schema and unified prompt
   - Write tests for range clamping
   - Implement `np.clip()` in `DistributionSampler`
   - Add PATCH hypothesis endpoint
   - Integration tests for confirm-question with hypotheses

2. Frontend tasks:
   - Add `relevance` to Hypothesis TypeScript type
   - Implement HSL saturation function in `DAGNodeCard`
   - Remove tooltip logic from `DAGNodeCard`
   - Create `NodeDetailSheet` component
   - Wire sheet to `DAGVisualization` with open/close state
   - Add `updateHypothesis` mutation hook
   - E2E tests for drawer flow

3. Documentation:
   - Update API docs with new fields
   - Mark PHASE1_COMPLETE.md
