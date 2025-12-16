# Tasks: Synth Avatar Generation

**Input**: Design documents from `/specs/008-synth-avatar-generation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are INCLUDED in this feature following TDD/BDD constitution requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- All paths below use repository root as base

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create avatar directory structure at `data/synths/avatar/`
- [x] T002 [P] Add Pillow dependency to `pyproject.toml` for image processing
- [x] T003 [P] Add requests dependency to `pyproject.toml` for image downloads
- [x] T004 Update OpenAI SDK to version >=2.8.0 in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 [P] Create avatar prompt builder module at `src/synth_lab/gen_synth/avatar_prompt.py`
- [x] T006 [P] Create avatar image processing module at `src/synth_lab/gen_synth/avatar_image.py`
- [x] T007 Create avatar generation orchestrator module at `src/synth_lab/gen_synth/avatar_generator.py`
- [x] T008 Add environment variable validation for OPENAI_API_KEY in `src/synth_lab/gen_synth/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate avatars in batches during synth creation (Priority: P1) 🎯 MVP

**Goal**: Enable automatic generation of 9 avatars per API call during synth creation, with each avatar correctly mapped to a synth ID

**Independent Test**: Can be fully tested by running `gensynth -n 9 --avatar` and verifying that 9 avatar images are created in `data/synths/avatar/` directory, with each image correctly mapped to a synth ID.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T009 [P] [US1] Unit test for prompt construction with 9 synths in `tests/unit/synth_lab/gen_synth/test_avatar_prompt.py`
- [ ] T010 [P] [US1] Unit test for image splitting 1024x1024 into 9 parts in `tests/unit/synth_lab/gen_synth/test_avatar_image.py`
- [x] T011 [P] [US1] Unit test for synth validation (required fields check) in `tests/unit/synth_lab/gen_synth/test_avatar_generator.py`
- [x] T012 [US1] Integration test for full avatar generation flow with mocked OpenAI API in `tests/integration/test_avatar_generation.py`

### Implementation for User Story 1

- [x] T013 [P] [US1] Implement `build_prompt()` function in `src/synth_lab/gen_synth/avatar_prompt.py` - construct OpenAI prompt from 9 synth descriptions
- [x] T014 [P] [US1] Implement `assign_random_filters()` function in `src/synth_lab/gen_synth/avatar_prompt.py` - randomly assign visual filters to 9 avatars
- [x] T015 [US1] Implement `split_grid_image()` function in `src/synth_lab/gen_synth/avatar_image.py` - split 1024x1024 into 9 individual 341x341 images
- [x] T016 [US1] Implement `download_image()` function in `src/synth_lab/gen_synth/avatar_image.py` - download image from OpenAI URL to temp file
- [x] T017 [US1] Implement `validate_synth_for_avatar()` function in `src/synth_lab/gen_synth/avatar_generator.py` - check synth has required demographic fields
- [x] T018 [US1] Implement `generate_avatar_block()` function in `src/synth_lab/gen_synth/avatar_generator.py` - orchestrate single block generation (API call + split + save)
- [x] T019 [US1] Implement `generate_avatars()` main function in `src/synth_lab/gen_synth/avatar_generator.py` - process list of synths in blocks of 9
- [x] T020 [US1] Add error handling for OpenAI API errors (RateLimitError, APIConnectionError, AuthenticationError) in `src/synth_lab/gen_synth/avatar_generator.py`
- [x] T021 [US1] Add progress indication using rich library in `src/synth_lab/gen_synth/avatar_generator.py`
- [x] T022 [US1] Modify `gen_synth.py` to add `--avatar` flag to argparse configuration
- [x] T023 [US1] Integrate `generate_avatars()` call in `gen_synth.py` CLI main function when `--avatar` flag is present
- [x] T024 [US1] Add logging for avatar generation operations using loguru in `src/synth_lab/gen_synth/avatar_generator.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - can generate 9 avatars with `gensynth -n 9 --avatar`

---

## Phase 4: User Story 2 - Control number of avatar blocks to generate (Priority: P2)

**Goal**: Allow users to specify exact number of blocks (groups of 9 avatars) to generate via `-b` parameter

**Independent Test**: Can be fully tested by running `gensynth --avatar -b 3` and verifying that exactly 3 blocks (27 avatars total) are generated regardless of synth count.

### Tests for User Story 2 ⚠️

- [x] T025 [P] [US2] Unit test for block count calculation logic in `tests/unit/synth_lab/gen_synth/test_avatar_generator.py`
- [x] T026 [US2] Integration test for block parameter override in `tests/integration/test_avatar_generation.py`

### Implementation for User Story 2

- [x] T027 [US2] Add `-b` / `--blocks` parameter to argparse in `gen_synth.py`
- [x] T028 [US2] Implement `calculate_block_count()` function in `src/synth_lab/gen_synth/avatar_generator.py` - determine blocks from synth count or -b parameter
- [x] T029 [US2] Update `generate_avatars()` to accept optional blocks parameter and override default calculation in `src/synth_lab/gen_synth/avatar_generator.py`
- [x] T030 [US2] Add validation to ensure blocks parameter is positive integer in `src/synth_lab/gen_synth/avatar_generator.py`
- [x] T031 [US2] Update progress messages to show "block X of Y" when using -b parameter in `src/synth_lab/gen_synth/avatar_generator.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - can generate specific block counts

---

## Phase 5: User Story 3 - Generate avatars for existing synths (Priority: P3)

**Goal**: Enable generation of avatars for synths that were created without avatars, by loading existing synth data

**Independent Test**: Can be fully tested by creating synths without avatars, then running a command to generate avatars for specific synth IDs, and verifying the avatar files are created correctly.

### Tests for User Story 3 ⚠️

- [x] T032 [P] [US3] Unit test for loading existing synth data by ID in `tests/unit/synth_lab/gen_synth/test_avatar_generator.py`
- [x] T033 [US3] Integration test for avatar generation with existing synth IDs in `tests/integration/test_avatar_generation.py`

### Implementation for User Story 3

- [x] T034 [US3] Implement `load_synth_by_id()` function in `src/synth_lab/gen_synth/avatar_generator.py` - load synth data from synths.json by ID
- [x] T035 [US3] Implement `load_synths_by_ids()` function in `src/synth_lab/gen_synth/avatar_generator.py` - load multiple synths by ID list
- [x] T036 [US3] Add `--synth-ids` parameter to argparse in `gen_synth.py` - accept comma-separated list of synth IDs
- [x] T037 [US3] Update `generate_avatars()` to handle both new synths and existing synth IDs in `src/synth_lab/gen_synth/avatar_generator.py`
- [x] T038 [US3] Add file overwrite confirmation when regenerating existing avatars in `src/synth_lab/gen_synth/avatar_generator.py`
- [x] T039 [US3] Add validation to check synth IDs exist in synths.json before generation in `src/synth_lab/gen_synth/avatar_generator.py`

**Checkpoint**: All user stories should now be independently functional - can generate avatars for both new and existing synths

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T040 [P] Add validation blocks (`if __name__ == "__main__":`) to all new modules following synth-lab conventions
- [x] T041 [P] Add docstrings (Portuguese) to all functions in avatar modules
- [x] T042 [P] Create slow test battery with real OpenAI API calls marked with `@pytest.mark.slow` in `tests/integration/test_avatar_generation.py`
- [x] T043 Add retry logic with exponential backoff for rate limit errors in `src/synth_lab/gen_synth/avatar_generator.py` (MAX_RETRIES=3, BACKOFF_FACTOR=2)
- [x] T044 Add cleanup of temporary grid images after processing in `src/synth_lab/gen_synth/avatar_image.py`
- [x] T045 [P] Update main README.md with avatar generation feature overview
- [ ] T046 Run quickstart.md validation scenarios manually to verify all examples work
- [x] T047 Add code coverage check for avatar modules (achieved: 42% - acceptable for MVP, see docs/avatar_coverage_report.md)
  - **CRITICAL BUG FIXED**: Shortened prompts from 1570 to ~600 chars to meet OpenAI's 1000-char limit
  - Updated PROMPT_TEMPLATE and portrait descriptions for conciseness
  - Fixed integration test mocks (patch at call site, not definition site)
  - All tests passing: 21/21 unit tests ✓, 3/3 integration tests ✓
- [x] T048 [P] Security review: ensure API key is never logged or exposed in error messages
- [x] T049 Performance optimization: add 1-2 second delay between blocks to avoid rate limits (INTER_BLOCK_DELAY=1.5)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 but is independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Integrates with US1 but is independently testable

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Helper functions (prompt, image processing) before orchestrator
- Orchestrator before CLI integration
- Core implementation before error handling and logging
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002, T003)
- All Foundational tasks marked [P] can run in parallel (T005, T006)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for User Story 1 marked [P] can run in parallel (T009, T010, T011)
- Helper functions within US1 marked [P] can run in parallel (T013-T014, T015-T016)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for prompt construction with 9 synths in tests/unit/synth_lab/gen_synth/test_avatar_prompt.py"
Task: "Unit test for image splitting 1024x1024 into 9 parts in tests/unit/synth_lab/gen_synth/test_avatar_image.py"
Task: "Unit test for synth validation in tests/unit/synth_lab/gen_synth/test_avatar_generator.py"

# Launch parallel implementation tasks (different modules):
Task: "Implement build_prompt() function in src/synth_lab/gen_synth/avatar_prompt.py"
Task: "Implement assign_random_filters() function in src/synth_lab/gen_synth/avatar_prompt.py"

# Then:
Task: "Implement split_grid_image() function in src/synth_lab/gen_synth/avatar_image.py"
Task: "Implement download_image() function in src/synth_lab/gen_synth/avatar_image.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently with `gensynth -n 9 --avatar`
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (adds block control)
4. Add User Story 3 → Test independently → Deploy/Demo (adds existing synth support)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD requirement)
- Commit after each task or logical group (constitution requirement)
- Stop at any checkpoint to validate story independently
- All modules must follow synth-lab conventions (validation blocks, Portuguese docstrings)
- Fast battery uses mocked OpenAI responses, slow battery uses real API (marked with @pytest.mark.slow)
- Target module sizes: avatar_prompt.py < 200 lines, avatar_image.py < 200 lines, avatar_generator.py < 300 lines
