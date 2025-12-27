# Tasks: Experiment Hub - Reorganização da Navegação

**Input**: Design documents from `/specs/018-experiment-hub/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml
**Status**: SIMPLIFIED for faster execution (respecting TDD)

## TDD/BDD Methodology

**Approach**: Test-First Development with consolidated tasks for speed

1. **RED**: Write failing test (or verify existing test fails)
2. **GREEN**: Implement to pass test
3. **Checkpoint**: Verify all tests pass before moving on

---

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[TEST]**: Test task | **[IMPL]**: Implementation task | **[BDD]**: Based on spec.md scenario

## Path Conventions

- **Backend**: `src/synth_lab/` (Python/FastAPI)
- **Frontend**: `frontend/src/` (React/TypeScript)
- **Tests**: `tests/` (pytest)

---

## Phase 1: Database Schema & Domain Entities ✅ COMPLETED

- [x] T001 [TEST] Schema validation test - experiments/synth_groups tables
- [x] T002 [IMPL] Update database schema - add all new tables and columns
- [x] T003 [P] [TEST] Experiment entity tests
- [x] T004 [P] [TEST] SynthGroup entity tests
- [x] T005 [P] [IMPL] Create Experiment domain entity
- [x] T006 [P] [IMPL] Create SynthGroup domain entity
- [x] T007 [P] Pydantic schemas for experiments
- [x] T008 [P] Pydantic schemas for synth groups
- [x] T009 [P] TypeScript types for Experiment
- [x] T010 [P] TypeScript types for SynthGroup

---

## Phase 2: Repositories (TDD) ✅ COMPLETED

- [x] T011 [TEST] ExperimentRepository unit tests
- [x] T012 [IMPL] ExperimentRepository implementation
- [x] T013 [P] [TEST] SynthGroupRepository unit tests
- [x] T014 [P] [IMPL] SynthGroupRepository implementation

---

## Phase 3: Services (TDD) ✅ COMPLETED

- [x] T015 [TEST] ExperimentService unit tests
- [x] T016 [IMPL] ExperimentService implementation
- [x] T017 [P] [TEST] SynthGroupService unit tests
- [x] T018 [P] [IMPL] SynthGroupService implementation

---

## Phase 4: API Endpoints (BDD) - SIMPLIFIED

**Purpose**: Complete and verify REST API endpoints

- [x] T019 [BDD] Fix and verify experiments API integration tests in tests/integration/api/test_experiments_api.py
  - Fix test database patching (monkeypatch _db and get_database)
  - Verify all 14 tests pass: create, list, get, update scenarios
- [x] T020 [P] [BDD] Fix and verify synth-groups API integration tests in tests/integration/api/test_synth_groups_api.py
  - Fix test database patching
  - Verify all 12 tests pass: create, list, get, delete scenarios

**Checkpoint**: All 27 API integration tests passing

---

## Phase 5: Frontend Data Layer - SIMPLIFIED

**Purpose**: API clients and React Query hooks (no tests per project standard)

- [x] T021 Create experiments API + hook in frontend/src/services/experiments-api.ts and frontend/src/hooks/use-experiments.ts
  - API: list, get, create, update, delete functions
  - Hook: useExperiments(), useExperiment(id), create/update/delete mutations
- [x] T022 [P] Create synth-groups API + hook in frontend/src/services/synth-groups-api.ts and frontend/src/hooks/use-synth-groups.ts
  - API: list, get, create, delete functions
  - Hook: useSynthGroups(), useSynthGroup(id), create/delete mutations

**Checkpoint**: Frontend can fetch experiments and synth-groups from API

---

## Phase 6: User Story 1 - Lista de Experimentos (P0) - MVP

**Goal**: Home page shows grid of experiment cards

**BDD Scenarios**:
1. Home + experiments exist → grid with name, hypothesis, counters, date
2. Home + no experiments → empty state with CTA
3. Click card → navigate to detail

### Implementation

- [x] T023 [US1] Create ExperimentCard and EmptyState components in frontend/src/components/experiments/
  - ExperimentCard: name, truncated hypothesis, counters, created_at, click handler
  - EmptyState: illustration + CTA button
- [x] T024 [US1] Refactor Index.tsx to show experiment list in frontend/src/pages/Index.tsx
  - Use useExperiments hook
  - Grid of ExperimentCard components
  - Show EmptyState when empty
  - Loading and error states
  - Click navigation to /experiments/:id

**Manual Validation**: Access home, verify grid displays, click card navigates

---

## Phase 7: User Story 2 - Criar Experimento (P0)

**Goal**: User can create new experiment via modal

**BDD Scenarios**:
1. Click "+ Novo" → modal opens
2. Fill name + hypothesis + save → experiment created
3. Missing required fields → validation error shown

### Implementation

- [x] T025 [US2] Create ExperimentForm component in frontend/src/components/experiments/ExperimentForm.tsx
  - Fields: name (required, max 100), hypothesis (required, max 500), description (optional)
  - Client-side validation with error messages
  - Submit handler with loading state
- [x] T026 [US2] Add create modal to Index.tsx
  - "+ Novo Experimento" button
  - Modal with ExperimentForm
  - On success: close modal, invalidate query (auto-refresh list)

**Manual Validation**: Click "+", fill form, save, verify appears in list

---

## Phase 8: User Story 3 - Detalhe do Experimento (P0) - MVP COMPLETE

**Goal**: Experiment detail page with simulations and interviews sections

**BDD Scenarios**:
1. Click experiment → detail page with info
2. Has simulations → show simulation cards
3. Has interviews → show interview cards
4. Empty sections → show CTAs
5. Click breadcrumb → back to home

### Implementation

- [x] T027 [US3] Add route and create ExperimentDetail page in frontend/src/App.tsx and frontend/src/pages/ExperimentDetail.tsx
  - Route: /experiments/:id
  - Header: name, hypothesis, created_at, Edit button
  - Breadcrumb: "<- Experimentos" back link
  - Simulations section (empty state for now)
  - Interviews section (empty state for now)
- [x] T028 [P] [US3] Create SimulationCard and InterviewCard components in frontend/src/components/experiments/
  - SimulationCard: scenario_id, score, status, has_insights
  - InterviewCard: topic_name, synth_count, status, has_summary
- [x] T029 [US3] Wire up simulations and interviews sections in ExperimentDetail
  - Fetch from useExperiment(id) - simulations and interviews arrays
  - Display cards or empty states with CTAs

**Manual Validation**: Navigate to experiment, verify sections display correctly

**Checkpoint**: MVP COMPLETE - Users can list, create, and view experiments

---

## Phase 9: User Story 9 - Editar Experimento (P2) - Quick Win

**Goal**: Edit experiment name/hypothesis/description

**Note**: Backend PUT endpoint already exists from T019. Just need frontend.

### Implementation

- [x] T030 [US9] Add edit functionality to ExperimentDetail
  - "Editar" button opens modal with ExperimentForm prefilled
  - Update mutation in useExperiments hook
  - On success: close modal, refetch experiment

**Manual Validation**: Click Edit, modify, save, verify changes persist

---

## Phase 10: Header + Synths Navigation (P1) - CONSOLIDATED

**Goal**: Global header with Synths access, separate synths page

### Implementation

- [x] T031 Create Header component and integrate in layout in frontend/src/components/layout/Header.tsx
  - Synths icon/button → navigates to /synths
  - Consistent design across pages
- [x] T032 [P] Add /synths route and create Synths page in frontend/src/pages/Synths.tsx
  - Move existing synth catalog functionality
  - Add synth_group_id display on cards
- [x] T033 Integrate Header in all pages (Index, ExperimentDetail, Synths)

**Manual Validation**: From any page, click Synths icon, catalog opens

---

## Phase 11: Simulation Navigation (P1) - CONSOLIDATED

**Goal**: Navigate from experiment to simulation detail

### Implementation

- [x] T034 [US6] Add simulation detail route and page in frontend/src/App.tsx and frontend/src/pages/SimulationDetail.tsx
  - Route: /experiments/:id/simulations/:simId
  - Reuse existing simulation components (ScoreDisplay, InsightsPanel, etc.)
  - Breadcrumb: "<- [Experiment Name]" → back to experiment
- [x] T035 [US6] Connect SimulationCard click to navigate to detail

**Manual Validation**: Click simulation card, detail opens, breadcrumb works

---

## Phase 12: Interview Navigation (P1) - CONSOLIDATED

**Goal**: Navigate from experiment to interview detail

**Note**: InterviewDetail page already exists - just need route change and breadcrumb

### Implementation

- [x] T036 [US7] Add interview route and update InterviewDetail in frontend/src/App.tsx and frontend/src/pages/InterviewDetail.tsx
  - Route: /experiments/:expId/interviews/:execId
  - Update breadcrumb to navigate to experiment (not home)
- [x] T037 [US7] Connect InterviewCard click to navigate to detail

**Manual Validation**: Click interview card, same page behavior, breadcrumb goes to experiment

---

## Phase 13: Link Simulations to Experiments (P1) - DEFERRED TO POST-MVP

**Goal**: Create simulations from experiment detail

**Note**: This requires extending the scorecard creation flow.
         Defer to post-MVP - simulations can be manually linked for now.

---

## Phase 14: Link Interviews to Experiments (P1) - DEFERRED TO POST-MVP

**Goal**: Create interviews from experiment detail

**Note**: This requires extending the research execution flow.
         Defer to post-MVP - interviews can be manually linked for now.

---

## Phase 15: Synth Groups Integration - DEFERRED TO POST-MVP

**Goal**: Auto-assign synth_group_id during synth generation

**Note**: Schema already supports synth_group_id.
         Defer to post-MVP - groups can be assigned manually for now.

---

## Phase 16: Polish & Final Validation

**Purpose**: Essential cleanup and validation

- [x] T038 [P] Add 404 handling for invalid experiment URLs in ExperimentDetail
- [x] T039 [P] Add loading skeletons for experiment cards and detail page
- [x] T040 Run quickstart.md validation - test all documented flows
- [x] T041 Run full test suite and verify all tests pass (528 tests passed)

---

## Dependencies & Execution Order

### Critical Path (MVP)

```
Phase 4 (Fix API Tests)
    |
    v
Phase 5 (Frontend Data Layer)
    |
    v
Phase 6 (US1: List) → Phase 7 (US2: Create) → Phase 8 (US3: Detail)
                                                    |
                                               MVP COMPLETE
```

### Post-MVP Additions

```
After MVP:
    +-------+-------+-------+
    |       |       |       |
    v       v       v       v
   US9    US6+7   US8    Polish
 (Edit) (Nav)  (Synths)  (T38-41)
```

---

## Summary Statistics

| Phase | Total Tasks | Status |
|-------|-------------|--------|
| 1. Schema & Entities | 10 | ✅ COMPLETED |
| 2. Repositories | 4 | ✅ COMPLETED |
| 3. Services | 4 | ✅ COMPLETED |
| 4. API Tests | 2 | ✅ COMPLETED |
| 5. Frontend Data | 2 | ✅ COMPLETED |
| 6. US1 (List) | 2 | ✅ COMPLETED |
| 7. US2 (Create) | 2 | ✅ COMPLETED |
| 8. US3 (Detail) | 3 | ✅ COMPLETED |
| 9. US9 (Edit) | 1 | ✅ COMPLETED |
| 10. Header/Synths | 3 | ✅ COMPLETED |
| 11. Simulation Nav | 2 | ✅ COMPLETED |
| 12. Interview Nav | 2 | ✅ COMPLETED |
| 13-15. DEFERRED | 0 | POST-MVP |
| 16. Polish | 4 | ✅ COMPLETED |
| **Active Total** | **41** | ✅ ALL COMPLETED |

**Reduction**: 81 → 41 tasks (50% reduction)

---

## Deferred Features (Post-MVP) - DETAILED

These features are deferred but documented for future implementation:

---

### Phase D1: US4 - Create Simulation from Experiment (Priority: P1)

**Goal**: User creates new simulation directly from experiment detail page, automatically linked.

**Spec Reference**: User Story 4 (spec.md lines 116-130)

**FR Requirements**:
- FR-009: feature_scorecards MUST have experiment_id column (FK, NOT NULL)
- FR-010: Scorecard creation from experiment page MUST auto-fill experiment_id
- FR-011: Experiment detail MUST list all scorecards/simulations with matching experiment_id
- FR-012: Simulation detail MUST have breadcrumb to return to parent experiment

**Acceptance Scenarios**:
1. Given experiment detail, When clicks "+ Nova Simulação", Then opens scorecard creation flow (feature 016)
2. Given creation flow, When completes scorecard and executes simulation, Then scorecard and simulation are created with experiment_id linked
3. Given simulation created, When returns to experiment detail, Then new simulation appears in "Simulações" section
4. Given simulation card, When user clicks, Then navigates to simulation detail (/experiments/:id/simulations/:simId)

**Implementation Tasks**:

- [x] T042 [US4] Add experiment_id column to feature_scorecards table in src/synth_lab/infrastructure/database.py
  - Column already exists in schema (nullable)
  - Schema initialization supports experiment_id
- [x] T043 [P] [US4] Update FeatureScorecard entity in src/synth_lab/domain/entities/feature_scorecard.py
  - Added experiment_id: str | None field
  - model_dump includes experiment_id
- [x] T044 [P] [US4] Update ScorecardRepository in src/synth_lab/repositories/scorecard_repository.py
  - Added experiment_id to create method
  - Added list_by_experiment_id method
- [x] T045 [US4] Create POST /experiments/{id}/scorecards endpoint in src/synth_lab/api/routers/experiments.py
  - Validate experiment exists
  - Create scorecard with experiment_id pre-filled
  - Return created scorecard
- [x] T046 [P] [US4] Create NewSimulationDialog component in frontend/src/components/experiments/NewSimulationDialog.tsx
  - Reuse existing scorecard form components
  - Pre-fill experiment_id from route param
  - On success: navigate to simulation or close and refresh
- [x] T047 [US4] Enable "+ Nova Simulação" button in frontend/src/pages/ExperimentDetail.tsx
  - Wire up NewSimulationDialog
  - On success: invalidate experiment query

**Test Tasks** (if TDD requested):
- [ ] T042-T [TEST] Unit tests for FeatureScorecard entity with experiment_id
- [ ] T044-T [TEST] Unit tests for ScorecardRepository.list_by_experiment_id
- [ ] T045-T [BDD] Integration tests for POST /experiments/{id}/scorecards

**Manual Validation**: Click "+ Nova Simulação" from experiment, complete flow, verify simulation appears in experiment detail

---

### Phase D2: US5 - Create Interview from Experiment (Priority: P1)

**Goal**: User creates new interview directly from experiment detail page, automatically linked.

**Spec Reference**: User Story 5 (spec.md lines 133-147)

**FR Requirements**:
- FR-013: research_executions MUST have experiment_id column (FK, NOT NULL)
- FR-014: Interview creation from experiment page MUST auto-fill experiment_id
- FR-015: Experiment detail MUST list all interviews with matching experiment_id
- FR-016: Interview detail MUST maintain existing behavior, only changing breadcrumb

**Acceptance Scenarios**:
1. Given experiment detail, When clicks "+ Nova Entrevista", Then opens dialog (similar to NewInterviewDialog)
2. Given creation dialog, When selects topic and configures parameters, Then interview is created with experiment_id linked
3. Given interview created, When returns to experiment detail, Then new interview appears in "Entrevistas" section
4. Given interview card, When user clicks, Then navigates to interview detail (/experiments/:id/interviews/:execId)

**Implementation Tasks**:

- [x] T048 [US5] Add experiment_id column to research_executions table in src/synth_lab/infrastructure/database.py
  - Column already exists in schema (nullable)
  - Schema initialization supports experiment_id
- [x] T049 [P] [US5] Update ResearchExecution entity in src/synth_lab/models/research.py
  - Added experiment_id: str | None field to ResearchExecuteRequest
  - Updated repository create_execution method
- [x] T050 [P] [US5] Update ResearchRepository in src/synth_lab/repositories/research_repository.py
  - Added list_executions_by_experiment method
  - Updated create_execution to accept experiment_id
- [x] T051 [US5] Create POST /experiments/{id}/interviews endpoint in src/synth_lab/api/routers/experiments.py
  - Validate experiment exists
  - Create research execution with experiment_id pre-filled
  - Trigger interview execution
  - Return created execution
- [x] T052 [P] [US5] Create NewInterviewFromExperimentDialog in frontend/src/components/experiments/NewInterviewFromExperimentDialog.tsx
  - Reuse TopicSelector and configuration components
  - Pre-fill experiment_id from route param
  - On success: navigate to interview or close and refresh
- [x] T053 [US5] Enable "+ Nova Entrevista" button in frontend/src/pages/ExperimentDetail.tsx
  - Wire up NewInterviewFromExperimentDialog
  - On success: invalidate experiment query

**Test Tasks** (if TDD requested):
- [ ] T048-T [TEST] Unit tests for ResearchExecution entity with experiment_id
- [ ] T050-T [TEST] Unit tests for ResearchRepository.list_by_experiment_id
- [ ] T051-T [BDD] Integration tests for POST /experiments/{id}/interviews

**Manual Validation**: Click "+ Nova Entrevista" from experiment, select topic, verify interview appears in experiment detail

---

### Phase D3: Synth Groups Integration (Priority: P2)

**Goal**: Auto-assign synth_group_id during synth generation.

**Spec Reference**: FR-017 to FR-022, FR-025 (spec.md lines 254-265)

**FR Requirements**:
- FR-017: synth_groups table MUST have: id (PK), name, description, created_at ✅ DONE
- FR-018: synths table MUST have synth_group_id column (FK, NOT NULL)
- FR-019: Synth generation MUST accept synth_group_id as optional parameter
- FR-020: If synth_group_id provided and group DOES NOT exist, system MUST create group automatically
- FR-021: If synth_group_id NOT provided, system MUST create new group with datetime-based name
- FR-022: Synth catalog MUST allow filtering by group
- FR-025: Synth catalog MUST display group info for each synth

**Acceptance Scenarios**:
1. Given synth generation, When synth_group_id provided and group exists, Then synths added to existing group
2. Given synth generation, When synth_group_id provided and group does NOT exist, Then group created with that id, synths added
3. Given synth generation, When synth_group_id NOT provided, Then new group auto-created with a proper random group_id
4. Given synth catalog, When user selects group filter, Then only synths from that group shown
5. Given synth catalog, When viewing list, Then each synth shows its group name/badge

**Implementation Tasks**:

- [x] T054 [US8] Add synth_group_id column to synths table in src/synth_lab/infrastructure/database.py
  - Column already exists in schema (nullable)
  - Schema initialization supports synth_group_id
- [x] T055 [P] [US8] Update Synth entity in src/synth_lab/models/synth.py
  - Added synth_group_id: str | None field to SynthBase model
- [x] T056 [P] [US8] Update SynthRepository in src/synth_lab/repositories/synth_repository.py
  - Added synth_group_id to _row_to_summary and _row_to_detail
  - Added list_by_group_id method
  - Added filter by synth_group_id to list_synths method
- [x] T057 [US8] Update synth storage in src/synth_lab/gen_synth/storage.py
  - Updated save_synth to accept synth_group_id parameter
  - Updated _row_to_dict to include synth_group_id
- [x] T058 [P] [US8] Synth generation endpoint update not needed
  - Synth generation is done via CLI, not API
- [x] T059 [P] [US8] Update GET /synths/list endpoint in src/synth_lab/api/routers/synths.py
  - Added optional synth_group_id query param for filtering
  - Updated SynthService.list_synths to support group filtering
- [x] T060 [US8] Update SynthList component in frontend/src/components/synths/SynthList.tsx
  - Added group filter dropdown with useSynthGroups hook
  - Display group name badge on each SynthCard
  - Clear filter button and active filter indicator

**Test Tasks** (if TDD requested):
- [ ] T054-T [TEST] Schema validation for synths.synth_group_id
- [ ] T056-T [TEST] Unit tests for SynthRepository with group filtering
- [ ] T057-T [TEST] Unit tests for synth generation with group assignment

**Manual Validation**:
- Generate synths without group_id, verify auto-group created
- Generate synths with existing group_id, verify added to that group
- Generate synths with new group_id, verify group created
- Filter synth catalog by group

---

### Phase D4: Backward Compatibility & Polish (Priority: P3)

**Goal**: Ensure backward compatibility and handle edge cases.

**Implementation Tasks**:

- [x] T061 [P] Add redirect from /interviews/:id to appropriate /experiments/:expId/interviews/:id
  - Added experiment_id to ResearchExecutionBase model
  - Updated ResearchRepository to return experiment_id
  - Added auto-redirect in InterviewDetail.tsx when accessed via legacy URL
- [SKIP] T062 [P] Handle orphaned simulations/interviews (created before experiment_id was required)
  - Postponed - orphaned records will be removed manually
- [SKIP] T063 [P] Add experiment_id to existing simulation/interview list views
  - Postponed - orphaned records will be removed manually
- [SKIP] T064 Add delete experiment confirmation dialog in frontend/src/pages/ExperimentDetail.tsx
  - Postponed for future iteration

**Edge Cases from Spec**:
- User accesses URL of non-existent experiment → Show 404 with link to home ✅ DONE
- User tries to delete experiment with running simulation/interview → Block or require extra confirmation
- User creates experiment with duplicate name → Allow (names not unique per spec)

---

## Deferred Tasks Summary

| Phase | User Story | Tasks | Priority | Dependencies |
|-------|-----------|-------|----------|--------------|
| D1 | US4 - Create Simulation | T042-T047 (6 tasks) | P1 | None (MVP complete) |
| D2 | US5 - Create Interview | T048-T053 (6 tasks) | P1 | None (MVP complete) |
| D3 | US8 - Synth Groups | T054-T060 (7 tasks) | P2 | None (schema ready) |
| D4 | Backward Compat | T061-T064 (4 tasks) | P3 | D1, D2 |
| **Total** | | **23 tasks** | | |

**Recommended Implementation Order**:
1. **D1 + D2 in parallel** - Both are P1 and independent
2. **D3** - Synth groups after core flows work
3. **D4** - Backward compatibility polish last

---

## Notes

- **TDD Maintained**: All backend features have tests written first
- **Frontend Pattern**: No automated tests (project standard), manual BDD validation
- **Commit Strategy**: Commit after each task or logical group
- **MVP First**: Phases 4-8 deliver full MVP functionality
- **Quick Wins**: US9 (Edit) is a quick win with minimal effort
- **Deferred Work**: Phases D1-D4 can be added later without breaking MVP
