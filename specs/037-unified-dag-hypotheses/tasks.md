# Tasks: Unified DAG & Hypothesis Generation

**Input**: Design documents from `/specs/037-unified-dag-hypotheses/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included (TDD required by constitution)

**Organization**: Tasks grouped by user story — US1 (Unified Generation), US2 (Relevance Visualization), US3 (Drawer Editing)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3)
- Exact file paths included

---

## Phase 1: Setup

**Purpose**: Database migration and domain entity changes shared by all stories

- [x] T001 Create Alembic migration to add `relevance VARCHAR(10) NOT NULL DEFAULT 'medium'` column to `hypotheses` table in alembic/versions/
- [x] T002 Add `Relevance` enum (LOW, MEDIUM, HIGH) to `src/synth_lab/domain/entities/hypothesis.py`
- [x] T003 Add `relevance: Relevance` field to `Hypothesis` dataclass in `src/synth_lab/domain/entities/hypothesis.py` (default: Relevance.MEDIUM)
- [x] T004 Add `relevance` column to Hypothesis ORM model in `src/synth_lab/models/orm/simulation.py`
- [x] T005 Update `HypothesisRepository._orm_to_entity()` to map `relevance` column in `src/synth_lab/repositories/hypothesis_repository.py`
- [x] T006 Update `HypothesisRepository.create_batch()` and `update()` to persist `relevance` field in `src/synth_lab/repositories/hypothesis_repository.py`
- [x] T007 Add `relevance` field to `HypothesisSchema` and `HypothesisResponse` in `src/synth_lab/api/schemas/hypothesis.py`
- [x] T008 [P] Add `relevance` field to `Hypothesis` TypeScript type in `frontend/src/types/hypothesis.ts`
- [x] T009 Run migration against dev database and verify existing rows get `'medium'` default

**Checkpoint**: Schema updated, relevance flows from DB → entity → API → frontend type. All existing tests still pass.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Hypothesis range clamping in simulation engine — required for US1 generation to produce useful range values

**⚠️ CRITICAL**: Range clamping must work before unified generation outputs range data

### Tests

- [x] T010 Write unit tests for range clamping in `tests/unit/services/test_distribution_sampler.py`: test np.clip with both bounds, only min, only max, null bounds (no clamp), edge case min==max
- [x] T011 Write unit test for range validation (min > max rejection) in `tests/unit/services/test_distribution_sampler.py`

### Implementation

- [x] T012 Add `np.clip()` range clamping to `DistributionSampler.sample()` in `src/synth_lab/services/simulation/distribution_sampler.py` — apply after sampling, using `hypothesis.range_min` and `hypothesis.range_max`
- [x] T013 Verify T010 and T011 tests pass

**Checkpoint**: Range clamping works. Existing distribution sampling unchanged when range is null.

---

## Phase 3: User Story 1 — Unified DAG + Hypotheses Generation (Priority: P1) 🎯 MVP

**Goal**: Single `gpt-4o-mini` call generates DAG structure AND distribution hypotheses (with relevance and range) simultaneously, replacing two separate `gpt-4o` calls.

**Independent Test**: Create a simulation → confirm question → system returns DAG nodes, edges, AND hypotheses with relevance/range in one response → all variables have distributions assigned.

### Tests for US1

- [x] T014 Write unit test for `UnifiedDAGResponse` Pydantic schema parsing (valid response with hypotheses) in `tests/unit/services/test_dag_constructor_service.py`
- [x] T015 Write unit test for fallback when LLM response is missing hypotheses for some variables (defaults to uniform, medium, no range) in `tests/unit/services/test_dag_constructor_service.py`
- [x] T016 Write unit test for `_convert_llm_hypotheses_to_entities()` mapping LLMHypothesis → Hypothesis domain entity in `tests/unit/services/test_dag_constructor_service.py`
- [ ] T017 Write integration test for `POST /{simulation_id}/confirm-question` returning hypotheses alongside DAG in `tests/integration/api/test_simulations_api.py`

### Implementation for US1

- [x] T018 [US1] Add `LLMHypothesis` and `UnifiedDAGResponse` Pydantic models to `src/synth_lab/services/simulation/dag_constructor_service.py` (extend existing DAGResponse with hypotheses field)
- [x] T019 [US1] Build unified prompt that combines DAG structure instructions AND hypothesis parametrization instructions (reuse few-shot examples from `hypothesis_parametrizer_service.py`) in `src/synth_lab/services/simulation/dag_constructor_service.py`
- [x] T020 [US1] Switch model from `gpt-4o` to `gpt-4o-mini` in `DAGConstructorService` (`DAG_MODEL` constant) in `src/synth_lab/services/simulation/dag_constructor_service.py`
- [x] T021 [US1] Implement `_convert_llm_hypotheses_to_entities()` method in `src/synth_lab/services/simulation/dag_constructor_service.py` — maps LLMHypothesis list to Hypothesis domain entities with relevance and range
- [x] T022 [US1] Implement fallback logic: for any DAG variable missing a hypothesis in LLM response, create default (uniform, medium relevance, no range) with warning log in `src/synth_lab/services/simulation/dag_constructor_service.py`
- [x] T023 [US1] Update `DAGConstructorService.generate()` to call `complete_structured()` with `UnifiedDAGResponse` and return both `CausalDAG` and `list[Hypothesis]` in `src/synth_lab/services/simulation/dag_constructor_service.py`
- [x] T024 [US1] Update `confirm-question` router endpoint to persist hypotheses (via `HypothesisRepository.create_batch()`) after DAG generation in `src/synth_lab/api/routers/simulations.py`
- [x] T025 [US1] Verify T014–T017 tests pass
- [x] T026 [US1] Ensure existing DAG validation tests still pass (no regression)

**Checkpoint**: `POST /confirm-question` generates DAG + hypotheses in one call. All variables have distributions, relevance, and optional ranges.

---

## Phase 4: User Story 2 — Relevance-Driven Node Visualization (Priority: P2)

**Goal**: DAG nodes display color saturation proportional to their relevance level — high = full color, medium = 70%, low = 40%.

**Independent Test**: View a DAG with mixed relevance levels → visually confirm saturation differs per relevance level. All high-relevance = backward compatible (full saturation).

### Tests for US2

- [ ] T027 [P] [US2] Write unit test for `getNodeColor(scope, relevance)` HSL computation: verify high=100% sat, medium=70%, low=40% for both user and world scopes — test file TBD (Vitest or inline in component file)

### Implementation for US2

- [x] T028 [P] [US2] Implement `getNodeColor(scope: string, relevance: string)` utility function returning HSL string in `frontend/src/components/simulation/DAGNodeCard.tsx` — base colors: user=HSL(263,84%,58%), world=HSL(189,95%,42%); multiply saturation by {high:1.0, medium:0.7, low:0.4}
- [x] T029 [US2] Modify `DAGNodeCard` to accept `relevance` prop (from hypothesis data) and use `getNodeColor()` for node border/background colors in `frontend/src/components/simulation/DAGNodeCard.tsx`
- [x] T030 [US2] Pass hypothesis relevance data to `DAGNodeCard` via `DAGVisualization.tsx` — map each node to its hypothesis relevance when building ReactFlow node data in `frontend/src/components/simulation/DAGVisualization.tsx`
- [ ] T031 [US2] Verify T027 test passes and visually confirm saturation differences in browser

**Checkpoint**: DAG nodes visually show relevance. High = current look, medium = slightly faded, low = noticeably faded.

---

## Phase 5: User Story 3 — Drawer-Based Node Editing (Priority: P3)

**Goal**: Click a DAG node → right-side Sheet opens with variable name, description, relevance selector, range editor. User edits are saved via PATCH API. Tooltips removed.

**Independent Test**: Click any node → sheet opens → edit relevance and range → save → sheet closes → node color updates.

### Tests for US3

- [ ] T032 [P] [US3] Write unit test for PATCH `/simulations/{id}/hypotheses/{hyp_id}` endpoint: test relevance update, range update, range validation (min > max → 422) in `tests/integration/api/test_hypotheses_api.py`
- [ ] T033 [P] [US3] Write unit test for range validation: reject min > max with 422 in `tests/integration/api/test_hypotheses_api.py`

### Backend Implementation for US3

- [x] T034 [US3] Add `HypothesisUpdateRequest` schema (optional relevance, optional range_min, optional range_max) in `src/synth_lab/api/schemas/hypothesis.py`
- [x] T035 [US3] Add PATCH endpoint `/{simulation_id}/hypotheses/{hypothesis_id}` to `src/synth_lab/api/routers/hypotheses.py` — validates range_min ≤ range_max, delegates to repository update
- [x] T036 [US3] Ensure `HypothesisRepository.update()` handles partial updates (only update provided fields) in `src/synth_lab/repositories/hypothesis_repository.py`
- [ ] T037 [US3] Verify T032–T033 tests pass

### Frontend Implementation for US3

- [x] T038 [P] [US3] Add `updateHypothesis(simulationId, hypothesisId, data)` API function to `frontend/src/services/simulations-api.ts` — PATCH request
- [x] T039 [P] [US3] Add `useUpdateHypothesis` mutation hook in `frontend/src/hooks/use-simulations.ts` — invalidates simulation query on success
- [x] T040 [US3] Create `NodeDetailSheet` component in `frontend/src/components/simulation/NodeDetailSheet.tsx` — Sheet with side="right", displays variable name (read-only), description (read-only), relevance selector (radio group: low/medium/high), range inputs (min/max numeric), save button. Does NOT show distribution type/params (FR-007).
- [x] T041 [US3] Add range validation in `NodeDetailSheet`: inline error when min > max (FR-010), empty fields = null (no clamp) in `frontend/src/components/simulation/NodeDetailSheet.tsx`
- [x] T042 [US3] Remove hover tooltip logic from `DAGNodeCard` — remove `onMouseEnter`/`onMouseLeave` handlers and tooltip portal rendering in `frontend/src/components/simulation/DAGNodeCard.tsx`
- [x] T043 [US3] Add `onClick` handler to `DAGNodeCard` that calls `onEditNode(variable)` prop in `frontend/src/components/simulation/DAGNodeCard.tsx`
- [x] T044 [US3] Wire `NodeDetailSheet` into `DAGValidationStep.tsx` — manage `selectedVariable` state, open sheet on node click, close on outside click or close button, update sheet content when different node clicked (FR-013)
- [x] T045 [US3] Connect `NodeDetailSheet` save to `useUpdateHypothesis` mutation — on save, PATCH hypothesis, close sheet, node saturation updates via query invalidation
- [x] T046 [US3] Handle responsive layout: sheet takes full width on screens < 768px (`className="w-full sm:w-[400px]"`) in `frontend/src/components/simulation/NodeDetailSheet.tsx`

**Checkpoint**: Click node → sheet opens → edit relevance/range → save → node updates. Tooltips removed. PATCH API validates ranges.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, cleanup, and documentation

- [ ] T047 Run `ruff check . && ruff format .` on all modified Python files
- [ ] T048 Run `npm run lint` in frontend/ on all modified TypeScript files
- [ ] T049 Run full backend test suite (`pytest tests/`) and verify zero regressions
- [ ] T050 Run TypeScript compilation check (`npm run build` in frontend/) and verify zero errors
- [ ] T051 [P] Verify backward compatibility: existing simulations with no relevance field display correctly (default medium = 70% saturation)
- [ ] T052 [P] Verify wizard flow from feature 036 still works after unified generation changes
- [ ] T053 Manual smoke test: create simulation → confirm question → verify DAG + hypotheses generated → click node → edit relevance/range → save → verify visual update → run simulation → verify clamping applied
- [ ] T054 Git commit all changes with descriptive message

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 (needs `range_min`/`range_max` on entity)
- **Phase 3 (US1)**: Depends on Phase 1 + Phase 2 (needs relevance field + clamping)
- **Phase 4 (US2)**: Depends on Phase 1 (needs relevance on Hypothesis type) + Phase 3 (needs hypotheses generated)
- **Phase 5 (US3)**: Depends on Phase 1 (needs relevance/range on type) + Phase 3 (needs hypotheses) + Phase 4 (needs saturation for visual feedback)
- **Phase 6 (Polish)**: Depends on all previous phases

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2. Core architectural change — all stories depend on this.
- **US2 (P2)**: Depends on US1 (needs hypothesis data with relevance to visualize). Frontend-only.
- **US3 (P3)**: Depends on US1 (needs hypotheses to edit) and US2 (needs saturation for visual feedback on save). Backend PATCH endpoint + frontend sheet.

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD)
- Backend before frontend (API must exist before UI consumes it)
- Core implementation before integration

### Parallel Opportunities

- T008 (frontend type) can run in parallel with T002-T007 (backend entity/ORM/schema)
- T010-T011 (clamping tests) can run in parallel
- T027 (saturation test), T032-T033 (PATCH tests), T038-T039 (frontend API/hook) can run in parallel
- T042-T043 (tooltip removal + click handler) can run in parallel with T040-T041 (sheet component)

---

## Parallel Example: Phase 1 Setup

```bash
# Backend entity changes (sequential — same file):
T002 → T003 → T004 → T005 → T006 → T007

# Frontend type change (parallel with backend):
T008  # Can run simultaneously with T002-T007
```

## Parallel Example: US3 Implementation

```bash
# Backend PATCH endpoint (sequential):
T034 → T035 → T036 → T037

# Frontend API + hook (parallel with backend):
T038 + T039  # Different files, no backend dependency for code writing

# Frontend components (after API/hook ready):
T040 + T041  # Sheet component
T042 + T043  # Tooltip removal + click handler (parallel with sheet)
T044 → T045  # Wire together (sequential, depends on above)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (migration + entity changes)
2. Complete Phase 2: Foundational (range clamping)
3. Complete Phase 3: User Story 1 (unified generation)
4. **STOP and VALIDATE**: Confirm DAG + hypotheses generated in single call
5. Deploy/demo — system works end-to-end with unified generation

### Incremental Delivery

1. Setup + Foundational → Schema and clamping ready
2. US1 → Unified generation works → Deploy (MVP!)
3. US2 → Nodes show relevance saturation → Deploy
4. US3 → Drawer editing replaces tooltips → Deploy
5. Polish → Cleanup and final validation

---

## Notes

- Constitution requires TDD — all tests included
- `range_min`/`range_max` columns already exist in ORM but unused — no migration needed for those
- `relevance` column needs migration with default `'medium'` — backward compatible
- Sheet component (not Drawer) used for right-side panel — see research.md Decision 4
- HSL saturation mapping — see research.md Decision 5
- Fallback defaults for missing hypotheses — see research.md Decision 6
