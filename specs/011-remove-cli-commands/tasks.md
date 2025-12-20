# Tasks: Remove CLI Commands & Fix Architecture

**Input**: Design documents from `/specs/011-remove-cli-commands/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: This is a refactoring feature - uses existing test suite to verify no regressions

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/synth_lab/`, `tests/` at repository root
- All file paths use absolute imports from `src/synth_lab/`

---

## Phase 1: Setup (Baseline Verification)

**Purpose**: Establish testing baseline before refactoring

- [X] T001 Run complete test suite and record baseline results (pytest tests/ --cov)
- [ ] T002 Verify all 17 API endpoints are functional (curl or API tests)
- [X] T003 [P] Document current CLI commands behavior (uv run synthlab --help)
- [X] T004 [P] Create backup of files to be modified (git stash or branch checkpoint)

---

## Phase 2: Foundational (Architecture Preparation)

**Purpose**: Prepare architecture for clean refactoring - MUST complete before user story work

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Rename src/synth_lab/research_prfaq/models.py to generation_models.py
- [X] T006 Update imports in src/synth_lab/research_prfaq/generator.py (use relative import from .generation_models)
- [X] T007 Update imports in src/synth_lab/research_prfaq/validator.py (use relative import from .generation_models)
- [X] T008 Rename src/synth_lab/topic_guides/models.py to internal_models.py
- [X] T009 Update imports in src/synth_lab/topic_guides/file_processor.py (use relative import from .internal_models)
- [X] T010 Update imports in src/synth_lab/topic_guides/summary_manager.py (use relative import from .internal_models)
- [X] T011 Run fast test battery to verify model renames don't break anything (pytest tests/ -k "model")
- [X] T012 Commit: "refactor: rename conflicting model files to avoid collisions"

**Checkpoint**: Foundation ready - model conflicts resolved, imports updated, tests passing

---

## Phase 3: User Story 1 - Simplificar Interface CLI Mantendo API Funcional (Priority: P1) 🎯 

**Goal**: Remove CLI commands while preserving API functionality - ensure CLI is simplified and API remains 100% functional

**Independent Test**:
1. `uv run synthlab --help` shows only `gensynth` command
2. Removed commands return "command not found" error
3. All 17 API endpoints return successful responses (GET /synths/list, POST /research/execute, etc.)

### Architecture Refactoring for User Story 1

**Substep 3A**: Move feature directories under services/

- [ ] T013 [US1] Create directory src/synth_lab/services/research_agentic/
- [ ] T014 [US1] Create directory src/synth_lab/services/research_prfaq/
- [ ] T015 [US1] Create directory src/synth_lab/services/topic_guides/
- [ ] T016 [P] [US1] Move src/synth_lab/research_agentic/runner.py to src/synth_lab/services/research_agentic/runner.py
- [ ] T017 [P] [US1] Move src/synth_lab/research_agentic/batch_runner.py to src/synth_lab/services/research_agentic/batch_runner.py
- [ ] T018 [P] [US1] Move src/synth_lab/research_agentic/agent_definitions.py to src/synth_lab/services/research_agentic/agent_definitions.py
- [ ] T019 [P] [US1] Move src/synth_lab/research_agentic/instructions.py to src/synth_lab/services/research_agentic/instructions.py
- [ ] T020 [P] [US1] Move src/synth_lab/research_agentic/tools.py to src/synth_lab/services/research_agentic/tools.py
- [ ] T021 [P] [US1] Move src/synth_lab/research_agentic/summarizer.py to src/synth_lab/services/research_agentic/summarizer.py
- [ ] T022 [P] [US1] Move src/synth_lab/research_agentic/tracing_bridge.py to src/synth_lab/services/research_agentic/tracing_bridge.py
- [ ] T023 [P] [US1] Move src/synth_lab/research_prfaq/generator.py to src/synth_lab/services/research_prfaq/generator.py
- [ ] T024 [P] [US1] Move src/synth_lab/research_prfaq/generation_models.py to src/synth_lab/services/research_prfaq/generation_models.py
- [ ] T025 [P] [US1] Move src/synth_lab/research_prfaq/prompts.py to src/synth_lab/services/research_prfaq/prompts.py
- [ ] T026 [P] [US1] Move src/synth_lab/research_prfaq/validator.py to src/synth_lab/services/research_prfaq/validator.py
- [ ] T027 [P] [US1] Move src/synth_lab/topic_guides/file_processor.py to src/synth_lab/services/topic_guides/file_processor.py
- [ ] T028 [P] [US1] Move src/synth_lab/topic_guides/summary_manager.py to src/synth_lab/services/topic_guides/summary_manager.py
- [ ] T029 [P] [US1] Move src/synth_lab/topic_guides/internal_models.py to src/synth_lab/services/topic_guides/internal_models.py
- [ ] T030 [US1] Create __init__.py files for new service subdirectories (research_agentic, research_prfaq, topic_guides)
- [ ] T031 [US1] Commit: "refactor: move feature modules under services/ for clean architecture"

**Substep 3B**: Update service imports to use new paths

- [ ] T032 [P] [US1] Update imports in src/synth_lab/services/prfaq_service.py (line 114: from .research_prfaq.generator import)
- [ ] T033 [P] [US1] Update imports in src/synth_lab/services/research_service.py (line 224: from .research_agentic.batch_runner import)
- [ ] T034 [P] [US1] Update imports in src/synth_lab/services/topic_service.py (use .topic_guides.file_processor, .topic_guides.summary_manager)
- [ ] T035 [US1] Update internal cross-references in moved files (research_agentic modules importing each other)
- [ ] T036 [US1] Update internal cross-references in moved files (research_prfaq modules importing each other)
- [ ] T037 [US1] Update internal cross-references in moved files (topic_guides modules importing each other)
- [ ] T038 [US1] Run fast test battery to verify import updates (pytest tests/ -k "service")
- [ ] T039 [US1] Commit: "refactor: update service imports to use new architecture paths"

**Substep 3C**: Delete CLI files

- [ ] T040 [P] [US1] Delete src/synth_lab/query/cli.py
- [ ] T041 [P] [US1] Delete src/synth_lab/topic_guides/cli.py
- [ ] T042 [P] [US1] Delete src/synth_lab/research_agentic/cli.py
- [ ] T043 [P] [US1] Delete src/synth_lab/research_prfaq/cli.py
- [ ] T044 [US1] Commit: "refactor: delete obsolete CLI command files"

**Substep 3D**: Remove CLI registrations from master dispatcher

- [ ] T045 [US1] Update src/synth_lab/__main__.py: remove import of query.cli
- [ ] T046 [US1] Update src/synth_lab/__main__.py: remove import of research_agentic.cli
- [ ] T047 [US1] Update src/synth_lab/__main__.py: remove import of topic_guides.cli
- [ ] T048 [US1] Update src/synth_lab/__main__.py: remove import of research_prfaq.cli
- [ ] T049 [US1] Update src/synth_lab/__main__.py: remove app.add_typer() calls for removed commands
- [ ] T050 [US1] Verify src/synth_lab/__main__.py only registers gensynth command
- [ ] T051 [US1] Commit: "refactor: remove CLI command registrations from main dispatcher"

**Substep 3E**: Clean up empty/obsolete directories

- [ ] T052 [US1] Remove src/synth_lab/research_agentic/ directory (now empty after moves)
- [ ] T053 [US1] Remove src/synth_lab/research_prfaq/ directory (now empty after moves)
- [ ] T054 [US1] Remove src/synth_lab/topic_guides/ directory (now empty after moves)
- [ ] T055 [US1] Verify src/synth_lab/query/ still contains database.py, formatter.py, validator.py (kept utilities)
- [ ] T056 [US1] Commit: "refactor: remove empty feature directories after reorganization"

**Substep 3F**: Verification

- [ ] T057 [US1] Run complete test suite (pytest tests/ --cov) - all tests must pass
- [ ] T058 [US1] Verify CLI help text: uv run synthlab --help shows only gensynth
- [ ] T059 [US1] Verify removed commands fail gracefully: uv run synthlab listsynth (should error)
- [ ] T060 [US1] Verify removed commands fail gracefully: uv run synthlab research (should error)
- [ ] T061 [US1] Verify removed commands fail gracefully: uv run synthlab topic-guide (should error)
- [ ] T062 [US1] Verify removed commands fail gracefully: uv run synthlab research-prfaq (should error)

**Checkpoint**: At this point, User Story 1 should be complete - CLI simplified, API functional, architecture clean

---

## Phase 4: User Story 2 - Serviços da API Continuam Funcionais (Priority: P1)

**Goal**: Verify API services remain 100% functional after refactoring

**Independent Test**: Execute all 17 API endpoints and verify correct responses

### API Verification for User Story 2

- [ ] T063 [P] [US2] Start API server: uvicorn synth_lab.api.main:app --reload
- [ ] T064 [P] [US2] Test GET /synths/list endpoint (should return 200 with synth data)
- [ ] T065 [P] [US2] Test GET /synths/{synth_id} endpoint (should return 200 with synth details)
- [ ] T066 [P] [US2] Test GET /synths/{synth_id}/avatar endpoint (should return 200 or 404)
- [ ] T067 [P] [US2] Test POST /research/execute endpoint (should return SSE stream)
- [ ] T068 [P] [US2] Test GET /research/executions endpoint (should return 200 with execution list)
- [ ] T069 [P] [US2] Test GET /research/executions/{exec_id} endpoint (should return 200 with execution details)
- [ ] T070 [P] [US2] Test GET /research/executions/{exec_id}/summary endpoint (should return 200 or 404)
- [ ] T071 [P] [US2] Test POST /topics endpoint (should create topic, return 201)
- [ ] T072 [P] [US2] Test GET /topics endpoint (should return 200 with topic list)
- [ ] T073 [P] [US2] Test GET /topics/{topic_id} endpoint (should return 200 with topic details)
- [ ] T074 [P] [US2] Test POST /prfaq/generate endpoint (should generate PR-FAQ, return 200)
- [ ] T075 [P] [US2] Test GET /prfaq endpoint (should return 200 with PR-FAQ list)
- [ ] T076 [P] [US2] Test GET /prfaq/{exec_id} endpoint (should return 200 with PR-FAQ metadata)
- [ ] T077 [P] [US2] Test GET /prfaq/{exec_id}/markdown endpoint (should return 200 with markdown content)
- [ ] T078 [US2] Verify API documentation accessible: http://localhost:8000/docs
- [ ] T079 [US2] Verify OpenAPI spec accessible: http://localhost:8000/openapi.json
- [ ] T080 [US2] Run service unit tests (pytest tests/unit/synth_lab/services/)
- [ ] T081 [US2] Run API integration tests (pytest tests/integration/)
- [ ] T082 [US2] Commit: "test: verify all API endpoints functional after refactoring"

**Checkpoint**: All 17 API endpoints verified functional, services working correctly

---

## Phase 5: User Story 3 - Limpeza de Código Obsoleto (Priority: P2)

**Goal**: Clean up obsolete code and verify no unused imports or references

**Independent Test**: Code search finds zero references to removed CLI modules, linter shows no warnings

### Code Cleanup for User Story 3

- [ ] T083 [P] [US3] Search codebase for imports from synth_lab.research_prfaq.models (should find 0)
- [ ] T084 [P] [US3] Search codebase for imports from synth_lab.topic_guides.models (should find 0)
- [ ] T085 [P] [US3] Search codebase for imports from synth_lab.research_agentic (excluding services.research_agentic) (should find 0)
- [ ] T086 [P] [US3] Search codebase for imports from synth_lab.research_prfaq (excluding services.research_prfaq) (should find 0)
- [ ] T087 [P] [US3] Search codebase for imports from synth_lab.topic_guides (excluding services.topic_guides) (should find 0)
- [ ] T088 [US3] Run linter: ruff check src/synth_lab/ (should have no warnings about unused imports)
- [ ] T089 [US3] Run type checker if available (verify no type errors from refactoring)
- [ ] T090 [US3] Remove unused imports from src/synth_lab/__main__.py (clean up)
- [ ] T091 [US3] Remove unused imports from service files if any found
- [ ] T092 [US3] Verify directory structure matches target architecture from plan.md
- [ ] T093 [US3] Commit: "refactor: final cleanup of obsolete imports and references"

**Checkpoint**: Codebase clean, no obsolete references, linter happy

---

## Phase 6: User Story 4 - Documentação Atualizada (Priority: P2)

**Goal**: Update all documentation to reflect new CLI and architecture

**Independent Test**: Documentation search finds zero mentions of removed commands, only shows gensynth + API

### Documentation Updates for User Story 4

- [ ] T094 [P] [US4] Update README.md: remove mentions of listsynth command
- [ ] T095 [P] [US4] Update README.md: remove mentions of research command
- [ ] T096 [P] [US4] Update README.md: remove mentions of research-batch command
- [ ] T097 [P] [US4] Update README.md: remove mentions of topic-guide command
- [ ] T098 [P] [US4] Update README.md: remove mentions of research-prfaq command
- [ ] T099 [P] [US4] Update README.md: add note directing users to REST API for removed functionality
- [ ] T100 [P] [US4] Update docs/cli.md: show only gensynth command documentation
- [ ] T101 [P] [US4] Update docs/cli.md: add migration guide section pointing to quickstart.md
- [ ] T102 [P] [US4] Update docs/arquitetura.md: reflect new services/ subdirectory structure
- [ ] T103 [P] [US4] Verify docs/api.md still accurate (should be unchanged)
- [ ] T104 [P] [US4] Add note to CHANGELOG.md about removed CLI commands (breaking change)
- [ ] T105 [US4] Search all docs/ for references to removed commands (grep -r "listsynth\|research-batch\|topic-guide\|research-prfaq" docs/)
- [ ] T106 [US4] Update any examples in docs/ to use API instead of CLI
- [ ] T107 [US4] Commit: "docs: update documentation to reflect CLI removal and new architecture"

**Checkpoint**: Documentation complete and accurate

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements affecting multiple user stories

- [ ] T108 [P] Run complete test suite one final time (pytest tests/ --cov)
- [ ] T109 [P] Verify test coverage hasn't decreased from baseline (compare with T001 results)
- [ ] T110 [P] Run quickstart.md validation: follow migration guide examples
- [ ] T111 [P] Test API server starts without errors: uvicorn synth_lab.api.main:app
- [ ] T112 [P] Verify gensynth command still works: uv run synthlab gensynth --help
- [ ] T113 Create final summary of changes: files moved, files deleted, lines of code removed
- [ ] T114 Review git log for proper commit messages and atomic commits
- [ ] T115 Commit: "chore: final polish and validation before PR"

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-6)**: All depend on Foundational phase completion
  - US1 (Phase 3): Can start after Foundational - No dependencies on other stories
  - US2 (Phase 4): Depends on US1 completion (needs refactored API to test)
  - US3 (Phase 5): Depends on US1 completion (needs refactored code to clean)
  - US4 (Phase 6): Can start after US1, ideally after US2 verification
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: BLOCKING - Must complete before US2, US3, US4
  - Implements the core refactoring (architecture + CLI removal)
- **User Story 2 (P1)**: Depends on US1
  - Verifies API still works after US1 changes
- **User Story 3 (P2)**: Depends on US1
  - Cleans up code after US1 refactoring
- **User Story 4 (P2)**: Can start after US1, ideally after US2
  - Documents the changes from US1

### Within Each User Story

**User Story 1** (critical path):
1. Architecture moves (T013-T031) → must complete before imports update
2. Import updates (T032-T039) → must complete before CLI deletion
3. CLI deletion (T040-T044) → must complete before registration removal
4. Registration removal (T045-T051) → must complete before cleanup
5. Directory cleanup (T052-T056) → must complete before verification
6. Verification (T057-T062) → confirms story complete

**User Story 2, 3, 4**: All parallelizable tasks marked [P]

### Parallel Opportunities

- **Phase 1** (Setup): All tasks can run in parallel (T001-T004)
- **Phase 2** (Foundational): Model renames sequential, but within each rename the import updates can be parallel
- **Phase 3** (US1):
  - Substep 3A: All file moves marked [P] can run together (T016-T029)
  - Substep 3B: All service import updates marked [P] can run together (T032-T034)
  - Substep 3C: All CLI file deletions marked [P] can run together (T040-T043)
- **Phase 4** (US2): All API endpoint tests marked [P] can run in parallel (T064-T077)
- **Phase 5** (US3): All code searches marked [P] can run in parallel (T083-T087)
- **Phase 6** (US4): All documentation updates marked [P] can run in parallel (T094-T104)
- **Phase 7** (Polish): All verification tasks marked [P] can run in parallel (T108-T112)

---

## Parallel Example: User Story 1 - Substep 3A (File Moves)

```bash
# Launch all file moves for research_agentic together:
Task T016: "Move src/synth_lab/research_agentic/runner.py to src/synth_lab/services/research_agentic/runner.py"
Task T017: "Move src/synth_lab/research_agentic/batch_runner.py to src/synth_lab/services/research_agentic/batch_runner.py"
Task T018: "Move src/synth_lab/research_agentic/agent_definitions.py to src/synth_lab/services/research_agentic/agent_definitions.py"
# ... (all 7 research_agentic files can move in parallel)

# Launch all file moves for research_prfaq together:
Task T023: "Move src/synth_lab/research_prfaq/generator.py to src/synth_lab/services/research_prfaq/generator.py"
Task T024: "Move src/synth_lab/research_prfaq/generation_models.py to src/synth_lab/services/research_prfaq/generation_models.py"
# ... (all 4 research_prfaq files can move in parallel)

# Launch all file moves for topic_guides together:
Task T027: "Move src/synth_lab/topic_guides/file_processor.py to src/synth_lab/services/topic_guides/file_processor.py"
# ... (all 3 topic_guides files can move in parallel)
```

---

## Parallel Example: User Story 2 (API Verification)

```bash
# Launch all API endpoint tests together:
Task T064: "Test GET /synths/list endpoint"
Task T065: "Test GET /synths/{synth_id} endpoint"
Task T066: "Test GET /synths/{synth_id}/avatar endpoint"
Task T067: "Test POST /research/execute endpoint"
# ... (all 14 endpoint tests can run in parallel)
```

---

## Implementation Strategy


1. Complete Phase 1: Setup (establish baseline)
2. Complete Phase 2: Foundational (rename models, update imports)
3. Complete Phase 3: User Story 1 (architecture refactoring + CLI removal)
4. Complete Phase 4: User Story 2 (API verification)
5. **VALIDATE**: All CLI commands removed, API 100% functional
6. Deploy/demo if ready (core objective achieved)

1. Complete Setup + Foundational → Architecture prepared
2. Add User Story 1 → Test CLI removal → CLI simplified ✓
3. Add User Story 2 → Test API endpoints → API verified ✓
4. **CHECKPOINT**: Core functionality complete (can deploy here)
5. Add User Story 3 → Code cleanup → Codebase clean ✓
6. Add User Story 4 → Documentation → Docs updated ✓
7. Polish phase → Final validation → Ready for PR ✓

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. **User Story 1 MUST be sequential** (architecture refactoring is blocking)
   - Developer A: Complete entire US1 (T013-T062)
3. Once US1 complete, parallel work possible:
   - Developer B: User Story 2 (API verification)
   - Developer C: User Story 3 (Code cleanup)
   - Developer D: User Story 4 (Documentation)
4. Stories complete independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- User Story 1 is BLOCKING - all other stories depend on it
- User Stories 2, 3, 4 can proceed in parallel after US1 completes
- Commit after each substep or logical group (following constitution)
- Run fast tests before each commit (< 5s)
- Run complete tests before PR (all tests must pass)
- Verify API functionality continuously throughout refactoring
- Avoid: breaking changes to API, losing service functionality, incomplete cleanup

---

## Summary

**Total Tasks**: 115 tasks
- Phase 1 (Setup): 4 tasks
- Phase 2 (Foundational): 8 tasks
- Phase 3 (US1): 50 tasks (architecture refactoring + CLI removal)
- Phase 4 (US2): 20 tasks (API verification)
- Phase 5 (US3): 11 tasks (code cleanup)
- Phase 6 (US4): 14 tasks (documentation)
- Phase 7 (Polish): 8 tasks

**Parallel Opportunities**:
- Phase 1: 2 parallel tasks
- Phase 3: 29 parallel tasks (file moves, imports, deletions, docs)
- Phase 4: 14 parallel tasks (API tests)
- Phase 5: 5 parallel tasks (code searches)
- Phase 6: 11 parallel tasks (documentation updates)
- Phase 7: 5 parallel tasks (final validation)

**Full Scope**: All phases = 115 tasks

**Independent Test Criteria**:
- US1: CLI shows only gensynth, removed commands error, API functional
- US2: All 17 endpoints return correct responses
- US3: Zero obsolete references, linter clean
- US4: Docs mention only gensynth + API, no removed commands
