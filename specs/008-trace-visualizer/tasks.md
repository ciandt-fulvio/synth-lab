# Tasks: Mini-Jaeger Local para Conversas LLM Multi-turn

**Feature**: 008-trace-visualizer | **Branch**: `008-trace-visualizer`
**Input**: Design documents from `/specs/008-trace-visualizer/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: TDD approach - write tests FIRST, ensure they FAIL, then implement (Constitution Principle I)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Python SDK**: `src/synth_lab/trace_visualizer/`
- **Tests**: `tests/unit/synth_lab/trace_visualizer/`
- **UI**: `logui/` (static HTML/CSS/JS)
- **Documentation**: `specs/008-trace-visualizer/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create Python SDK directory structure: src/synth_lab/trace_visualizer/ with __init__.py
- [x] T002 Create test directory structure: tests/unit/synth_lab/trace_visualizer/
- [x] T003 Create UI directory structure: logui/ with index.html, styles.css placeholders
- [x] T004 [P] Add trace_visualizer to src/synth_lab/__init__.py public exports
- [x] T005 [P] Create data/traces/ directory for trace file storage

**Checkpoint**: Project structure ready for implementation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and enums that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 [P] Define SpanType enum (llm_call, tool_call, turn, error, logic) in src/synth_lab/trace_visualizer/models.py
- [x] T007 [P] Define SpanStatus enum (success, error, pending) in src/synth_lab/trace_visualizer/models.py
- [x] T008 Write unit test for Step dataclass validation in tests/unit/synth_lab/trace_visualizer/test_models.py
- [x] T009 Implement Step dataclass with span_id, type, start_time, end_time, duration_ms, status, attributes in src/synth_lab/trace_visualizer/models.py
- [x] T010 Write unit test for Turn dataclass validation in tests/unit/synth_lab/trace_visualizer/test_models.py
- [x] T011 Implement Turn dataclass with turn_id, turn_number, start_time, end_time, duration_ms, steps in src/synth_lab/trace_visualizer/models.py
- [x] T012 Write unit test for Trace dataclass validation in tests/unit/synth_lab/trace_visualizer/test_models.py
- [x] T013 Implement Trace dataclass with trace_id, start_time, end_time, duration_ms, turns, metadata in src/synth_lab/trace_visualizer/models.py
- [x] T014 Run tests: pytest tests/unit/synth_lab/trace_visualizer/test_models.py - verify all pass and run <5s

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Visualizar Conversa como Timeline (Priority: P1) 🎯 MVP

**Goal**: Registrar conversa multi-turn e visualizar como waterfall timeline (FR-001, FR-002, FR-003, FR-004)

**Independent Test**: Load trace with 3+ turns, see waterfall with duration bars, expand/collapse turns

**Success Criteria**:
- SC-001: Developer explains behavior from waterfall only
- SC-002: Identify bottlenecks in <10s
- SC-006: 100-step traces load in <2s

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T015 [P] [US1] Write test for Tracer.__init__() in tests/unit/synth_lab/trace_visualizer/test_tracer.py
- [ ] T016 [P] [US1] Write test for Tracer.start_turn() context manager in tests/unit/synth_lab/trace_visualizer/test_tracer.py
- [ ] T017 [P] [US1] Write test for Tracer.start_span() context manager in tests/unit/synth_lab/trace_visualizer/test_tracer.py
- [ ] T018 [P] [US1] Write test for Tracer.save_trace() JSON serialization in tests/unit/synth_lab/trace_visualizer/test_tracer.py
- [ ] T019 [P] [US1] Write test for load_trace() JSON deserialization in tests/unit/synth_lab/trace_visualizer/test_persistence.py
- [ ] T020 [P] [US1] Write test for save_trace() file creation in tests/unit/synth_lab/trace_visualizer/test_persistence.py

### Implementation for User Story 1

**SDK Core (Recording)**:

- [ ] T021 [US1] Implement Tracer.__init__() with trace_id and metadata in src/synth_lab/trace_visualizer/tracer.py
- [ ] T022 [US1] Implement Tracer.start_turn() context manager with timestamp recording in src/synth_lab/trace_visualizer/tracer.py
- [ ] T023 [US1] Implement Tracer.start_span() context manager with Span object yielding in src/synth_lab/trace_visualizer/tracer.py
- [ ] T024 [US1] Implement Span.set_attribute() and Span.set_status() methods in src/synth_lab/trace_visualizer/tracer.py
- [ ] T025 [US1] Implement Tracer.trace property (read-only access) in src/synth_lab/trace_visualizer/tracer.py
- [ ] T026 [US1] Run SDK tests: pytest tests/unit/synth_lab/trace_visualizer/test_tracer.py - verify all pass <5s

**Persistence Layer**:

- [ ] T027 [US1] Implement save_trace(trace, path) with JSON serialization in src/synth_lab/trace_visualizer/persistence.py
- [ ] T028 [US1] Implement load_trace(path) with JSON deserialization in src/synth_lab/trace_visualizer/persistence.py
- [ ] T029 [US1] Add Tracer.save_trace(path) wrapper method in src/synth_lab/trace_visualizer/tracer.py
- [ ] T030 [US1] Run persistence tests: pytest tests/unit/synth_lab/trace_visualizer/test_persistence.py - verify all pass <5s

**Public API**:

- [ ] T031 [US1] Export Tracer, SpanType, SpanStatus in src/synth_lab/trace_visualizer/__init__.py
- [ ] T032 [US1] Create example script demonstrating multi-turn recording in examples/trace_visualizer/basic_conversation.py
- [ ] T033 [US1] Run example script and generate test trace: uv run examples/trace_visualizer/basic_conversation.py

**UI Core (Visualization)**:

- [ ] T034 [US1] Implement HTML shell with file upload button and waterfall container in logui/index.html
- [ ] T035 [US1] Implement trace-renderer.js: loadTrace(file), parseJSON(data) in logui/trace-renderer.js
- [ ] T036 [US1] Implement waterfall.js: renderWaterfall(trace) with horizontal bars in logui/waterfall.js
- [ ] T037 [US1] Implement waterfall.js: renderTurn(turn) with duration scaling in logui/waterfall.js
- [ ] T038 [US1] Implement waterfall.js: renderStep(step) with nested positioning in logui/waterfall.js
- [ ] T039 [US1] Add expand/collapse functionality for turns in logui/waterfall.js
- [ ] T040 [US1] Implement basic CSS layout (flexbox container, waterfall grid) in logui/styles.css
- [ ] T041 [US1] Implement CSS for duration bars (width proportional to time) in logui/styles.css

**Manual Testing (BDD Acceptance)**:

- [ ] T042 [US1] BDD Test 1.1: Load trace with 3 turns → verify 3 bars with labels
- [ ] T043 [US1] BDD Test 1.2: Expand turn → verify 5 sub-bars, durations sum correctly
- [ ] T044 [US1] BDD Test 1.3: Identify slowest step in <10s by visual inspection only

**Checkpoint**: At this point, User Story 1 should be fully functional - recording + waterfall visualization working end-to-end

---

## Phase 4: User Story 2 - Inspecionar Detalhes de Etapas (Priority: P1) 🎯 MVP

**Goal**: Click span to see prompt/response/args/results in detail panel (FR-005, FR-006)

**Independent Test**: Click LLM call → see prompt/response, click tool call → see args/result, verify <1s response time

**Success Criteria**:
- SC-005: Details appear in <1s after click

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T045 [P] [US2] Write test for detail panel population (LLM call attributes) in tests/unit/synth_lab/trace_visualizer/test_ui_integration.py
- [ ] T046 [P] [US2] Write test for detail panel population (tool call attributes) in tests/unit/synth_lab/trace_visualizer/test_ui_integration.py
- [ ] T047 [P] [US2] Write test for prompt truncation (>500 chars) in tests/unit/synth_lab/trace_visualizer/test_ui_integration.py

### Implementation for User Story 2

**UI Details Panel**:

- [ ] T048 [US2] Implement HTML sidebar detail panel structure in logui/index.html
- [ ] T049 [US2] Implement details.js: showDetails(span) with click event binding in logui/details.js
- [ ] T050 [US2] Implement details.js: renderLLMCallDetails(attributes) showing prompt/response/model in logui/details.js
- [ ] T051 [US2] Implement details.js: renderToolCallDetails(attributes) showing tool_name/args/result in logui/details.js
- [ ] T052 [US2] Implement details.js: renderErrorDetails(attributes) showing error_type/message in logui/details.js
- [ ] T053 [US2] Implement details.js: truncateContent(text, maxLength=500) with "Show More" toggle in logui/details.js
- [ ] T054 [US2] Add CSS for detail panel (fixed sidebar, scrollable content) in logui/styles.css
- [ ] T055 [US2] Add CSS for truncated content (ellipsis, expand button) in logui/styles.css

**Manual Testing (BDD Acceptance)**:

- [ ] T056 [US2] BDD Test 2.1: Click LLM call span → verify prompt/response/model shown in <1s
- [ ] T057 [US2] BDD Test 2.2: Click tool call span → verify tool_name/args/result shown
- [ ] T058 [US2] BDD Test 2.3: Load trace with >500 char prompt → verify truncation + "Show More"
- [ ] T059 [US2] BDD Test 2.4: Click error span → verify error message in red

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - full recording + visualization + detail inspection

---

## Phase 5: User Story 3 - Exportar e Compartilhar Traces (Priority: P2)

**Goal**: Export trace as .trace.json, import trace from file, share with colleagues (FR-008, FR-009)

**Independent Test**: Export trace → send file to another browser/machine → import and visualize identically

**Success Criteria**:
- SC-004: .trace.json portable across environments

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T060 [P] [US3] Write test for export functionality (file download trigger) in tests/unit/synth_lab/trace_visualizer/test_ui_integration.py
- [ ] T061 [P] [US3] Write test for import functionality (file upload parsing) in tests/unit/synth_lab/trace_visualizer/test_ui_integration.py
- [ ] T062 [P] [US3] Write test for trace roundtrip (export → import → identical) in tests/unit/synth_lab/trace_visualizer/test_persistence.py

### Implementation for User Story 3

**UI Export/Import**:

- [ ] T063 [US3] Add "Export Trace" button to UI in logui/index.html
- [ ] T064 [US3] Implement exportTrace(trace) with Blob download in logui/trace-renderer.js
- [ ] T065 [US3] Implement file naming: conversation_id_timestamp.trace.json in logui/trace-renderer.js
- [ ] T066 [US3] Add "Import Trace" file input to UI (drag-and-drop support) in logui/index.html
- [ ] T067 [US3] Implement importTrace(file) with FileReader in logui/trace-renderer.js
- [ ] T068 [US3] Add validation: check JSON structure before rendering in logui/trace-renderer.js
- [ ] T069 [US3] Add error handling: show "Invalid trace file" message for corrupted JSON in logui/trace-renderer.js

**Manual Testing (BDD Acceptance)**:

- [ ] T070 [US3] BDD Test 3.1: Click "Export" → verify .trace.json downloaded
- [ ] T071 [US3] BDD Test 3.2: Click "Import" → select file → verify waterfall renders identically
- [ ] T072 [US3] BDD Test 3.3: Send .trace.json to colleague → verify they can open without infrastructure

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should work independently - full tracing + export/import

---

## Phase 6: User Story 4 - Cores Semânticas para Tipo de Etapa (Priority: P2)

**Goal**: Color-code spans by type (LLM=Blue, Tool=Green, Error=Red, Logic=Yellow) for quick visual identification (FR-007)

**Independent Test**: Load trace with mixed span types → identify errors by red color only, no reading required

**Success Criteria**:
- SC-007: Colors distinguishable without legend

### Implementation for User Story 4

**UI Semantic Colors**:

- [ ] T073 [P] [US4] Define CSS color variables (--color-llm-call, --color-tool-call, --color-error, --color-logic) in logui/styles.css
- [ ] T074 [P] [US4] Apply background color to waterfall bars based on span.type in logui/waterfall.js
- [ ] T075 [P] [US4] Add color legend to UI header (LLM=Blue, Tool=Green, Error=Red, Logic=Yellow) in logui/index.html
- [ ] T076 [P] [US4] Style error spans with red text and background in logui/styles.css
- [ ] T077 [P] [US4] Ensure colors are accessible (WCAG AA contrast ratio) in logui/styles.css

**Manual Testing (BDD Acceptance)**:

- [ ] T078 [US4] BDD Test 4.1: Load trace with multiple span types → verify distinct colors
- [ ] T079 [US4] BDD Test 4.2: Load trace with error span → verify red color makes error obvious
- [ ] T080 [US4] BDD Test 4.3: View legend → verify each color is documented

**Checkpoint**: All user stories (US1-US4) should now be independently functional with semantic coloring

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T081 [P] Add comprehensive docstrings (Google style) to all SDK modules (tracer.py, models.py, persistence.py)
- [ ] T082 [P] Add type hints to all SDK functions and methods
- [ ] T083 [P] Run ruff linter on SDK: ruff check src/synth_lab/trace_visualizer/
- [ ] T084 [P] Format code with ruff: ruff format src/synth_lab/trace_visualizer/
- [ ] T085 Add usage examples to quickstart.md based on working code
- [ ] T086 Create comprehensive trace for testing (20 turns, 50 steps, all span types) in examples/trace_visualizer/comprehensive_demo.py
- [ ] T087 Run full test battery: pytest tests/unit/synth_lab/trace_visualizer/ - verify all pass <5s
- [ ] T088 Run quickstart.md validation: execute all code examples and verify outputs
- [ ] T089 [P] Optimize waterfall rendering for large traces (virtual scrolling if >100 steps) in logui/waterfall.js
- [ ] T090 Add performance test: load 100-step trace, verify <2s load time (SC-006)
- [ ] T091 Code review: verify <300 lines per Python module (Constitution V)
- [ ] T092 Security review: check for XSS vulnerabilities in detail panel rendering
- [ ] T093 [P] Update repository CLAUDE.md with trace_visualizer tech stack
- [ ] T094 Create release notes for feature 008 in specs/008-trace-visualizer/RELEASE_NOTES.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User Story 1 (P1) → Can start after Phase 2
  - User Story 2 (P1) → Can start after Phase 2, integrates with US1 UI but independent
  - User Story 3 (P2) → Can start after Phase 2, extends US1/US2 but independent
  - User Story 4 (P2) → Can start after Phase 2, enhances US1 but independent
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Extends US1 UI but independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Uses US1 trace format but independent
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Enhances US1 visualization but independent

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD - Constitution I)
- SDK tests before SDK implementation
- UI implementation after SDK is working
- BDD manual tests after UI is complete
- Story complete before moving to next priority

### Parallel Opportunities

- Phase 1 (Setup): T001-T005 can all run in parallel (different directories)
- Phase 2 (Foundational): T006-T007 (enums) can run in parallel, tests/implementation alternate (TDD)
- User Story 1: T015-T020 (all tests) can run in parallel, T034-T041 (UI files) can run in parallel
- User Story 2: T045-T047 (tests) can run in parallel, T048-T055 (UI) can run in parallel
- User Story 3: T060-T062 (tests) can run in parallel
- User Story 4: T073-T077 (all CSS/styling) can run in parallel
- Phase 7 (Polish): T081-T084, T089, T092-T093 can run in parallel (different files)

---

## Parallel Example: User Story 1 (SDK Core)

```bash
# Launch all SDK tests for User Story 1 together:
Task: "Write test for Tracer.__init__() in tests/unit/synth_lab/trace_visualizer/test_tracer.py"
Task: "Write test for Tracer.start_turn() context manager in tests/unit/synth_lab/trace_visualizer/test_tracer.py"
Task: "Write test for Tracer.start_span() context manager in tests/unit/synth_lab/trace_visualizer/test_tracer.py"
Task: "Write test for Tracer.save_trace() JSON serialization in tests/unit/synth_lab/trace_visualizer/test_tracer.py"
Task: "Write test for load_trace() JSON deserialization in tests/unit/synth_lab/trace_visualizer/test_persistence.py"
Task: "Write test for save_trace() file creation in tests/unit/synth_lab/trace_visualizer/test_persistence.py"

# After tests fail, launch UI files in parallel:
Task: "Implement HTML shell with file upload button and waterfall container in logui/index.html"
Task: "Implement trace-renderer.js: loadTrace(file), parseJSON(data) in logui/trace-renderer.js"
Task: "Implement waterfall.js: renderWaterfall(trace) with horizontal bars in logui/waterfall.js"
Task: "Implement basic CSS layout (flexbox container, waterfall grid) in logui/styles.css"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only - Both P1)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T014) - CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T015-T044) - Recording + Waterfall
4. **CHECKPOINT**: Validate US1 independently (BDD tests T042-T044)
5. Complete Phase 4: User Story 2 (T045-T059) - Detail Inspection
6. **CHECKPOINT**: Validate US1+US2 together
7. **STOP and DEMO**: MVP complete - can record, visualize, and inspect traces

### Incremental Delivery

1. **Foundation**: Setup + Foundational (T001-T014) → SDK models ready
2. **MVP v1**: Add US1 (T015-T044) → Test independently → Demo waterfall visualization
3. **MVP v2**: Add US2 (T045-T059) → Test independently → Demo detail inspection
4. **Feature Complete v1**: Add US3 (T060-T072) → Test independently → Demo export/import
5. **Feature Complete v2**: Add US4 (T073-T080) → Test independently → Demo semantic colors
6. **Production Ready**: Polish (T081-T094) → Full validation → Release

### Parallel Team Strategy

With 2 developers:

1. **Together**: Complete Setup + Foundational (T001-T014)
2. **Split after Phase 2**:
   - Developer A: User Story 1 (SDK + UI for recording/waterfall) - T015-T044
   - Developer B: User Story 2 (Detail panel) - T045-T059 (can start UI in parallel)
3. **Rejoin**: Integrate US1+US2, validate together
4. **Split again**:
   - Developer A: User Story 3 (Export/Import) - T060-T072
   - Developer B: User Story 4 (Semantic Colors) - T073-T080
5. **Together**: Polish (T081-T094)

---

## Task Summary

**Total Tasks**: 94
- **Setup (Phase 1)**: 5 tasks
- **Foundational (Phase 2)**: 9 tasks (BLOCKING)
- **User Story 1 (P1)**: 30 tasks (Recording + Waterfall)
- **User Story 2 (P1)**: 15 tasks (Detail Inspection)
- **User Story 3 (P2)**: 13 tasks (Export/Import)
- **User Story 4 (P2)**: 8 tasks (Semantic Colors)
- **Polish (Phase 7)**: 14 tasks

**Parallel Opportunities**: 38 tasks marked [P] can run in parallel
**MVP Scope**: Phases 1-4 (T001-T059) = 59 tasks
**Feature Complete**: Phases 1-6 (T001-T080) = 80 tasks

**Test Coverage**:
- Unit tests: 17 tests (TDD approach)
- BDD acceptance tests: 11 tests (manual validation)
- Constitution compliant: Tests <5s (Constitution II)

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label (US1-US4) maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **TDD Required**: Tests must FAIL before implementation (Constitution I)
- Commit after each task or logical group (Constitution IV)
- Stop at any checkpoint to validate story independently
- Target: <300 lines per Python module (Constitution V)
- All code in English, all documentation in Portuguese (Constitution VI)
