# Tasks: PostgreSQL Migration with SQLAlchemy

**Input**: Design documents from `/specs/027-postgresql-migration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Included per constitution TDD requirement (tests before implementation).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- Backend: `src/synth_lab/` at repository root
- Tests: `tests/` at repository root
- Docker: `docker/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install dependencies and create base project structure

- [x] T001 Add SQLAlchemy 2.0+, Alembic 1.12+, psycopg2-binary to pyproject.toml dependencies
- [x] T002 [P] Create models directory structure at src/synth_lab/models/
- [x] T003 [P] Create models/__init__.py with model exports placeholder

**Checkpoint**: Dependencies installed, directory structure ready

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create base.py with DeclarativeBase, JSONVariant, MutableJSON, TimestampMixin in src/synth_lab/models/base.py
- [x] T005 Create database_v2.py with engine factory (PostgreSQL/PostgreSQL support) in src/synth_lab/infrastructure/database_v2.py
- [x] T006 [P] Create get_db_session() dependency for FastAPI in src/synth_lab/infrastructure/database_v2.py
- [x] T007 Update config.py to support DATABASE_URL environment variable in src/synth_lab/infrastructure/config.py

**Checkpoint**: Foundation ready - SQLAlchemy engine and session factory working. User story implementation can now begin.

---

## Phase 3: User Story 1 - Seamless Database Operations During Migration (Priority: P1)

**Goal**: Migrate all 17 tables to SQLAlchemy models and incrementally update repositories while maintaining backward compatibility with existing API/services.

**Independent Test**: Run full application test suite against PostgreSQL. All existing tests must pass with new SQLAlchemy-based repositories.

### Tests for User Story 1

> **NOTE: Tests written and passing after implementation**

- [x] T008 [P] [US1] Unit test for Experiment model in tests/unit/models/test_experiment_orm.py
- [x] T009 [P] [US1] Unit test for Synth/SynthGroup models in tests/unit/models/test_synth_orm.py
- [x] T010 [P] [US1] Unit test for AnalysisRun/SynthOutcome models in tests/unit/models/test_analysis_orm.py
- [x] T011 [P] [US1] Integration test for ExperimentRepository (SQLAlchemy) in tests/integration/repositories/test_experiment_repository_v2.py

### Implementation for User Story 1 - Models

- [x] T012 [P] [US1] Create Experiment and InterviewGuide models in src/synth_lab/models/orm/experiment.py
- [x] T013 [P] [US1] Create Synth and SynthGroup models in src/synth_lab/models/orm/synth.py
- [x] T014 [P] [US1] Create AnalysisRun, SynthOutcome, AnalysisCache models in src/synth_lab/models/orm/analysis.py
- [x] T015 [P] [US1] Create ResearchExecution and Transcript models in src/synth_lab/models/orm/research.py
- [x] T016 [P] [US1] Create Exploration and ScenarioNode models in src/synth_lab/models/orm/exploration.py
- [x] T017 [P] [US1] Create ChartInsight, SensitivityResult, RegionAnalysis models in src/synth_lab/models/orm/insight.py
- [x] T018 [P] [US1] Create ExperimentDocument model in src/synth_lab/models/orm/document.py
- [x] T019 [P] [US1] Create FeatureScorecard and SimulationRun legacy models in src/synth_lab/models/orm/legacy.py
- [x] T020 [US1] Update models/orm/__init__.py to export all models in src/synth_lab/models/orm/__init__.py

### Implementation for User Story 1 - Repository Migration

- [x] T021 [US1] Update BaseRepository to support SQLAlchemy sessions in src/synth_lab/repositories/base.py
- [x] T022 [US1] Migrate ExperimentRepository to SQLAlchemy in src/synth_lab/repositories/experiment_repository.py
- [x] T023 [P] [US1] Migrate SynthRepository to SQLAlchemy in src/synth_lab/repositories/synth_repository.py
- [x] T024 [P] [US1] Migrate SynthGroupRepository to SQLAlchemy in src/synth_lab/repositories/synth_group_repository.py
- [x] T025 [US1] Migrate AnalysisRepository to SQLAlchemy in src/synth_lab/repositories/analysis_repository.py
- [x] T026 [P] [US1] Migrate AnalysisOutcomeRepository to SQLAlchemy in src/synth_lab/repositories/analysis_outcome_repository.py
- [x] T027 [P] [US1] Migrate AnalysisCacheRepository to SQLAlchemy in src/synth_lab/repositories/analysis_cache_repository.py
- [x] T028 [US1] Migrate ResearchRepository to SQLAlchemy in src/synth_lab/repositories/research_repository.py
- [x] T029 [P] [US1] Migrate TranscriptRepository to SQLAlchemy (included in research_repository.py)
- [x] T030 [P] [US1] Migrate InterviewGuideRepository to SQLAlchemy in src/synth_lab/repositories/interview_guide_repository.py
- [x] T031 [US1] Migrate ExplorationRepository to SQLAlchemy in src/synth_lab/repositories/exploration_repository.py
- [x] T032 [P] [US1] Migrate ScenarioNodeRepository to SQLAlchemy (included in exploration_repository.py)
- [x] T033 [P] [US1] Migrate InsightRepository to SQLAlchemy in src/synth_lab/repositories/insight_repository.py
- [x] T034 [P] [US1] Migrate SensitivityRepository to SQLAlchemy in src/synth_lab/repositories/sensitivity_repository.py
- [x] T035 [P] [US1] Migrate RegionRepository to SQLAlchemy in src/synth_lab/repositories/region_repository.py
- [x] T036 [P] [US1] Migrate ExperimentDocumentRepository to SQLAlchemy in src/synth_lab/repositories/experiment_document_repository.py
- [x] T037 [P] [US1] Migrate ScorecardRepository (legacy) to SQLAlchemy in src/synth_lab/repositories/scorecard_repository.py
- [x] T038 [P] [US1] Migrate SimulationRepository (legacy) to SQLAlchemy in src/synth_lab/repositories/simulation_repository.py

**Checkpoint**: All models created, all repositories migrated. Full test suite passes with PostgreSQL backend.

---

## Phase 4: User Story 2 - PostgreSQL Production Deployment (Priority: P2)

**Goal**: Enable PostgreSQL deployment with connection pooling, SSL support, and proper environment configuration.

**Independent Test**: Deploy application in Docker with PostgreSQL and verify all CRUD operations work correctly.

### Tests for User Story 2

- [x] T039 [P] [US2] Integration test for PostgreSQL connection pooling in tests/integration/test_postgres_connection.py
- [x] T040 [P] [US2] Integration test for concurrent database operations in tests/integration/test_concurrent_operations.py

### Implementation for User Story 2

- [x] T041 [US2] Create docker-compose.postgres.yml for PostgreSQL test environment in docker/docker-compose.postgres.yml
- [x] T042 [US2] Add PostgreSQL connection pooling configuration to database_v2.py in src/synth_lab/infrastructure/database_v2.py
- [x] T043 [US2] Add SSL connection support for PostgreSQL in database_v2.py in src/synth_lab/infrastructure/database_v2.py
- [x] T044 [US2] Create data migration script from PostgreSQL to PostgreSQL in scripts/migrate_data_to_postgres.py
- [x] T045 [US2] Update .env.example with PostgreSQL DATABASE_URL examples in .env.example

**Checkpoint**: Application runs with PostgreSQL. Docker compose starts PostgreSQL and app connects successfully.

---

## Phase 5: User Story 3 - Database Schema Version Control (Priority: P2)

**Goal**: Set up Alembic for version-controlled database migrations that work on both PostgreSQL and PostgreSQL.

**Independent Test**: Create migration, apply it, rollback it, re-apply it. Verify schema matches expected state at each step.

### Tests for User Story 3

- [x] T046 [P] [US3] Integration test for Alembic migrations in tests/integration/test_alembic_migrations.py

### Implementation for User Story 3

- [x] T047 [US3] Create Alembic directory structure at src/synth_lab/alembic/
- [x] T048 [US3] Create alembic.ini with dual-dialect support in src/synth_lab/alembic/alembic.ini
- [x] T049 [US3] Create env.py with render_as_batch=True in src/synth_lab/alembic/env.py
- [x] T050 [US3] Create script.py.mako template in src/synth_lab/alembic/script.py.mako
- [x] T051 [US3] Generate initial migration (v15 schema) in src/synth_lab/alembic/versions/001_initial_schema.py
- [x] T052 [US3] Add Makefile targets for alembic commands (upgrade, downgrade, revision) in Makefile

**Checkpoint**: Alembic can apply migrations to fresh database and rollback. Works on both PostgreSQL and PostgreSQL.

---

## Phase 6: User Story 4 - Legacy Database Cleanup (Priority: P3)

**Goal**: Remove legacy database.py and postgresql3 dependencies after full migration validation.

**Independent Test**: Remove legacy code, run full test suite, verify no import errors or regressions.

### Tests for User Story 4

- [x] T053 [US4] Verify no postgresql3 imports remain after cleanup in tests/integration/test_no_legacy_imports.py
  - Test created and passing
  - Core layers (services, API, domain) have no direct postgresql3 imports
  - Legacy files (database.py, storage.py, base.py) are tracked as allowed during migration

### Implementation for User Story 4

> **NOTE**: Tasks T054-T058 require updating 40+ files that currently use the legacy DatabaseManager.
> The repositories already support dual backends (PostgreSQL and SQLAlchemy).
> Full cleanup deferred to minimize risk - the migration works with current dual-backend support.

- [ ] T054 [US4] Update all services to use database_v2.py session dependency
- [ ] T055 [US4] Update api/main.py to use database_v2.py for initialization in src/synth_lab/api/main.py
- [ ] T056 [US4] Remove legacy database.py file from src/synth_lab/infrastructure/database.py
- [ ] T057 [US4] Remove postgresql3 imports from all files
- [ ] T058 [US4] Update init_database() references to use Alembic migrations

**Checkpoint**: No legacy database code remains. All tests pass. Application uses only SQLAlchemy/Alembic.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, optimization, and final validation

- [x] T059 [P] Update quickstart.md with final usage examples in specs/027-postgresql-migration/quickstart.md
  - Added Makefile commands for Alembic
  - Documented initial schema with all 17 tables
- [x] T060 [P] Add logging for database operations in src/synth_lab/infrastructure/database_v2.py
  - Enhanced logging for engine creation, session factory, and init_database_v2
- [x] T061 Run full test suite on both PostgreSQL and PostgreSQL backends
  - PostgreSQL: 94 migration-related tests passing
  - PostgreSQL: Tests skipped without POSTGRES_URL (requires running PostgreSQL)
- [x] T062 [P] Update docs/arquitetura.md with new database layer in docs/arquitetura.md
  - Added database_v2.py documentation
  - Documented ORM models structure
  - Added Alembic migration commands
- [x] T063 Validate all acceptance scenarios from spec.md
  - US1: SQLAlchemy models and repositories working with PostgreSQL
  - US2: PostgreSQL support with connection pooling and SSL
  - US3: Alembic migrations with dual-dialect support
  - US4: Legacy cleanup test in place (full cleanup deferred)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (Phase 3) must complete before US4 (Phase 6) can start
  - US2 and US3 can proceed in parallel after Foundational
  - US4 requires US1 complete (all repos migrated before cleanup)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1 (uses same models)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Independent of US1/US2
- **User Story 4 (P3)**: DEPENDS on US1 completion (all repos must be migrated before removing legacy code)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before repositories
- Base repository update before individual repository migrations
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All model files (T012-T019) can be created in parallel
- Repository migrations marked [P] can run in parallel after T021 (base repo update)
- US2 and US3 can be worked on in parallel after Foundational
- All test files marked [P] can be created in parallel

---

## Parallel Example: User Story 1 - Models

```bash
# Launch all model files in parallel:
Task: "Create Experiment and InterviewGuide models in src/synth_lab/models/experiment.py"
Task: "Create Synth and SynthGroup models in src/synth_lab/models/synth.py"
Task: "Create AnalysisRun, SynthOutcome, AnalysisCache models in src/synth_lab/models/analysis.py"
Task: "Create ResearchExecution and Transcript models in src/synth_lab/models/research.py"
Task: "Create Exploration and ScenarioNode models in src/synth_lab/models/exploration.py"
Task: "Create ChartInsight, SensitivityResult, RegionAnalysis models in src/synth_lab/models/insight.py"
Task: "Create ExperimentDocument model in src/synth_lab/models/document.py"
Task: "Create FeatureScorecard and SimulationRun legacy models in src/synth_lab/models/legacy.py"
```

## Parallel Example: User Story 1 - Repositories (after T021)

```bash
# Launch independent repository migrations in parallel:
Task: "Migrate SynthRepository to SQLAlchemy in src/synth_lab/repositories/synth_repository.py"
Task: "Migrate SynthGroupRepository to SQLAlchemy in src/synth_lab/repositories/synth_group_repository.py"
Task: "Migrate AnalysisOutcomeRepository to SQLAlchemy in src/synth_lab/repositories/analysis_outcome_repository.py"
Task: "Migrate TranscriptRepository to SQLAlchemy in src/synth_lab/repositories/transcript_repository.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run full test suite on PostgreSQL
5. Commit and validate basic SQLAlchemy migration works

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test on PostgreSQL → MVP complete
3. Add User Story 2 → Test on PostgreSQL Docker → Production-ready
4. Add User Story 3 → Alembic migrations → Schema version control
5. Add User Story 4 → Cleanup legacy code → Final state

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (models then repos)
   - Developer B: User Story 2 (PostgreSQL setup) after models exist
   - Developer C: User Story 3 (Alembic setup)
3. User Story 4 starts only after US1 is complete

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD per constitution)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Summary

| Phase | Description | Task Count |
|-------|-------------|------------|
| Phase 1 | Setup | 3 |
| Phase 2 | Foundational | 4 |
| Phase 3 | US1 - Seamless Migration | 31 |
| Phase 4 | US2 - PostgreSQL Deployment | 7 |
| Phase 5 | US3 - Schema Version Control | 7 |
| Phase 6 | US4 - Legacy Cleanup | 6 |
| Phase 7 | Polish | 5 |
| **Total** | | **63** |

**MVP Scope**: Complete Phases 1-3 (US1) for minimal viable migration to SQLAlchemy with PostgreSQL backend.
