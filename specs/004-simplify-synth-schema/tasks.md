# Tasks: Simplify Synth Schema

**Input**: Design documents from `/specs/004-simplify-synth-schema/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are included per constitution requirement (TDD/BDD mandatory). Tests MUST be written FIRST and FAIL before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/synth_lab/`, `tests/` at repository root
- All paths shown use single project structure per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and schema version management

- [x] T001 Archive current schema v1.0.0 to data/schemas/synth-schema-v1.json for reference
- [x] T002 Create backup of existing synth data in data/synths/ directory (N/A - directory empty)
- [x] T003 [P] Update project documentation in README.md to reference schema v2.0.0

**Checkpoint**: Schema versioning prepared, backups in place

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Review and understand existing schema structure in data/schemas/synth-schema-cleaned.json
- [x] T005 Review existing synth generation modules in src/synth_lab/gen_synth/ directory
- [x] T006 [P] Review existing validation logic in src/synth_lab/gen_synth/validation.py
- [x] T007 [P] Review existing bias generation in src/synth_lab/gen_synth/biases.py

**Checkpoint**: Foundation understood - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Simplified Schema for Faster Generation (Priority: P1) 🎯 MVP

**Goal**: Remove 5 redundant psychographic and behavioral fields from schema to reduce complexity and improve generation performance by ~10%

**Independent Test**: Generate a synth with v2.0.0 schema and verify removed fields are absent, schema file is ≤15KB, and validation rejects synths with removed fields

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T008 [P] [US1] Unit test for schema field removal in tests/unit/test_schema_v2.py
- [x] T009 [P] [US1] Unit test for schema version validation in tests/unit/test_schema_version.py
- [x] T010 [P] [US1] Contract test for v2 schema structure in tests/contract/test_schema_contract.py
- [x] T011 [P] [US1] Integration test for synth generation without removed fields in tests/integration/test_schema_validation.py

### Implementation for User Story 1

- [ ] T012 [US1] Update schema $id from v1.0.0 to v2.0.0 in data/schemas/synth-schema-cleaned.json
- [ ] T013 [US1] Update version pattern from ^1\\.0\\.0$ to ^2\\.0\\.0$ in data/schemas/synth-schema-cleaned.json
- [ ] T014 [US1] Remove psicografia.valores field definition from data/schemas/synth-schema-cleaned.json
- [ ] T015 [US1] Remove psicografia.hobbies field definition from data/schemas/synth-schema-cleaned.json
- [ ] T016 [US1] Remove psicografia.estilo_vida field definition from data/schemas/synth-schema-cleaned.json
- [ ] T017 [US1] Remove comportamento.uso_tecnologia field definition from data/schemas/synth-schema-cleaned.json
- [ ] T018 [US1] Remove comportamento.comportamento_compra field definition from data/schemas/synth-schema-cleaned.json
- [ ] T019 [US1] Set additionalProperties: false on psicografia object in data/schemas/synth-schema-cleaned.json
- [ ] T020 [US1] Set additionalProperties: false on comportamento object in data/schemas/synth-schema-cleaned.json
- [ ] T021 [US1] Remove valores generation logic from src/synth_lab/gen_synth/psychographics.py
- [ ] T022 [US1] Remove hobbies generation logic from src/synth_lab/gen_synth/psychographics.py
- [ ] T023 [US1] Remove estilo_vida generation logic from src/synth_lab/gen_synth/psychographics.py
- [ ] T024 [US1] Remove uso_tecnologia generation logic from src/synth_lab/gen_synth/behavior.py
- [ ] T025 [US1] Remove comportamento_compra generation logic from src/synth_lab/gen_synth/behavior.py
- [ ] T026 [US1] Update synth_builder.py to skip removed fields in src/synth_lab/gen_synth/synth_builder.py
- [ ] T027 [US1] Verify schema file size ≤15KB (target: -17% from ~18KB)
- [ ] T028 [US1] Run all US1 tests and verify they pass

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - schema simplified, generation updated, tests passing

---

## Phase 4: User Story 2 - Coherent Bias-Personality Relationships (Priority: P1)

**Goal**: Implement personality-bias coherence rules so cognitive biases align with Big Five personality traits for psychologically realistic synths

**Independent Test**: Generate synths with extreme personality trait values (0-20, 80-100) and verify bias values fall within expected coherence ranges defined in research.md

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T029 [P] [US2] Unit test for get_coherence_expectations function in tests/unit/test_coherence_rules.py
- [ ] T030 [P] [US2] Unit test for each of 10 personality-bias mappings in tests/unit/test_coherence_rules.py
- [ ] T031 [P] [US2] Unit test for generate_biases_with_coherence function in tests/unit/test_biases.py
- [ ] T032 [P] [US2] Integration test for synth generation with coherent biases in tests/integration/test_coherent_generation.py

### Implementation for User Story 2

- [ ] T033 [P] [US2] Define COHERENCE_RULES constant with 10 trait-bias mappings in src/synth_lab/gen_synth/biases.py
- [ ] T034 [US2] Implement get_coherence_expectations(personality) function in src/synth_lab/gen_synth/biases.py
- [ ] T035 [US2] Implement generate_biases_with_coherence(personality) function in src/synth_lab/gen_synth/biases.py
- [ ] T036 [US2] Update synth generation to use generate_biases_with_coherence in src/synth_lab/gen_synth/synth_builder.py
- [ ] T037 [US2] Add unit tests for edge cases (moderate traits 40-60) in tests/unit/test_coherence_rules.py
- [ ] T038 [US2] Add unit tests for conflicting rules (multiple traits affecting same bias) in tests/unit/test_coherence_rules.py
- [ ] T039 [US2] Run all US2 tests and verify they pass

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - schema simplified, biases coherent with personality

---

## Phase 5: User Story 3 - Validation of Schema Coherence Rules (Priority: P2)

**Goal**: Implement automated validation that enforces personality-bias coherence rules so all generated synths maintain psychological consistency

**Independent Test**: Create synths that violate coherence rules (e.g., high conscientiousness with high hyperbolic discounting) and verify validation fails with meaningful error messages

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T040 [P] [US3] Unit test for validate_coherence function in tests/unit/test_validation.py
- [ ] T041 [P] [US3] Unit test for coherence error messages in tests/unit/test_validation.py
- [ ] T042 [P] [US3] Unit test for CoherenceError exception handling in tests/unit/test_validation.py
- [ ] T043 [P] [US3] Integration test for end-to-end validation in tests/integration/test_schema_validation.py

### Implementation for User Story 3

- [ ] T044 [US3] Define CoherenceError exception class in src/synth_lab/gen_synth/validation.py
- [ ] T045 [US3] Implement validate_coherence(synth) function in src/synth_lab/gen_synth/validation.py
- [ ] T046 [US3] Implement validate_synth_full(synth, strict) function in src/synth_lab/gen_synth/validation.py
- [ ] T047 [US3] Add coherence validation to synth generation pipeline in src/synth_lab/gen_synth/synth_builder.py
- [ ] T048 [US3] Implement meaningful error messages for each violation type in src/synth_lab/gen_synth/validation.py
- [ ] T049 [US3] Add backward compatibility check for removed fields in src/synth_lab/gen_synth/validation.py
- [ ] T050 [US3] Run all US3 tests and verify they pass

**Checkpoint**: All user stories should now be independently functional - schema simplified, biases coherent, validation automated

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and finalization

- [ ] T051 [P] Update schema documentation in data/schemas/synth-schema-cleaned.json with v2.0.0 changes
- [ ] T052 [P] Create schema migration guide documentation (informational) in specs/004-simplify-synth-schema/
- [ ] T053 [P] Update README.md with schema v2.0.0 usage examples
- [ ] T054 [P] Add performance benchmarks for schema validation (<50ms) in tests/
- [ ] T055 [P] Add performance benchmarks for coherence validation (<20ms) in tests/
- [ ] T056 [P] Verify schema file size meets ≤15KB target
- [ ] T057 [P] Run full test suite (fast battery <5s, complete battery <10s)
- [ ] T058 [P] Code cleanup: remove unused imports and dead code
- [ ] T059 [P] Add Portuguese docstrings to all modified functions
- [ ] T060 [P] Validate quickstart.md examples work end-to-end
- [ ] T061 Final validation: Generate 100 synths, verify all pass coherence validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (US1 → US2 → US3)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (US1 and US2 can be developed in parallel)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories BUT depends on US2 coherence rules being defined to validate them

**Note**: While US1 and US2 are both P1, US2 depends on personality traits (which are retained in US1), so US1 should complete first if working sequentially. If working in parallel, US1 should at least reach T012-T013 (version update) before US2 begins.

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Schema changes before code changes
- Core logic before integration
- Story complete and validated before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 and US2 can start in parallel (with caveat above)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- All Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task T008: "Unit test for schema field removal in tests/unit/test_schema_v2.py"
Task T009: "Unit test for schema version validation in tests/unit/test_schema_version.py"
Task T010: "Contract test for v2 schema structure in tests/contract/test_schema_contract.py"
Task T011: "Integration test for synth generation without removed fields in tests/integration/test_schema_validation.py"

# After tests written and failing, implement schema changes sequentially (same file):
Task T012-T020: Schema modifications in data/schemas/synth-schema-cleaned.json

# Then launch code changes in parallel (different files):
Task T021-T023: "Remove field generation from src/synth_lab/gen_synth/psychographics.py"
Task T024-T025: "Remove field generation from src/synth_lab/gen_synth/behavior.py"
Task T026: "Update src/synth_lab/gen_synth/synth_builder.py"
```

---

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together:
Task T029: "Unit test for get_coherence_expectations in tests/unit/test_coherence_rules.py"
Task T030: "Unit test for 10 mappings in tests/unit/test_coherence_rules.py"
Task T031: "Unit test for generate_biases_with_coherence in tests/unit/test_biases.py"
Task T032: "Integration test in tests/integration/test_coherent_generation.py"

# After tests written and failing, implement in biases.py:
Task T033: "Define COHERENCE_RULES in src/synth_lab/gen_synth/biases.py"
Task T034: "Implement get_coherence_expectations in src/synth_lab/gen_synth/biases.py"
Task T035: "Implement generate_biases_with_coherence in src/synth_lab/gen_synth/biases.py"

# Then update builder:
Task T036: "Update synth_builder.py to use new coherence function"

# Launch additional tests in parallel:
Task T037: "Edge case tests"
Task T038: "Conflicting rules tests"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (~3 tasks, 15 min)
2. Complete Phase 2: Foundational (~4 tasks, 30 min)
3. Complete Phase 3: User Story 1 (~21 tasks, 3-4 hours)
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Run fast battery (<5s)
   - Generate 10 synths, verify no removed fields
   - Verify schema ≤15KB
5. Demo/deploy if ready

**Estimated MVP Time**: 4-5 hours for schema simplification only

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (45 min)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! ~4-5 hours total)
3. Add User Story 2 → Test independently → Deploy/Demo (~3-4 hours additional)
4. Add User Story 3 → Test independently → Deploy/Demo (~2-3 hours additional)
5. Add Polish → Final release (~1-2 hours additional)

**Total Estimated Time**: 11-14 hours for complete feature

### Parallel Team Strategy

With 2 developers:

1. Both complete Setup + Foundational together (45 min)
2. Once Foundational is done:
   - Developer A: User Story 1 (schema simplification)
   - Developer B: User Story 2 (coherence rules) - start after US1 reaches T013
3. Developer A (after US1): User Story 3 (validation)
4. Both: Polish together

**Parallel Time Savings**: ~9-11 hours (vs 11-14 sequential)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **CRITICAL**: Verify tests fail before implementing (TDD/BDD requirement)
- Commit after completing each task or logical task group (Principle IV)
- Fast battery must complete in <5s (Principle II)
- Complete battery must complete in <10s (Principle III)
- Stop at any checkpoint to validate story independently
- All files must remain <500 lines (Principle V)
- Code in English, docs in Portuguese (Principle VI)

---

## Task Count Summary

- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational)**: 4 tasks
- **Phase 3 (US1 - P1)**: 21 tasks (4 tests + 17 implementation)
- **Phase 4 (US2 - P1)**: 11 tasks (4 tests + 7 implementation)
- **Phase 5 (US3 - P2)**: 11 tasks (4 tests + 7 implementation)
- **Phase 6 (Polish)**: 11 tasks
- **TOTAL**: 61 tasks

**Parallel Opportunities**: 29 tasks marked [P] can run in parallel (48% parallelizable)

**Test Tasks**: 12 test tasks (20% of total - per TDD/BDD requirement)

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 = 28 tasks (~46% of total)
