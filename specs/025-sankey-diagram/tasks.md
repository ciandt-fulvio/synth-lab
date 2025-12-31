# Tasks: Sankey Diagram for Outcome Flow Visualization

**Input**: Design documents from `/specs/025-sankey-diagram/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/sankey-flow.yaml

**Tests**: TDD approach per constitution - tests written before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `src/synth_lab/` (Python)
- **Frontend**: `frontend/src/` (TypeScript/React)
- **Tests Backend**: `tests/`
- **Tests Frontend**: `frontend/src/` (colocated)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add dependencies, shared types and query keys for Sankey feature

- [x] T001 Install D3-Sankey dependencies: `npm install d3-sankey d3-shape @types/d3-sankey @types/d3-shape` in `frontend/`
- [x] T002 [P] Add `sankeyFlow` key to query keys in `frontend/src/lib/query-keys.ts`
- [x] T003 [P] Add `SankeyFlowChart` TypeScript type in `frontend/src/types/simulation.ts`

---

## Phase 2: Foundational (Backend Core)

**Purpose**: Backend entities and gap calculation logic

- [x] T004 Add `SankeyNode`, `SankeyLink`, `OutcomeCounts`, `SankeyFlowChart` entities in `src/synth_lab/domain/entities/chart_data.py`
- [x] T005 Implement `diagnose_did_not_try` gap calculation function in `src/synth_lab/services/simulation/chart_data_service.py`
- [x] T006 Implement `diagnose_failed` gap calculation function in `src/synth_lab/services/simulation/chart_data_service.py`
- [x] T007 Implement `get_dominant_outcome` function in `src/synth_lab/services/simulation/chart_data_service.py`

---

## Phase 3: User Story 1 - View Outcome Distribution Flow

**Goal**: Display Sankey diagram showing Population → Outcomes with correct counts

### Tests for User Story 1

- [x] T008 [P] [US1] Unit test for `get_dominant_outcome` function in `tests/unit/services/test_sankey_flow.py`
- [x] T009 [P] [US1] Unit test for outcome aggregation in `tests/unit/services/test_sankey_flow.py`

### Implementation for User Story 1

- [x] T010 [US1] Implement `get_sankey_flow` service method (Level 1→2 flows only) in `src/synth_lab/services/simulation/chart_data_service.py`
- [x] T011 [US1] Add `GET /experiments/{experiment_id}/analysis/charts/sankey-flow` endpoint in `src/synth_lab/api/routers/analysis.py`
- [x] T012 [P] [US1] Add `getAnalysisSankeyFlow` API function in `frontend/src/services/experiments-api.ts`
- [x] T013 [P] [US1] Add `useAnalysisSankeyFlow` hook in `frontend/src/hooks/use-analysis-charts.ts`
- [x] T014 [US1] Create `SankeyFlowChart.tsx` component using D3-Sankey (basic 2-level rendering) in `frontend/src/components/experiments/results/charts/SankeyFlowChart.tsx`
- [x] T015 [US1] Create `SankeyFlowSection.tsx` wrapper with loading/error states in `frontend/src/components/experiments/results/SankeyFlowSection.tsx`
- [x] T016 [US1] Integrate `SankeyFlowSection` into `PhaseOverview.tsx` above TryVsSuccessSection in `frontend/src/components/experiments/results/PhaseOverview.tsx`

---

## Phase 4: User Story 2 - Root Causes for Non-Adoption

**Goal**: Show "did_not_try" → root causes (Esforço inicial alto, Risco percebido, Complexidade aparente)

### Tests for User Story 2

- [x] T017 [P] [US2] Unit test for `diagnose_did_not_try` with motivation gap in `tests/unit/services/test_sankey_flow.py`
- [x] T018 [P] [US2] Unit test for `diagnose_did_not_try` with trust gap in `tests/unit/services/test_sankey_flow.py`
- [x] T019 [P] [US2] Unit test for `diagnose_did_not_try` with friction gap in `tests/unit/services/test_sankey_flow.py`
- [x] T020 [P] [US2] Unit test for `diagnose_did_not_try` tie-breaking priority in `tests/unit/services/test_sankey_flow.py`

### Implementation for User Story 2

- [x] T021 [US2] Extend `get_sankey_flow` to include did_not_try → root cause flows in `src/synth_lab/services/simulation/chart_data_service.py`
- [x] T022 [US2] Add Level 3 nodes for did_not_try causes (effort_barrier, risk_barrier, complexity_barrier) in `src/synth_lab/services/simulation/chart_data_service.py`
- [x] T023 [US2] Update `SankeyFlowChart.tsx` to render 3-level flows in `frontend/src/components/experiments/results/charts/SankeyFlowChart.tsx`

---

## Phase 5: User Story 3 - Root Causes for Failure

**Goal**: Show "failed" → root causes (Capability insuficiente, Desistiu antes do valor)

### Tests for User Story 3

- [x] T024 [P] [US3] Unit test for `diagnose_failed` with capability gap in `tests/unit/services/test_sankey_flow.py`
- [x] T025 [P] [US3] Unit test for `diagnose_failed` with patience gap in `tests/unit/services/test_sankey_flow.py`
- [x] T026 [P] [US3] Unit test for `diagnose_failed` tie-breaking priority in `tests/unit/services/test_sankey_flow.py`

### Implementation for User Story 3

- [x] T027 [US3] Extend `get_sankey_flow` to include failed → root cause flows in `src/synth_lab/services/simulation/chart_data_service.py`
- [x] T028 [US3] Add Level 3 nodes for failed causes (capability_barrier, patience_barrier) in `src/synth_lab/services/simulation/chart_data_service.py`

---

## Phase 6: User Story 4 - View Success Distribution

**Goal**: Success category displays as terminal node (no Level 3 breakdown)

### Tests for User Story 4

- [x] T029 [P] [US4] Unit test verifying success has no root cause in `tests/unit/services/test_sankey_flow.py`

### Implementation for User Story 4

- [x] T030 [US4] Ensure success node is correctly marked as terminal (no outgoing links) in `src/synth_lab/services/simulation/chart_data_service.py`
- [x] T031 [US4] Verify `SankeyFlowChart.tsx` renders success as terminal node in `frontend/src/components/experiments/results/charts/SankeyFlowChart.tsx`

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, performance, and documentation

- [x] T032 [P] Integration test for endpoint with completed analysis in `tests/integration/test_analysis_sankey.py`
- [x] T033 [P] Integration test for endpoint with incomplete analysis (400 error) in `tests/integration/test_analysis_sankey.py`
- [x] T034 Handle edge case: zero synths in an outcome category (omit empty flows) in `src/synth_lab/services/simulation/chart_data_service.py`
- [x] T035 Handle edge case: all synths same outcome in `src/synth_lab/services/simulation/chart_data_service.py`
- [x] T036 Add tooltip with synth count to flow links in `frontend/src/components/experiments/results/charts/SankeyFlowChart.tsx`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (P1): Can start after Foundational
  - US2 (P2): Can start after US1 (extends get_sankey_flow)
  - US3 (P3): Can start after US2 (extends get_sankey_flow)
  - US4 (P4): Can start after US1 (minimal changes)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: After Foundational - Creates base Sankey with Level 1→2
- **User Story 2 (P2)**: After US1 - Adds did_not_try → root causes (extends same service method)
- **User Story 3 (P3)**: After US2 - Adds failed → root causes (extends same service method)
- **User Story 4 (P4)**: After US1 - Verifies success terminal behavior (independent of US2/US3)

### Within Each User Story

1. Tests MUST be written and FAIL before implementation
2. Backend entities/service before API endpoint
3. API endpoint before frontend integration
4. Frontend types/services before components

### Parallel Opportunities

**Phase 1** (all parallel):
- T001 + T002 can run together

**Phase 2** (sequential within, parallel T004+T005):
- T003 first (entities)
- T004 + T005 can run together (different functions)
- T006 after T003

**Phase 3 - US1**:
- T007 + T008 can run together (tests)
- T011 + T012 can run together (frontend types/hooks)
- T013 depends on T011, T012

**Phase 4 - US2**:
- T016 + T017 + T018 + T019 can all run together (tests)

**Phase 5 - US3**:
- T023 + T024 + T025 can all run together (tests)

**Phase 7 - Polish**:
- T031 + T032 can run together (integration tests)
- T033 + T034 can run together (edge cases)

---

## Parallel Example: User Story 1

```bash
# Launch tests together (Phase 3):
Task: "Unit test for get_dominant_outcome function"
Task: "Unit test for outcome aggregation"

# Launch frontend infrastructure together:
Task: "Add getAnalysisSankeyFlow API function"
Task: "Add useAnalysisSankeyFlow hook"
```

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Backend uses existing patterns from chart_data_service.py
- Frontend uses D3-Sankey for professional Sankey rendering with custom React component
- Execute all phases sequentially without pauses
