# Phase 1 Completion Summary

**Feature**: Simplified Hypothesis Selection Wizard
**Branch**: 036-simplified-hypothesis-wizard
**Date**: 2026-01-28
**Status**: ✅ Phase 1 Complete - Ready for Phase 2 (Task Generation)

## Deliverables

### 1. Research (Phase 0) ✅
**File**: [research.md](research.md)

All research questions resolved:
- ✅ Scenario profile parameter mapping (Conservative/Realistic/Optimistic)
- ✅ Criticality ranking algorithm (impact × uncertainty)
- ✅ Qualitative response mapping (more/less/equal/don't know → distribution adjustments)
- ✅ Decision context classification (simple = 3 questions, complex = 5 questions)
- ✅ LLM prompt engineering (minimal changes, algorithmic question generation)
- ✅ Backward compatibility (zero schema changes, full compatibility with simulation engine)

**Key Findings**:
- Low LLM cost: 1 call per wizard run (reuse existing parametrization with scenario hints)
- Fast execution: <10s total (scenario adjustment ~100ms, ranking ~50ms, question gen ~1ms)
- High testability: All algorithms deterministic (no LLM variability)
- Safe deployment: No schema changes, wizard hypotheses identical to manual at storage layer

### 2. Data Model (Phase 1) ✅
**File**: [data-model.md](data-model.md)

**Database Changes**: NONE (zero migrations)

**Existing Entities Reused**:
- `Hypothesis` (domain + ORM) - stores distribution configurations
- `CausalDAG` (domain + ORM) - provides variables for quantification
- `HypothesisVersion` (ORM) - versioning support
- `Variable` (domain) - variable metadata for questions

**New In-Memory Entities** (not persisted):
- `ScenarioProfile` (enum): Conservative, Realistic, Optimistic
- `ClarificationQuestion` (dataclass): variable_name, question_text, criticality_score
- `ClarificationResponse` (dataclass): variable_name, response
- `WizardState` (dataclass): orchestration state during wizard execution

### 3. API Contracts (Phase 1) ✅
**File**: [contracts/openapi.yaml](contracts/openapi.yaml)

**New Endpoints**:
1. `POST /api/simulations/{id}/hypotheses/wizard/init`
   - Request: `{ scenario_profile: "conservative"|"realistic"|"optimistic" }`
   - Response: `{ hypotheses[], clarification_questions[] }`
   - Side effect: Persists hypotheses to database

2. `POST /api/simulations/{id}/hypotheses/wizard/clarify`
   - Request: `{ responses: [{ variable_name, response: "more"|"less"|"equal"|"dont_know" }] }`
   - Response: `{ hypotheses[] }`
   - Side effect: Updates hypotheses in database

**Reused Endpoints**:
- `GET /api/simulations/{id}/hypotheses` - Retrieve hypotheses
- `PUT /api/simulations/{id}/hypotheses/{hyp_id}` - Manual override
- `POST /api/simulations/{id}/hypotheses/versions` - Save snapshot
- `POST /api/simulations/{id}/run` - Run simulation

### 4. Quickstart Guide (Phase 1) ✅
**File**: [quickstart.md](quickstart.md)

**Contents**:
- API usage examples (curl + TypeScript)
- Complete workflow walkthrough
- Integration with existing endpoints
- Testing strategies
- Troubleshooting guide

### 5. Agent Context Update (Phase 1) ✅
**Command**: `.specify/scripts/bash/update-agent-context.sh claude`

**Updates**:
- Added Python 3.13+ (backend), TypeScript 5.5+ (frontend) to language list
- Added FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK, React 18, TanStack Query, shadcn/ui to framework list
- Added PostgreSQL 14+ (no schema changes) to database list
- Updated `CLAUDE.md` with feature 036 technology context

## Constitution Check (Re-validation)

### Backend Architecture ✅
- ✅ Router layer: New endpoints delegate to `HypothesisWizardService`
- ✅ Service layer: New `HypothesisWizardService` orchestrates wizard logic
- ✅ Repository layer: Reuse existing repositories (no new repositories)
- ✅ LLM calls: All wrapped with `_tracer.start_as_current_span()` for Phoenix tracing
- ✅ SQL: Reuse existing parameterized queries (no new SQL)

### Frontend Architecture ✅
- ✅ Pages: New `HypothesisWizard.tsx` page composes wizard steps
- ✅ Components: Pure components for wizard steps (props → JSX)
- ✅ Hooks: New `use-hypothesis-wizard.ts` hook encapsulates wizard mutations
- ✅ Services: New `hypothesis-wizard-api.ts` functions use `fetchAPI`

### Test-First Development ✅
- ✅ TDD plan: Tests written before implementation for all new services
- ✅ Fast battery: Unit tests for scenario profile logic, clarification questions (<5s)
- ✅ Slow battery: Integration tests for wizard workflow, E2E tests for complete journey

### Code Quality ✅
- ✅ Function size: <30 lines per function (algorithmic logic is simple)
- ✅ File size: <500 lines per file (wizard service estimated ~300 lines)
- ✅ Dependencies: Zero new external dependencies (reuse OpenAI SDK, React, etc.)
- ✅ Linting: ruff (backend), ESLint (frontend)

### Language & Documentation ✅
- ✅ Code: English (classes, variables, functions)
- ✅ Comments/Docs: Portuguese (following project convention)
- ✅ User-facing strings: i18n-ready (English + Portuguese)

**Result**: ALL gates pass ✅ No constitution violations.

## Implementation Scope

### Backend Files (New)
- `src/synth_lab/services/simulation/hypothesis_wizard_service.py` (~300 lines)
  - `init_wizard()` - Initialize with scenario profile
  - `generate_clarification_questions()` - Rank variables, generate questions
  - `apply_clarifications()` - Map responses to distribution adjustments
  - `_classify_decision_context()` - Simple/complex heuristic
  - `_rank_critical_variables()` - Impact × uncertainty scoring
  - `_apply_profile_adjustments()` - Scenario profile parameter mapping
  - `_apply_response_adjustments()` - Qualitative response mapping

### Backend Files (Extended)
- `src/synth_lab/api/routers/hypotheses.py` (+30 lines)
  - Add 2 wizard endpoints

- `src/synth_lab/api/schemas/hypothesis.py` (+80 lines)
  - Add wizard request/response schemas

- `src/synth_lab/services/simulation/hypothesis_parametrizer_service.py` (+20 lines)
  - Extend prompt with scenario profile hints

### Frontend Files (New)
- `frontend/src/pages/HypothesisWizard.tsx` (~200 lines)
  - Wizard page with step navigation

- `frontend/src/components/simulation/hypothesis/ScenarioProfileSelector.tsx` (~80 lines)
  - Radio buttons for Conservative/Realistic/Optimistic

- `frontend/src/components/simulation/hypothesis/ClarificationQuestionsStep.tsx` (~150 lines)
  - Question cards with 4-choice responses

- `frontend/src/components/simulation/hypothesis/HypothesisReviewStep.tsx` (~100 lines)
  - Review generated hypotheses before proceeding

- `frontend/src/hooks/use-hypothesis-wizard.ts` (~120 lines)
  - `useInitWizard()` - Init mutation
  - `useClarifyHypotheses()` - Clarify mutation

- `frontend/src/services/hypothesis-wizard-api.ts` (~60 lines)
  - `initWizard()` - API function
  - `clarifyHypotheses()` - API function

### Test Files (New)
- `tests/unit/services/test_hypothesis_wizard_service.py` (~400 lines)
  - Test scenario profile adjustments
  - Test criticality ranking
  - Test clarification response mapping
  - Test decision context classification

- `tests/integration/api/test_hypothesis_wizard_api.py` (~200 lines)
  - Test `/wizard/init` endpoint
  - Test `/wizard/clarify` endpoint
  - Test error cases

- `frontend/tests/e2e/hypothesis-wizard.spec.ts` (~150 lines)
  - E2E test for complete wizard flow

**Total Estimated Lines**: ~1,890 lines (backend: ~700, frontend: ~710, tests: ~750)

## Reuse Analysis

### Existing Components Reused (No Changes)
- `HypothesisParametrizerService` (add scenario profile hint to prompt only)
- `HypothesisRepository` (zero changes)
- `CausalDAGRepository` (zero changes)
- `DistributionPicker` component (frontend)
- `HypothesisTable` component (frontend)
- `ScenarioSelector` component (adapt for 3 profiles)
- `useHypotheses` hook (frontend)
- `hypothesis-api.ts` service (frontend)

**Reuse Percentage**: ~90% of functionality reuses existing infrastructure.

## Risk Assessment

### Low Risk ✅
- **Schema changes**: NONE (zero migration risk)
- **Backward compatibility**: FULL (wizard hypotheses identical to manual at storage layer)
- **LLM cost**: MINIMAL (1 call per wizard run, same as current flow)
- **Latency**: LOW (<10s total, vs current ~5s, acceptable increase for wizard UX)

### Medium Risk ⚠️
- **LLM availability**: Wizard depends on OpenAI API (mitigation: retry logic, fallback to defaults)
- **Prompt engineering**: Scenario profile hints may not always produce expected adjustments (mitigation: algorithmic post-processing)

### Mitigations
- **LLM failure**: Fall back to realistic profile defaults, log error, notify user
- **Prompt variability**: Apply algorithmic adjustments AFTER LLM generation (guarantee profile consistency)
- **Testing**: Comprehensive unit tests for all algorithmic logic (deterministic, no LLM variability)

## Next Steps (Phase 2)

Run `/speckit.tasks` to generate implementation task breakdown.

**Expected Task Structure**:
1. **Backend TDD** (2-3 days)
   - Write unit tests for `HypothesisWizardService` methods
   - Implement service methods (scenario adjustments, ranking, mapping)
   - Add wizard endpoints to router
   - Write integration tests for endpoints

2. **Frontend Component-First** (1-2 days)
   - Create wizard UI components
   - Create wizard page
   - Create hooks and API service
   - Write E2E tests

3. **Documentation** (0.5 days)
   - Update user guide with wizard workflow
   - Update API documentation

**Estimated Total**: 3-5 days implementation + 1-2 days testing/review = 4-7 days

## Approval Checklist

Before proceeding to Phase 2 (task generation):

- ✅ All research questions answered with concrete decisions
- ✅ Data model designed (zero schema changes)
- ✅ API contracts defined (OpenAPI spec complete)
- ✅ Integration points identified (reuse maximized)
- ✅ Constitution compliance verified (all gates pass)
- ✅ Agent context updated with new technology
- ✅ Quickstart guide complete with examples
- ✅ Risk assessment complete with mitigations

**Status**: ✅ READY FOR PHASE 2

---

**Command to proceed**: `/speckit.tasks`

This will generate the detailed task breakdown in `tasks.md` with:
- Granular implementation tasks
- Dependencies between tasks
- Testing requirements
- Acceptance criteria per task
