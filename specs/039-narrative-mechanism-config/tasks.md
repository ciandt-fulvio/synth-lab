# Tasks: Narrative Mechanism Configuration

**Input**: Design documents from `/specs/039-narrative-mechanism-config/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.yaml, quickstart.md

**Tests**: Tests are NOT explicitly requested in the specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `src/synth_lab/` (Python FastAPI)
- **Frontend**: `frontend/src/` (TypeScript React)
- **Database**: `src/synth_lab/infrastructure/` (SQLAlchemy models)
- **Scripts**: `scripts/` (seed data, migrations)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database schema and seed data for mechanism definitions

- [x] T001 Create SQLAlchemy models for mechanism_definitions, mechanism_options, feature_types in src/synth_lab/infrastructure/database.py
- [x] T002 [P] Create SQL initialization script for new tables in scripts/init_mechanism_tables.sql
- [x] T003 [P] Create seed script for mechanisms, options, and feature types in scripts/seed_mechanisms.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend entities, repository, and API schemas that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 [P] Create MechanismDefinition entity in src/synth_lab/domain/entities/mechanism_definition.py
- [x] T005 [P] Create MechanismOption entity in src/synth_lab/domain/entities/mechanism_option.py
- [x] T006 [P] Create FeatureType entity in src/synth_lab/domain/entities/feature_type.py
- [x] T007 [P] Create NarrativeResponse entity (transient) in src/synth_lab/domain/entities/narrative_response.py
- [x] T008 Create MechanismRepository in src/synth_lab/repositories/mechanism_repository.py
- [x] T009 [P] Create API schemas (MechanismListResponse, FeatureTypeListResponse, GenerateNarrativeRequest/Response) in src/synth_lab/api/schemas/mechanisms.py
- [x] T010 [P] Create TypeScript types (MechanismDefinition, MechanismOption, FeatureType, NarrativeResponse) in frontend/src/types/mechanisms.ts
- [x] T011 [P] Create mechanisms API client in frontend/src/services/mechanisms-api.ts
- [x] T012 [P] Create useMechanisms hook in frontend/src/hooks/use-mechanisms.ts
- [x] T013 Export new entities from src/synth_lab/domain/entities/__init__.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Configurar Mecanismos via Narrativa (Priority: P1)

**Goal**: Replace Step 2 sliders with narrative text containing inline mechanism dropdowns. PM sees LLM-generated narrative, selects options from dropdowns, values are persisted.

**Independent Test**: Create an experiment with name "Pix via WhatsApp" and hypothesis about payments. System generates narrative mentioning irreversibility and institutional trust, with functional dropdowns.

### Implementation for User Story 1

- [x] T014 [US1] Implement NarrativeService with generate_narrative() method in src/synth_lab/services/narrative_service.py
- [x] T015 [US1] Add LLM prompt builder for narrative generation (load mechanisms from DB) in src/synth_lab/services/narrative_service.py
- [x] T016 [US1] Add Phoenix tracing to narrative generation LLM calls in src/synth_lab/services/narrative_service.py
- [x] T017 [P] [US1] Create GET /api/v1/mechanisms endpoint in src/synth_lab/api/routers/mechanisms.py
- [x] T018 [P] [US1] Create GET /api/v1/mechanisms/feature-types endpoint in src/synth_lab/api/routers/mechanisms.py
- [x] T019 [US1] Create POST /api/v1/experiments/generate-narrative endpoint in src/synth_lab/api/routers/mechanisms.py
- [x] T020 [US1] Register mechanisms router in src/synth_lab/api/main.py
- [x] T021 [US1] Create useGenerateNarrative mutation hook in frontend/src/hooks/use-mechanisms.ts
- [x] T022 [US1] Create MechanismDropdown component (single dropdown for one mechanism) in frontend/src/components/experiments/MechanismDropdown.tsx
- [x] T023 [US1] Create NarrativeMechanismEditor component (parses template, renders dropdowns inline) in frontend/src/components/experiments/NarrativeMechanismEditor.tsx
- [x] T024 [US1] Update experiments-api.ts to send/receive mechanisms in create/update in frontend/src/services/experiments-api.ts
- [x] T025 [US1] Create NarrativeStep component for wizard Step 2 in frontend/src/components/experiments/NarrativeStep.tsx
- [x] T026 [US1] Integrate NarrativeStep in experiment creation wizard, replacing current Step 2 in frontend/src/components/experiments/ExperimentForm.tsx
- [x] T027 [US1] Add getMechanismValues() function to extract numeric values from selected options in frontend/src/components/experiments/NarrativeMechanismEditor.tsx
- [x] T028 [US1] Persist mechanism values to experiment.scorecard_data.mechanisms on "Continue" in frontend/src/components/experiments/ExperimentForm.tsx

**Checkpoint**: At this point, User Story 1 should be fully functional - PMs can configure mechanisms via narrative dropdowns

---

## Phase 4: User Story 2 - Regenerar Narrativa (Priority: P2)

**Goal**: PM can regenerate the narrative if unsatisfied with the LLM output. Previous selections are discarded, new narrative is displayed with new defaults.

**Independent Test**: Click "Regenerar" 3 times and verify different narratives are generated, potentially with different mechanisms selected.

### Implementation for User Story 2

- [x] T029 [US2] Add "Regenerar" button to NarrativeStep component in frontend/src/components/experiments/NarrativeStep.tsx
- [x] T030 [US2] Implement handleRegenerate that calls useGenerateNarrative.mutate() in frontend/src/components/experiments/NarrativeStep.tsx
- [x] T031 [US2] Add loading state during regeneration with skeleton/spinner in frontend/src/components/experiments/NarrativeStep.tsx
- [x] T032 [US2] Reset local dropdown selections when new narrative is received in frontend/src/components/experiments/NarrativeMechanismEditor.tsx

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - PMs can generate and regenerate narratives

---

## Phase 5: User Story 3 - Consultar Definições de Mecanismos (Priority: P3)

**Goal**: PM can see tooltip with mechanism description when hovering over a dropdown.

**Independent Test**: Hover over a dropdown and verify tooltip with mechanism label and description appears.

### Implementation for User Story 3

- [x] T033 [US3] Add Tooltip wrapper around MechanismDropdown with mechanism.label_pt and mechanism.description in frontend/src/components/experiments/MechanismDropdown.tsx
- [x] T034 [US3] Import TooltipProvider and ensure it wraps NarrativeMechanismEditor in frontend/src/components/experiments/NarrativeStep.tsx

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should work - PMs can configure, regenerate, and understand mechanisms

---

## Phase 6: User Story 4 - Administrar Definições de Mecanismos (Priority: P4)

**Goal**: Admin can add/edit mechanisms and options via API without code changes.

**Independent Test**: Via API, add a new option "quase irreversível" (value=0.85) to irreversibility mechanism, verify it appears in dropdowns.

### Implementation for User Story 4

- [x] T035 [P] [US4] Create POST /api/v1/mechanisms endpoint (create mechanism) in src/synth_lab/api/routers/mechanisms.py
- [x] T036 [P] [US4] Create PUT /api/v1/mechanisms/{key} endpoint (update mechanism) in src/synth_lab/api/routers/mechanisms.py
- [x] T037 [P] [US4] Create POST /api/v1/mechanisms/{key}/options endpoint (add option) in src/synth_lab/api/routers/mechanisms.py
- [x] T038 [P] [US4] Create PUT /api/v1/mechanisms/{key}/options/{option_id} endpoint (update option) in src/synth_lab/api/routers/mechanisms.py
- [x] T039 [US4] Add CRUD methods to MechanismRepository (create_mechanism, update_mechanism, add_option, update_option) in src/synth_lab/repositories/mechanism_repository.py
- [x] T040 [US4] Add admin schemas (CreateMechanismRequest, UpdateMechanismRequest, CreateOptionRequest, UpdateOptionRequest) in src/synth_lab/api/schemas/mechanisms.py

**Checkpoint**: All user stories complete - system is fully extensible without code changes

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, error handling, and documentation

- [x] T041 [P] Handle edge case: no relevant mechanisms (show message to enrich description) in frontend/src/components/experiments/NarrativeStep.tsx
- [x] T042 [P] Handle edge case: LLM generation error (show retry button, preserve Step 1 data) in frontend/src/components/experiments/NarrativeStep.tsx
- [x] T043 [P] Handle edge case: description too short (<20 words) with warning message in frontend/src/components/experiments/NarrativeStep.tsx
- [x] T044 [P] Handle edge case: incomplete mechanism selection (block "Continue", show which mechanism is missing) in frontend/src/components/experiments/NarrativeStep.tsx
- [ ] T045 Run quickstart.md validation with manual test
- [x] T046 [P] Update experiments-api.ts to handle mechanisms field in experiment updates in frontend/src/services/experiments-api.ts

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can proceed in priority order (P1 → P2 → P3 → P4)
  - Or in parallel if multiple developers available
- **Polish (Phase 7)**: Depends on User Story 1 being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 components existing (NarrativeStep, NarrativeMechanismEditor)
- **User Story 3 (P3)**: Depends on US1 MechanismDropdown component existing
- **User Story 4 (P4)**: Independent of UI stories - only backend work

### Within Each User Story

- Backend entities and repository before service
- Service before router endpoints
- API schemas before router implementation
- Frontend types before API client
- API client before hooks
- Hooks before components
- Components before page integration

### Parallel Opportunities

**Phase 1 (Setup)**:
```
T002 (SQL script) || T003 (seed script)
```

**Phase 2 (Foundational)**:
```
T004 (MechanismDefinition entity) || T005 (MechanismOption entity) || T006 (FeatureType entity) || T007 (NarrativeResponse entity)
T009 (API schemas) || T010 (TypeScript types) || T011 (mechanisms-api.ts) || T012 (useMechanisms hook)
```

**Phase 3 (User Story 1)**:
```
T017 (GET /mechanisms) || T018 (GET /feature-types)
```

**Phase 6 (User Story 4)**:
```
T035 || T036 || T037 || T038 (all admin CRUD endpoints)
```

**Phase 7 (Polish)**:
```
T041 || T042 || T043 || T044 || T046 (all edge cases)
```

---

## Parallel Example: Foundational Phase

```bash
# Launch all entity tasks together:
Task: "Create MechanismDefinition entity in src/synth_lab/domain/entities/mechanism_definition.py"
Task: "Create MechanismOption entity in src/synth_lab/domain/entities/mechanism_option.py"
Task: "Create FeatureType entity in src/synth_lab/domain/entities/feature_type.py"
Task: "Create NarrativeResponse entity in src/synth_lab/domain/entities/narrative_response.py"

# Launch all frontend foundation tasks together:
Task: "Create TypeScript types in frontend/src/types/mechanisms.ts"
Task: "Create mechanisms API client in frontend/src/services/mechanisms-api.ts"
Task: "Create useMechanisms hook in frontend/src/hooks/use-mechanisms.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (database, seed data)
2. Complete Phase 2: Foundational (entities, repository, schemas, types)
3. Complete Phase 3: User Story 1 (narrative generation + inline dropdowns)
4. **STOP and VALIDATE**: Test with "Pix via WhatsApp" scenario
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (regeneration)
4. Add User Story 3 → Test independently → Deploy/Demo (tooltips)
5. Add User Story 4 → Test independently → Deploy/Demo (admin API)
6. Add Polish → Final validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (frontend)
   - Developer B: User Story 1 (backend)
   - Developer C: User Story 4 (admin API - independent)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- LLM calls MUST use Phoenix tracing (`_tracer.start_as_current_span()`)
- Frontend components MUST be pure (props → JSX, no internal fetch)
- API schemas follow existing patterns in src/synth_lab/api/schemas/
