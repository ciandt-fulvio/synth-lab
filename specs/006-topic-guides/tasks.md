# Tasks: Topic Guides with Multi-Modal Context

**Input**: Design documents from `/specs/006-topic-guides/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-interface.md

**Tests**: Included - TDD approach required per Constitution Principle I

**Organization**: Tasks grouped by user story to enable independent implementation and testing

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/synth_lab/topic_guides/`, `tests/topic_guides/`
- Paths use absolute references from repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and module structure

- [x] T001 Create topic_guides module directory at src/synth_lab/topic_guides/ with __init__.py
- [x] T002 Create test directory structure at tests/topic_guides/ with unit/, integration/, contract/ subdirectories
- [x] T003 [P] Add pdfplumber>=0.11.0 and tenacity>=8.0.0 to pyproject.toml dependencies
- [x] T004 [P] Install new dependencies with uv sync
- [x] T005 [P] Create data/topic_guides/ directory with .gitkeep file

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and utilities that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 [P] Create FileType enum in src/synth_lab/topic_guides/models.py with PNG, JPEG, PDF, MD, TXT values
- [x] T007 [P] Create FileDescription dataclass in src/synth_lab/topic_guides/models.py with filename, content_hash, description, generated_at, is_placeholder fields
- [x] T008 [P] Create ContextFile dataclass in src/synth_lab/topic_guides/models.py with filename, path, file_type, size_bytes, content_hash, is_documented fields
- [x] T009 Create SummaryFile dataclass in src/synth_lab/topic_guides/models.py with path, context_description, file_descriptions fields (depends on T007)
- [x] T010 Create TopicGuide dataclass in src/synth_lab/topic_guides/models.py with name, path, summary_file, files, created_at, updated_at fields (depends on T008, T009)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Create New Topic Guide Directory (Priority: P1) 🎯 MVP

**Goal**: Enable researchers to create structured topic guide directories with initialized summary.md files

**Independent Test**: Run CLI command with new topic guide name and verify directory + summary.md are created correctly

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T011 [P] [US1] Create test_cli_create in tests/topic_guides/contract/test_cli_interface.py for create command contract
- [x] T012 [P] [US1] Create test_directory_creation in tests/topic_guides/integration/test_topic_guide_creation.py for full directory creation workflow
- [x] T013 [P] [US1] Create test_summary_file_initialization in tests/topic_guides/unit/test_summary_manager.py for summary.md generation logic

### Implementation for User Story 1

- [x] T014 [P] [US1] Implement detect_file_type function in src/synth_lab/topic_guides/file_processor.py for detecting FileType from file extension
- [x] T015 [P] [US1] Implement compute_file_hash function in src/synth_lab/topic_guides/file_processor.py for MD5 hash computation
- [x] T016 [US1] Implement create_initial_summary function in src/synth_lab/topic_guides/summary_manager.py to generate summary.md with template content
- [x] T017 [US1] Implement parse_summary function in src/synth_lab/topic_guides/summary_manager.py to read and parse existing summary.md files
- [x] T018 [US1] Implement write_summary function in src/synth_lab/topic_guides/summary_manager.py to serialize SummaryFile to disk
- [x] T019 [US1] Create Typer app and create_topic_guide command in src/synth_lab/topic_guides/cli.py with --name parameter
- [x] T020 [US1] Implement topic guide directory creation logic in cli.py create command: check existence, create directories, initialize summary.md
- [x] T021 [US1] Add input validation for topic guide name in cli.py (no special characters /\:*?"<>|)
- [x] T022 [US1] Add error handling for directory creation failures (permissions, disk full) in cli.py
- [x] T023 [US1] Add logging with loguru for create operations in cli.py
- [x] T024 [US1] Register topic-guide subcommand group in src/synth_lab/__main__.py

**Checkpoint**: User Story 1 complete - users can create topic guides via CLI

---

## Phase 4: User Story 2 - Auto-Document Existing Files (Priority: P2)

**Goal**: Automatically generate AI-powered descriptions for files in topic guide directories

**Independent Test**: Create topic guide, add files (PNG, PDF, TXT), run update command, verify AI descriptions in summary.md

### Tests for User Story 2

- [ ] T025 [P] [US2] Create test_cli_update in tests/topic_guides/contract/test_cli_interface.py for update command contract
- [ ] T026 [P] [US2] Create test_file_scanning in tests/topic_guides/unit/test_file_processor.py for directory scanning and filtering logic
- [ ] T027 [P] [US2] Create test_hash_detection in tests/topic_guides/unit/test_file_processor.py for hash-based change detection
- [ ] T028 [P] [US2] Create test_llm_integration in tests/topic_guides/integration/test_llm_descriptions.py for OpenAI API calls (with mocked responses)
- [ ] T029 [P] [US2] Create test_error_handling in tests/topic_guides/integration/test_error_scenarios.py for API failures, unsupported files, corrupted files

### Implementation for User Story 2

- [ ] T030 [P] [US2] Implement scan_directory function in src/synth_lab/topic_guides/file_processor.py to list all files excluding summary.md
- [ ] T031 [P] [US2] Implement is_supported_type function in src/synth_lab/topic_guides/file_processor.py to check if file type is in supported list
- [ ] T032 [P] [US2] Implement extract_pdf_text function in src/synth_lab/topic_guides/file_processor.py using pdfplumber for PDF preview extraction
- [ ] T033 [P] [US2] Implement encode_image_for_vision function in src/synth_lab/topic_guides/file_processor.py for base64 encoding PNG/JPEG files
- [ ] T034 [US2] Implement call_openai_api function in src/synth_lab/topic_guides/file_processor.py with tenacity retry logic and exponential backoff
- [ ] T035 [US2] Implement generate_file_description function in src/synth_lab/topic_guides/file_processor.py that routes to appropriate LLM prompt based on file type
- [ ] T036 [US2] Implement add_file_description function in src/synth_lab/topic_guides/summary_manager.py to append new descriptions to ## FILE DESCRIPTION section
- [ ] T037 [US2] Implement has_file function in src/synth_lab/topic_guides/summary_manager.py to check if file with matching hash exists
- [ ] T038 [US2] Create update_topic_guide command in src/synth_lab/topic_guides/cli.py with --name and --force parameters
- [ ] T039 [US2] Implement file processing loop in cli.py update command: scan directory, filter unsupported, compute hashes, skip unchanged
- [ ] T040 [US2] Implement LLM description generation in cli.py update command: call generate_file_description, handle API failures
- [ ] T041 [US2] Implement error handling for unsupported files: log warning with list of skipped files
- [ ] T042 [US2] Implement error handling for corrupted files: skip silently and continue processing
- [ ] T043 [US2] Implement error handling for LLM API failures: add placeholder entry with "API failure - manual documentation needed"
- [ ] T044 [US2] Implement missing FILE DESCRIPTION section handling: auto-append section if missing
- [ ] T045 [US2] Add progress indicators and summary output (X files documented, Y skipped, Z failed)
- [ ] T046 [US2] Add logging with loguru for all update operations

**Checkpoint**: User Story 2 complete - users can auto-generate file descriptions

---

## Phase 5: User Story 3 - Access Context During Interviews (Priority: P3)

**Goal**: Enable synths to access topic guide materials during UX research interviews

**Independent Test**: Conduct synth interview with topic guide parameter and verify synth responses reference materials

### Tests for User Story 3

- [ ] T047 [P] [US3] Create test_topic_guide_loading in tests/research/integration/test_interview_with_context.py for loading topic guide in interview
- [ ] T048 [P] [US3] Create test_context_integration in tests/research/integration/test_interview_with_context.py for verifying materials in LLM context
- [ ] T049 [P] [US3] Create test_interview_cli_with_topic_guide in tests/topic_guides/contract/test_cli_interface.py for --topic-guide parameter

### Implementation for User Story 3

- [ ] T050 [P] [US3] Implement load_topic_guide_context function in src/synth_lab/topic_guides/summary_manager.py to parse summary.md and return file descriptions list
- [ ] T051 [US3] Add topic_guide optional parameter to conduct_interview function in src/synth_lab/research/interview.py
- [ ] T052 [US3] Implement topic guide loading logic in src/synth_lab/research/interview.py: check if parameter provided, load context
- [ ] T053 [US3] Implement context integration in src/synth_lab/research/interview.py: add "Available Context Materials" section to LLM prompt with file descriptions
- [ ] T054 [US3] Add --topic-guide parameter to research interview CLI command in src/synth_lab/research/cli.py
- [ ] T055 [US3] Add error handling for missing topic guides: log warning if guide not found, continue interview without context
- [ ] T056 [US3] Add logging for topic guide integration in interview initialization

**Checkpoint**: All user stories complete - full feature functional

---

## Phase 6: Additional CLI Commands & Polish

**Purpose**: Complete CLI interface and cross-cutting improvements

- [ ] T057 [P] Create list_topic_guides command in src/synth_lab/topic_guides/cli.py with --verbose option
- [ ] T058 [P] Create show_topic_guide command in src/synth_lab/topic_guides/cli.py with --name parameter to display guide details
- [ ] T059 [P] Implement list logic in cli.py: scan data/topic_guides/, display names, optionally show file counts
- [ ] T060 [P] Implement show logic in cli.py: load summary.md, display context and file descriptions with formatting
- [ ] T061 [P] Add comprehensive unit tests for all utility functions in tests/topic_guides/unit/
- [ ] T062 [P] Create example topic guide for testing and quickstart validation in data/topic_guides/example-guide/
- [ ] T063 [P] Validate quickstart.md examples work correctly with implemented CLI commands
- [ ] T064 [P] Add rich console formatting for CLI output (success ✓, warning ⚠, error ✗ symbols)
- [ ] T065 [P] Add environment variable check for OPENAI_API_KEY in cli.py with helpful error message
- [ ] T066 Code review and refactoring: ensure functions are <30 lines, files <500 lines
- [ ] T067 Performance optimization: profile hash computation and LLM calls to ensure performance targets met
- [ ] T068 Security review: validate file path handling, prevent directory traversal
- [ ] T069 [P] Update CLAUDE.md with topic_guides module documentation
- [ ] T070 [P] Run ruff linter and fix any violations
- [ ] T071 Run full test suite and ensure 85% coverage minimum
- [ ] T072 Manual testing: validate all acceptance scenarios from spec.md work correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001-T005) - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (T006-T010)
- **User Story 2 (Phase 4)**: Depends on Foundational (T006-T010) - Can start in parallel with US1 if resources available
- **User Story 3 (Phase 5)**: Depends on Foundational (T006-T010) AND User Story 2 (T025-T046) for summary.md parsing
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent - only depends on Foundational phase
- **User Story 2 (P2)**: Independent - only depends on Foundational phase (uses summary manager from US1 but can implement in parallel)
- **User Story 3 (P3)**: Depends on User Story 2 (needs summary.md parsing and file descriptions to exist)

### Within Each User Story

**TDD Flow (Constitution Requirement)**:
1. Write tests FIRST (all test tasks marked [P] within story)
2. Verify tests FAIL
3. Implement features to make tests pass
4. Refactor if needed
5. Verify tests PASS

**Implementation Order**:
- Tests before implementation (TDD)
- Utility functions before CLI commands
- Core logic before error handling
- Integration before polish

### Parallel Opportunities

**Setup Phase (Phase 1)**:
- T003, T004, T005 can run in parallel

**Foundational Phase (Phase 2)**:
- T006, T007, T008 can run in parallel (independent dataclasses)

**User Story 1 Tests**:
- T011, T012, T013 can run in parallel (different test files)

**User Story 1 Implementation**:
- T014, T015 can run in parallel (independent utility functions)

**User Story 2 Tests**:
- T025, T026, T027, T028, T029 can run in parallel (different test files)

**User Story 2 Implementation**:
- T030, T031, T032, T033 can run in parallel (independent utility functions)

**User Story 3 Tests**:
- T047, T048, T049 can run in parallel (different test files)

**User Story 3 Implementation**:
- T050, T054 can run in parallel (different modules)

**Polish Phase**:
- T057, T058, T061, T062, T063, T064, T065, T069, T070 can run in parallel

**Multiple User Stories**:
- After Foundational phase, US1 and US2 can be developed in parallel by different team members
- US3 must wait for US2 to complete

---

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together (TDD - write these first):
Task T025: "Contract test for update command in tests/topic_guides/contract/test_cli_interface.py"
Task T026: "Unit test for file scanning in tests/topic_guides/unit/test_file_processor.py"
Task T027: "Unit test for hash detection in tests/topic_guides/unit/test_file_processor.py"
Task T028: "Integration test for LLM API in tests/topic_guides/integration/test_llm_descriptions.py"
Task T029: "Integration test for error handling in tests/topic_guides/integration/test_error_scenarios.py"

# After tests are written and failing, launch parallel implementation tasks:
Task T030: "Implement scan_directory in src/synth_lab/topic_guides/file_processor.py"
Task T031: "Implement is_supported_type in src/synth_lab/topic_guides/file_processor.py"
Task T032: "Implement extract_pdf_text in src/synth_lab/topic_guides/file_processor.py"
Task T033: "Implement encode_image_for_vision in src/synth_lab/topic_guides/file_processor.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T010) - **CRITICAL**
3. Complete Phase 3: User Story 1 (T011-T024)
   - Write tests T011-T013 FIRST
   - Verify tests FAIL
   - Implement T014-T024
   - Verify tests PASS
4. **STOP and VALIDATE**: Test create command manually
5. Ready for basic use - researchers can create topic guide directories

### Incremental Delivery

1. **Foundation** (T001-T010): Setup + models ready
2. **MVP** (T011-T024): User Story 1 → Create topic guides ✅
3. **Core Feature** (T025-T046): User Story 2 → Auto-document files ✅✅
4. **Full Feature** (T047-T056): User Story 3 → Synth integration ✅✅✅
5. **Polish** (T057-T072): Complete CLI + optimization

Each increment adds value without breaking previous functionality.

### Parallel Team Strategy

With 2 developers after Foundational phase:
- **Developer A**: User Story 1 (T011-T024) - Create topic guides
- **Developer B**: User Story 2 (T025-T046) - File documentation

With 3 developers:
- **Developer A**: User Story 1 (T011-T024)
- **Developer B**: User Story 2 (T025-T046)
- **Developer C**: Polish tasks (T057-T060) + documentation

User Story 3 starts after US2 completes.

---

## Notes

- **[P] tasks**: Different files, no dependencies - can run in parallel
- **[Story] labels**: Map tasks to user stories for traceability (US1, US2, US3)
- **TDD Required**: Write tests FIRST per Constitution Principle I
- **Fast Battery**: Mock file I/O and LLM calls - should run in <5 seconds
- **Slow Battery**: Real file operations and API calls (with VCR.py recording)
- **Commit Frequently**: After each task or logical group per Constitution Principle IV
- **Validation Points**: Each user story has checkpoint to validate independently
- **File Size Limits**: Keep files <500 lines per Constitution Principle V
- **Coverage Target**: 85% minimum for new code

---

## Task Summary

- **Total Tasks**: 72
- **Setup**: 5 tasks
- **Foundational**: 5 tasks
- **User Story 1**: 14 tasks (3 tests + 11 implementation)
- **User Story 2**: 22 tasks (5 tests + 17 implementation)
- **User Story 3**: 10 tasks (3 tests + 7 implementation)
- **Polish**: 16 tasks
- **Parallel Opportunities**: 42 tasks marked [P]
- **Independent Stories**: US1 and US2 (US3 depends on US2)
- **Suggested MVP**: Phase 1 + Phase 2 + Phase 3 (User Story 1 only) = 24 tasks
