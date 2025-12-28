# Tasks: Experiment Results Frontend

**Input**: Design documents from `/specs/020-experiment-results-frontend/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not required (frontend feature - manual testing + TypeScript type checking)

**Organization**: Tasks grouped by user story (6 analysis phases) to enable independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US6)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Types, services, and shared components used by all user stories

- [x] T001 Create TypeScript types for simulation results in frontend/src/types/simulation.ts
- [x] T002 Create simulation API service with all endpoint functions in frontend/src/services/simulation-api.ts
- [x] T003 [P] Extend query keys with simulation keys in frontend/src/lib/query-keys.ts
- [x] T004 [P] Create ChartContainer wrapper component for loading/error/empty states in frontend/src/components/shared/ChartContainer.tsx

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core hooks and page integration that all phases depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create base useSimulationCharts hook with overview chart queries in frontend/src/hooks/use-simulation-charts.ts
- [x] T006 [P] Create useClustering hook with cluster management in frontend/src/hooks/use-clustering.ts
- [x] T007 [P] Create useOutliers hook with extreme cases and outliers in frontend/src/hooks/use-outliers.ts
- [x] T008 [P] Create useExplainability hook with SHAP and PDP queries in frontend/src/hooks/use-explainability.ts
- [x] T009 [P] Create useInsights hook with LLM insight generation in frontend/src/hooks/use-insights.ts
- [x] T010 Integrate AnalysisPhaseTabs with phase content in frontend/src/pages/ExperimentDetail.tsx
- [x] T011 Create results directory structure in frontend/src/components/experiments/results/

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Visão Geral (Overview) (Priority: P1)

**Goal**: UX Researcher views overall simulation results with Try vs Success, Distribution, and Sankey charts

**Independent Test**: Navigate to `/experiments/{id}`, select "Visão Geral" tab, verify all three charts render correctly with data

### Implementation for User Story 1

- [x] T012 [P] [US1] Create TryVsSuccessChart scatter component using Recharts in frontend/src/components/experiments/results/charts/TryVsSuccessChart.tsx
- [x] T013 [P] [US1] Create OutcomeDistributionChart pie component using Recharts in frontend/src/components/experiments/results/charts/OutcomeDistributionChart.tsx
- [x] T014 [P] [US1] Create SankeyDiagram component using Recharts Sankey in frontend/src/components/experiments/results/charts/SankeyDiagram.tsx
- [x] T015 [US1] Create PhaseOverview container component assembling charts in frontend/src/components/experiments/results/PhaseOverview.tsx
- [x] T016 [US1] Wire PhaseOverview to AnalysisPhaseTabs in frontend/src/pages/ExperimentDetail.tsx

**Checkpoint**: User Story 1 is fully functional and independently testable

---

## Phase 4: User Story 2 - Localização (Problem Location) (Priority: P1)

**Goal**: UX Researcher identifies problem locations using Heatmap, Box Plot, Scatter, and Tornado charts

**Independent Test**: Navigate to "Localização" tab, verify all four visualization types render with correct data

### Implementation for User Story 2

- [x] T017 [P] [US2] Create FailureHeatmap grid component using CSS Grid in frontend/src/components/experiments/results/charts/FailureHeatmap.tsx
- [x] T018 [P] [US2] Create BoxPlotChart component using custom SVG in frontend/src/components/experiments/results/charts/BoxPlotChart.tsx
- [x] T019 [P] [US2] Create ScatterCorrelationChart component using Recharts in frontend/src/components/experiments/results/charts/ScatterCorrelationChart.tsx
- [x] T020 [P] [US2] Create TornadoChart horizontal bar component using Recharts in frontend/src/components/experiments/results/charts/TornadoChart.tsx
- [x] T021 [US2] Create PhaseLocation container with axis selection controls in frontend/src/components/experiments/results/PhaseLocation.tsx
- [x] T022 [US2] Wire PhaseLocation to AnalysisPhaseTabs in frontend/src/pages/ExperimentDetail.tsx

**Checkpoint**: User Stories 1 AND 2 both work independently

---

## Phase 5: User Story 3 - Segmentação (Persona Segmentation) (Priority: P2)

**Goal**: UX Researcher groups synths into clusters using K-Means, Elbow, Radar, and Dendrogram visualizations

**Independent Test**: Navigate to "Segmentação" tab, generate clusters, verify elbow chart, radar comparison, and dendrogram display

### Implementation for User Story 3

- [x] T023 [P] [US3] Create ElbowChart line component using Recharts in frontend/src/components/experiments/results/charts/ElbowChart.tsx
- [x] T024 [P] [US3] Create RadarComparisonChart component using Recharts RadarChart in frontend/src/components/experiments/results/charts/RadarComparisonChart.tsx
- [x] T025 [P] [US3] Create DendrogramChart component using custom SVG tree in frontend/src/components/experiments/results/charts/DendrogramChart.tsx
- [x] T026 [US3] Create PhaseSegmentation container with cluster generation UI in frontend/src/components/experiments/results/PhaseSegmentation.tsx
- [x] T027 [US3] Wire PhaseSegmentation to AnalysisPhaseTabs in frontend/src/pages/ExperimentDetail.tsx

**Checkpoint**: User Stories 1, 2, AND 3 all work independently

---

## Phase 6: User Story 4 - Casos Especiais (Edge Cases) (Priority: P2)

**Goal**: UX Researcher identifies extreme cases and outliers for qualitative follow-up

**Independent Test**: Navigate to "Casos Especiais" tab, verify extreme cases table and outlier detection results display correctly

### Implementation for User Story 4

- [ ] T028 [P] [US4] Create ExtremeCasesTable component with worst/best/unexpected sections in frontend/src/components/experiments/results/ExtremeCasesTable.tsx
- [ ] T029 [P] [US4] Create OutliersTable component with anomaly scores in frontend/src/components/experiments/results/OutliersTable.tsx
- [ ] T030 [US4] Create PhaseEdgeCases container with synth profile cards in frontend/src/components/experiments/results/PhaseEdgeCases.tsx
- [ ] T031 [US4] Wire PhaseEdgeCases to AnalysisPhaseTabs in frontend/src/pages/ExperimentDetail.tsx

**Checkpoint**: User Stories 1, 2, 3, AND 4 all work independently

---

## Phase 7: User Story 5 - Aprofundamento (Deep Explanation) (Priority: P2)

**Goal**: UX Researcher understands WHY specific synths succeeded or failed using SHAP and PDP visualizations

**Independent Test**: Select a synth from edge cases, view SHAP waterfall chart and PDP curves for key features

### Implementation for User Story 5

- [ ] T032 [P] [US5] Create ShapWaterfallChart horizontal bar component in frontend/src/components/experiments/results/charts/ShapWaterfallChart.tsx
- [ ] T033 [P] [US5] Create ShapSummaryChart global importance component in frontend/src/components/experiments/results/charts/ShapSummaryChart.tsx
- [ ] T034 [P] [US5] Create PDPChart line component with confidence intervals in frontend/src/components/experiments/results/charts/PDPChart.tsx
- [ ] T035 [US5] Create PhaseExplainability container with synth selector in frontend/src/components/experiments/results/PhaseExplainability.tsx
- [ ] T036 [US5] Wire PhaseExplainability to AnalysisPhaseTabs in frontend/src/pages/ExperimentDetail.tsx

**Checkpoint**: User Stories 1-5 all work independently

---

## Phase 8: User Story 6 - Insights LLM (AI-Generated Insights) (Priority: P3)

**Goal**: UX Researcher obtains AI-generated insights and executive summary for stakeholder communication

**Independent Test**: Navigate to "Insights" tab, generate insights for charts, generate executive summary

### Implementation for User Story 6

- [ ] T037 [P] [US6] Create InsightCard component with caption, explanation, evidence, recommendation in frontend/src/components/experiments/results/charts/InsightCard.tsx
- [ ] T038 [P] [US6] Create InsightsList component with all generated insights in frontend/src/components/experiments/results/InsightsList.tsx
- [ ] T039 [US6] Create PhaseInsights container with generation controls in frontend/src/components/experiments/results/PhaseInsights.tsx
- [ ] T040 [US6] Wire PhaseInsights to AnalysisPhaseTabs in frontend/src/pages/ExperimentDetail.tsx
- [ ] T041 [US6] Add executive summary generation with MarkdownPopup display in frontend/src/components/experiments/results/PhaseInsights.tsx

**Checkpoint**: All 6 user stories are independently functional

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 Add keyboard navigation (←/→) for phase tabs in frontend/src/pages/ExperimentDetail.tsx
- [ ] T043 [P] Add responsive layouts for all phase components
- [ ] T044 [P] Run TypeScript type checking and fix any errors (npx tsc --noEmit)
- [ ] T045 Manual E2E test: navigate through all 6 phases with valid simulation data
- [ ] T046 Manual E2E test: verify loading, error, and empty states for all charts
- [ ] T047 Performance test: verify charts render within 2 seconds, tab switch under 1 second

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User stories can proceed in priority order (P1 → P2 → P3)
  - Within same priority, can run in parallel (US1 || US2, then US3 || US4 || US5)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

| Story | Priority | Depends On | Can Start After |
|-------|----------|------------|-----------------|
| US1 (Visão Geral) | P1 | Foundational | Phase 2 |
| US2 (Localização) | P1 | Foundational | Phase 2 |
| US3 (Segmentação) | P2 | Foundational | Phase 2 |
| US4 (Casos Especiais) | P2 | Foundational | Phase 2 |
| US5 (Aprofundamento) | P2 | Foundational | Phase 2 |
| US6 (Insights LLM) | P3 | Foundational | Phase 2 |

**Note**: US4-US5 have logical flow dependency (selecting synth from edge cases to view SHAP) but are independently testable.

### Within Each User Story

- Chart components (marked [P]) can run in parallel
- Container component depends on chart components
- Page wiring depends on container component

### Parallel Opportunities

**Phase 1 (Setup)**:
```bash
# T001 and T002 are sequential (types before service)
# T003 and T004 can run in parallel after T001
```

**Phase 2 (Foundational)**:
```bash
# T006, T007, T008, T009 can run in parallel (different hooks)
# T010 and T011 depend on hooks
```

**Phase 3 (US1 - Overview)**:
```bash
# Launch all chart components in parallel:
Task: "TryVsSuccessChart in charts/TryVsSuccessChart.tsx"
Task: "OutcomeDistributionChart in charts/OutcomeDistributionChart.tsx"
Task: "SankeyDiagram in charts/SankeyDiagram.tsx"
```

**Phase 4 (US2 - Location)**:
```bash
# Launch all chart components in parallel:
Task: "FailureHeatmap in charts/FailureHeatmap.tsx"
Task: "BoxPlotChart in charts/BoxPlotChart.tsx"
Task: "ScatterCorrelationChart in charts/ScatterCorrelationChart.tsx"
Task: "TornadoChart in charts/TornadoChart.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T011)
3. Complete Phase 3: User Story 1 (T012-T016)
4. **STOP and VALIDATE**: Test US1 independently - "Visão Geral" tab works
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Visão Geral) → Test → Deploy (MVP!)
3. Add US2 (Localização) → Test → Deploy
4. Add US3 (Segmentação) → Test → Deploy
5. Add US4 (Casos Especiais) → Test → Deploy
6. Add US5 (Aprofundamento) → Test → Deploy
7. Add US6 (Insights LLM) → Test → Deploy (Complete!)

### P1 Priority Sprint

Focus on P1 stories first (US1 + US2):

1. Complete Setup + Foundational
2. Complete US1 (Visão Geral) - 5 tasks
3. Complete US2 (Localização) - 6 tasks
4. **STOP and VALIDATE**: Core analysis flow works

---

## Summary

| Phase | Tasks | Parallel Tasks |
|-------|-------|----------------|
| Setup | 4 | 2 |
| Foundational | 7 | 4 |
| US1 - Visão Geral | 5 | 3 |
| US2 - Localização | 6 | 4 |
| US3 - Segmentação | 5 | 3 |
| US4 - Casos Especiais | 4 | 2 |
| US5 - Aprofundamento | 5 | 3 |
| US6 - Insights LLM | 5 | 2 |
| Polish | 6 | 2 |
| **Total** | **47** | **25** |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies
