# Implementation Plan: Unified Experiment Documents

**Branch**: `026-experiment-documents` | **Date**: 2025-12-31 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/026-experiment-documents/spec.md`

## Summary

Complete the unified experiment documents feature by:
1. Adding the `experiment_documents` table to the database schema with migration
2. Registering the documents router in the FastAPI main application
3. Fixing the import issue in the documents router (`get_db` import path)

This is a "finalization" task - most code already exists but is not properly integrated.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.5 (frontend)
**Primary Dependencies**: FastAPI 0.109+, Pydantic 2.5+, SQLite 3 with JSON1, React 18, TanStack Query 5.56+
**Storage**: SQLite 3 with WAL mode (`output/synthlab.db`)
**Testing**: pytest 8.0+, pytest-asyncio 0.23+
**Target Platform**: Linux/macOS server, web browser
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Document listing < 200ms, document retrieval < 100ms
**Constraints**: Backward compatible with existing databases (migration required)
**Scale/Scope**: Single document per type per experiment, 3 document types

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | PASS | Existing code has validation blocks; new changes require tests |
| II. Fast Test Battery | PASS | Changes are small, tests will be fast |
| III. Complete Test Battery | PASS | Will run full suite before PR |
| IV. Frequent Commits | PASS | Plan includes incremental commits |
| V. Simplicity | PASS | No new complexity - integrating existing code |
| VI. Language | PASS | Code in English, docs in Portuguese |
| VII. Architecture | PASS | Follows existing patterns (repository, service, router) |
| VIII. Other Principles | PASS | Phoenix tracing already in ExecutiveSummaryService |

**Gate Result**: PASS - No violations

## Project Structure

### Documentation (this feature)

```text
specs/026-experiment-documents/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── documents-api.yaml
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
# Backend - existing files to modify
src/synth_lab/
├── infrastructure/
│   └── database.py              # ADD: experiment_documents table to SCHEMA_SQL + migration
├── api/
│   ├── main.py                  # ADD: documents router registration
│   ├── dependencies.py          # EXISTS: get_db function
│   ├── routers/
│   │   └── documents.py         # FIX: import get_db from api.dependencies
│   └── schemas/
│       └── documents.py         # EXISTS: API schemas
├── domain/entities/
│   └── experiment_document.py   # EXISTS: Entity definition
├── repositories/
│   └── experiment_document_repository.py  # EXISTS: Data access layer
└── services/
    ├── document_service.py      # EXISTS: Document service
    └── executive_summary_service.py  # EXISTS: Uses document_service

# Frontend - existing files (no changes needed)
frontend/src/
├── types/
│   └── document.ts              # EXISTS: TypeScript types
├── services/
│   └── documents-api.ts         # EXISTS: API client
├── hooks/
│   └── use-documents.ts         # EXISTS: React Query hooks
└── components/shared/
    └── DocumentViewer.tsx       # EXISTS: UI component

# Tests
tests/
├── unit/
│   └── test_experiment_document_repository.py  # ADD: Repository tests
└── integration/
    └── test_documents_api.py    # ADD: API integration tests
```

**Structure Decision**: Web application with backend + frontend. Backend changes only - frontend is ready.

## Complexity Tracking

> No violations to justify - feature follows existing patterns.

N/A - This is a simple integration task with no new complexity.

## Implementation Notes

### Key Findings from Codebase Analysis

1. **Missing Table in Schema**: The `experiment_documents` table is defined in test fixtures but NOT in `SCHEMA_SQL` in `database.py`

2. **Missing Router Registration**: The documents router exists at `api/routers/documents.py` but is not imported/registered in `main.py`

3. **Import Bug**: The documents router has an incorrect import:
   ```python
   # Current (broken):
   from synth_lab.infrastructure.database import get_db

   # Should be:
   from synth_lab.api.dependencies import get_db
   ```

4. **Table Schema** (from existing test fixtures):
   ```sql
   CREATE TABLE experiment_documents (
       id TEXT PRIMARY KEY,
       experiment_id TEXT NOT NULL,
       document_type TEXT NOT NULL,
       markdown_content TEXT NOT NULL,
       metadata TEXT,
       generated_at TEXT NOT NULL,
       model TEXT DEFAULT 'gpt-4o-mini',
       status TEXT NOT NULL DEFAULT 'completed',
       error_message TEXT,
       UNIQUE(experiment_id, document_type),
       FOREIGN KEY (experiment_id) REFERENCES experiments(id)
   );
   ```

### Migration Strategy

The migration will use the existing pattern in `init_database()`:
1. Check if table exists using `PRAGMA table_info`
2. If not exists, create the table
3. Log migration completion

This is consistent with migrations v10 (status column), v11 (scenario_id), and v14 (short_action).
