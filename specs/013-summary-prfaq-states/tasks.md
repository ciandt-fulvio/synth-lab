# Tasks: Summary and PR-FAQ State Management

**Input**: Design documents from `/specs/013-summary-prfaq-states/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included as per constitution requirement (TDD/BDD principle)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `src/synth_lab/` (Python/FastAPI)
- **Frontend**: `frontend/src/` (React/TypeScript)
- **Tests**: `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migrations and shared enums/models

- [x] T001 Create database migration for prfaq_metadata status columns in src/synth_lab/infrastructure/database/migrations/
- [x] T002 [P] Add ArtifactStateEnum and PRFAQStatus enums in src/synth_lab/domain/entities/artifact_state.py
- [x] T003 [P] Add TypeScript types for artifact states in frontend/src/types/artifact-state.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core state computation logic that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Add compute_summary_state factory function in src/synth_lab/domain/entities/artifact_state.py
- [x] T005 Add compute_prfaq_state factory function in src/synth_lab/domain/entities/artifact_state.py
- [x] T006 Add ArtifactState and ArtifactStatesResponse Pydantic models in src/synth_lab/api/schemas/artifact_state.py
- [x] T007 [P] Extend ResearchRepository with get_prfaq_metadata method in src/synth_lab/infrastructure/repositories/research.py
- [x] T008 Add get_artifact_states method to ResearchService in src/synth_lab/domain/services/research.py
- [x] T009 Add GET /research/{exec_id}/artifacts endpoint in src/synth_lab/api/routes/research.py
- [x] T010 [P] Add getArtifactStates API function in frontend/src/services/research-api.ts
- [x] T011 [P] Add queryKeys.artifactStates in frontend/src/lib/query-keys.ts

**Checkpoint**: Foundation ready - unified state endpoint available

---

## Phase 3: User Story 1 - View Summary When Available (Priority: P1) 🎯 MVP

**Goal**: Users can view research summary with clear state indication (available, unavailable, generating, failed)

**Independent Test**: Complete a research execution, verify summary button shows correct state and opens summary content when available

### Tests for User Story 1

- [ ] T012 [P] [US1] Unit test for compute_summary_state in tests/unit/domain/test_artifact_state.py
- [ ] T013 [P] [US1] Contract test for GET /research/{exec_id}/artifacts summary state in tests/contract/test_artifact_state_contract.py
- [ ] T014 [P] [US1] Integration test for summary state transitions in tests/integration/api/test_artifact_state_api.py

### Implementation for User Story 1

- [x] T015 [US1] Create useArtifactStates hook in frontend/src/hooks/use-artifact-state.ts
- [x] T016 [US1] Create ArtifactButton component for summary in frontend/src/components/shared/ArtifactButton.tsx
- [x] T017 [US1] Update InterviewDetail page to use ArtifactButton for summary in frontend/src/pages/InterviewDetail.tsx
- [x] T018 [US1] Add summary state-specific button labels and icons (Visualizar, Indisponível, Gerando...)

**Checkpoint**: User Story 1 complete - summary viewing with state indication works independently

---

## Phase 4: User Story 2 - Generate PR-FAQ When Prerequisites Met (Priority: P2)

**Goal**: Users can generate PR-FAQ when summary is available, with loading state and concurrent request prevention

**Independent Test**: Have execution with available summary, click "Gerar PR/FAQ", observe loading state, verify PR-FAQ is generated

### Tests for User Story 2

- [ ] T019 [P] [US2] Unit test for compute_prfaq_state in tests/unit/domain/test_artifact_state.py
- [ ] T020 [P] [US2] Contract test for POST /prfaq/generate responses in tests/contract/test_artifact_state_contract.py
- [ ] T021 [P] [US2] Integration test for concurrent request prevention in tests/integration/api/test_artifact_state_api.py

### Implementation for User Story 2

- [x] T022 [US2] Extend PRFAQRepository with create_pending_prfaq and update_prfaq_status methods in src/synth_lab/infrastructure/repositories/prfaq.py
- [x] T023 [US2] Add concurrent request check to PRFAQService.generate_prfaq in src/synth_lab/domain/services/prfaq.py
- [x] T024 [US2] Update POST /prfaq/generate to return 409 if already generating in src/synth_lab/api/routes/prfaq.py
- [x] T025 [US2] Add usePrfaqGenerate mutation hook in frontend/src/hooks/use-prfaq-generate.ts
- [x] T026 [US2] Update ArtifactButton to handle generating state with loading spinner
- [x] T027 [US2] Add conditional polling (refetchInterval: 2000) when prfaq.state === 'generating'
- [x] T028 [US2] Add disabled state with tooltip for prerequisite not met (summary required)

**Checkpoint**: User Story 2 complete - PR-FAQ generation with state management works independently

---

## Phase 5: User Story 3 - View PR-FAQ When Available (Priority: P3)

**Goal**: Users can view previously generated PR-FAQ content

**Independent Test**: Have execution with prfaq_available = true, click "Visualizar", verify PR-FAQ content displays in modal

### Tests for User Story 3

- [ ] T029 [P] [US3] Contract test for prfaq available state response in tests/contract/test_artifact_state_contract.py

### Implementation for User Story 3

- [x] T030 [US3] Update ArtifactButton to show "Visualizar" when prfaq state is available
- [x] T031 [US3] Ensure MarkdownPopup displays PR-FAQ content correctly in frontend/src/pages/InterviewDetail.tsx
- [x] T032 [US3] Add completed_at timestamp display for PR-FAQ viewing

**Checkpoint**: User Story 3 complete - PR-FAQ viewing works independently

---

## Phase 6: User Story 4 - Clear State Indication Across All Artifacts (Priority: P4)

**Goal**: All artifact states are clearly communicated through consistent UI patterns

**Independent Test**: View execution details in various states, verify button labels, colors, and enabled/disabled states match documented state machine

### Tests for User Story 4

- [ ] T033 [P] [US4] Integration test for all state combinations (unavailable, generating, available, failed) in tests/integration/api/test_artifact_state_api.py

### Implementation for User Story 4

- [x] T034 [US4] Add error state handling with retry button in ArtifactButton component
- [x] T035 [US4] Add Tooltip with error message for failed state
- [x] T036 [US4] Add visual differentiation (colors/icons) for each state in ArtifactButton
- [x] T037 [US4] Update PR-FAQ generation to store error_message on failure in PRFAQService
- [x] T038 [US4] Add retry functionality that clears error and restarts generation

**Checkpoint**: User Story 4 complete - consistent state indication across all artifacts

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [x] T039 [P] Run full test suite (make test-full) and fix any failures
- [x] T040 [P] Run linter (make lint-format) and fix any issues
- [ ] T041 Validate quickstart.md scenarios manually
- [ ] T042 Update API documentation if needed
- [x] T043 Add logging for state transitions in backend services

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can proceed in priority order (P1 → P2 → P3 → P4)
  - Some parallel work possible within each story
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Builds on US1 ArtifactButton component
- **User Story 3 (P3)**: Can start after US2 (needs prfaq generation to exist)
- **User Story 4 (P4)**: Can start after US2 (needs generating/failed states to exist)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Backend models/services before API endpoints
- API endpoints before frontend hooks
- Frontend hooks before UI components
- Core implementation before integration

### Parallel Opportunities

- T002, T003 (Setup) can run in parallel
- T007, T010, T011 (Foundational) can run in parallel
- T012, T013, T014 (US1 tests) can run in parallel
- T019, T020, T021 (US2 tests) can run in parallel
- Different user stories can be worked on in parallel by different team members (after US1 component is ready)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for compute_summary_state in tests/unit/domain/test_artifact_state.py"
Task: "Contract test for GET /research/{exec_id}/artifacts in tests/contract/test_artifact_state_contract.py"
Task: "Integration test for summary state transitions in tests/integration/api/test_artifact_state_api.py"
```

---

## Implementation Strategy


1. Complete Phase 1: Setup (database migration, enums)
2. Complete Phase 2: Foundational (state computation, endpoint, frontend setup)
3. Complete Phase 3: User Story 1 (summary state indication)
4. **VALIDATE**: Test summary viewing independently
5. Deploy/demo if ready
6. Complete Setup + Foundational → State endpoint ready
7. Add User Story 1 → Summary viewing with states → Deploy/Demo (MVP!)
8. Add User Story 2 → PR-FAQ generation with loading → Deploy/Demo
9. Add User Story 3 → PR-FAQ viewing → Deploy/Demo
10. Add User Story 4 → Complete state indication → Deploy/Demo
11. Each story adds value without breaking previous stories

---

## Summary

| Phase | Tasks | Parallel Tasks | Story Tasks |
|-------|-------|----------------|-------------|
| Setup | 3 | 2 | - |
| Foundational | 8 | 3 | - |
| US1 (P1) | 7 | 3 | 7 |
| US2 (P2) | 10 | 3 | 10 |
| US3 (P3) | 4 | 1 | 4 |
| US4 (P4) | 6 | 1 | 6 |
| Polish | 5 | 2 | - |
| **Total** | **43** | **15** | **27** |

### Independent Test Criteria

- **US1**: Research execution with completed summary shows "Visualizar" button
- **US2**: Click "Gerar PR/FAQ" shows loading, generates PR-FAQ, changes to "Visualizar"
- **US3**: Execution with prfaq_available = true shows "Visualizar", opens PR-FAQ content
- **US4**: All states (unavailable, generating, available, failed) have distinct visual treatment

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
