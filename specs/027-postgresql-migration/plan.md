# Implementation Plan: PostgreSQL Migration with SQLAlchemy

**Branch**: `027-postgresql-migration` | **Date**: 2026-01-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/027-postgresql-migration/spec.md`

## Summary

Migrate the synth-lab application from SQLite to PostgreSQL using SQLAlchemy ORM and Alembic migrations. The migration follows a phased approach that maintains backward compatibility during transition, allowing incremental repository migration without application downtime. Key deliverables include SQLAlchemy models for all 19 existing tables, an Alembic migration environment, updated repositories using the new ORM, and Docker-based PostgreSQL testing infrastructure.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: SQLAlchemy 2.0+, Alembic 1.12+, psycopg2-binary (PostgreSQL driver)
**Storage**: PostgreSQL 14+ (production), SQLite 3 with JSON1 (development/fallback)
**Testing**: pytest 8.0+, pytest-asyncio 0.23+
**Target Platform**: Linux server (Docker), macOS (development)
**Project Type**: Web application (FastAPI backend + React frontend)
**Performance Goals**: 100 concurrent database operations, <5s application startup
**Constraints**: Zero downtime during migration, 100% data fidelity, backward compatibility
**Scale/Scope**: 19 database tables, 18 repository files, single database instance

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development (TDD/BDD) | PASS | Acceptance scenarios defined in spec; tests will be written before implementation |
| II. Fast Test Battery (<5s) | PASS | Unit tests for models/repositories will be fast; integration tests in slow battery |
| III. Complete Test Battery Before PR | PASS | Full test suite runs against both SQLite and PostgreSQL |
| IV. Frequent Version Control Commits | PASS | Phased migration enables atomic commits per repository |
| V. Simplicity and Code Quality | PASS | SQLAlchemy ORM simplifies database access; files <500 lines |
| VI. Language | PASS | Code in English, documentation in Portuguese as needed |
| VII. Architecture | PASS | Repositories remain in repositories/; no router/service changes |
| VIII. Other Principles | PASS | Alembic for migrations (constitution requirement); DRY via base models |

**Gate Result**: PASS - No violations. Proceed with Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/027-postgresql-migration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - no new API endpoints)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/synth_lab/
├── infrastructure/
│   ├── database.py              # Legacy SQLite (kept during migration)
│   ├── database_v2.py           # NEW: SQLAlchemy engine + session factory
│   └── config.py                # Updated: DATABASE_URL support
├── models/                      # NEW: SQLAlchemy ORM models
│   ├── __init__.py
│   ├── base.py                  # Declarative base, common mixins
│   ├── experiment.py            # Experiment, InterviewGuide models
│   ├── synth.py                 # Synth, SynthGroup models
│   ├── analysis.py              # AnalysisRun, SynthOutcome, AnalysisCache
│   ├── research.py              # ResearchExecution, Transcript models
│   ├── exploration.py           # Exploration, ScenarioNode models
│   ├── insight.py               # ChartInsight, SensitivityResult, RegionAnalysis
│   ├── document.py              # ExperimentDocument model
│   └── legacy.py                # FeatureScorecard, SimulationRun (deprecated)
├── repositories/
│   ├── base.py                  # Updated: SQLAlchemy session support
│   ├── experiment_repository.py # Migrated to SQLAlchemy
│   ├── synth_repository.py      # Migrated to SQLAlchemy
│   ├── analysis_repository.py   # Migrated to SQLAlchemy
│   └── [... 15 more repositories]
└── alembic/                     # NEW: Alembic migration environment
    ├── alembic.ini
    ├── env.py
    ├── script.py.mako
    └── versions/
        └── 001_initial_schema.py

tests/
├── unit/
│   └── models/                  # NEW: Model unit tests
└── integration/
    └── repositories/            # Updated: Test both backends

docker/
└── docker-compose.postgres.yml  # NEW: PostgreSQL test environment
```

**Structure Decision**: Existing web application structure preserved. New `models/` directory for SQLAlchemy ORM models. Alembic environment in `src/synth_lab/alembic/`. Repositories updated in-place with backward-compatible interfaces.

## Complexity Tracking

> No violations requiring justification. Migration follows standard SQLAlchemy/Alembic patterns.
