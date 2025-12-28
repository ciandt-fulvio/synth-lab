# Implementation Plan: Experiment Results Frontend

**Branch**: `020-experiment-results-frontend` | **Date**: 2025-12-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/020-experiment-results-frontend/spec.md`

## Summary

Implement frontend display of experiment analysis results with 6 sequential phases (Visão Geral, Localização, Segmentação, Casos Especiais, Aprofundamento, Insights LLM). The implementation follows the existing frontend architecture patterns (pages → hooks → services → types), integrates with backend API endpoints already implemented, and uses Recharts for visualizations with shadcn/ui for consistent styling.

## Technical Context

**Language/Version**: TypeScript 5.5.3 (frontend)
**Primary Dependencies**: React 18.3.1, TanStack React Query 5.56+, Recharts 2.12.7+, shadcn/ui (Radix UI), Tailwind CSS 3.4+
**Storage**: N/A (data from backend API)
**Testing**: Manual testing + TypeScript type checking (`npx tsc --noEmit`)
**Target Platform**: Web browser (React SPA)
**Project Type**: Web application (frontend only for this feature)
**Performance Goals**: Charts render within 2 seconds, tab switching under 1 second
**Constraints**: Follow existing frontend architecture patterns (docs/arquitetura_front.md)
**Scale/Scope**: 6 analysis phases, ~15 chart types, integration with 20+ backend endpoints

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | N/A | Frontend feature - manual testing with TypeScript type checking |
| II. Fast Test Battery | N/A | No automated frontend tests required for this feature |
| III. Complete Test Battery | N/A | Manual E2E testing before PR |
| IV. Frequent Commits | PASS | Commit per phase/component |
| V. Simplicity & Code Quality | PASS | Follow existing patterns, max 500 lines per file |
| VI. Language | PASS | Code in English, documentation in Portuguese |
| VII. Architecture - Frontend | PASS | Pages → Hooks → Services → Types pattern |

**Gate Violations**: None

## Project Structure

### Documentation (this feature)

```text
specs/020-experiment-results-frontend/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (TypeScript types)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API contracts from backend)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
frontend/src/
├── pages/
│   └── ExperimentDetail.tsx         # Existing page (extend with results tabs)
│
├── components/
│   ├── experiments/
│   │   ├── AnalysisPhaseTabs.tsx    # Existing tab navigation (extend)
│   │   └── results/                 # NEW: Results components
│   │       ├── PhaseOverview.tsx    # Phase 1: Visão Geral
│   │       ├── PhaseLocation.tsx    # Phase 2: Localização
│   │       ├── PhaseSegmentation.tsx# Phase 3: Segmentação
│   │       ├── PhaseEdgeCases.tsx   # Phase 4: Casos Especiais
│   │       ├── PhaseExplainability.tsx # Phase 5: Aprofundamento
│   │       ├── PhaseInsights.tsx    # Phase 6: Insights LLM
│   │       └── charts/              # Reusable chart components
│   │           ├── TryVsSuccessChart.tsx
│   │           ├── OutcomeDistributionChart.tsx
│   │           ├── SankeyDiagram.tsx
│   │           ├── FailureHeatmap.tsx
│   │           ├── BoxPlotChart.tsx
│   │           ├── ScatterCorrelationChart.tsx
│   │           ├── TornadoChart.tsx
│   │           ├── ElbowChart.tsx
│   │           ├── RadarComparisonChart.tsx
│   │           ├── DendrogramChart.tsx
│   │           ├── ShapWaterfallChart.tsx
│   │           ├── ShapSummaryChart.tsx
│   │           ├── PDPChart.tsx
│   │           └── InsightCard.tsx
│   │
│   └── shared/
│       ├── ChartContainer.tsx       # NEW: Wrapper with loading/error/empty states
│       └── MarkdownPopup.tsx        # Existing (reuse for insights)
│
├── hooks/
│   ├── use-simulation-charts.ts     # NEW: Chart data fetching hooks
│   ├── use-clustering.ts            # NEW: Clustering hooks
│   ├── use-outliers.ts              # NEW: Outlier detection hooks
│   ├── use-explainability.ts        # NEW: SHAP/PDP hooks
│   └── use-insights.ts              # NEW: LLM insights hooks
│
├── services/
│   └── simulation-api.ts            # NEW: Simulation API service
│
├── types/
│   └── simulation.ts                # NEW: Simulation result types
│
└── lib/
    └── query-keys.ts                # Extend with simulation keys
```

**Structure Decision**: Extend existing frontend structure with new components under `components/experiments/results/` and dedicated hooks/services for simulation data.

## Complexity Tracking

> **No violations to justify** - architecture follows existing patterns.
