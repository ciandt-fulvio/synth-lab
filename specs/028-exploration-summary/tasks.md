# Tasks: Exploration Summary and PRFAQ Generation

**Input**: Design documents from `/specs/028-exploration-summary/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL - the spec mentions TDD but does not explicitly require test tasks in the task list.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Key Pattern**: Reutiliza `experiment_documents` existente - NÃO cria tabela/entity/migration nova.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `src/synth_lab/`
- **Frontend**: `frontend/src/`
- **Tests**: `tests/synth_lab/` and `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing infrastructure and prepare for implementation

- [x] T001 Verify `ExperimentDocument` entity exists with required fields in `src/synth_lab/domain/entities/experiment_document.py`
- [x] T002 Verify `DocumentType` enum includes SUMMARY and PRFAQ in `src/synth_lab/domain/entities/experiment_document.py`
- [x] T003 Verify `DocumentStatus` enum includes GENERATING, COMPLETED, FAILED in `src/synth_lab/domain/entities/experiment_document.py`
- [x] T004 Verify `ExperimentDocumentRepository` exists with create/get/update methods in `src/synth_lab/repositories/experiment_document_repository.py`
- [x] T005 Verify `experiment_documents` table exists with metadata JSONB column (no migration needed)

**Checkpoint**: All existing infrastructure verified - can proceed with new services

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Implement `_get_winning_path()` helper method for finding best leaf node in `src/synth_lab/services/exploration_summary_generator_service.py`
  - Tiebreaker: success_rate DESC → depth ASC → created_at ASC
  - Returns list of ScenarioNode from root to best leaf
- [x] T007 Implement `_build_summary_prompt()` helper method for LLM prompt construction in `src/synth_lab/services/exploration_summary_generator_service.py`
  - Include: scenario description, actions, rationales, final scorecard
  - Output: Non-sequential narrative format (Portuguese)
- [x] T008 [P] Add exploration document query keys in `frontend/src/lib/query-keys.ts`
  - Add `summary(explorationId)` and `prfaq(explorationId)` keys

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View Generated Summary After Exploration Completes (Priority: P1) 🎯 MVP

**Goal**: Researcher can view auto-generated narrative summary describing the winning path after exploration completes

**Independent Test**: Run an exploration to completion → verify summary is generated with winning path narrative

### Backend Implementation for US1

- [x] T009 [US1] Create `ExplorationSummaryGeneratorService` class in `src/synth_lab/services/exploration_summary_generator_service.py`
  - Constructor: ExplorationRepository, ScenarioNodeRepository, ExperimentDocumentRepository, LLMClient
  - Method: `generate_for_exploration(exploration_id: str) -> ExperimentDocument`
  - Validate exploration status (GOAL_ACHIEVED, DEPTH_LIMIT_REACHED, COST_LIMIT_REACHED)
  - Check for existing GENERATING status (return 409)
  - Use `_get_winning_path()` and `_build_summary_prompt()`
  - Save to `experiment_documents` with metadata `source: "exploration"`

- [x] T010 [US1] Add Phoenix tracing to LLM call in `src/synth_lab/services/exploration_summary_generator_service.py`
  - Wrap LLM call with `_tracer.start_as_current_span("generate_exploration_summary")`
  - Set attributes: exploration_id, path_length, generation_time

- [x] T011 [US1] Add dependency injection for `ExplorationSummaryGeneratorService` in `src/synth_lab/api/dependencies.py`
  - Note: Using helper function in router instead of FastAPI dependency

- [x] T012 [US1] Add POST `/explorations/{exploration_id}/documents/summary/generate` endpoint in `src/synth_lab/api/routers/exploration.py`
  - Return `ExperimentDocumentResponse` (existing schema)
  - Handle 404 (exploration not found), 409 (already generating), 422 (not completed)

- [x] T013 [US1] Add GET `/explorations/{exploration_id}/documents/summary` endpoint in `src/synth_lab/api/routers/exploration.py`
  - Fetch via `exploration.experiment_id` from `ExperimentDocumentRepository`
  - Verify metadata `source=exploration`
  - Return 404 if not found

- [x] T014 [US1] Add DELETE `/explorations/{exploration_id}/documents/summary` endpoint in `src/synth_lab/api/routers/exploration.py`

### Frontend Implementation for US1

- [x] T015 [P] [US1] Add `generateExplorationSummary()` function in `frontend/src/services/exploration-api.ts`
  - POST to `/explorations/{id}/documents/summary/generate`
  - Return `ExperimentDocumentResponse` type

- [x] T016 [P] [US1] Add `getExplorationSummary()` function in `frontend/src/services/exploration-api.ts`
  - GET from `/explorations/{id}/documents/summary`

- [x] T017 [P] [US1] Add `deleteExplorationSummary()` function in `frontend/src/services/exploration-api.ts`

- [x] T018 [US1] Create `useGenerateExplorationSummary` hook in `frontend/src/hooks/use-exploration.ts`
  - TanStack Query mutation
  - Invalidate summary query on success

- [x] T019 [US1] Create `useExplorationSummary` hook in `frontend/src/hooks/use-exploration.ts`
  - TanStack Query with retry=false (404 expected for new explorations)

- [x] T020 [P] [US1] Create `ExplorationDocumentCard` component in `frontend/src/components/exploration/ExplorationDocumentCard.tsx`
  - Props: documentType, document, isLoading, isGenerating, canGenerate, onGenerate
  - Show spinner when generating
  - Note: Combined summary and PRFAQ cards into single component

- [x] T021 [US1] Create `ExplorationDocumentCard` component in `frontend/src/components/exploration/ExplorationDocumentCard.tsx`
  - Props: documentType, document, isLoading, isGenerating, canGenerate, onGenerate
  - States: loading, empty, generating, completed, failed
  - Uses DocumentViewer for content

- [x] T022 [US1] Integrate Summary components into `frontend/src/pages/ExplorationDetail.tsx`
  - Add Summary section below exploration tree
  - Enable button only when exploration status is completed (GOAL_ACHIEVED, DEPTH_LIMIT_REACHED, COST_LIMIT_REACHED)
  - Disable button when RUNNING or NO_VIABLE_PATHS

**Checkpoint**: User Story 1 complete - can view generated summary after exploration completes

---

## Phase 4: User Story 2 - View Generated PRFAQ After Exploration Completes (Priority: P2)

**Goal**: Researcher can generate and view a structured PRFAQ document formalizing recommendations

**Independent Test**: Trigger PRFAQ generation on completed exploration → verify output follows Press Release + FAQ + Recommendations format

### Backend Implementation for US2

- [x] T023 [US2] Implement `_build_prfaq_prompt()` helper method in `src/synth_lab/services/exploration_prfaq_generator_service.py`
  - PRFAQ format: Press Release + FAQ (5 questions) + Recommendations
  - Portuguese, professional tone

- [x] T024 [US2] Create `ExplorationPRFAQGeneratorService` class in `src/synth_lab/services/exploration_prfaq_generator_service.py`
  - Same pattern as Summary service
  - Use `document_type=DocumentType.PRFAQ`
  - Include Phoenix tracing

- [x] T025 [US2] Add dependency injection for `ExplorationPRFAQGeneratorService` in `src/synth_lab/api/dependencies.py`
  - Note: Using helper function in router instead of FastAPI dependency

- [x] T026 [US2] Add POST `/explorations/{exploration_id}/documents/prfaq/generate` endpoint in `src/synth_lab/api/routers/exploration.py`

- [x] T027 [US2] Add GET `/explorations/{exploration_id}/documents/prfaq` endpoint in `src/synth_lab/api/routers/exploration.py`

- [x] T028 [US2] Add DELETE `/explorations/{exploration_id}/documents/prfaq` endpoint in `src/synth_lab/api/routers/exploration.py`

### Frontend Implementation for US2

- [x] T029 [P] [US2] Add `generateExplorationPRFAQ()` function in `frontend/src/services/exploration-api.ts`

- [x] T030 [P] [US2] Add `getExplorationPRFAQ()` function in `frontend/src/services/exploration-api.ts`

- [x] T031 [P] [US2] Add `deleteExplorationPRFAQ()` function in `frontend/src/services/exploration-api.ts`

- [x] T032 [US2] Create `useGenerateExplorationPRFAQ` hook in `frontend/src/hooks/use-exploration.ts`

- [x] T033 [US2] Create `useExplorationPRFAQ` hook in `frontend/src/hooks/use-exploration.ts`

- [x] T034 [US2] Create `ExplorationDocumentCard` component in `frontend/src/components/exploration/ExplorationDocumentCard.tsx`
  - Same pattern as SummaryCard
  - Display PRFAQ sections with proper formatting
  - Note: Combined summary and PRFAQ cards into single component

- [x] T035 [US2] Integrate PRFAQ components into `frontend/src/pages/ExplorationDetail.tsx`
  - Add PRFAQ section below Summary
  - Same enable/disable logic as Summary button

**Checkpoint**: User Stories 1 AND 2 complete - can view both Summary and PRFAQ

---

## Phase 5: User Story 3 - Manual Summary Regeneration (Priority: P3)

**Goal**: Researcher can regenerate summary/PRFAQ to get updated content or recover from failures

**Independent Test**: Click generate button multiple times → verify each generates new document overwriting previous

### Implementation for US3

- [x] T036 [US3] Add regeneration logic to `ExplorationSummaryGeneratorService.generate_for_exploration()` in `src/synth_lab/services/exploration_summary_generator_service.py`
  - If document exists with status=completed, delete and recreate
  - If status=failed, allow retry
  - Note: Uses create_pending() which handles upsert

- [x] T037 [US3] Add regeneration logic to `ExplorationPRFAQGeneratorService.generate_for_exploration()` in `src/synth_lab/services/exploration_prfaq_generator_service.py`

- [x] T038 [US3] Add "Regenerar" button to `ExplorationDocumentCard` in `frontend/src/components/exploration/ExplorationDocumentCard.tsx`
  - Only show when document exists with status=completed or status=failed

- [x] T039 [US3] Add "Regenerar" button to `ExplorationDocumentCard` in `frontend/src/components/exploration/ExplorationDocumentCard.tsx`
  - Note: Combined into single ExplorationDocumentCard component

- [x] T040 [US3] Add "Tentar Novamente" button for failed state in ExplorationDocumentCard
  - Show when status=failed with error message
  - Note: Uses same button with different label when document exists

**Checkpoint**: All user stories complete - full regeneration support

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T041 [P] Add error handling for LLM timeout in both generator services
  - Uses LLMClient default timeout configuration
  - Store error_message on failure via update_status()

- [x] T042 [P] Add loading states for button disabled conditions in `frontend/src/pages/ExplorationDetail.tsx`
  - Show disabled state when exploration not completed
  - Note: Implemented with canGenerate prop in ExplorationDocumentCard

- [x] T043 [P] Verify button enable/disable logic handles all exploration statuses
  - RUNNING → disabled
  - GOAL_ACHIEVED → enabled
  - DEPTH_LIMIT_REACHED → enabled
  - COST_LIMIT_REACHED → enabled
  - NO_VIABLE_PATHS → disabled (canGenerateDocuments = false)

- [ ] T044 Run manual testing checklist from quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - verify existing infrastructure
- **Foundational (Phase 2)**: Depends on Setup - creates shared helper methods
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can proceed in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Shares pattern with US1 but independent
- **User Story 3 (P3)**: Depends on US1 and US2 being implemented (extends their functionality)

### Within Each User Story

- Backend service before endpoints
- Endpoints before frontend hooks
- Hooks before components
- Components before page integration

### Parallel Opportunities

**Phase 2 (Foundational)**:
```
T006, T007, T008 can run in parallel (different files)
```

**Phase 3 (US1) - Backend parallel**:
```
T015, T016, T017 (frontend services) can run in parallel
T020 (GenerateDocumentButton) can run in parallel with hooks
```

**Phase 4 (US2) - Frontend parallel**:
```
T029, T030, T031 (frontend services) can run in parallel
```

---

## Parallel Example: User Story 1

```bash
# After T014 (backend endpoints complete), launch frontend in parallel:
Task: "Add generateExplorationSummary() in frontend/src/services/exploration.ts"
Task: "Add getExplorationSummary() in frontend/src/services/exploration.ts"
Task: "Add deleteExplorationSummary() in frontend/src/services/exploration.ts"
Task: "Create GenerateDocumentButton in frontend/src/components/exploration/GenerateDocumentButton.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify infrastructure)
2. Complete Phase 2: Foundational (helper methods)
3. Complete Phase 3: User Story 1 (Summary generation)
4. **STOP and VALIDATE**: Test summary generation end-to-end
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (PRFAQ added)
4. Add User Story 3 → Test independently → Deploy/Demo (Regeneration)
5. Each story adds value without breaking previous stories

### Existing Infrastructure Reuse

| Component | Action | File |
|-----------|--------|------|
| Table | REUSE | `experiment_documents` |
| Entity | REUSE | `ExperimentDocument` |
| Enums | REUSE | `DocumentType`, `DocumentStatus` |
| Repository | REUSE | `ExperimentDocumentRepository` |
| Schemas | REUSE | `ExperimentDocumentResponse` |
| Migration | NONE | Not needed |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Use `experiment_documents` table - do NOT create new tables
- **CRITICAL**: Use `exploration.experiment_id` as FK for documents
- **CRITICAL**: Include `metadata.source = "exploration"` to identify origin

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 44 |
| **Phase 1 (Setup)** | 5 tasks |
| **Phase 2 (Foundational)** | 3 tasks |
| **Phase 3 (US1 - Summary)** | 14 tasks |
| **Phase 4 (US2 - PRFAQ)** | 13 tasks |
| **Phase 5 (US3 - Regeneration)** | 5 tasks |
| **Phase 6 (Polish)** | 4 tasks |
| **Parallel Opportunities** | 15 tasks marked [P] |
| **MVP Scope** | US1 only (22 tasks to MVP) |
