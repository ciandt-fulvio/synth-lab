# Implementation Plan: PDF Download for Document Viewer

**Branch**: `027-pdf-download` | **Date**: 2026-01-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/027-pdf-download/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add PDF download functionality to the DocumentViewer component, enabling users to export generated documents (PR/FAQ, Executive Summary, Summary) as PDF files for offline reading, sharing, and archiving. The implementation uses html2canvas to capture the rendered markdown content and jsPDF to generate high-quality PDF files with automatic download. The feature includes state management for button states (enabled/disabled/loading) and proper error handling.

## Technical Context

**Language/Version**: TypeScript 5.5.3 with React 18.3.1
**Primary Dependencies**: html2canvas ^1.4.1, jspdf ^3.0.4, React, Lucide React (for icons)
**Storage**: N/A (client-side only, no server-side persistence)
**Testing**: Component testing with React Testing Library, browser compatibility testing
**Target Platform**: Modern browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web frontend (React component enhancement)
**Performance Goals**: PDF generation in under 5 seconds per document, 2x scale factor for quality
**Constraints**: Client-side PDF generation only, maximum document length ~50 pages, 100% content preservation
**Scale/Scope**: Single component modification (DocumentViewer.tsx), affects 3 document types (prfaq, executive_summary, summary)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Test-First Development (TDD/BDD)
- ✅ **Status**: PASS
- **Plan**: Tests will be written first for PDF generation functionality
  - Test: Button render and state management (disabled/enabled/loading)
  - Test: PDF generation function with mock html2canvas and jsPDF
  - Test: Filename sanitization utility
  - Test: Error handling scenarios
- **BDD Coverage**: All acceptance criteria from spec will have corresponding tests

### Principle II: Fast Test Battery on Every Commit
- ✅ **Status**: PASS
- **Plan**: Component unit tests (button states, filename generation) will be fast (<0.5s each)
- **Note**: PDF generation tests will use mocks to avoid slow rendering

### Principle III: Complete Test Battery Before Pull Requests
- ✅ **Status**: PASS
- **Plan**: Complete test suite will include:
  - Unit tests: Button states, filename generation, error handling
  - Integration tests: PDF generation with actual html2canvas/jsPDF (slower)
  - Browser compatibility checks (manual testing documented)

### Principle IV: Frequent Version Control Commits
- ✅ **Status**: PASS
- **Plan**: Commits will be made at each logical step:
  1. Add tests for button component changes
  2. Implement button UI changes
  3. Add tests for PDF generation utilities
  4. Implement PDF generation function
  5. Add tests for error handling
  6. Implement error handling
  7. Update documentation

### Principle V: Simplicity and Code Quality
- ✅ **Status**: PASS
- **Analysis**:
  - Single component modification (DocumentViewer.tsx)
  - Component currently 127 lines, will add ~100 lines (PDF logic)
  - Final size ~227 lines (within 1000 line limit for TSX files)
  - Single-purpose functions: `handleDownloadPdf()`, `sanitizeFilename()`
  - No new dependencies required (html2canvas and jspdf already installed)

### Principle VI: Language
- ✅ **Status**: PASS
- **Plan**:
  - Code (component, functions, variables) will be in English
  - Comments and documentation in Portuguese
  - User-facing strings (button label, error messages) in Portuguese

### Principle VII: Architecture - Frontend
- ✅ **Status**: PASS
- **Compliance**:
  - Component remains pure: receives props, returns JSX
  - No API calls or data fetching (client-side only)
  - No hooks needed (local state with useState)
  - No query keys needed (no React Query involvement)
- **Pattern**: Self-contained component with local state for PDF generation

### Principle VIII: Other Principles
- ✅ **Status**: PASS (N/A for client-side component)
- **Note**: No tracing needed (client-side operation), no database migrations

### Overall Gate Status (Initial)
- ✅ **PASS** - All constitution principles satisfied
- **Proceed to Phase 0**: Research approved

---

## Constitution Re-Check (Post-Design)

*Re-evaluated after Phase 1 design completion*

### Principle I: Test-First Development (TDD/BDD)
- ✅ **Status**: PASS (Confirmed)
- **Verification**: Design includes comprehensive test plan in quickstart.md
- **Test Strategy Confirmed**:
  - Unit tests for utility functions (sanitizeFilename, generatePdfFilename, generatePdfFromElement)
  - Component tests for button states and rendering
  - Integration tests for full PDF generation workflow
  - Manual browser compatibility testing checklist

### Principle II: Fast Test Battery on Every Commit
- ✅ **Status**: PASS (Confirmed)
- **Verification**: Unit tests will use mocks for html2canvas/jsPDF to ensure speed
- **Expected Performance**: <0.5s per unit test, <5s total for fast battery

### Principle III: Complete Test Battery Before Pull Requests
- ✅ **Status**: PASS (Confirmed)
- **Verification**: Quickstart includes manual testing checklist with 10 scenarios
- **Coverage**: All functional requirements and acceptance criteria covered

### Principle IV: Frequent Version Control Commits
- ✅ **Status**: PASS (Confirmed)
- **Commit Plan** (7 logical commits):
  1. test: add tests for PDF utility functions
  2. feat: add PDF utility functions (pdf-utils.ts)
  3. test: add tests for DocumentViewer button UI
  4. feat: add download button to DocumentViewer
  5. test: add tests for PDF generation integration
  6. feat: implement PDF generation handler
  7. docs: update component documentation

### Principle V: Simplicity and Code Quality
- ✅ **Status**: PASS (Confirmed)
- **Final Analysis**:
  - DocumentViewer.tsx: 127 → ~230 lines (within 1000 limit)
  - New pdf-utils.ts: ~150 lines (3 utility functions)
  - Test file: ~200 lines
  - Single responsibility maintained: PDF utils are pure functions
  - Component logic is straightforward state management

### Principle VI: Language
- ✅ **Status**: PASS (Confirmed)
- **Verification**: Design documents confirm:
  - Code in English (functions: generatePdfFromElement, sanitizeFilename)
  - Documentation in Portuguese (comments, quickstart user sections)
  - User-facing strings in Portuguese ("Erro ao gerar PDF", toast messages)

### Principle VII: Architecture - Frontend
- ✅ **Status**: PASS (Confirmed)
- **Design Compliance Verified**:
  - Component remains pure: props → JSX + local state
  - No API calls (client-side only, confirmed in data-model.md)
  - No React Query hooks needed (confirmed in architecture notes)
  - Utility functions are pure and testable
  - Follows existing DocumentViewer patterns

### Principle VIII: Other Principles
- ✅ **Status**: PASS (Confirmed)
- **Notes**:
  - DRY: Filename logic extracted to reusable utility
  - KISS: Simple state machine for button states
  - No database migrations (client-side only)

### Overall Gate Status (Post-Design)
- ✅ **PASS** - All constitution principles remain satisfied after detailed design
- **Design Approved**: No violations introduced during Phase 1
- **Ready for Phase 2**: Tasks generation approved

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/
│   │   └── shared/
│   │       └── DocumentViewer.tsx          # Modified: Add PDF download functionality
│   └── lib/
│       └── pdf-utils.ts                    # New: PDF generation utilities
└── tests/
    └── components/
        └── shared/
            └── DocumentViewer.test.tsx      # New: Component tests for PDF feature
```

**Structure Decision**: Web frontend project structure. This feature modifies only the frontend (no backend changes). The main change is to the existing `DocumentViewer.tsx` component with a new utility file for PDF generation logic to keep the component focused.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - No constitution violations requiring justification.
