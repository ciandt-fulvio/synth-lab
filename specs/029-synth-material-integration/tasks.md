# Tasks: Synth Material Integration

**Input**: Design documents from `/specs/029-synth-material-integration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are included following TDD/BDD constitution requirement (Principle I). All tests MUST be written and FAIL before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `src/synth_lab/` at repository root
- **Tests**: `tests/` at repository root
- No frontend changes (materials already displayed via feature 001)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and verify existing infrastructure

- [X] T001 Verify ExperimentMaterial ORM model exists in src/synth_lab/models/orm/material.py
- [X] T002 Verify ExperimentMaterialRepository exists in src/synth_lab/repositories/experiment_material_repository.py
- [X] T003 [P] Verify S3 client exists in MaterialService (src/synth_lab/services/material_service.py)
- [X] T004 [P] Verify Phoenix tracing setup in src/synth_lab/infrastructure/phoenix_tracing.py
- [X] T005 [P] Verify OpenAI Agents SDK is available (check existing tools.py imports)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core materials context infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational Phase

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T006 [P] Unit test for format_materials_for_prompt() in tests/unit/services/test_materials_context.py
- [X] T007 [P] Unit test for to_material_context() in tests/unit/services/test_materials_context.py
- [X] T008 [P] Unit test for validate_token_budget() in tests/unit/services/test_materials_context.py
- [X] T009 [P] Contract test for materials formatting in tests/contract/test_materials_context.py

### Implementation for Foundational Phase

- [X] T010 Create MaterialContext Pydantic model in src/synth_lab/services/materials_context.py
- [X] T011 Implement to_material_context() transformation function in src/synth_lab/services/materials_context.py
- [X] T012 Implement format_materials_for_prompt() for interview context in src/synth_lab/services/materials_context.py
- [X] T013 Implement format_materials_for_prompt() for prfaq context in src/synth_lab/services/materials_context.py
- [X] T014 Implement format_materials_for_prompt() for exploration context in src/synth_lab/services/materials_context.py
- [X] T015 Implement validate_token_budget() with tiktoken in src/synth_lab/services/materials_context.py
- [X] T016 Add MaterialReference Pydantic model in src/synth_lab/services/materials_context.py
- [X] T017 Add logging and error handling to materials_context.py
- [X] T018 Run foundational tests and verify all pass

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synths Reference Materials During Interviews 

**Goal**: Enable Synths (interviewer and interviewee) to view and reference experiment materials during interviews, providing contextual feedback based on personality traits

**Independent Test**: Conduct an interview with attached materials and verify that the Synth references specific visual elements in responses, delivering realistic user feedback on designs

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T019 [P] [US1] Unit test for create_materials_tool() in tests/unit/services/research_agentic/test_materials_tool.py
- [X] T020 [P] [US1] Integration test for materials tool with S3 mock in tests/integration/services/test_materials_tool.py
- [X] T021 [P] [US1] Contract test for interviewer prompt with materials in tests/contract/test_interview_prompts.py
- [X] T022 [P] [US1] End-to-end test for interview with materials in tests/integration/services/test_interview_with_materials.py

### Implementation for User Story 1

- [X] T023 [P] [US1] Create MaterialToolResponse Pydantic model in src/synth_lab/services/research_agentic/tools.py
- [X] T024 [US1] Implement create_materials_tool() factory function in src/synth_lab/services/research_agentic/tools.py
- [X] T025 [US1] Implement view_material() function with @function_tool decorator in src/synth_lab/services/research_agentic/tools.py
- [X] T026 [US1] Add S3 download and base64 encoding logic to view_material() in src/synth_lab/services/research_agentic/tools.py
- [X] T027 [US1] Add error handling for missing/corrupted materials in view_material() in src/synth_lab/services/research_agentic/tools.py
- [X] T028 [US1] Add Phoenix tracing to view_material() tool in src/synth_lab/services/research_agentic/tools.py
- [X] T029 [US1] Modify format_interviewer_instructions() to accept materials parameter in src/synth_lab/services/research_agentic/instructions.py
- [X] T030 [US1] Integrate format_materials_for_prompt() into interviewer instructions in src/synth_lab/services/research_agentic/instructions.py
- [X] T031 [US1] Modify format_interviewee_instructions() to accept materials parameter in src/synth_lab/services/research_agentic/instructions.py
- [X] T032 [US1] Integrate format_materials_for_prompt() into interviewee instructions in src/synth_lab/services/research_agentic/instructions.py
- [X] T033 [US1] Update create_interviewer() to register materials tool in src/synth_lab/services/research_agentic/agent_definitions.py
- [X] T034 [US1] Update create_interviewee() to register materials tool in src/synth_lab/services/research_agentic/agent_definitions.py
- [X] T035 [US1] Add materials parameter to interview service entry point (wherever interviews are started)
- [X] T036 [US1] Run all User Story 1 tests and verify they pass

**Checkpoint**: At this point, Synths can reference materials during interviews - User Story 1 is fully functional and testable independently

---

## Phase 4: User Story 2 - Materials Inform PR-FAQ Generation 

**Goal**: Generated PR-FAQs automatically reference experiment materials with timestamps and visual element citations

**Independent Test**: Generate a PR-FAQ for an experiment with materials and verify that the document includes material references with specific visual details and contextual insights

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T037 [P] [US2] Unit test for PR-FAQ prompt with materials in tests/unit/services/research_prfaq/test_prompts_with_materials.py
- [X] T038 [P] [US2] Integration test for PR-FAQ generation with materials in tests/integration/services/test_prfaq_with_materials.py
- [X] T039 [P] [US2] Contract test for material reference format in PR-FAQs in tests/contract/test_prfaq_material_references.py

### Implementation for User Story 2

- [X] T040 [P] [US2] Modify get_system_prompt() to accept materials parameter in src/synth_lab/services/research_prfaq/prompts.py
- [X] T041 [US2] Integrate format_materials_for_prompt() into PR-FAQ system prompt in src/synth_lab/services/research_prfaq/prompts.py
- [X] T042 [US2] Add material reference format instructions to PR-FAQ prompt in src/synth_lab/services/research_prfaq/prompts.py
- [X] T043 [US2] Modify PR-FAQ generator to fetch materials by experiment_id in src/synth_lab/services/research_prfaq/generator.py
- [X] T044 [US2] Pass materials to get_system_prompt() in generator in src/synth_lab/services/research_prfaq/generator.py
- [X] T045 [US2] Add Phoenix tracing for PR-FAQ generation with materials in src/synth_lab/services/research_prfaq/generator.py
- [X] T046 [US2] Run all User Story 2 tests and verify they pass

**Checkpoint**: At this point, PR-FAQs include material references - User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Materials Enhance Scenario Exploration 

**Goal**: During exploration scenario generation, Synths can reference experiment materials to create more realistic and contextually relevant scenario nodes

**Independent Test**: Run an exploration with attached materials and verify that scenario nodes include material-based considerations and references

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T047 [P] [US3] Unit test for exploration action proposal with materials in tests/unit/services/exploration/test_action_proposal_with_materials.py
- [X] T048 [P] [US3] Integration test for exploration with materials in tests/integration/services/test_exploration_with_materials.py

### Implementation for User Story 3

- [X] T049 [P] [US3] Modify _build_prompt() in ActionProposalService to accept materials parameter in src/synth_lab/services/exploration/action_proposal_service.py
- [X] T050 [US3] Integrate format_materials_for_prompt() into action proposal prompts in src/synth_lab/services/exploration/action_proposal_service.py
- [X] T051 [US3] Fetch materials in ActionProposalService.propose() method in src/synth_lab/services/exploration/action_proposal_service.py
- [X] T052 [US3] Add Phoenix tracing for exploration with materials in src/synth_lab/services/exploration/action_proposal_service.py
- [X] T053 [US3] Run all User Story 3 tests and verify they pass

**Checkpoint**: At this point, scenario exploration can use materials - User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Exploration Summaries Reference Materials 

**Goal**: Generated exploration summaries and PR-FAQs include material references to support scenario-based insights

**Independent Test**: Complete an exploration with materials and verify that the summary document includes material references supporting scenario insights

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T054 [P] [US4] Unit test for exploration summary with materials in tests/unit/services/exploration/test_summary_with_materials.py
- [X] T055 [P] [US4] Integration test for exploration summary generation in tests/integration/services/test_exploration_summary_with_materials.py

### Implementation for User Story 4

- [X] T056 [P] [US4] Modify _build_prompt() in ExplorationSummaryGenerator to accept materials in src/synth_lab/services/exploration_summary_generator_service.py
- [X] T057 [US4] Integrate format_materials_for_prompt() into summary prompts in src/synth_lab/services/exploration_summary_generator_service.py
- [X] T058 [US4] Fetch materials in summary generation method in src/synth_lab/services/exploration_summary_generator_service.py
- [X] T059 [US4] Add material reference format to summary prompt in src/synth_lab/services/exploration_summary_generator_service.py
- [X] T060 [US4] Add Phoenix tracing for summary with materials in src/synth_lab/services/exploration_summary_generator_service.py
- [X] T061 [US4] Run all User Story 4 tests and verify they pass

**Checkpoint**: All user stories should now be independently functional - materials integrated across all workflows

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T062 [P] Add comprehensive docstrings to all new functions in src/synth_lab/services/materials_context.py
- [ ] T063 [P] Add comprehensive docstrings to materials tool in src/synth_lab/services/research_agentic/tools.py
- [ ] T064 [P] Verify all Phoenix tracing spans are correctly named and attributed
- [X] T065 [P] Run linter (ruff) on all modified files and fix issues
- [ ] T066 [P] Add token budget validation warnings in all prompt builders
- [ ] T067 [P] Test edge cases: empty materials, missing S3 files, corrupted files
- [ ] T068 [P] Test edge cases: materials >20 items, large videos, unsupported MIME types
- [ ] T069 Verify performance targets: material retrieval <5s for images/PDFs, <10s for videos
- [ ] T070 Verify PR-FAQ generation time increase is <30% with materials vs without
- [X] T071 Run complete test suite (fast + slow battery) and verify all tests pass
- [ ] T072 Validate quickstart.md examples work as documented
- [ ] T073 Create commit with all changes following constitution commit guidelines
- [ ] T074 Run fast test battery (<5s) before committing
- [ ] T075 Prepare for PR: verify all tests pass, documentation updated, linting clean

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1 (but can reference it for consistency)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent of US1/US2
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Independent of US1/US2/US3

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD/BDD)
- Models/data structures before service logic
- Service logic before integration into existing systems
- Phoenix tracing added during implementation (not after)
- Story complete and tested before moving to nex

### Parallel Opportunities

- **Setup (Phase 1)**: Tasks T002-T005 can run in parallel (verification tasks)
- **Foundational Tests (Phase 2)**: Tasks T006-T009 can run in parallel (different test files)
- **Foundational Implementation (Phase 2)**: Models and utilities can be built in parallel, but format functions depend on models
- **Once Foundational completes**: All 4 user stories can start in parallel (if team capacity allows)
- **Within User Story 1**: Tests T019-T022 in parallel, then implementation tasks in logical order
- **Within User Story 2**: Tests T037-T039 in parallel, then implementation tasks
- **Within User Story 3**: Tests T047-T048 in parallel, then implementation tasks
- **Within User Story 4**: Tests T054-T055 in parallel, then implementation tasks
- **Polish (Phase 7)**: Most tasks marked [P] can run in parallel (documentation, linting, validation)

---

## Parallel Example: User Story 1

```bash
# Step 1: Launch all tests for User Story 1 together (they will FAIL):
Task T019: "Unit test for create_materials_tool() in tests/unit/services/research_agentic/test_materials_tool.py"
Task T020: "Integration test for materials tool with S3 mock in tests/integration/services/test_materials_tool.py"
Task T021: "Contract test for interviewer prompt with materials in tests/contract/test_interview_prompts.py"
Task T022: "End-to-end test for interview with materials in tests/integration/services/test_interview_with_materials.py"

# Step 2: Launch parallelizable implementation tasks together:
Task T023: "Create MaterialToolResponse Pydantic model in src/synth_lab/services/research_agentic/tools.py"
Task T029: "Modify format_interviewer_instructions() to accept materials parameter in src/synth_lab/services/research_agentic/instructions.py"
Task T031: "Modify format_interviewee_instructions() to accept materials parameter in src/synth_lab/services/research_agentic/instructions.py"
```

---

## Implementation Strategy


1. Complete Phase 1: Setup (verify infrastructure)
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
   - Write tests T006-T009 → verify they FAIL
   - Implement T010-T017 → verify tests PASS
3. Complete Phase 3: User Story 1
   - Write tests T019-T022 → verify they FAIL
   - Implement T023-T035 → verify tests PASS
4. Test User Story 1 independently
5. Run fast test battery (<5s), commit atomically
7. Complete Setup + Foundational → Foundation ready (commit)
8. Add User Story 1 → Test independently
  - Write tests → Implement → Verify tests PASS → Commit
9. Add User Story 2 → Test independently
  - Write tests → Implement → Verify tests PASS → Commit
10. Add User Story 3 → Test independently
  - Write tests → Implement → Verify tests PASS → Commit
11. Add User Story 4 → Test independently
  - Write tests → Implement → Verify tests PASS → Commit
12. Polish phase → Final commit → Complete feature

Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done (T018 complete):
   - Developer A: User Story 1 (interviews with materials)
   - Developer B: User Story 2 (PR-FAQ with materials)
   - Developer C: User Story 3 (exploration scenarios)
   - Developer D: User Story 4 (exploration summaries)
3. Stories complete and integrate independently
4. Team regroups for Polish phase

---

## Notes

- **[P] tasks**: Different files, no dependencies - can run in parallel
- **[Story] label**: Maps task to specific user story for traceability
- **Each user story**: Independently completable and testable
- **TDD/BDD**: Verify tests FAIL before implementing (constitution requirement)
- **Fast test battery**: Must complete in <5s before each commit
- **Complete test battery**: Must pass before PR (constitution requirement)
- **Atomic commits**: One commit per logical milestone (constitution requirement)
- **Phoenix tracing**: All LLM calls must be traced (architecture requirement)
- **Stop at any checkpoint**: Validate story independently before proceeding
- **Avoid**: Vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Summary

- **Total Tasks**: 75
- **Completed**: 63/75 (84%)
- **User Story 1 (P1)**: 18/18 tasks completed ✅ (T019-T036)
- **User Story 2 (P2)**: 10/10 tasks completed ✅ (T037-T046)
- **User Story 3 (P3)**: 7/7 tasks completed ✅ (T047-T053)
- **User Story 4 (P3)**: 8/8 tasks completed ✅ (T054-T061)
- **Foundational (blocks all)**: 13/13 tasks completed ✅ (T006-T018)
- **Setup**: 5/5 tasks completed ✅ (T001-T005)
- **Polish**: 2/14 tasks completed (T065, T071) - remaining tasks optional
- **Parallel opportunities**: 40+ parallelizable tasks marked [P]
- **Independent tests**: Each user story has clear validation criteria
