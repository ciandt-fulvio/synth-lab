# Tasks: PDF Download for Document Viewer

**Input**: Design documents from `/specs/027-pdf-download/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included per Constitution Principle I (TDD/BDD mandatory)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/`, `frontend/tests/`
- This is a frontend-only feature (no backend changes)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for PDF feature

- [x] T001 [P] Verify html2canvas ^1.4.1 is installed in frontend/package.json
- [x] T002 [P] Verify jspdf ^3.0.4 is installed in frontend/package.json
- [x] T003 [P] Verify Lucide React Download icon is available
- [x] T004 Create frontend/src/lib/ directory if it doesn't exist
- [x] T005 Create frontend/tests/components/shared/ directory if it doesn't exist

**Validation**: Run `npm list html2canvas jspdf` from frontend directory - both should show installed versions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core PDF utilities that MUST be complete before user story implementation

**⚠️ CRITICAL**: No user story work can begin until these utilities are implemented and tested

### Tests (Write First - Must Fail)

- [x] T006 [P] Create test file frontend/tests/lib/pdf-utils.test.ts with test structure
- [x] T007 [P] Write test for sanitizeFilename function - various inputs (spaces, special chars, empty, unicode)
- [x] T008 [P] Write test for generatePdfFilename function - all document types (prfaq, executive_summary, summary)
- [x] T009 [P] Write test for generatePdfFromElement function - mock html2canvas and jsPDF, verify calls

**Run Tests**: `npm test -- pdf-utils.test.ts` - All tests should FAIL (functions don't exist yet)

### Implementation (Make Tests Pass)

- [x] T010 Create frontend/src/lib/pdf-utils.ts file
- [x] T011 [P] Implement sanitizeFilename function in frontend/src/lib/pdf-utils.ts per research.md specification
- [x] T012 [P] Implement generatePdfFilename function in frontend/src/lib/pdf-utils.ts
- [x] T013 Implement generatePdfFromElement function in frontend/src/lib/pdf-utils.ts with html2canvas and jsPDF integration

**Validation**: Run `npm test -- pdf-utils.test.ts` - All tests should PASS

**Checkpoint**: Foundation ready - PDF utilities are working and tested, user story implementation can now begin

**Commit**: `git add . && git commit -m "feat: add PDF generation utilities with tests"`

---

## Phase 3: User Story 1 - Export Document to PDF (Priority: P1) 🎯 MVP

**Goal**: Enable users to download documents as PDF files by clicking a download button in the DocumentViewer dialog header

**Independent Test**: Open any completed document in DocumentViewer and click the download button - PDF file should download with correct filename and full content

### Tests for User Story 1 (Write First - Must Fail)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T014 [US1] Create test file frontend/tests/components/shared/DocumentViewer.test.tsx
- [x] T015 [P] [US1] Write test: Download button renders in dialog header when dialog is open
- [x] T016 [P] [US1] Write test: Download button shows Download icon when not generating
- [x] T017 [P] [US1] Write test: Download button shows Loader2 spinner when isGeneratingPdf is true
- [x] T018 [P] [US1] Write test: Download button is enabled when status is 'completed' and has content
- [x] T019 [P] [US1] Write test: onClick calls handleDownloadPdf function
- [x] T020 [P] [US1] Write test: handleDownloadPdf generates correct filename for prfaq documents
- [x] T021 [P] [US1] Write test: handleDownloadPdf generates correct filename for executive_summary documents
- [x] T022 [P] [US1] Write test: handleDownloadPdf generates correct filename for summary documents
- [x] T023 [P] [US1] Write test: handleDownloadPdf calls generatePdfFromElement with contentRef.current
- [x] T024 [P] [US1] Write test: handleDownloadPdf sets isGeneratingPdf to true during generation
- [x] T025 [P] [US1] Write test: handleDownloadPdf sets isGeneratingPdf to false after completion
- [x] T026 [P] [US1] Write test: handleDownloadPdf shows error toast on failure

**Run Tests**: `npm test -- DocumentViewer.test.tsx` - All tests should FAIL (implementation doesn't exist yet)

### Implementation for User Story 1

- [x] T027 [US1] Import Download and Loader2 icons from lucide-react in frontend/src/components/shared/DocumentViewer.tsx
- [x] T028 [US1] Import Button component from @/components/ui/button in frontend/src/components/shared/DocumentViewer.tsx
- [x] T029 [US1] Import toast from sonner in frontend/src/components/shared/DocumentViewer.tsx
- [x] T030 [US1] Import PDF utilities (generatePdfFromElement, generatePdfFilename) in frontend/src/components/shared/DocumentViewer.tsx
- [x] T031 [US1] Add useState hook for isGeneratingPdf state in frontend/src/components/shared/DocumentViewer.tsx
- [x] T032 [US1] Add useRef hook for contentRef in frontend/src/components/shared/DocumentViewer.tsx
- [x] T033 [US1] Attach contentRef to article.markdown-content element in frontend/src/components/shared/DocumentViewer.tsx
- [x] T034 [US1] Create handleDownloadPdf async function in frontend/src/components/shared/DocumentViewer.tsx
- [x] T035 [US1] Implement handleDownloadPdf logic: set isGeneratingPdf true, call generatePdfFromElement, handle errors, set isGeneratingPdf false
- [x] T036 [US1] Add download button to DialogHeader in frontend/src/components/shared/DocumentViewer.tsx
- [x] T037 [US1] Configure button: variant="ghost" size="icon" onClick={handleDownloadPdf}
- [x] T038 [US1] Add conditional icon rendering: Loader2 (spinning) if isGeneratingPdf, else Download
- [x] T039 [US1] Add error handling with Portuguese toast message "Erro ao gerar PDF"

**Validation**: Run `npm test -- DocumentViewer.test.tsx` - All tests should PASS

**Manual Test**: Start dev server (`npm run dev`), navigate to experiment, open any document, click download button, verify PDF downloads with correct name and content

**Checkpoint**: At this point, User Story 1 should be fully functional - users can download documents as PDF

**Commit**: `git add . && git commit -m "feat(US1): add PDF download button to DocumentViewer"`

---

## Phase 4: User Story 2 - Prevent Invalid Download Attempts (Priority: P2)

**Goal**: Disable download button when document is not ready (generating, failed, or empty) to prevent user confusion

**Independent Test**: View DocumentViewer in various states (generating, failed, empty) and verify download button is disabled in each case

### Tests for User Story 2 (Write First - Must Fail)

- [x] T040 [P] [US2] Write test: Download button is disabled when status is 'generating'
- [x] T041 [P] [US2] Write test: Download button is disabled when status is 'failed'
- [x] T042 [P] [US2] Write test: Download button is disabled when markdownContent is empty string
- [x] T043 [P] [US2] Write test: Download button is disabled when markdownContent is undefined
- [x] T044 [P] [US2] Write test: Download button is disabled when isGeneratingPdf is true
- [x] T045 [P] [US2] Write test: Download button is enabled when status is 'completed' and has valid content

**Run Tests**: `npm test -- DocumentViewer.test.tsx` - New tests should FAIL (button state logic not implemented)

### Implementation for User Story 2

- [x] T046 [US2] Compute isButtonDisabled from isGenerating, isFailed, hasContent, isGeneratingPdf in frontend/src/components/shared/DocumentViewer.tsx
- [x] T047 [US2] Apply disabled={isButtonDisabled} to download Button component in frontend/src/components/shared/DocumentViewer.tsx
- [x] T048 [US2] Add visual disabled state styling (button already uses shadcn/ui disabled styles)

**Validation**: Run `npm test -- DocumentViewer.test.tsx` - All tests including US2 tests should PASS

**Manual Test**:
1. View document while generating - button should be disabled (gray)
2. View failed document - button should be disabled
3. View document with no content - button should be disabled
4. View completed document with content - button should be enabled
5. Click download and observe button disabled during PDF generation

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - download works AND button states are correct

**Commit**: `git add . && git commit -m "feat(US2): disable download button for invalid states"`

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect the overall feature quality

- [ ] T049 [P] Add comments to handleDownloadPdf function explaining PDF generation flow in frontend/src/components/shared/DocumentViewer.tsx
- [ ] T050 [P] Add JSDoc comment to sanitizeFilename function in frontend/src/lib/pdf-utils.ts
- [ ] T051 [P] Add JSDoc comment to generatePdfFilename function in frontend/src/lib/pdf-utils.ts
- [ ] T052 [P] Add JSDoc comment to generatePdfFromElement function in frontend/src/lib/pdf-utils.ts
- [ ] T053 Verify all tests pass: `npm test -- pdf-utils.test.ts DocumentViewer.test.tsx`
- [ ] T054 Verify component stays under 1000 lines (currently ~230 lines per plan.md)
- [ ] T055 Run linter: `npm run lint` and fix any issues
- [ ] T056 Manual browser testing using quickstart.md checklist (10 test scenarios)
- [ ] T057 Test across browsers: Chrome, Firefox, Safari, Edge (basic smoke test)
- [ ] T058 Update component documentation header in frontend/src/components/shared/DocumentViewer.tsx

**Validation**: All automated tests pass, manual testing checklist complete, code quality checks pass

**Commit**: `git add . && git commit -m "docs: add documentation and comments for PDF download feature"`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-4)**: All depend on Foundational phase completion
  - User Story 1 (P1) can proceed after Foundational
  - User Story 2 (P2) depends on User Story 1 (enhances the same button)
- **Polish (Phase 5)**: Depends on User Stories 1 and 2 being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational (Phase 2) - No dependencies on other stories (can be MVP)
- **User Story 2 (P2)**: Depends on User Story 1 completion (adds state logic to same button) - NOT independently implementable

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD)
- Implementation tasks make tests pass
- Validation confirms tests pass
- Manual testing confirms feature works
- Commit after story completion

### Parallel Opportunities

**Phase 1 - Setup**: All T001-T005 can run in parallel (different files/checks)

**Phase 2 - Foundational Tests**: T006-T009 can run in parallel (different test cases)

**Phase 2 - Foundational Implementation**: T011-T012 can run in parallel (sanitizeFilename and generatePdfFilename are independent), T013 depends on both

**Phase 3 - User Story 1 Tests**: T015-T026 can run in parallel (different test cases)

**Phase 3 - User Story 1 Implementation**:
- T027-T030 (imports) can run in parallel
- T031-T033 (state/refs) must be sequential
- T034-T039 (handleDownloadPdf) must be sequential

**Phase 4 - User Story 2 Tests**: T040-T045 can run in parallel (different test cases)

**Phase 5 - Polish**: T049-T052 (documentation) can run in parallel, T053-T058 must be sequential

---

## Parallel Example: User Story 1 Tests

```bash
# Launch all tests for User Story 1 together:
# Task T015: "Download button renders in dialog header"
# Task T016: "Download button shows Download icon"
# Task T017: "Download button shows Loader2 spinner"
# Task T018: "Download button is enabled for completed docs"
# Task T019: "onClick calls handleDownloadPdf"
# Task T020-T022: "Filename generation for all doc types"
# Task T023: "Calls generatePdfFromElement"
# Task T024-T025: "isGeneratingPdf state management"
# Task T026: "Error toast on failure"

# All can be written in parallel, added to same test file
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. ✅ Complete Phase 1: Setup (verify dependencies)
2. ✅ Complete Phase 2: Foundational (PDF utilities + tests)
3. ✅ Complete Phase 3: User Story 1 (download button + tests)
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Run automated tests: `npm test -- DocumentViewer.test.tsx`
   - Manual test: Download PDF from completed document
   - Verify filename format, content preservation, quality
5. Deploy/demo if ready - Users can now download documents!

### Full Feature (Both User Stories)

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Commit (MVP!)
3. Add User Story 2 → Test independently → Commit (Enhanced UX)
4. Complete Polish phase → Final validation → Commit
5. Create Pull Request with all commits

### Parallel Team Strategy

This feature is small enough for a single developer, but if splitting:

1. Developer A: Complete Setup + Foundational (everyone needs these)
2. Once Foundational is done:
   - Developer A: User Story 1 (core functionality)
   - Developer B: Write User Story 2 tests (can prepare while A finishes)
3. After User Story 1 complete:
   - Developer A or B: User Story 2 (quick - just button state logic)
4. Both review and complete Polish phase together

---

## Notes

- [P] tasks = different files/test cases, no dependencies
- [Story] label maps task to specific user story for traceability
- User Story 2 is NOT independently completable (depends on US1's button)
- Verify tests fail before implementing (Red-Green-Refactor)
- Commit after each user story or logical group
- Fast test battery (<5s): Unit tests with mocks for html2canvas/jsPDF
- Slow test battery: Integration tests with actual PDF generation
- Stop at US1 checkpoint for MVP, or continue to US2 for full feature
- Constitution compliant: TDD mandatory, frequent commits, Portuguese user-facing strings

## Quick Validation Commands

```bash
# Run all tests
cd frontend && npm test -- pdf-utils.test.ts DocumentViewer.test.tsx

# Run linter
cd frontend && npm run lint

# Start dev server for manual testing
cd frontend && npm run dev

# Verify dependencies
cd frontend && npm list html2canvas jspdf
```

## Success Criteria Mapping

- **SC-001** (PDF in <5s): Validated in T056 manual testing
- **SC-002** (100% content): Validated in T056 manual testing
- **SC-003** (Readable text): Validated in T056 manual testing, enforced by 2x scale in T013
- **SC-004** (Button states): Validated in T040-T045 tests + T056 manual
- **SC-005** (Valid filenames): Validated in T007-T008 tests
- **SC-006** (Error feedback): Validated in T026 test + T039 implementation
- **SC-007** (Browser compat): Validated in T057 manual testing
