# Tasks: synth-lab REST API with Database Layer

**Input**: Design documents from `/specs/010-rest-api/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/openapi.yaml ✓

**Tests**: Tests are included as per constitution requirements (TDD/BDD).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure

- [X] T001 Create new directory structure: `src/synth_lab/api/`, `src/synth_lab/services/`, `src/synth_lab/repositories/`, `src/synth_lab/infrastructure/`, `src/synth_lab/models/`
- [X] T002 [P] Add FastAPI and uvicorn dependencies to `pyproject.toml`
- [X] T003 [P] Create `__init__.py` files for all new packages

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Infrastructure Layer

- [X] T004 Implement `src/synth_lab/infrastructure/config.py` with environment variables (DB path, log level, default model)
- [X] T005 [P] Implement `src/synth_lab/infrastructure/database.py` with SQLite connection manager (WAL mode, foreign keys, connection pooling)
- [X] T006 [P] Implement `src/synth_lab/infrastructure/llm_client.py` with centralized OpenAI client (retry logic via tenacity, timeout handling, model selection)

### Database Setup

- [X] T007 Create `scripts/migrate_to_sqlite.py` migration script per data-model.md schema
- [X] T008 Run migration to create `output/synthlab.db` with initial data from JSON sources

### Domain Models

- [X] T009 [P] Implement `src/synth_lab/models/pagination.py` with PaginationParams, PaginationMeta, PaginatedResponse
- [X] T010 [P] Implement `src/synth_lab/models/synth.py` with Synth, SynthSummary, SynthDemografia, SynthPsicografia models
- [X] T011 [P] Implement `src/synth_lab/models/topic.py` with TopicGuide, TopicGuideSummary, ScriptQuestion models
- [X] T012 [P] Implement `src/synth_lab/models/research.py` with ResearchExecution, Transcript, TranscriptSummary, ResearchExecuteRequest models
- [X] T013 [P] Implement `src/synth_lab/models/prfaq.py` with PRFAQSummary, PRFAQGenerateRequest models

### Error Handling

- [X] T014 Implement `src/synth_lab/services/errors.py` with domain exception hierarchy (SynthLabError, NotFoundError, ValidationError, etc.)

### Repository Base

- [X] T015 Implement `src/synth_lab/repositories/base.py` with BaseRepository class (pagination helpers, connection management)

### API Foundation

- [X] T016 Implement `src/synth_lab/api/main.py` with FastAPI app, lifespan events, CORS configuration
- [X] T017 [P] Implement `src/synth_lab/api/errors.py` with exception handlers mapping domain errors to HTTP responses
- [X] T018 [P] Implement `src/synth_lab/api/dependencies.py` with dependency injection functions for services

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Access Synth Data Programmatically 🎯 

**Goal**: External systems can query and retrieve synth persona data through REST API

**Independent Test**: `curl http://localhost:8000/synths/list` returns paginated synth list

### Tests for User Story 1

- [X] T019 [P] [US1] Unit test for SynthRepository in `tests/unit/repositories/test_synth_repository.py`
- [X] T020 [P] [US1] Unit test for SynthService in `tests/unit/services/test_synth_service.py`
- [X] T021 [P] [US1] Integration test for synth endpoints in `tests/integration/api/test_synths.py`

### Implementation for User Story 1

- [X] T022 [US1] Implement `src/synth_lab/repositories/synth_repository.py` with list, get_by_id, search, get_avatar_path methods
- [X] T023 [US1] Implement `src/synth_lab/services/synth_service.py` with list_synths, get_synth, search_synths methods
- [X] T024 [US1] Implement `src/synth_lab/api/routers/synths.py` with 5 endpoints:
  - `GET /synths/list` - paginated list with field selection
  - `GET /synths/{synth_id}` - full synth profile
  - `GET /synths/{synth_id}/avatar` - PNG image response
  - `POST /synths/search` - WHERE clause or full query search
  - `GET /synths/fields` - available field metadata
- [X] T025 [US1] Register synths router in `src/synth_lab/api/main.py`

**Checkpoint**: User Story 1 should be fully functional - test with `curl http://localhost:8000/synths/list`

---

## Phase 4: User Story 2 - Retrieve Research Execution Data

**Goal**: Users can access interview transcripts, research summaries, and execution metadata

**Independent Test**: `curl http://localhost:8000/research/{exec_id}` returns execution metadata

### Tests for User Story 2

- [X] T026 [P] [US2] Unit test for ResearchRepository in `tests/unit/repositories/test_research_repository.py`
- [X] T027 [P] [US2] Unit test for ResearchService (read operations) in `tests/unit/services/test_research_service.py`
- [X] T028 [P] [US2] Integration test for research read endpoints in `tests/integration/api/test_research_read.py`

### Implementation for User Story 2

- [X] T029 [US2] Implement `src/synth_lab/repositories/research_repository.py` with:
  - get_execution, list_executions methods
  - get_transcripts, get_transcript methods
  - get_summary_path method (for filesystem Markdown)
- [X] T030 [US2] Implement `src/synth_lab/services/research_service.py` (read operations only) with:
  - get_execution, list_executions methods
  - get_transcripts, get_transcript methods
  - get_summary method (returns Markdown content)
- [X] T031 [US2] Implement `src/synth_lab/api/routers/research.py` with read endpoints:
  - `GET /research/{exec_id}` - execution metadata
  - `GET /research/{exec_id}/transcripts` - transcript list
  - `GET /research/{exec_id}/transcripts/{synth_id}` - full transcript
  - `GET /research/{exec_id}/summary` - Markdown summary
- [X] T032 [US2] Register research router in `src/synth_lab/api/main.py`

**Checkpoint**: User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Browse Topic Guides

**Goal**: Users can discover and review available topic guides

**Independent Test**: `curl http://localhost:8000/topics/list` returns topic list

### Tests for User Story 3

- [X] T033 [P] [US3] Unit test for TopicRepository in `tests/unit/repositories/test_topic_repository.py`
- [X] T034 [P] [US3] Unit test for TopicService in `tests/unit/services/test_topic_service.py`
- [X] T035 [P] [US3] Integration test for topic endpoints in `tests/integration/api/test_topics.py`

### Implementation for User Story 3

- [X] T036 [US3] Implement `src/synth_lab/repositories/topic_repository.py` with:
  - list_topics (scan filesystem + DB cache)
  - get_by_name (load script.json, summary.md, file list)
  - get_executions_for_topic
- [X] T037 [US3] Implement `src/synth_lab/services/topic_service.py` with:
  - list_topics, get_topic, get_topic_executions methods
- [X] T038 [US3] Implement `src/synth_lab/api/routers/topics.py` with 3 endpoints:
  - `GET /topics/list` - paginated topic list
  - `GET /topics/{topic_name}` - full topic guide
  - `GET /topics/{topic_name}/research` - executions for topic
- [X] T039 [US3] Register topics router in `src/synth_lab/api/main.py`

**Checkpoint**: User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Access PR-FAQ Documents

**Goal**: Users can retrieve generated PR-FAQ documents and metadata

**Independent Test**: `curl http://localhost:8000/prfaq/list` returns PR-FAQ list

### Tests for User Story 4

- [X] T040 [P] [US4] Unit test for PRFAQRepository in `tests/unit/repositories/test_prfaq_repository.py`
- [X] T041 [P] [US4] Unit test for PRFAQService (read operations) in `tests/unit/services/test_prfaq_service.py`
- [X] T042 [P] [US4] Integration test for PR-FAQ read endpoints in `tests/integration/api/test_prfaq_read.py`

### Implementation for User Story 4

- [X] T043 [US4] Implement `src/synth_lab/repositories/prfaq_repository.py` with:
  - list_prfaqs, get_by_exec_id methods
  - get_markdown_path (for filesystem content)
- [X] T044 [US4] Implement `src/synth_lab/services/prfaq_service.py` (read operations only) with:
  - list_prfaqs, get_prfaq, get_markdown methods
- [X] T045 [US4] Implement `src/synth_lab/api/routers/prfaq.py` with read endpoints:
  - `GET /prfaq/list` - paginated PR-FAQ list
  - `GET /prfaq/{exec_id}/markdown` - Markdown content
- [X] T046 [US4] Register prfaq router in `src/synth_lab/api/main.py`

**Checkpoint**: All P1 and P2 user stories should work independently

---

## Phase 7: User Story 5 - Execute New Research

**Goal**: Users can trigger new research executions programmatically

**Independent Test**: `POST http://localhost:8000/research/execute` triggers research and returns exec_id

### Tests for User Story 5

- [X] T047 [P] [US5] Unit test for ResearchService (execute) in `tests/unit/services/test_research_execute.py` (mocked LLM)
- [X] T048 [P] [US5] Integration test for execute endpoint in `tests/integration/api/test_research_execute.py`

### Implementation for User Story 5

- [X] T049 [US5] Extract interview execution logic from `src/synth_lab/research_agentic/` to ResearchService
- [X] T050 [US5] Add execute_research method to `src/synth_lab/services/research_service.py`:
  - Validate topic exists
  - Select synths (by IDs or random count)
  - Execute interviews using LLMClient
  - Generate summary if requested
  - Save execution and transcripts to database
- [X] T051 [US5] Add `POST /research/execute` endpoint to `src/synth_lab/api/routers/research.py`
- [ ] T052 [US5] Refactor `src/synth_lab/research_agentic/cli.py` to use ResearchService (thin CLI wrapper)

**Checkpoint**: Research can be executed via API or CLI using same service

---

## Phase 8: User Story 6 - Generate PR-FAQ from Research

**Goal**: Users can trigger PR-FAQ generation from completed research

**Independent Test**: `POST http://localhost:8000/prfaq/generate` creates PR-FAQ from execution

### Tests for User Story 6

- [X] T053 [P] [US6] Unit test for PRFAQService (generate) in `tests/unit/services/test_prfaq_generate.py` (mocked LLM)
- [X] T054 [P] [US6] Integration test for generate endpoint in `tests/integration/api/test_prfaq_generate.py`

### Implementation for User Story 6

- [X] T055 [US6] Extract PR-FAQ generation logic from `src/synth_lab/research_prfaq/` to PRFAQService
- [X] T056 [US6] Add generate_prfaq method to `src/synth_lab/services/prfaq_service.py`:
  - Validate execution exists with summary
  - Generate PR-FAQ using LLMClient
  - Save metadata to database, content to filesystem
- [X] T057 [US6] Add `POST /prfaq/generate` endpoint to `src/synth_lab/api/routers/prfaq.py`
- [ ] T058 [US6] Refactor `src/synth_lab/research_prfaq/cli.py` to use PRFAQService (thin CLI wrapper)

**Checkpoint**: PR-FAQ generation can be triggered via API or CLI using same service

---

## Phase 9: User Story 7 - Retrieve Synth Avatars

**Goal**: UI applications can display synth avatar images

**Independent Test**: `GET http://localhost:8000/synths/{id}/avatar` returns PNG image

### Tests for User Story 7

- [X] T059 [P] [US7] Integration test for avatar endpoint in `tests/integration/api/test_synth_avatar.py`

### Implementation for User Story 7

- [X] T060 [US7] Add get_avatar method to SynthService that returns FileResponse
- [X] T061 [US7] Ensure avatar endpoint in synths router returns `Content-Type: image/png`
- [X] T062 [US7] Add 404 handling for synths without avatar files

**Checkpoint**: All 7 user stories should now be independently functional

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### CLI Refactoring (Backward Compatibility)

- [ ] T063 Verify existing CLI commands work after service layer migration:
  - `uv run python -m synth_lab research batch --topic X --synth-count N`
  - `uv run python -m synth_lab research-prfaq generate --exec-id X`
  - `uv run python -m synth_lab listsynth`
- [ ] T064 Update CLI commands to use services if not already done

### Documentation

- [X] T065 [P] Create startup script `scripts/start_api.sh` for convenience
- [ ] T066 [P] Validate quickstart.md examples work correctly
- [X] T067 [P] Verify OpenAPI spec matches implementation at `http://localhost:8000/docs`

### Performance Validation

- [X] T068 Verify SC-002: Metadata queries under 200ms
- [X] T069 Verify SC-003: Document retrieval under 1 second
- [ ] T070 Verify SC-004: 10 concurrent clients without degradation

### Security

- [X] T071 Verify SQL injection prevention in search endpoint (block INSERT, DELETE, UPDATE, DROP)
- [X] T072 Add input validation for all request parameters

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-9)**: All depend on Foundational phase completion
  - US1 (Synths) and US2 (Research Read) can proceed in parallel
  - US3 (Topics) and US4 (PR-FAQ Read) can proceed in parallel
  - US5 (Research Execute), US6 (PR-FAQ Generate), US7 (Avatars) can proceed in parallel
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

| Story | Depends On | Can Start After |
|-------|------------|-----------------|
| US1 (Synths) | Foundational | Phase 2 |
| US2 (Research Read) | Foundational | Phase 2 |
| US3 (Topics) | Foundational | Phase 2 |
| US4 (PR-FAQ Read) | Foundational | Phase 2 |
| US5 (Research Execute) | US1, US2, US3 | Phase 5 |
| US6 (PR-FAQ Generate) | US2, US4 | Phase 6 |
| US7 (Avatars) | US1 | Phase 3 |

### Within Each User Story

- Tests written FIRST and FAIL before implementation
- Repository before service
- Service before router
- Register router after implementation
- Verify independently before moving to next story

### Parallel Opportunities

- All models (T009-T013) can run in parallel
- All repository implementations can start in parallel after models
- Tests for each story can run in parallel
- P1 stories (US1, US2) can proceed in parallel
- P2 stories (US3, US4) can proceed in parallel
- P3 stories (US5, US6, US7) can proceed in parallel

---

## Implementation Strategy

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: US1 (Synths)
4. Complete Phase 4: US2 (Research Read)
5. **VALIDATE**: Test synth and research read endpoints
6. Deploy/demo if ready - basic data access API is functional


1. Add Phase 5: US3 (Topics)
2. Add Phase 6: US4 (PR-FAQ Read)
3. **VALIDATE**: All read operations work
4. API now provides complete read access to all data

1. Add Phase 7: US5 (Research Execute)
2. Add Phase 8: US6 (PR-FAQ Generate)
3. Add Phase 9: US7 (Avatars)
4. **VALIDATE**: All 17 endpoints work
5. Complete Phase 10: Polish

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Existing CLI commands must continue to work throughout migration
