---
description: "Task list for Simplified Hypothesis Selection Wizard implementation"
---

# Tasks: Simplified Hypothesis Selection Wizard

**Branch**: `036-simplified-hypothesis-wizard`
**Input**: Design documents from `/specs/036-simplified-hypothesis-wizard/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: TDD approach required per constitution. Tests written BEFORE implementation for all new services.

**Organization**: Tasks grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This is a web application:
- Backend: `src/synth_lab/` (Python)
- Frontend: `frontend/src/` (TypeScript/React)
- Backend Tests: `tests/` (pytest)
- Frontend Tests: `frontend/tests/` (Vitest + Playwright)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify prerequisites and prepare for wizard implementation

- [X] T001 Verify existing causal simulation infrastructure (specs/035) is functional and deployed
- [X] T002 Review existing HypothesisParametrizerService in src/synth_lab/services/simulation/hypothesis_parametrizer_service.py
- [X] T003 Review existing hypothesis endpoints in src/synth_lab/api/routers/hypotheses.py
- [X] T004 Review existing hypothesis frontend components in frontend/src/components/simulation/hypothesis/

**Checkpoint**: Existing infrastructure confirmed - ready to extend with wizard features

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared code that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Add ScenarioProfile enum to src/synth_lab/domain/entities/hypothesis.py
- [X] T006 [P] Add ResponseType enum to src/synth_lab/domain/entities/hypothesis.py
- [X] T007 [P] Add wizard request/response schemas to src/synth_lab/api/schemas/hypothesis.py (WizardInitRequest, WizardInitResponse, WizardClarifyRequest, WizardClarifyResponse, ClarificationQuestionSchema, ClarificationResponseSchema)
- [X] T008 Create HypothesisWizardService stub in src/synth_lab/services/simulation/hypothesis_wizard_service.py with class definition and __init__ method

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Select General Scenario Profile (Priority: P1) 🎯 MVP

**Goal**: Users select Conservative/Realistic/Optimistic profile and receive complete simulation-ready hypotheses for all DAG variables

**Independent Test**: Create DAG → select scenario profile → verify all variables receive appropriate distribution configurations → run simulation successfully

### Tests for User Story 1 (TDD - Write FIRST)

> **⚠️ WRITE THESE TESTS FIRST, ENSURE THEY FAIL BEFORE IMPLEMENTATION**

- [X] T009 [P] [US1] Unit test for _classify_decision_context() in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T010 [P] [US1] Unit test for _apply_profile_adjustments() for Normal distribution in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T011 [P] [US1] Unit test for _apply_profile_adjustments() for Beta distribution in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T012 [P] [US1] Unit test for _apply_profile_adjustments() for Uniform distribution in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T013 [P] [US1] Unit test for _apply_profile_adjustments() for LogNormal distribution in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T014 [P] [US1] Unit test for _apply_profile_adjustments() for Bernoulli distribution in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T015 [P] [US1] Unit test for _apply_profile_adjustments() for Triangular distribution in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T016 [US1] Unit test for init_wizard() method in tests/unit/services/test_hypothesis_wizard_service.py (verify hypotheses persisted and returned)
- [X] T017 [US1] Integration test for POST /wizard/init endpoint in tests/integration/api/test_hypothesis_wizard_api.py (test Conservative profile)
- [X] T018 [US1] Integration test for POST /wizard/init endpoint in tests/integration/api/test_hypothesis_wizard_api.py (test Realistic profile)
- [X] T019 [US1] Integration test for POST /wizard/init endpoint in tests/integration/api/test_hypothesis_wizard_api.py (test Optimistic profile)

### Implementation for User Story 1

- [X] T020 [P] [US1] Implement _classify_decision_context() in src/synth_lab/services/simulation/hypothesis_wizard_service.py (uses DAG structure heuristics from research.md Decision 4)
- [X] T021 [P] [US1] Implement _apply_profile_adjustments() for Normal distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py (research.md Decision 1)
- [X] T022 [P] [US1] Implement _apply_profile_adjustments() for Beta distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T023 [P] [US1] Implement _apply_profile_adjustments() for Uniform distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T024 [P] [US1] Implement _apply_profile_adjustments() for LogNormal distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T025 [P] [US1] Implement _apply_profile_adjustments() for Bernoulli distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T026 [P] [US1] Implement _apply_profile_adjustments() for Triangular distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T027 [US1] Extend HypothesisParametrizerService._build_parametrization_prompt() in src/synth_lab/services/simulation/hypothesis_parametrizer_service.py to include scenario profile hints
- [X] T028 [US1] Implement init_wizard() method in src/synth_lab/services/simulation/hypothesis_wizard_service.py (calls HypothesisParametrizerService, applies profile adjustments, persists hypotheses)
- [X] T029 [US1] Add POST /wizard/init endpoint to src/synth_lab/api/routers/hypotheses.py (delegates to HypothesisWizardService.init_wizard)
- [X] T030 [P] [US1] Create ScenarioProfileSelector component in frontend/src/components/simulation/hypothesis/ScenarioProfileSelector.tsx (radio buttons for Conservative/Realistic/Optimistic)
- [X] T031 [US1] Create useInitWizard hook in frontend/src/hooks/use-hypothesis-wizard.ts (wraps useMutation for /wizard/init endpoint)
- [X] T032 [US1] Create initWizard API function in frontend/src/services/hypothesis-wizard-api.ts (calls POST /wizard/init with fetchAPI)
- [X] T033 [US1] Create HypothesisWizard page in frontend/src/pages/HypothesisWizard.tsx (scenario selection step + review step)
- [X] T034 [US1] Add wizard route to frontend router (e.g., /simulations/:id/wizard)
- [ ] T035 [US1] E2E test for complete US1 flow in frontend/tests/e2e/hypothesis-wizard.spec.ts (DAG → scenario selection → hypothesis review → simulation)

**Checkpoint**: User Story 1 complete and independently testable. Users can generate simulation-ready hypotheses with a single scenario profile selection. This is a viable MVP.

---

## Phase 4: User Story 2 - Answer Targeted Clarification Questions (Priority: P2)

**Goal**: System identifies 3-5 critical variables and asks qualitative questions. Users answer with "more"/"less"/"equal"/"don't know" to refine distributions.

**Independent Test**: After US1 (scenario profile selected), receive 3-5 clarification questions → answer with qualitative responses → verify affected variables' distributions adjusted accordingly

### Tests for User Story 2 (TDD - Write FIRST)

> **⚠️ WRITE THESE TESTS FIRST, ENSURE THEY FAIL BEFORE IMPLEMENTATION**

- [X] T036 [P] [US2] Unit test for _calculate_impact_score() in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T037 [P] [US2] Unit test for _calculate_uncertainty_score() for Normal distribution in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T038 [P] [US2] Unit test for _calculate_uncertainty_score() for Beta distribution in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T039 [P] [US2] Unit test for _rank_critical_variables() in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T040 [P] [US2] Unit test for _generate_clarification_question() for EVENT variable in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T041 [P] [US2] Unit test for _generate_clarification_question() for METRIC variable in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T042 [P] [US2] Unit test for _generate_clarification_question() for RATE variable in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T043 [P] [US2] Unit test for _apply_response_adjustment() for "more" response on Normal distribution in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T044 [P] [US2] Unit test for _apply_response_adjustment() for "less" response on Beta distribution in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T045 [P] [US2] Unit test for _apply_response_adjustment() for "equal" response (no change) in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T046 [P] [US2] Unit test for _apply_response_adjustment() for "dont_know" response (increase variance) in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T047 [US2] Unit test for apply_clarifications() method in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T048 [US2] Integration test for POST /wizard/clarify endpoint in tests/integration/api/test_hypothesis_wizard_api.py (test partial responses)
- [X] T049 [US2] Integration test for POST /wizard/clarify endpoint in tests/integration/api/test_hypothesis_wizard_api.py (test empty responses - skip all)

### Implementation for User Story 2

- [X] T050 [P] [US2] Implement _calculate_impact_score() in src/synth_lab/services/simulation/hypothesis_wizard_service.py (research.md Decision 2)
- [X] T051 [P] [US2] Implement _calculate_uncertainty_score() for Normal distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T052 [P] [US2] Implement _calculate_uncertainty_score() for Beta distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T053 [P] [US2] Implement _calculate_uncertainty_score() for Uniform distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T054 [P] [US2] Implement _calculate_uncertainty_score() for LogNormal distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T055 [P] [US2] Implement _calculate_uncertainty_score() for Bernoulli distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T056 [P] [US2] Implement _calculate_uncertainty_score() for Triangular distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T057 [US2] Implement _rank_critical_variables() in src/synth_lab/services/simulation/hypothesis_wizard_service.py (combines impact × uncertainty scores)
- [X] T058 [P] [US2] Implement _generate_clarification_question() for EVENT variable type in src/synth_lab/services/simulation/hypothesis_wizard_service.py (research.md Decision 5b)
- [X] T059 [P] [US2] Implement _generate_clarification_question() for METRIC variable type in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T060 [P] [US2] Implement _generate_clarification_question() for RATE variable type in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T061 [P] [US2] Implement _generate_clarification_question() for DURATION variable type in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T062 [US2] Implement generate_clarification_questions() method in src/synth_lab/services/simulation/hypothesis_wizard_service.py (ranks variables, generates 3-5 questions based on decision context)
- [X] T063 [P] [US2] Implement _apply_response_adjustment() for "more" response on Normal distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py (research.md Decision 3)
- [X] T064 [P] [US2] Implement _apply_response_adjustment() for "more" response on Beta distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T065 [P] [US2] Implement _apply_response_adjustment() for "more" response on Uniform distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T066 [P] [US2] Implement _apply_response_adjustment() for "less" response on Normal distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T067 [P] [US2] Implement _apply_response_adjustment() for "less" response on Beta distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T068 [P] [US2] Implement _apply_response_adjustment() for "less" response on Uniform distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T069 [P] [US2] Implement _apply_response_adjustment() for "equal" response (no adjustment) in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T070 [P] [US2] Implement _apply_response_adjustment() for "dont_know" response (increase variance) for Normal distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T071 [P] [US2] Implement _apply_response_adjustment() for "dont_know" response for Beta distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T072 [P] [US2] Implement _apply_response_adjustment() for "dont_know" response for Uniform distribution in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T073 [US2] Update init_wizard() method in src/synth_lab/services/simulation/hypothesis_wizard_service.py to call generate_clarification_questions() and return questions in response
- [X] T074 [US2] Implement apply_clarifications() method in src/synth_lab/services/simulation/hypothesis_wizard_service.py (loads hypotheses, applies adjustments, persists updates)
- [X] T075 [US2] Add POST /wizard/clarify endpoint to src/synth_lab/api/routers/hypotheses.py (delegates to HypothesisWizardService.apply_clarifications)
- [X] T076 [P] [US2] Create ClarificationQuestionsStep component in frontend/src/components/simulation/hypothesis/ClarificationQuestionsStep.tsx (question cards with 4-choice radio buttons)
- [X] T077 [US2] Create useClarifyHypotheses hook in frontend/src/hooks/use-hypothesis-wizard.ts (wraps useMutation for /wizard/clarify endpoint)
- [X] T078 [US2] Create clarifyHypotheses API function in frontend/src/services/hypothesis-wizard-api.ts (calls POST /wizard/clarify with fetchAPI)
- [X] T079 [US2] Update HypothesisWizard page in frontend/src/pages/HypothesisWizard.tsx to add clarification questions step after scenario selection
- [ ] T080 [US2] E2E test for complete US2 flow in frontend/tests/e2e/hypothesis-wizard.spec.ts (scenario selection → clarification questions → answer responses → verify adjusted hypotheses)

**Checkpoint**: User Story 2 complete and independently testable. Users can refine critical variable distributions with 3-5 qualitative questions. Enhances US1's scenario profile with targeted precision.

---

## Phase 5: User Story 3 - Proceed with Simulation Despite Uncertainty (Priority: P3)

**Goal**: Users can skip clarification questions and still get simulation results with clear uncertainty indicators

**Independent Test**: After US1 (scenario profile selected), skip all clarification questions → run simulation → verify results display with uncertainty indicators for variables with high uncertainty

### Tests for User Story 3 (TDD - Write FIRST)

> **⚠️ WRITE THESE TESTS FIRST, ENSURE THEY FAIL BEFORE IMPLEMENTATION**

- [X] T081 [P] [US3] Unit test for _identify_high_uncertainty_variables() in tests/unit/services/test_hypothesis_wizard_service.py
- [X] T082 [US3] Integration test for skipping clarification questions in tests/integration/api/test_hypothesis_wizard_api.py (POST /wizard/clarify with empty responses)
- [ ] T083 [US3] E2E test for skip clarifications flow in frontend/tests/e2e/hypothesis-wizard.spec.ts (scenario → skip questions → run simulation → verify uncertainty indicators)

### Implementation for User Story 3

- [X] T084 [US3] Implement _identify_high_uncertainty_variables() in src/synth_lab/services/simulation/hypothesis_wizard_service.py (identifies variables with uncertainty_score > threshold)
- [X] T085 [US3] Update apply_clarifications() method in src/synth_lab/services/simulation/hypothesis_wizard_service.py to handle empty responses (no-op, use profile defaults)
- [X] T086 [P] [US3] Create HypothesisReviewStep component in frontend/src/components/simulation/hypothesis/HypothesisReviewStep.tsx (displays generated hypotheses with uncertainty indicators)
- [X] T087 [US3] Update HypothesisWizard page in frontend/src/pages/HypothesisWizard.tsx to add review step with "Skip Questions" button and uncertainty indicators
- [X] T088 [US3] Update simulation results display (if not already showing uncertainty) to include uncertainty indicators for high-uncertainty variables (may be out of scope - check existing implementation)

**Checkpoint**: User Story 3 complete. Users can proceed to simulation even with incomplete clarifications, and see clear uncertainty indicators. All three user stories now independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Integration, documentation, and final touches

- [X] T089 [P] Add Portuguese i18n strings for wizard UI in frontend/src/locales/pt.json (scenario profile labels, question text, button labels) - N/A: no i18n system in project
- [X] T090 [P] Add English i18n strings for wizard UI in frontend/src/locales/en.json - N/A: no i18n system in project
- [X] T091 [P] Add docstrings to all HypothesisWizardService methods in src/synth_lab/services/simulation/hypothesis_wizard_service.py (Portuguese, following project convention)
- [X] T092 [P] Add type hints to all HypothesisWizardService methods in src/synth_lab/services/simulation/hypothesis_wizard_service.py
- [X] T093 [P] Add Phoenix tracing spans to init_wizard() and apply_clarifications() in src/synth_lab/services/simulation/hypothesis_wizard_service.py (_tracer.start_as_current_span)
- [X] T094 [P] Add error handling for LLM failures in init_wizard() (fallback to realistic profile defaults)
- [X] T095 [P] Add error handling for invalid clarification responses in apply_clarifications() (skip invalid, log warning)
- [X] T096 [P] Add logging for wizard operations in src/synth_lab/services/simulation/hypothesis_wizard_service.py (scenario selected, questions generated, clarifications applied)
- [X] T097 Run ruff check and ruff format on all backend files
- [X] T098 Run ESLint and Prettier on all frontend files
- [X] T099 Run fast test battery (pytest -m fast) and verify <5s execution
- [X] T100 Run complete test battery (pytest) and verify 80%+ coverage for wizard service
- [ ] T101 Run E2E test suite (Playwright) and verify all wizard flows pass
- [ ] T102 [P] Update user documentation with wizard workflow guide (if user guide exists)
- [ ] T103 [P] Update API documentation with wizard endpoint examples (OpenAPI/Swagger annotations)
- [ ] T104 Manual smoke test: Create DAG → Conservative profile → verify hypotheses → run simulation
- [ ] T105 Manual smoke test: Create DAG → Realistic profile → answer clarifications → run simulation
- [ ] T106 Manual smoke test: Create DAG → Optimistic profile → skip clarifications → run simulation
- [ ] T107 Create git commit with all changes (message: "feat: add simplified hypothesis wizard with scenario profiles and clarification questions")

**Final Checkpoint**: Feature complete, tested, documented, and ready for PR

---

## Dependencies & Execution Strategy

### User Story Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational)
                    ↓
    ┌───────────────┼───────────────┐
    ↓               ↓               ↓
  US1 (P1)       US2 (P2)        US3 (P3)
    ↓               ↓               ↓
    └───────────────┼───────────────┘
                    ↓
              Phase 6 (Polish)
```

**User Story 1 (P1)**: INDEPENDENT after Phase 2. Can be implemented and tested alone. This is the MVP.

**User Story 2 (P2)**: DEPENDS on US1 (extends init_wizard to generate questions). Can be implemented after US1 is complete.

**User Story 3 (P3)**: DEPENDS on US1 and US2 (handles skipping questions). Can be implemented after US2 is complete.

### Parallel Execution Opportunities

**Within Phase 2 (Foundational)**: All tasks T005-T008 can run in parallel (different files, no dependencies).

**Within US1 Implementation**:
- Tests T009-T015 (unit tests for different distributions) can run in parallel
- Tests T017-T019 (integration tests for different profiles) can run in parallel
- Implementation T021-T026 (profile adjustments for different distributions) can run in parallel after T020
- Frontend T030, T031, T032 can run in parallel (different files)

**Within US2 Implementation**:
- Tests T036-T042 (unit tests for ranking/question generation) can run in parallel
- Tests T043-T046 (unit tests for response adjustments) can run in parallel
- Implementation T050-T056 (uncertainty scores for different distributions) can run in parallel
- Implementation T058-T061 (questions for different variable types) can run in parallel
- Implementation T063-T072 (response adjustments for different distributions/responses) can run in parallel
- Frontend T076, T077, T078 can run in parallel

**Within Phase 6 (Polish)**:
- Documentation tasks T089-T092 can run in parallel
- Error handling tasks T093-T096 can run in parallel

### MVP Scope Recommendation

**Minimum Viable Product**: User Story 1 (P1) only

This delivers:
- ✅ Scenario profile selection (Conservative/Realistic/Optimistic)
- ✅ Automatic hypothesis generation for all DAG variables
- ✅ Complete simulation-ready hypotheses
- ✅ Simplifies hypothesis configuration from manual parameter editing to single profile selection

Users can run simulations immediately after selecting a profile. US2 and US3 are enhancements that add precision and flexibility.

### Incremental Delivery Plan

1. **Sprint 1**: Setup + Foundational + US1 (MVP)
   - Tasks: T001-T035
   - Deliverable: Working wizard with scenario profile selection

2. **Sprint 2**: US2 (Clarification Questions)
   - Tasks: T036-T080
   - Deliverable: Enhanced wizard with targeted clarification

3. **Sprint 3**: US3 (Uncertainty Handling) + Polish
   - Tasks: T081-T107
   - Deliverable: Complete feature with all enhancements

---

## Task Summary

**Total Tasks**: 107

**By Phase**:
- Phase 1 (Setup): 4 tasks
- Phase 2 (Foundational): 4 tasks
- Phase 3 (US1 - MVP): 27 tasks (11 tests + 16 implementation)
- Phase 4 (US2): 45 tasks (14 tests + 31 implementation)
- Phase 5 (US3): 5 tasks (3 tests + 2 implementation)
- Phase 6 (Polish): 22 tasks

**By Type**:
- Tests: 28 tasks (TDD approach)
- Backend Implementation: 50 tasks
- Frontend Implementation: 11 tasks
- Documentation/Polish: 18 tasks

**Parallelizable Tasks**: 65 tasks marked with [P] (can run simultaneously)

**User Story Breakdown**:
- US1: 27 tasks (deliverable MVP)
- US2: 45 tasks (enhancement)
- US3: 5 tasks (enhancement)

---

## Format Validation

✅ All tasks follow checklist format: `- [ ] [ID] [P?] [Story?] Description with file path`
✅ All user story tasks labeled with [US1], [US2], or [US3]
✅ All parallelizable tasks marked with [P]
✅ All tasks include specific file paths
✅ Tasks organized by user story priority (P1 → P2 → P3)
✅ Independent test criteria defined per user story
✅ MVP scope clearly identified (US1 only)
✅ Parallel execution opportunities documented
✅ Dependencies mapped showing completion order
