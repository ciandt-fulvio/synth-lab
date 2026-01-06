# Tasks: Experiment Materials Upload

**Input**: Design documents from `/specs/001-experiment-materials/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/materials-api.yaml, quickstart.md

**Tests**: Following Gate I (TDD), tests are included but marked as Write tests before implementation.

**Organization**: Tasks are grouped by user story (4 stories: P1-Upload, P2-Preview, P3-Interview, P4-PRFAQ).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Paths follow web app structure: `src/synth_lab/` (backend), `frontend/src/` (frontend)

---

## Phase 1: Setup (Shared Infrastructure) ✅

**Purpose**: Dependencies, configuration, and database migration

- [x] T001 Add boto3, Pillow, pdf2image, moviepy dependencies to pyproject.toml
- [x] T002 Add react-dropzone dependency to frontend/package.json
- [x] T003 [P] Add S3 environment variables to src/synth_lab/infrastructure/config.py (BUCKET_NAME, S3_ENDPOINT_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
- [x] T004 [P] Create S3 storage client in src/synth_lab/infrastructure/storage_client.py
- [x] T005 Create Alembic migration for experiment_materials table in alembic/versions/
- [x] T006 Apply migration to DATABASE_URL and DATABASE_TEST_URL

---

## Phase 2: Foundational (Blocking Prerequisites) ✅

**Purpose**: Core backend components that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 [P] Create ExperimentMaterial domain entity in src/synth_lab/domain/entities/experiment_material.py
- [x] T008 [P] Create ExperimentMaterial ORM model in src/synth_lab/models/orm/material.py
- [x] T009 Add materials relationship to Experiment ORM model in src/synth_lab/models/orm/experiment.py
- [x] T010 Create ExperimentMaterialRepository in src/synth_lab/repositories/experiment_material_repository.py
- [x] T011 [P] Create API schemas in src/synth_lab/api/schemas/materials.py
- [x] T012 [P] Create Material TypeScript types in frontend/src/types/material.ts

**Checkpoint**: Foundation ready - user story implementation can now begin ✅

---

## Phase 3: User Story 1 - Upload Materials During Experiment Creation (Priority: P1)

**Goal**: Enable researchers to upload images, videos, and documents to experiments via drag-and-drop with presigned S3 URLs

**Independent Test**: Create experiment, drag-drop files, save experiment, verify files stored in S3 and metadata in database

### Tests for User Story 1 

- [ ] T013 [P] [US1] Unit test for MaterialService.request_upload_url in tests/unit/services/test_material_service.py
- [ ] T014 [P] [US1] Unit test for MaterialService.confirm_upload in tests/unit/services/test_material_service.py
- [ ] T015 [P] [US1] Unit test for size/count limit validation in tests/unit/services/test_material_service.py
- [ ] T016 [P] [US1] Integration test for upload-url endpoint in tests/integration/test_materials_api.py
- [ ] T017 [P] [US1] Integration test for confirm endpoint in tests/integration/test_materials_api.py

### Implementation for User Story 1

- [x] T018 [US1] Create MaterialService with request_upload_url method in src/synth_lab/services/material_service.py
- [x] T019 [US1] Add confirm_upload method to MaterialService in src/synth_lab/services/material_service.py
- [x] T020 [US1] Add file type and size validation methods to MaterialService
- [x] T021 [US1] Add limit validation methods (10 files, 250MB total) to MaterialService
- [x] T022 [US1] Create materials router with POST /upload-url endpoint in src/synth_lab/api/routers/materials.py
- [x] T023 [US1] Add POST /confirm endpoint to materials router
- [x] T024 [US1] Add GET /materials list endpoint to materials router
- [x] T025 [US1] Add PUT /reorder endpoint to materials router
- [x] T026 [US1] Add DELETE /{material_id} endpoint to materials router
- [x] T027 [US1] Register materials router in src/synth_lab/api/main.py
- [x] T028 [P] [US1] Create materials-api.ts with requestUploadUrl, uploadToS3, confirmUpload functions in frontend/src/services/materials-api.ts
- [x] T029 [P] [US1] Create useMaterials hook (list, invalidate) in frontend/src/hooks/use-materials.ts
- [x] T030 [US1] Create useUploadMaterial mutation hook in frontend/src/hooks/use-materials.ts
- [x] T031 [US1] Create MaterialUpload component with react-dropzone in frontend/src/components/experiments/MaterialUpload.tsx
- [x] T032 [US1] Add file type categorization selector (design, prototype, competitor, spec, other) to MaterialUpload component
- [x] T033 [US1] Add staged files preview with upload status indicators to MaterialUpload component
- [x] T034 [US1] Add drag-to-reorder functionality for staged files in MaterialUpload component
- [x] T035 [US1] Integrate MaterialUpload into experiment creation/edit page

**Checkpoint**: User Story 1 complete - can upload files to experiments and verify in database/S3 ✅

---

## Phase 4: User Story 2 - View Materials Preview on Experiment Page (Priority: P2)

**Goal**: Display thumbnail previews of all materials with metadata in a gallery format on the experiment page

**Independent Test**: Navigate to experiment with materials, verify thumbnails render with filename/type/size, click to view full-size

### Tests for User Story 2 

- [ ] T036 [P] [US2] Unit test for thumbnail generation in tests/unit/services/test_material_service.py
- [ ] T037 [P] [US2] Integration test for GET /view-url endpoint in tests/integration/test_materials_api.py
- [ ] T038 [P] [US2] Frontend test for MaterialGallery component in frontend/src/__tests__/MaterialGallery.test.tsx

### Implementation for User Story 2

- [ ] T039 [US2] Add generate_thumbnail method for images (Pillow resize 200x200) to MaterialService
- [ ] T040 [US2] Add generate_thumbnail method for videos (extract frame 0 with moviepy) to MaterialService
- [ ] T041 [US2] Add generate_thumbnail method for PDFs (first page with pdf2image) to MaterialService
- [x] T042 [US2] Add GET /{material_id}/view-url endpoint (presigned URL for viewing) to materials router
- [ ] T043 [US2] Trigger thumbnail generation after upload confirmation in MaterialService.confirm_upload
- [x] T044 [P] [US2] Add getMaterialViewUrl function to frontend/src/services/materials-api.ts
- [ ] T045 [US2] Create MaterialGallery component displaying thumbnails with metadata in frontend/src/components/experiments/MaterialGallery.tsx
- [ ] T046 [US2] Add full-size modal viewer to MaterialGallery (click thumbnail to expand)
- [ ] T047 [US2] Add video player modal for video materials in MaterialGallery
- [ ] T048 [US2] Integrate MaterialGallery into experiment detail page

**Checkpoint**: User Story 2 complete - can view material previews and full-size files on experiment page

---

## Phase 5: User Story 3 - Synths Process Materials During Interviews (Priority: P3)

**Goal**: Enable synths to "see" and reference attached materials during simulated interviews via LLM tool

**Independent Test**: Run interview with materials attached, verify synth responses reference specific visual elements

- [ ] T049 [P] [US3] Unit test for MaterialDescriptionService in tests/unit/services/test_material_description_service.py
- [ ] T050 [P] [US3] Unit test for ver_material tool in tests/unit/services/research_agentic/test_tools.py
- [ ] T051 [P] [US3] Integration test for interview with materials in tests/integration/test_interview_with_materials.py

- [ ] T052 [US3] Create MaterialDescriptionService in src/synth_lab/services/material_description_service.py
- [ ] T053 [US3] Implement generate_description method using gpt-4o-mini with vision in MaterialDescriptionService
- [ ] T054 [US3] Add image content extraction (base64 encoding) for LLM in MaterialDescriptionService
- [ ] T055 [US3] Add video frame extraction for LLM (first frame) in MaterialDescriptionService
- [ ] T056 [US3] Add PDF text/image extraction for LLM (first page) in MaterialDescriptionService
- [ ] T057 [US3] Add Phoenix tracing span wrapper to MaterialDescriptionService.generate_description
- [ ] T058 [US3] Queue description generation in MaterialService.confirm_upload (async background task)
- [x] T059 [US3] Add retry-description endpoint POST /{material_id}/retry-description to materials router
- [ ] T060 [US3] Create create_material_viewer_tool function in src/synth_lab/services/research_agentic/tools.py
- [ ] T061 [US3] Implement view_material tool body (return description + base64 image) in tools.py
- [ ] T062 [US3] Modify create_interviewer to accepttools parameter in src/synth_lab/services/research_agentic/agent_definitions.py
- [ ] T063 [US3] Modify create_interviewee to accepttools parameter in agent_definitions.py
- [ ] T064 [US3] Load experiment materials and create tool in run_interview in src/synth_lab/services/research_agentic/runner.py
- [ ] T065 [US3] Pass material_tool to interviewer and interviewee agents in runner.py
- [ ] T066 [P] [US3] Add description status polling to MaterialGallery component (show pending/generating/completed/failed)
- [ ] T067 [P] [US3] Add retry button for failed descriptions in MaterialGallery component

**Checkpoint**: User Story 3 complete - synths can view and reference materials during interviews

---

## Phase 6: User Story 4 - Materials Referenced in PR-FAQ Generation (Priority: P4)

**Goal**: Automatically reference materials in generated PR-FAQ documents with specific visual evidence

**Independent Test**: Generate PR-FAQ for experiment with materials, verify "Reference Materials" section with file names

### Tests for User Story 4 

- [ ] T068 [P] [US4] Unit test for materials section in PR-FAQ in tests/unit/services/research_prfaq/test_generator.py

### Implementation for User Story 4

- [ ] T069 [US4] Add format_materials_section helper function in src/synth_lab/services/research_prfaq/generator.py
- [ ] T070 [US4] Integrate material references into PR-FAQ generation in src/synth_lab/services/research_prfaq/generator.py
- [ ] T071 [US4] Include material file names and descriptions in PR-FAQ output
- [ ] T072 [US4] Extract and format material references from interview transcripts (e.g., "ref: wireframe.png")

**Checkpoint**: User Story 4 complete - PR-FAQs include material references

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, edge cases, and documentation

- [ ] T073 [P] Add error handling for S3 upload failures in MaterialService
- [ ] T074 [P] Add error handling for S3 unavailable during interview in tools.py (fallback to description only)
- [ ] T075 [P] Add file cleanup job for orphaned S3 files (materials with no DB record)
- [ ] T076 [P] Add size limit error messages to MaterialUpload component (25MB images/docs, 100MB videos)
- [ ] T077 [P] Add max files error message to MaterialUpload component (10 files limit)
- [ ] T078 Validate all acceptance scenarios from spec.md
- [ ] T079 Run quickstart.md validation end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup (T001-T006)
    ↓
Phase 2: Foundational (T007-T012)
    ↓ (BLOCKS all user stories)
    ├── Phase 3: User Story 1 (T013-T035) - Upload
    ├── Phase 4: User Story 2 (T036-T048) - Preview (can start after T027)
    ├── Phase 5: User Story 3 (T049-T067) - Interview (depends on US1, US2)
    └── Phase 6: User Story 4 (T068-T072) - PR-FAQ (depends on US3)
    ↓
Phase 7: Polish (T073-T079)
```

### User Story Dependencies

- **User Story 1 (P1)**: Foundational only - can start immediately after Phase 2
- **User Story 2 (P2)**: Depends on US1 being complete (needs materials to preview)
- **User Story 3 (P3)**: Depends on US1 (materials) and US2 (thumbnails/descriptions)
- **User Story 4 (P4)**: Depends on US3 (interview references)

### Parallel Opportunities

**Phase 1 (Setup):**
```bash
# Parallel group 1:
T001 Add boto3, Pillow deps
T002 Add react-dropzone

# Parallel group 2:
T003 Add S3 env vars
T004 Create storage client
```

**Phase 2 (Foundational):**
```bash
# Parallel group:
T007 Domain entity
T008 ORM model
T011 API schemas
T012 TypeScript types
```

**Phase 3 (US1) Implementation:**
```bash
# After T027 (router registered), run parallel:
T028 materials-api.ts
T029 useMaterials hook
```

**Phase 5 (US3) - After core implementation:**
```bash
# Parallel group:
T066 Description status polling
T067 Retry button
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T012)
3. Complete Phase 3: User Story 1 (T013-T035)
4. **STOP and VALIDATE**: Upload files, verify in S3 and DB
5. Deploy/demo - researchers can attach materials to experiments

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test upload flow → **Deploy (MVP!)**
3. Add User Story 2 → Test previews → Deploy (visible value!)
4. Add User Story 3 → Test synth interviews → Deploy (core differentiation!)
5. Add User Story 4 → Test PR-FAQ → Deploy (complete feature!)

---

## Summary

| Phase | User Story | Tasks | Completed | Remaining |
|-------|------------|-------|-----------|-----------|
| 1 | Setup | 6 | 6 ✅ | 0 |
| 2 | Foundational | 6 | 6 ✅ | 0 |
| 3 | US1 - Upload | 23 | 18 ✅ | 5 tests) |
| 4 | US2 - Preview | 13 | 2 | 11 |
| 5 | US3 - Interview | 19 | 1 | 18 |
| 6 | US4 - PR-FAQ | 5 | 0 | 5 |
| 7 | Polish | 7 | 0 | 7 |
| **Total** | | **79** | **33** | **46** |

**MVP Scope**: Phases 1-3 (35 tasks) - Upload materials to experiments
**Full Feature**: All phases (79 tasks) - Complete materials integration

**Current Status**: Phase 3 (US1 - Upload) implementation complete! All backend + frontend implementation tasks done. Onlytests remain.

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable after completion
- Tests follow TDD: write first, verify they FAIL, then implement
- Commit after each task or logical group
- All LLM calls must use Phoenix tracing spans
- Database migrations must be applied to both DATABASE_URL and DATABASE_TEST_URL
