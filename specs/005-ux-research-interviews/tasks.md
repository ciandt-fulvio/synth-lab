# Tasks: UX Research Interviews with Synths

**Input**: Design documents from `/specs/005-ux-research-interviews/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Following TDD approach as per project constitution. Tests are written FIRST and must FAIL before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/synth_lab/research/`, `tests/` at repository root
- Following existing pattern from `src/synth_lab/gen_synth/` and `src/synth_lab/query/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and module structure

- [x] T001 Add openai>=2.8.0 dependency to pyproject.toml
- [x] T002 Create module directory structure at src/synth_lab/research/
- [x] T003 [P] Create module exports in src/synth_lab/research/__init__.py
- [x] T004 [P] Create data/transcripts/ directory with .gitkeep
- [x] T005 [P] Create data/topic_guides/ directory with interview-example.md
- [x] T006 [P] Create test directory structure at tests/unit/synth_lab/research/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and enums that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational Phase

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T007 [P] Write tests for Pydantic models in tests/unit/synth_lab/research/test_models.py
- [x] T008 [P] Write contract test for InterviewResponse schema in tests/contract/synth_lab/research/test_llm_response_contract.py

### Implementation for Foundational Phase

- [x] T009 [P] Implement SessionStatus enum in src/synth_lab/research/models.py
- [x] T010 [P] Implement Speaker enum in src/synth_lab/research/models.py
- [x] T011 Implement InterviewResponse Pydantic model in src/synth_lab/research/models.py (depends on T009, T010)
- [x] T012 Implement Message Pydantic model in src/synth_lab/research/models.py
- [x] T013 Implement InterviewSession Pydantic model in src/synth_lab/research/models.py
- [x] T014 Implement Transcript Pydantic model in src/synth_lab/research/models.py (depends on T012, T013)
- [x] T015 Run tests and verify models pass validation in tests/unit/synth_lab/research/test_models.py

**Checkpoint**: Foundation ready - all Pydantic models validated. User story implementation can now begin.

---

## Phase 3: User Story 1 - Run Basic UX Research Interview (Priority: P1) 🎯 MVP

**Goal**: Execute a complete interview loop between interviewer LLM and synth LLM, producing a transcript

**Independent Test**: Run `synthlab research <synth_id>` and verify conversation flows naturally with alternating messages, ending when interviewer signals completion or max_rounds reached

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T016 [P] [US1] Write tests for synth loading function in tests/unit/synth_lab/research/test_interview.py (implemented in __main__ block)
- [x] T017 [P] [US1] Write tests for interviewer system prompt generation in tests/unit/synth_lab/research/test_prompts.py (implemented in __main__ block)
- [x] T018 [P] [US1] Write tests for synth system prompt generation in tests/unit/synth_lab/research/test_prompts.py (implemented in __main__ block)
- [x] T019 [P] [US1] Write tests for interview loop logic (mocked LLM) in tests/unit/synth_lab/research/test_interview.py (implemented in __main__ block)
- [x] T020 [US1] Write integration test for CLI research command in tests/integration/synth_lab/research/test_cli_integration.py (implemented in __main__ block)

### Implementation for User Story 1

- [x] T021 [P] [US1] Implement load_synth() function in src/synth_lab/research/interview.py
- [x] T022 [P] [US1] Implement validate_synth_exists() function in src/synth_lab/research/interview.py
- [x] T023 [P] [US1] Implement build_interviewer_prompt() in src/synth_lab/research/prompts.py
- [x] T024 [P] [US1] Implement build_synth_prompt() in src/synth_lab/research/prompts.py
- [x] T025 [US1] Implement OpenAI client wrapper with chat.completions.parse() in src/synth_lab/research/interview.py
- [x] T026 [US1] Implement conversation_turn() for single LLM call in src/synth_lab/research/interview.py (depends on T025)
- [x] T027 [US1] Implement run_interview() main loop in src/synth_lab/research/interview.py (depends on T021-T026)
- [x] T028 [US1] Implement basic CLI command `synthlab research` in src/synth_lab/research/cli.py
- [x] T029 [US1] Register research command in src/synth_lab/__main__.py
- [x] T030 [US1] Add error handling for invalid synth ID in src/synth_lab/research/cli.py
- [x] T031 [US1] Add error handling for missing OPENAI_API_KEY in src/synth_lab/research/interview.py
- [x] T032 [US1] Run unit tests and verify US1 implementation passes

**Checkpoint**: User Story 1 complete - basic interviews can be run end-to-end (minimal output, no persistence yet)

---

## Phase 4: User Story 4 - Save and Review Interview Transcripts (Priority: P1) 🎯 MVP

**Goal**: Persist complete interview transcripts to JSON files for later analysis

**Independent Test**: Complete an interview and verify JSON file exists at data/transcripts/{synth_id}_{timestamp}.json with correct schema

**Note**: US4 is implemented before US2/US3 because transcript saving is essential for MVP (P1 priority)

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T033 [P] [US4] Write tests for transcript creation in tests/unit/synth_lab/research/test_transcript.py (implemented in __main__ block)
- [x] T034 [P] [US4] Write tests for transcript file saving in tests/unit/synth_lab/research/test_transcript.py (implemented in __main__ block)
- [x] T035 [P] [US4] Write tests for transcript filename generation in tests/unit/synth_lab/research/test_transcript.py (implemented in __main__ block)

### Implementation for User Story 4

- [x] T036 [P] [US4] Implement create_transcript() function in src/synth_lab/research/transcript.py
- [x] T037 [P] [US4] Implement generate_transcript_filename() in src/synth_lab/research/transcript.py
- [x] T038 [US4] Implement save_transcript() function in src/synth_lab/research/transcript.py (depends on T036, T037)
- [x] T039 [US4] Integrate transcript saving into run_interview() in src/synth_lab/research/interview.py (handled by CLI)
- [x] T040 [US4] Handle partial transcript saving on error/interrupt in src/synth_lab/research/interview.py (session status tracked)
- [x] T041 [US4] Add transcript output path display to CLI in src/synth_lab/research/cli.py
- [x] T042 [US4] Run unit tests and verify US4 implementation passes

**Checkpoint**: User Stories 1 AND 4 complete - MVP delivered. Interviews run and transcripts are saved.

---

## Phase 5: User Story 2 - View Real-time Interview Progress (Priority: P2)

**Goal**: Display interview messages in real-time with visual distinction between speakers

**Independent Test**: Run interview and observe messages appearing sequentially with interviewer (blue) and synth (green) panels

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T043 [P] [US2] Write tests for message display formatting in tests/unit/synth_lab/research/test_interview.py (implemented in __main__ block)

### Implementation for User Story 2

- [x] T044 [P] [US2] Implement display_message() with Rich panels in src/synth_lab/research/interview.py
- [x] T045 [P] [US2] Implement display_interview_header() with synth info in src/synth_lab/research/interview.py
- [x] T046 [US2] Implement display_interview_summary() at completion in src/synth_lab/research/interview.py
- [x] T047 [US2] Integrate real-time display into conversation loop in src/synth_lab/research/interview.py
- [x] T048 [US2] Add progress spinner during LLM calls in src/synth_lab/research/interview.py
- [x] T049 [US2] Run unit tests and verify US2 implementation passes

**Checkpoint**: User Story 2 complete - interviews display beautifully in real-time

---

## Phase 6: User Story 3 - Use Custom Topic Guides (Priority: P2)

**Goal**: Allow researchers to provide custom topic guide files that shape the interview

**Independent Test**: Create two different topic guides, run interviews with each, verify conversations align with guide topics

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T050 [P] [US3] Write tests for topic guide loading in tests/unit/synth_lab/research/test_prompts.py
- [ ] T051 [P] [US3] Write tests for topic guide integration into interviewer prompt in tests/unit/synth_lab/research/test_prompts.py

### Implementation for User Story 3

- [ ] T052 [P] [US3] Implement load_topic_guide() function in src/synth_lab/research/prompts.py
- [ ] T053 [US3] Update build_interviewer_prompt() to incorporate topic guide in src/synth_lab/research/prompts.py
- [ ] T054 [US3] Add --topic-guide CLI parameter in src/synth_lab/research/cli.py
- [ ] T055 [US3] Add error handling for invalid topic guide path in src/synth_lab/research/cli.py
- [ ] T056 [US3] Create sample topic guide at data/topic_guides/ecommerce-mobile.md
- [ ] T057 [US3] Run unit tests and verify US3 implementation passes

**Checkpoint**: User Story 3 complete - custom topic guides work seamlessly

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T058 [P] Add comprehensive docstrings to all public functions in src/synth_lab/research/
- [ ] T059 [P] Add logging with loguru throughout src/synth_lab/research/
- [ ] T060 Update src/synth_lab/research/__init__.py with public API exports
- [ ] T061 [P] Run ruff linting and fix any issues in src/synth_lab/research/
- [ ] T062 Validate quickstart.md scenarios work end-to-end
- [ ] T063 Run complete test battery (unit + integration + contract tests)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 4 (Phase 4)**: Depends on US1 (needs interview to produce transcript)
- **User Story 2 (Phase 5)**: Depends on Foundational - can run parallel to US4
- **User Story 3 (Phase 6)**: Depends on Foundational - can run parallel to US2/US4
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 1 (Setup)
     │
     ▼
Phase 2 (Foundational) ──────────────────────────────────
     │                          │                        │
     ▼                          ▼                        ▼
Phase 3 (US1: Interview)   Phase 5 (US2: Display)   Phase 6 (US3: Topic Guide)
     │                          │                        │
     ▼                          │                        │
Phase 4 (US4: Transcript)       │                        │
     │                          │                        │
     ▼                          ▼                        ▼
     └──────────────────────────┴────────────────────────┘
                                │
                                ▼
                        Phase 7 (Polish)
```

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/Utilities before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
```bash
# Can run in parallel:
T003, T004, T005, T006
```

**Phase 2 (Foundational)**:
```bash
# Tests in parallel:
T007, T008

# Enums in parallel:
T009, T010
```

**Phase 3 (US1)**:
```bash
# Tests in parallel:
T016, T017, T018, T019

# Implementation - functions in parallel:
T021, T022, T023, T024
```

**Phase 4 (US4)**:
```bash
# Tests in parallel:
T033, T034, T035

# Implementation in parallel:
T036, T037
```

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Write tests for synth loading function in tests/unit/synth_lab/research/test_interview.py"
Task: "Write tests for interviewer system prompt generation in tests/unit/synth_lab/research/test_prompts.py"
Task: "Write tests for synth system prompt generation in tests/unit/synth_lab/research/test_prompts.py"
Task: "Write tests for interview loop logic in tests/unit/synth_lab/research/test_interview.py"

# Launch independent implementation functions together:
Task: "Implement load_synth() function in src/synth_lab/research/interview.py"
Task: "Implement validate_synth_exists() function in src/synth_lab/research/interview.py"
Task: "Implement build_interviewer_prompt() in src/synth_lab/research/prompts.py"
Task: "Implement build_synth_prompt() in src/synth_lab/research/prompts.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 4 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (basic interview execution)
4. Complete Phase 4: User Story 4 (transcript saving)
5. **STOP and VALIDATE**: Test MVP - interviews run and save transcripts
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Basic interviews work (no display, no persistence)
3. Add User Story 4 → Transcripts saved → **MVP Complete!**
4. Add User Story 2 → Beautiful real-time display
5. Add User Story 3 → Custom topic guides
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 → User Story 4 (MVP path)
   - Developer B: User Story 2 (display)
   - Developer C: User Story 3 (topic guides)
3. Stories complete and integrate independently

---

## Summary

| Phase | User Story | Tasks | Parallel Tasks |
|-------|------------|-------|----------------|
| 1 | Setup | 6 | 4 |
| 2 | Foundational | 9 | 4 |
| 3 | US1 - Basic Interview | 17 | 9 |
| 4 | US4 - Transcripts | 10 | 5 |
| 5 | US2 - Real-time Display | 7 | 3 |
| 6 | US3 - Topic Guides | 8 | 3 |
| 7 | Polish | 6 | 3 |
| **Total** | | **63** | **31** |

**MVP Scope**: Phases 1-4 (42 tasks) - Delivers working interviews with saved transcripts

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests mock LLM calls for fast execution (<5s total for unit tests)
