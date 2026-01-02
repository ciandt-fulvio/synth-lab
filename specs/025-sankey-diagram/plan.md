# Implementation Plan: Sankey Diagram for Outcome Flow Visualization

**Branch**: `025-sankey-diagram` | **Date**: 2025-12-31 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/025-sankey-diagram/spec.md`

## Summary

Implement a Sankey diagram visualization showing outcome flow: Population → Outcomes (did_not_try, failed, success) → Root Causes. The diagram will be displayed in the "Geral" (Overview) tab of quantitative analysis, positioned above the "Tentativa vs Sucesso" chart. Root cause diagnosis uses gap analysis between synth traits and feature scorecard dimensions.

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5.5+ (frontend)
**Primary Dependencies**: FastAPI, Pydantic, React 18, D3-Sankey (d3-sankey + d3-shape), TanStack Query
**Storage**: PostgreSQL 3 with JSON1 extension (output/synthlab.db)
**Testing**: pytest (backend), React Testing Library (frontend)
**Target Platform**: Web application (Linux/macOS server, modern browsers)
**Project Type**: Web (frontend + backend)
**Performance Goals**: Render within 2 seconds for up to 10,000 synths
**Constraints**: Follow existing analysis chart patterns (React Query caching, parallel fetch)
**Scale/Scope**: Single chart component with backend endpoint

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. TDD/BDD | PASS | Acceptance scenarios defined in spec with Given-When-Then format |
| II. Fast Test Battery | PASS | Unit tests for gap calculation will run < 0.5s each |
| III. Complete Tests Before PR | PASS | Integration tests planned for endpoint |
| IV. Frequent Commits | PASS | Will commit at each task completion |
| V. Simplicity | PASS | Single service method, single endpoint, single component |
| VI. Language | PASS | Code in English, labels in Portuguese (i18n ready) |
| VII. Architecture | PASS | Backend: router → service → repository; Frontend: hooks → services |
| VIII. Other Principles | PASS | Using existing patterns, no new dependencies |

## Project Structure

### Documentation (this feature)

```text
specs/025-sankey-diagram/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── sankey-flow.yaml # OpenAPI spec
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/synth_lab/
│   ├── api/routers/
│   │   └── analysis.py          # Add GET endpoint for sankey-flow
│   ├── domain/entities/
│   │   └── chart_data.py        # Add SankeyFlowChart entity
│   └── services/simulation/
│       └── chart_data_service.py # Add get_sankey_flow method
└── tests/
    ├── unit/
    │   └── test_sankey_flow.py  # Unit tests for gap calculation
    └── integration/
        └── test_analysis_sankey.py # Integration tests for endpoint

frontend/
├── src/
│   ├── components/experiments/results/
│   │   ├── SankeyFlowSection.tsx    # Section with chart
│   │   └── charts/
│   │       └── SankeyFlowChart.tsx  # Sankey diagram component
│   ├── hooks/
│   │   └── use-analysis-charts.ts   # Add useAnalysisSankeyFlow hook
│   ├── services/
│   │   └── experiments-api.ts       # Add getAnalysisSankeyFlow function
│   ├── lib/
│   │   └── query-keys.ts            # Add sankeyFlow key
│   └── types/
│       └── simulation.ts            # Add SankeyFlowChart type
└── tests/
    └── components/
        └── SankeyFlowChart.test.tsx # Component tests
```

**Structure Decision**: Web application with separate backend (FastAPI) and frontend (React/TypeScript). Following existing patterns in the codebase.

## Complexity Tracking

No violations requiring justification. The implementation follows existing patterns and does not introduce new complexity.
