# Implementation Plan: Mechanism-Based Simulation

**Branch**: `038-mechanism-based-simulation` | **Date**: 2026-02-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/038-mechanism-based-simulation/spec.md`

## Summary

Enhance the Monte Carlo simulation engine to incorporate feature mechanism identities (irreversibility, network effects, institutional trust, etc.) that interact with user sensitivities to produce emergent behavioral states. This replaces the current scorecard-only approach where two features with identical scores produce identical outcomes regardless of their nature.

**Technical approach**: Extend FeatureScorecard with a FeatureMechanisms component (6 mechanism types), extend synth simulation_attributes with UserSensitivities (6 sensitivity types), and modify the simulation engine to calculate emergent states from mechanism×sensitivity interactions before probability calculations.

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5.5+ (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0+, Pydantic, NumPy (simulation), React 18, TanStack Query
**Storage**: PostgreSQL 14+ (JSONB for scorecard_data, simulation_attributes)
**Testing**: pytest (backend), Jest/Playwright (frontend)
**Target Platform**: Linux server (Railway), Web browser (React SPA)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: 100 synths × 100 executions < 1 second (existing target, must maintain)
**Constraints**: Backward compatibility with existing experiments (no mechanism = current behavior)
**Scale/Scope**: ~500 synths per simulation, 6 mechanisms × 6 sensitivities = 36 interaction terms

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | ✅ PASS | Tests for new entities, engine modifications, and API endpoints |
| II. Fast Test Battery | ✅ PASS | Unit tests for mechanism calculations will run < 5s |
| III. Complete Test Battery | ✅ PASS | Integration tests for full simulation flow |
| IV. Frequent Commits | ✅ PASS | Atomic commits per component |
| V. Simplicity | ✅ PASS | Simple multiplication interaction model |
| VI. Language | ✅ PASS | Code in English, docs in Portuguese |
| VII. Architecture | ✅ PASS | See notes below |

**Architecture Compliance**:
- Router: Only request → service → response
- Business logic: In simulation services (engine, probability)
- Data access: In repositories (experiment, synth)
- New entities: In domain/entities (FeatureMechanisms, UserSensitivities)
- Validation: Pydantic models with [0,1] constraints

## Project Structure

### Documentation (this feature)

```text
specs/038-mechanism-based-simulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/synth_lab/
│   ├── domain/entities/
│   │   ├── feature_scorecard.py      # MODIFY: Add FeatureMechanisms
│   │   ├── simulation_attributes.py  # MODIFY: Add UserSensitivities
│   │   └── emergent_state.py         # NEW: Calculation results
│   ├── services/simulation/
│   │   ├── engine.py                 # MODIFY: mechanism-aware simulation
│   │   ├── probability.py            # MODIFY: emergent-state-based calculations
│   │   ├── sample_state.py           # MODIFY: sample sensitivities
│   │   └── mechanism_interaction.py  # NEW: mechanism × sensitivity logic
│   ├── api/
│   │   ├── schemas/experiments.py    # MODIFY: Add mechanisms to schemas
│   │   └── routers/experiments.py    # MODIFY: Update endpoints
│   └── alembic/versions/
│       └── 20260204_xxxx_add_mechanisms.py  # NEW: Migration (if needed)
└── tests/
    ├── unit/
    │   ├── test_feature_mechanisms.py
    │   ├── test_user_sensitivities.py
    │   ├── test_emergent_state.py
    │   └── test_mechanism_interaction.py
    └── integration/
        └── test_mechanism_simulation.py

frontend/
├── src/
│   ├── types/
│   │   └── simulation.ts             # MODIFY: Add mechanism types
│   ├── components/
│   │   └── MechanismEditor.tsx       # NEW: Mechanism input UI
│   └── pages/
│       └── ExperimentDetail.tsx      # MODIFY: Display mechanisms
└── tests/
    └── e2e/
        └── mechanism-simulation.spec.ts
```

**Structure Decision**: Web application with backend/frontend separation. Changes are primarily backend (simulation engine, entities) with minimal frontend changes (mechanism editor, result display).

## Complexity Tracking

No violations requiring justification. The feature follows existing patterns:
- New Pydantic entities (like existing ScorecardDimension)
- Extension of existing structures (scorecard_data JSONB, simulation_attributes JSONB)
- Modification of simulation engine (localized to probability calculations)

## Constitution Check (Post-Design)

*Re-evaluated after Phase 1 design completion.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Test-First Development | ✅ PASS | Test files defined in project structure (test_feature_mechanisms.py, etc.) |
| II. Fast Test Battery | ✅ PASS | Unit tests are pure calculations, no I/O - will run < 5s |
| III. Complete Test Battery | ✅ PASS | Integration test (test_mechanism_simulation.py) covers full flow |
| IV. Frequent Commits | ✅ PASS | Plan defines atomic components for separate commits |
| V. Simplicity | ✅ PASS | Simple multiplication model, no over-engineering |
| VI. Language | ✅ PASS | quickstart.md in Portuguese, code entities in English |
| VII. Architecture | ✅ PASS | Verified against CLAUDE.md rules below |

**Architecture Verification (Post-Design)**:
- ✅ Router: No business logic in routers - only request → service → response
- ✅ Services: mechanism_interaction.py in services/simulation/ for business logic
- ✅ Entities: FeatureMechanisms, UserSensitivities in domain/entities/
- ✅ JSONB extension: No new tables, extends existing scorecard_data and simulation_attributes
- ✅ Validation: Pydantic with Field(ge=0.0, le=1.0) constraints
- ✅ Backward compatibility: Defaults (0.0 for mechanisms, 0.5 for sensitivities) preserve existing behavior

## Generated Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Research | `specs/038-mechanism-based-simulation/research.md` | ✅ Complete |
| Data Model | `specs/038-mechanism-based-simulation/data-model.md` | ✅ Complete |
| API Contracts | `specs/038-mechanism-based-simulation/contracts/api.yaml` | ✅ Complete |
| Quickstart | `specs/038-mechanism-based-simulation/quickstart.md` | ✅ Complete |
| Tasks | `specs/038-mechanism-based-simulation/tasks.md` | ⏳ Pending (/speckit.tasks) |
