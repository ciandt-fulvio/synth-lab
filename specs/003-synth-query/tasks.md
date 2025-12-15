# Tasks: Synth Data Query Tool

**Input**: Design documents from `/specs/003-synth-query/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included (TDD approach required by constitution)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/synth_lab/`, `tests/` at repository root
- All paths are absolute from repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependencies

- [x] T001 Add DuckDB, Typer, and Loguru dependencies to pyproject.toml
- [x] T002 [P] Create query module structure: src/synth_lab/query/__init__.py
- [x] T003 [P] Create test directories: tests/unit/synth_lab/query/ and tests/integration/synth_lab/query/
- [x] T004 [P] Create test fixtures directory: tests/fixtures/query/
- [x] T005 Install dependencies with uv: `uv pip install -e .[dev]`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and error classes that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 [P] Create QueryMode enum and error hierarchy in src/synth_lab/query/__init__.py
- [x] T007 [P] Create sample synth data fixture in tests/fixtures/query/sample_synths.json for testing
- [x] T008 [P] Create invalid JSON fixture in tests/fixtures/query/invalid_synths.json for error testing
- [x] T009 Create pytest conftest.py in tests/unit/synth_lab/query/ with shared fixtures
- [x] T010 Create pytest conftest.py in tests/integration/synth_lab/query/ with database fixtures

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic Data Listing (Priority: P1) 🎯 MVP

**Goal**: Users can view all synthetic data using simple `synthlab listsynth` command

**Independent Test**: Run `synthlab listsynth` without parameters and verify all synth records are displayed in a formatted table

### Tests for User Story 1 (TDD - Write These FIRST)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T011 [P] [US1] Unit test for QueryMode.BASIC in tests/unit/synth_lab/query/test_validator.py
- [x] T012 [P] [US1] Unit test for QueryRequest with BASIC mode in tests/unit/synth_lab/query/test_validator.py
- [x] T013 [P] [US1] Unit test for QueryRequest.to_sql() basic mode in tests/unit/synth_lab/query/test_validator.py
- [x] T014 [P] [US1] Unit test for DatabaseConfig creation and validation in tests/unit/synth_lab/query/test_database.py
- [x] T015 [P] [US1] Unit test for empty QueryResult formatting in tests/unit/synth_lab/query/test_formatter.py
- [x] T016 [P] [US1] Unit test for normal QueryResult formatting in tests/unit/synth_lab/query/test_formatter.py
- [x] T017 [US1] Integration test for database initialization from JSON in tests/integration/synth_lab/query/test_query_integration.py
- [x] T018 [US1] Integration test for basic query execution (all records) in tests/integration/synth_lab/query/test_query_integration.py
- [x] T019 [US1] Integration test for empty result handling in tests/integration/synth_lab/query/test_query_integration.py
- [x] T020 [US1] Integration test for missing data file error in tests/integration/synth_lab/query/test_query_integration.py

### Implementation for User Story 1

- [x] T021 [P] [US1] Implement QueryRequest dataclass with BASIC mode support in src/synth_lab/query/validator.py
- [x] T022 [P] [US1] Implement DatabaseConfig dataclass in src/synth_lab/query/database.py
- [x] T023 [US1] Implement initialize_database() function in src/synth_lab/query/database.py (depends on T022)
- [x] T024 [US1] Implement execute_query() function with error handling in src/synth_lab/query/database.py (depends on T023)
- [x] T025 [P] [US1] Implement format_results() function for Rich tables in src/synth_lab/query/formatter.py
- [x] T026 [US1] Implement display_results() function with empty result handling in src/synth_lab/query/formatter.py (depends on T025)
- [x] T027 [US1] Implement listsynth CLI command for BASIC mode in src/synth_lab/query/cli.py (depends on T024, T026)
- [x] T028 [US1] Integrate listsynth command into main CLI in src/synth_lab/__main__.py (depends on T027)
- [x] T029 [US1] Add module validation blocks (if __name__ == "__main__":) with real data to all modules
- [x] T030 [US1] Add logging statements for database operations and query execution
- [x] T031 [US1] Run all User Story 1 tests and verify they pass
- [x] T032 [US1] Manual test: Generate synth data and run `synthlab listsynth` to verify output
- [x] T033 [US1] Git commit for User Story 1 completion

**Checkpoint**: At this point, User Story 1 should be fully functional - users can list all synth data

---

## Phase 4: User Story 2 - Filtered Data Query (Priority: P2)

**Goal**: Users can filter synthetic data using `--where` parameter without writing full SQL

**Independent Test**: Run `synthlab listsynth --where "age > 30"` and verify only matching records are displayed

### Tests for User Story 2 (TDD - Write These FIRST)

- [ ] T034 [P] [US2] Unit test for QueryMode.WHERE in tests/unit/synth_lab/query/test_validator.py
- [ ] T035 [P] [US2] Unit test for QueryRequest with WHERE mode in tests/unit/synth_lab/query/test_validator.py
- [ ] T036 [P] [US2] Unit test for QueryRequest.to_sql() WHERE mode in tests/unit/synth_lab/query/test_validator.py
- [ ] T037 [P] [US2] Unit test for mutual exclusivity validation (--where vs --full-query) in tests/unit/synth_lab/query/test_validator.py
- [ ] T038 [P] [US2] Unit test for invalid WHERE clause error handling in tests/unit/synth_lab/query/test_database.py
- [ ] T039 [US2] Integration test for WHERE clause filtering in tests/integration/synth_lab/query/test_query_integration.py
- [ ] T040 [US2] Integration test for WHERE clause with no matching results in tests/integration/synth_lab/query/test_query_integration.py
- [ ] T041 [US2] Integration test for invalid WHERE syntax error in tests/integration/synth_lab/query/test_query_integration.py
- [ ] T042 [US2] Integration test for mutual exclusivity error (both --where and --full-query) in tests/integration/synth_lab/query/test_query_integration.py

### Implementation for User Story 2

- [ ] T043 [US2] Extend QueryRequest to support WHERE mode in src/synth_lab/query/validator.py
- [ ] T044 [US2] Implement mutual exclusivity validation in QueryRequest.__post_init__ in src/synth_lab/query/validator.py
- [ ] T045 [US2] Extend execute_query() to handle WHERE queries with error translation in src/synth_lab/query/database.py
- [ ] T046 [US2] Add --where parameter to listsynth CLI command in src/synth_lab/query/cli.py
- [ ] T047 [US2] Implement mutual exclusivity check in CLI (error before execution) in src/synth_lab/query/cli.py
- [ ] T048 [US2] Add logging for WHERE queries with clause details
- [ ] T049 [US2] Update module validation blocks to test WHERE mode
- [ ] T050 [US2] Run all User Story 2 tests and verify they pass
- [ ] T051 [US2] Manual test: Run `synthlab listsynth --where "age > 30"` and verify filtering works
- [ ] T052 [US2] Git commit for User Story 2 completion

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Custom SQL Query (Priority: P3)

**Goal**: Advanced users can execute custom SQL queries for complex analysis and aggregations

**Independent Test**: Run `synthlab listsynth --full-query "SELECT city, COUNT(*) as total FROM synths GROUP BY city"` and verify aggregated results

### Tests for User Story 3 (TDD - Write These FIRST)

- [ ] T053 [P] [US3] Unit test for QueryMode.FULL_QUERY in tests/unit/synth_lab/query/test_validator.py
- [ ] T054 [P] [US3] Unit test for QueryRequest with FULL_QUERY mode in tests/unit/synth_lab/query/test_validator.py
- [ ] T055 [P] [US3] Unit test for QueryRequest.to_sql() FULL_QUERY mode in tests/unit/synth_lab/query/test_validator.py
- [ ] T056 [P] [US3] Unit test for SELECT-only validation (reject INSERT/UPDATE/DELETE) in tests/unit/synth_lab/query/test_validator.py
- [ ] T057 [P] [US3] Unit test for QueryResult truncation (large result sets) in tests/unit/synth_lab/query/test_formatter.py
- [ ] T058 [US3] Integration test for aggregation query (GROUP BY) in tests/integration/synth_lab/query/test_query_integration.py
- [ ] T059 [US3] Integration test for custom SELECT with LIMIT in tests/integration/synth_lab/query/test_query_integration.py
- [ ] T060 [US3] Integration test for invalid SQL query error in tests/integration/synth_lab/query/test_query_integration.py
- [ ] T061 [US3] Integration test for non-SELECT query rejection (security) in tests/integration/synth_lab/query/test_query_integration.py
- [ ] T062 [US3] Integration test for result set truncation (>1000 rows) in tests/integration/synth_lab/query/test_query_integration.py

### Implementation for User Story 3

- [ ] T063 [US3] Extend QueryRequest to support FULL_QUERY mode in src/synth_lab/query/validator.py
- [ ] T064 [US3] Implement validate_query_security() to reject non-SELECT queries in src/synth_lab/query/validator.py
- [ ] T065 [US3] Integrate security validation into execute_query() in src/synth_lab/query/database.py
- [ ] T066 [US3] Implement QueryResult.from_duckdb_result() with truncation logic in src/synth_lab/query/database.py
- [ ] T067 [US3] Implement display_results_with_truncation_warning() in src/synth_lab/query/formatter.py
- [ ] T068 [US3] Add --full-query parameter to listsynth CLI command in src/synth_lab/query/cli.py
- [ ] T069 [US3] Add logging for full query execution with query text (truncated if long)
- [ ] T070 [US3] Update module validation blocks to test FULL_QUERY mode
- [ ] T071 [US3] Run all User Story 3 tests and verify they pass
- [ ] T072 [US3] Manual test: Run aggregation query and verify results
- [ ] T073 [US3] Manual test: Test non-SELECT query and verify rejection
- [ ] T074 [US3] Git commit for User Story 3 completion

**Checkpoint**: All three user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements affecting multiple user stories

- [ ] T075 [P] Add comprehensive docstrings (Google style) to all modules
- [ ] T076 [P] Run ruff format on all query modules
- [ ] T077 [P] Run ruff check and fix any linting issues
- [ ] T078 [P] Verify mypy strict mode passes for all modules
- [ ] T079 Run full pytest suite with coverage check (minimum 80% required)
- [ ] T080 Performance test: Verify query execution <2s for 10,000 records
- [ ] T081 Performance test: Verify table display <1s for 1,000 rows
- [ ] T082 Validate quickstart.md examples manually (all commands work)
- [ ] T083 Review all error messages for clarity and helpfulness
- [ ] T084 Review all logging output for completeness
- [ ] T085 Final integration test: Complete user workflow from data generation to querying
- [ ] T086 Git commit for polish phase completion
- [ ] T087 Final git commit with feature complete message

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion - BLOCKS all user stories
- **User Stories (Phases 3-5)**: All depend on Foundational (Phase 2) completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order: US1 → US2 → US3
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational - Extends US1 components but is independently testable
- **User Story 3 (P3)**: Can start after Foundational - Extends US1 and US2 components but is independently testable

### Within Each User Story

1. Write all tests FIRST (T011-T020 for US1, T034-T042 for US2, T053-T062 for US3)
2. Verify tests FAIL (Red in TDD cycle)
3. Implement code to make tests pass (Green in TDD cycle)
4. Refactor while keeping tests passing
5. Run all tests for story before marking complete
6. Manual validation before git commit

### Parallel Opportunities

- **Phase 1 (Setup)**: Tasks T002, T003, T004 can run in parallel
- **Phase 2 (Foundational)**: Tasks T006, T007, T008 can run in parallel
- **Within each user story**:
  - All test tasks marked [P] can run in parallel
  - Implementation tasks marked [P] can run in parallel (after tests written)
- **Across user stories**: Once Foundational completes, US1, US2, US3 can be worked on in parallel by different developers

---

## Parallel Example: User Story 1

```bash
# After Foundational phase completes, can parallelize:

# Terminal 1 - Unit tests (can write all in parallel)
# T011-T016 all in parallel since they test different functions

# Terminal 2 - Integration tests (can write all in parallel)
# T017-T020 all in parallel since they test different scenarios

# After tests are written and FAILING:

# Terminal 1 - Core data structures
# T021, T022 in parallel (validator.py and database.py - different files)

# Terminal 2 - Formatter
# T025 (formatter.py - different file from Terminal 1)

# Then sequential:
# T023 → T024 → T026 → T027 → T028 (due to dependencies)

# Finally polish in parallel:
# T029-T030 in parallel, then T031-T033 sequential
```

---

## Parallel Example: All User Stories

```bash
# After Foundational (Phase 2) completes:

# Team Member 1: Implements User Story 1
# Tasks T011-T033

# Team Member 2: Implements User Story 2 (in parallel with US1)
# Tasks T034-T052

# Team Member 3: Implements User Story 3 (in parallel with US1 and US2)
# Tasks T053-T074

# This assumes no blocking dependencies between stories
# Integration conflicts resolved at Polish phase
```

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**Include**: User Story 1 only (T001-T033)
- Basic data listing functionality
- Full database initialization and query execution
- Table formatting and display
- Error handling for missing data

**Value**: Users can immediately view their synthetic data with a simple command

**Timeline**: ~40 tasks including tests

### Incremental Delivery

1. **MVP Release**: User Story 1 (basic listing)
2. **V1.1 Release**: Add User Story 2 (WHERE clause filtering)
3. **V1.2 Release**: Add User Story 3 (custom SQL queries)
4. **V1.3 Release**: Polish phase improvements

### Testing Strategy

1. **TDD Required**: Constitution mandates tests before implementation
2. **Test Markers**:
   - `@pytest.mark.unit` for isolated tests (no database)
   - `@pytest.mark.integration` for real DuckDB tests
3. **Coverage Target**: Minimum 80% (enforced in pyproject.toml)
4. **Validation Blocks**: Each module must have working `if __name__ == "__main__":` validation

### Quality Gates

Before marking any user story complete:
1. All tests must pass (unit + integration)
2. Module validation blocks must work with real data
3. Coverage must be >80% for story modules
4. Manual end-to-end test must succeed
5. Git commit created with conventional format

---

## Task Count Summary

- **Total Tasks**: 87
- **Phase 1 (Setup)**: 5 tasks
- **Phase 2 (Foundational)**: 5 tasks
- **Phase 3 (US1)**: 23 tasks (10 tests + 13 implementation)
- **Phase 4 (US2)**: 19 tasks (9 tests + 10 implementation)
- **Phase 5 (US3)**: 22 tasks (10 tests + 12 implementation)
- **Phase 6 (Polish)**: 13 tasks

**Parallel Tasks**: 41 marked with [P]
**Sequential Tasks**: 46 (due to dependencies)

---

## Validation Checklist

Before marking feature as complete, verify:

- [ ] All 87 tasks completed
- [ ] All tests passing (pytest with >80% coverage)
- [ ] All module validation blocks working with real data
- [ ] ruff format and ruff check passing
- [ ] mypy strict mode passing
- [ ] quickstart.md examples validated manually
- [ ] Performance targets met (SC-001: <2s queries, SC-005: <1s display)
- [ ] All error messages clear and helpful (SC-004, SC-006)
- [ ] Git commits follow conventional format
- [ ] Feature branch ready for merge to main
