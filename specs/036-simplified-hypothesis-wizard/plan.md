# Implementation Plan: Simplified Hypothesis Selection Wizard

**Branch**: `036-simplified-hypothesis-wizard` | **Date**: 2026-01-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/036-simplified-hypothesis-wizard/spec.md`

**Note**: This plan maximizes reuse of existing causal simulation infrastructure (branch 035) to minimize implementation scope.

## Summary

Add a simplified wizard for hypothesis configuration that reduces user burden from manual parameter specification to 3-5 qualitative questions. After DAG validation, users select a scenario profile (Conservative/Realistic/Optimistic), answer targeted clarification questions using qualitative responses (more/less/equal/don't know), and receive complete simulation-ready hypotheses. This enhances the existing hypothesis parametrization flow with an opinionated, user-friendly interface while preserving the full-control editor for advanced users.

**Technical Approach**: Extend existing `HypothesisParametrizerService` with scenario-aware profile generation and implement a new clarification question service that identifies critical variables and maps qualitative responses to distribution adjustments. Frontend adds a wizard UI component that wraps existing hypothesis editing components with a guided flow.

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5.5+ (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK, React 18, TanStack Query, shadcn/ui
**Storage**: PostgreSQL 14+ (existing tables: simulations, causal_dags, hypotheses, hypothesis_versions - no schema changes needed)
**Testing**: pytest (backend), Vitest + Playwright (frontend)
**Target Platform**: Web application (containerized for Railway deployment)
**Project Type**: Web application (fullstack)
**Performance Goals**: <3 minute hypothesis configuration for 10-variable DAG, <10s simulation start, LLM calls <5s p95
**Constraints**: Max 5 clarification questions per workflow, LLM costs <$0.10 per hypothesis set, maintain backward compatibility with existing hypothesis editor
**Scale/Scope**: Extend existing causal simulation feature (specs/035), reuse 90% of backend/frontend components, add ~3-5 new files per layer

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Backend Architecture Compliance

- ✅ **Router layer**: New endpoint `POST /api/simulations/{id}/hypotheses/wizard` delegates to service
- ✅ **Service layer**: New `HypothesisWizardService` orchestrates scenario profile selection and clarification questions
- ✅ **Repository layer**: Reuse existing `HypothesisRepository` and `CausalDAGRepository` - no new repositories needed
- ✅ **LLM calls**: All LLM operations wrapped with `_tracer.start_as_current_span()` for Phoenix tracing
- ✅ **SQL**: Reuse existing parameterized queries in repositories - no new SQL

### Frontend Architecture Compliance

- ✅ **Pages**: New `HypothesisWizard.tsx` page composes wizard steps
- ✅ **Components**: Pure components for wizard steps (props → JSX), no direct fetch
- ✅ **Hooks**: New `use-hypothesis-wizard.ts` hook encapsulates wizard-specific mutations
- ✅ **Services**: New `hypothesis-wizard-api.ts` functions use `fetchAPI`

### Test-First Development

- ✅ **TDD Required**: Tests written before implementation for all new services
- ✅ **Fast Battery**: Unit tests for scenario profile logic, clarification question generation (<5s)
- ✅ **Slow Battery**: Integration tests for wizard workflow, E2E tests for complete user journey
- ✅ **Coverage**: Minimum 80% for new code, integration with existing test infrastructure

### Code Quality

- ✅ **Function size**: <30 lines per function
- ✅ **File size**: <500 lines per file (wizard service may be split into helpers if needed)
- ✅ **Dependencies**: Reuse existing OpenAI SDK, no new external dependencies
- ✅ **Linting**: ruff (backend), ESLint (frontend)

### Language & Documentation

- ✅ **Code**: English (classes, variables, functions)
- ✅ **Comments/Docs**: Portuguese (following project convention)
- ✅ **User-facing strings**: i18n-ready (English + Portuguese)

### Version Control

- ✅ **Atomic commits**: Each logical milestone (e.g., "Add scenario profile selection service")
- ✅ **Fast tests on commit**: Run fast battery before each commit
- ✅ **Complete tests before PR**: All tests pass before opening PR

## Project Structure

### Documentation (this feature)

```text
specs/036-simplified-hypothesis-wizard/
├── plan.md              # This file
├── research.md          # Phase 0: Scenario profile strategies, clarification logic
├── data-model.md        # Phase 1: ScenarioProfile, ClarificationQuestion entities (if needed)
├── quickstart.md        # Phase 1: How to use the wizard API
├── contracts/           # Phase 1: OpenAPI schemas for wizard endpoints
└── tasks.md             # Phase 2: Implementation task breakdown (created by /speckit.tasks)
```

### Source Code (repository root)

```text
# Backend (extends existing src/synth_lab/)
src/synth_lab/
├── domain/entities/
│   └── hypothesis.py         # [EXISTING] Reuse Hypothesis, DistributionType, ScenarioOption
├── services/simulation/
│   ├── hypothesis_parametrizer_service.py  # [EXISTING] Extend with scenario profiles
│   └── hypothesis_wizard_service.py        # [NEW] Wizard orchestration + clarification questions
├── repositories/
│   └── hypothesis_repository.py            # [EXISTING] Reuse as-is
├── api/
│   ├── routers/hypotheses.py               # [EXISTING] Add wizard endpoint
│   └── schemas/hypothesis.py               # [EXISTING] Add wizard request/response schemas
└── tests/
    ├── unit/services/
    │   └── test_hypothesis_wizard_service.py    # [NEW] Unit tests for wizard logic
    └── integration/api/
        └── test_hypothesis_wizard_api.py        # [NEW] Integration tests for wizard endpoint

# Frontend (extends existing frontend/src/)
frontend/src/
├── pages/
│   └── HypothesisWizard.tsx                # [NEW] Wizard page with step navigation
├── components/simulation/hypothesis/
│   ├── ScenarioProfileSelector.tsx         # [NEW] Conservative/Realistic/Optimistic radio buttons
│   ├── ClarificationQuestionsStep.tsx      # [NEW] Qualitative question cards with 4-choice responses
│   ├── HypothesisReviewStep.tsx            # [NEW] Review generated hypotheses before proceeding
│   └── [existing components reused]        # ScenarioSelector, CriticalUncertaintiesStep, etc.
├── hooks/
│   └── use-hypothesis-wizard.ts            # [NEW] Wizard workflow hooks (useScenarioProfile, useClarificationQuestions)
├── services/
│   └── hypothesis-wizard-api.ts            # [NEW] API functions for wizard endpoints
└── tests/e2e/
    └── hypothesis-wizard.spec.ts           # [NEW] E2E tests for complete wizard flow
```

**Structure Decision**: Web application structure (Option 2). Extends existing synth-lab backend/frontend with minimal new files. Prioritizes reuse of existing hypothesis, DAG, and LLM infrastructure. No database schema changes required - all data fits in existing `hypotheses` table with new generation logic.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. All gates pass:
- Architecture follows established backend (Router → Service → Repository) and frontend (Page → Component → Hook → Service) patterns
- No new external dependencies
- Reuses existing database schema
- Follows TDD workflow
- Maintains code quality standards

## Phase 0: Research & Design Decisions

### Research Tasks

1. **Scenario Profile Strategy**
   - **Question**: How should Conservative/Realistic/Optimistic profiles map to distribution parameters for each variable type?
   - **Research needed**: Define concrete rules for adjusting means, variances, and ranges based on profile selection
   - **Output**: Scenario profile parameter mapping table (e.g., Conservative = -1σ mean shift, +50% variance)

2. **Clarification Question Generation**
   - **Question**: How to identify 3-5 "critical" variables with highest impact and uncertainty?
   - **Research needed**: Ranking algorithm (e.g., impact score = out-degree × is_outcome × controllability; uncertainty score = variance)
   - **Output**: Criticality ranking algorithm specification

3. **Qualitative Response Mapping**
   - **Question**: How to map "more"/"less"/"equal"/"don't know" to quantitative distribution adjustments?
   - **Research needed**: Define adjustment rules (e.g., "more" = +0.5σ mean shift, "don't know" = +100% variance)
   - **Output**: Response mapping table with concrete parameter adjustments

4. **Decision Context Classification**
   - **Question**: How to classify DAG as "simple" (3 questions max) vs "complex" (5 questions max)?
   - **Research needed**: Heuristics based on node count, edge count, outcome count, controllable variable count
   - **Output**: Classification decision tree (e.g., if nodes ≤ 5 → simple, if nodes > 10 → complex)

5. **LLM Prompt Engineering**
   - **Question**: What prompts generate best scenario profiles and clarification questions?
   - **Research needed**: Test few-shot examples, structured output formats, chain-of-thought reasoning
   - **Output**: Prompt templates with examples for scenario generation and question generation

6. **Backward Compatibility**
   - **Question**: How to ensure wizard-generated hypotheses work with existing simulation engine?
   - **Research needed**: Validate that all DistributionType enums and parameter shapes remain compatible
   - **Output**: Compatibility validation checklist

### Research Output Location

All research findings will be documented in `specs/036-simplified-hypothesis-wizard/research.md` following this template:

```markdown
# Research Findings: Simplified Hypothesis Wizard

## Decision 1: Scenario Profile Parameter Mapping

**Decision**: [Conservative/Realistic/Optimistic → distribution parameter adjustments]
**Rationale**: [Why these specific adjustments]
**Alternatives Considered**: [Other mapping strategies evaluated]

## Decision 2: Criticality Ranking Algorithm

[...]
```

## Phase 1: Design & Contracts

### Data Model

**No new database entities required**. Reuse existing:
- `Hypothesis` (domain entity + ORM model) - stores distribution configurations
- `CausalDAG` (domain entity + ORM model) - provides variables for quantification
- `HypothesisVersion` (ORM model) - versioning for scenario profile changes

**New in-memory entities** (not persisted):
- `ScenarioProfile` (enum): Conservative, Realistic, Optimistic
- `ClarificationQuestion` (dataclass): variable_name, question_text, response (more/less/equal/don't know)
- `WizardState` (dataclass): selected_profile, clarification_responses, generated_hypotheses

### API Contracts

**New Endpoints**:

```
POST /api/simulations/{simulation_id}/hypotheses/wizard/init
  Request: { scenario_profile: "Conservative" | "Realistic" | "Optimistic" }
  Response: { hypotheses: Hypothesis[], clarification_questions: ClarificationQuestion[] }

POST /api/simulations/{simulation_id}/hypotheses/wizard/clarify
  Request: { responses: [{ variable_name, response: "more"|"less"|"equal"|"don't know" }] }
  Response: { hypotheses: Hypothesis[] }
```

**Reuse Existing Endpoints**:
- `GET /api/simulations/{id}/hypotheses` - Retrieve generated hypotheses
- `PUT /api/simulations/{id}/hypotheses` - Update hypotheses (for manual overrides)
- `POST /api/simulations/{id}/hypotheses/versions` - Save hypothesis version

### Frontend Flow

```
1. User validates DAG (existing flow)
   ↓
2. Navigate to /simulations/{id}/wizard
   ↓
3. ScenarioProfileSelector (Conservative/Realistic/Optimistic)
   → POST /wizard/init
   ↓
4. ClarificationQuestionsStep (if questions returned)
   → POST /wizard/clarify
   ↓
5. HypothesisReviewStep (show generated hypotheses)
   → Navigate to simulation detail or run simulation
```

### Integration Points

**Backend**:
- `HypothesisWizardService` calls `HypothesisParametrizerService` with scenario profile context
- `HypothesisParametrizerService._build_parametrization_prompt()` extended to include scenario profile hints
- New `_rank_critical_variables()` helper in `HypothesisWizardService`
- New `_apply_clarification_adjustments()` helper in `HypothesisWizardService`

**Frontend**:
- Wizard page uses existing `useHypotheses` hook for data fetching
- New `useHypothesisWizard` hook wraps wizard-specific mutations
- Reuse `DistributionPicker`, `HypothesisTable` for review step
- Reuse `ScenarioSelector` pattern (adapt for 3 profiles instead of controllable variable scenarios)

### Agent Context Update

After Phase 1 design, run:
```bash
.specify/scripts/bash/update-agent-context.sh claude
```

This updates `.specify/memory/claude_context.md` with new technology additions from this plan (none expected - all reuse).

## Phase 1 Deliverables

1. **research.md** - All 6 research questions answered with concrete decisions
2. **data-model.md** - In-memory entities documented (ScenarioProfile, ClarificationQuestion, WizardState)
3. **contracts/** - OpenAPI schemas for 2 new wizard endpoints
4. **quickstart.md** - How to use wizard API with curl examples

## Next Steps (Phase 2 - Not in this command)

After Phase 1 completion, run `/speckit.tasks` to generate implementation task breakdown. Expected task structure:

1. Backend tasks (TDD):
   - Write tests for scenario profile logic
   - Implement `HypothesisWizardService.init_wizard()`
   - Write tests for clarification question generation
   - Implement `HypothesisWizardService.generate_clarification_questions()`
   - Write tests for qualitative response mapping
   - Implement `HypothesisWizardService.apply_clarifications()`
   - Add wizard endpoints to router
   - Integration tests for complete wizard flow

2. Frontend tasks (Component-first):
   - Create `ScenarioProfileSelector` component
   - Create `ClarificationQuestionsStep` component
   - Create `HypothesisReviewStep` component
   - Create `HypothesisWizard` page
   - Create `use-hypothesis-wizard` hook
   - Create `hypothesis-wizard-api` service
   - E2E tests for wizard flow

3. Documentation:
   - Update user guide with wizard workflow
   - Update API documentation with wizard endpoints

**Estimated Implementation Time**: 3-5 days (2-3 backend, 1-2 frontend) due to high reuse of existing components.
