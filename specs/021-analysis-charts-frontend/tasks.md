# Tasks: Analysis Charts Frontend Integration

**Input**: Design documents from `/specs/021-analysis-charts-frontend/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are DEFERRED per plan.md (visual testing focus). Frontend tests will be written after component implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app frontend**: `frontend/src/`
- Hooks: `frontend/src/hooks/`
- Components: `frontend/src/components/experiments/results/`
- Charts: `frontend/src/components/experiments/results/charts/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing infrastructure and create missing hooks

- [x] T001 Verify existing types in frontend/src/types/simulation.ts cover all Phase 4-6 charts
- [x] T002 Verify existing API functions in frontend/src/services/simulation-api.ts cover all Phase 4-6 endpoints
- [x] T003 Verify existing query keys in frontend/src/lib/query-keys.ts cover all Phase 4-6 charts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create new hooks for phases 4-6 that all user stories depend on

**⚠️ CRITICAL**: User story implementation requires these hooks

- [x] T004 [P] Create use-edge-cases.ts hook with useExtremeCases() in frontend/src/hooks/use-edge-cases.ts
- [x] T005 [P] Create use-edge-cases.ts hook with useOutliers() in frontend/src/hooks/use-edge-cases.ts
- [x] T006 [P] Create use-explainability.ts hook with useShapSummary() in frontend/src/hooks/use-explainability.ts
- [x] T007 [P] Create use-explainability.ts hook with useShapExplanation() in frontend/src/hooks/use-explainability.ts
- [x] T008 [P] Create use-explainability.ts hook with usePDP() in frontend/src/hooks/use-explainability.ts
- [x] T009 [P] Create use-explainability.ts hook with usePDPComparison() in frontend/src/hooks/use-explainability.ts
- [x] T010 [P] Create use-insights.ts hook with useSimulationInsights() in frontend/src/hooks/use-insights.ts
- [x] T011 [P] Create use-insights.ts hook with useGenerateChartInsight() mutation in frontend/src/hooks/use-insights.ts
- [x] T012 [P] Create use-insights.ts hook with useGenerateExecutiveSummary() mutation in frontend/src/hooks/use-insights.ts

**Checkpoint**: All hooks ready - section component implementation can now begin in parallel

---

## Phase 3: User Story 1 - Problem Location Charts (Priority: P1) 🎯 MVP

**Goal**: UX Researcher accesses Problem Location phase to identify where user experience breaks using Heatmap, Box Plot, Scatter, and Tornado charts.

**Independent Test**: Navigate to an experiment's results page, select "Localização" tab, verify all four chart types render correctly with interactive controls.

### Implementation for User Story 1

- [x] T013 [P] [US1] Create HeatmapSection.tsx with axis selectors and explanation collapsible in frontend/src/components/experiments/results/HeatmapSection.tsx
- [x] T014 [P] [US1] Create BoxPlotSection.tsx with attribute selector and explanation collapsible in frontend/src/components/experiments/results/BoxPlotSection.tsx
- [x] T015 [P] [US1] Create ScatterSection.tsx with X/Y axis selectors and explanation collapsible in frontend/src/components/experiments/results/ScatterSection.tsx
- [x] T016 [P] [US1] Create TornadoSection.tsx with explanation collapsible in frontend/src/components/experiments/results/TornadoSection.tsx
- [x] T017 [US1] Update PhaseLocation.tsx to compose all four section components in frontend/src/components/experiments/results/PhaseLocation.tsx
- [x] T018 [US1] Export new sections from frontend/src/components/experiments/results/index.ts

**Checkpoint**: User Story 1 complete - Problem Location phase has all charts with explanations

---

## Phase 4: User Story 2 - Persona Segmentation (Priority: P2)

**Goal**: UX Researcher groups synths into clusters using K-Means or Hierarchical Clustering to identify distinct persona segments.

**Independent Test**: Navigate to Segmentation phase, configure clustering parameters, generate clusters, view Elbow/Dendrogram and Radar comparison charts.

### Implementation for User Story 2

- [x] T019 [P] [US2] Create ElbowSection.tsx with K-Means config and explanation collapsible in frontend/src/components/experiments/results/ElbowSection.tsx
- [x] T020 [P] [US2] Create DendrogramSection.tsx with cut height interaction and explanation collapsible in frontend/src/components/experiments/results/DendrogramSection.tsx
- [x] T021 [P] [US2] Create RadarSection.tsx with cluster comparison and explanation collapsible in frontend/src/components/experiments/results/RadarSection.tsx
- [x] T022 [US2] Update PhaseSegmentation.tsx to add explanation collapsibles to existing controls in frontend/src/components/experiments/results/PhaseSegmentation.tsx
- [x] T023 [US2] Export new sections from frontend/src/components/experiments/results/index.ts

**Checkpoint**: User Story 2 complete - Segmentation phase has explanation collapsibles and improved UX

---

## Phase 5: User Story 3 - Edge Cases Identification (Priority: P3)

**Goal**: UX Researcher identifies extreme synths and statistical outliers to select candidates for qualitative interviews.

**Independent Test**: Navigate to Edge Cases phase, view tables of extreme cases (worst failures, best successes, unexpected) and outliers.

### Implementation for User Story 3

- [x] T024 [P] [US3] Create ExtremeCasesSection.tsx with categorized tables and explanation collapsible in frontend/src/components/experiments/results/ExtremeCasesSection.tsx
- [x] T025 [P] [US3] Create OutliersSection.tsx with contamination slider and explanation collapsible in frontend/src/components/experiments/results/OutliersSection.tsx
- [x] T026 [US3] Update PhaseEdgeCases.tsx to compose ExtremeCasesSection and OutliersSection in frontend/src/components/experiments/results/PhaseEdgeCases.tsx
- [x] T027 [US3] Export new sections from frontend/src/components/experiments/results/index.ts

**Checkpoint**: User Story 3 complete - Edge Cases phase shows extreme cases and outliers for interview selection

---

## Phase 6: User Story 4 - Deep Explanation (Priority: P4)

**Goal**: UX Researcher understands why specific synths failed using SHAP explanations and PDP charts for feature impact analysis.

**Independent Test**: Navigate to Explainability phase, view SHAP summary, select synth for individual SHAP explanation, view PDP charts.

### Implementation for User Story 4

- [x] T028 [P] [US4] Create ShapSummaryChart.tsx bar chart in frontend/src/components/experiments/results/charts/ShapSummaryChart.tsx
- [x] T029 [P] [US4] Create ShapWaterfallChart.tsx waterfall chart in frontend/src/components/experiments/results/charts/ShapWaterfallChart.tsx
- [x] T030 [P] [US4] Create PDPChart.tsx line chart with area in frontend/src/components/experiments/results/charts/PDPChart.tsx
- [x] T031 [P] [US4] Create PDPComparisonChart.tsx multi-feature comparison in frontend/src/components/experiments/results/charts/PDPComparisonChart.tsx
- [x] T032 [P] [US4] Create ShapSummarySection.tsx with explanation collapsible in frontend/src/components/experiments/results/ShapSummarySection.tsx
- [x] T033 [P] [US4] Create ShapWaterfallSection.tsx with synth selector and explanation in frontend/src/components/experiments/results/ShapWaterfallSection.tsx
- [x] T034 [P] [US4] Create PDPSection.tsx with feature selector and explanation in frontend/src/components/experiments/results/PDPSection.tsx
- [x] T035 [US4] Update PhaseExplainability.tsx to compose SHAP and PDP sections in frontend/src/components/experiments/results/PhaseExplainability.tsx
- [x] T036 [US4] Export new charts and sections from frontend/src/components/experiments/results/index.ts and charts/index.ts

**Checkpoint**: User Story 4 complete - Explainability phase shows SHAP and PDP analysis

---

## Phase 7: User Story 5 - LLM Insights (Priority: P5)

**Goal**: UX Researcher obtains AI-generated insights and executive summary to communicate findings to stakeholders.

**Independent Test**: Navigate to Insights phase, view existing insights, generate new insights for charts or executive summary.

### Implementation for User Story 5

- [x] T037 [P] [US5] Create InsightsListSection.tsx with insight cards and generate button in frontend/src/components/experiments/results/InsightsListSection.tsx
- [x] T038 [P] [US5] Create ExecutiveSummarySection.tsx with markdown rendering and generate button in frontend/src/components/experiments/results/ExecutiveSummarySection.tsx
- [x] T039 [US5] Update PhaseInsights.tsx to compose InsightsListSection and ExecutiveSummarySection in frontend/src/components/experiments/results/PhaseInsights.tsx
- [x] T040 [US5] Export new sections from frontend/src/components/experiments/results/index.ts

**Checkpoint**: User Story 5 complete - Insights phase shows LLM-generated insights and executive summary

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T041 [P] Add "Generate Insight" button to all chart sections in Problem Location phase
- [x] T042 [P] Add "Generate Insight" button to all chart sections in Segmentation phase
- [x] T043 [P] Add "Generate Insight" button to all chart sections in Explainability phase
- [x] T044 Verify all charts have consistent loading/error/empty states using ChartErrorBoundary
- [x] T045 Update results/index.ts with all new exports in frontend/src/components/experiments/results/index.ts
- [x] T046 Update charts/index.ts with all new chart exports in frontend/src/components/experiments/results/charts/index.ts
- [x] T047 Run frontend build to verify no TypeScript errors: npm run build
- [ ] T048 Manual test: Navigate through all phases and verify charts render correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - verification only
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories (creates hooks)
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can proceed sequentially in priority order (P1 → P2 → P3 → P4 → P5)
  - Or in parallel if multiple developers available
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T004, T005 hooks
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on T006-T009 hooks
- **User Story 5 (P5)**: Can start after Foundational (Phase 2) - Depends on T010-T012 hooks

### Within Each User Story

- Create chart components before section components
- Create section components before updating phase components
- Update phase component last (composes all sections)
- Export after all components created

### Parallel Opportunities

- All Foundational hooks (T004-T012) can run in parallel
- Within US1: T013, T014, T015, T016 can run in parallel
- Within US2: T019, T020, T021 can run in parallel
- Within US3: T024, T025 can run in parallel
- Within US4: T028-T034 can run in parallel
- Within US5: T037, T038 can run in parallel
- All Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all sections for User Story 1 together:
Task: "Create HeatmapSection.tsx in frontend/src/components/experiments/results/HeatmapSection.tsx"
Task: "Create BoxPlotSection.tsx in frontend/src/components/experiments/results/BoxPlotSection.tsx"
Task: "Create ScatterSection.tsx in frontend/src/components/experiments/results/ScatterSection.tsx"
Task: "Create TornadoSection.tsx in frontend/src/components/experiments/results/TornadoSection.tsx"

# Then update phase component (depends on all above):
Task: "Update PhaseLocation.tsx to compose all four section components"
```

---

## Parallel Example: User Story 4

```bash
# Launch all chart components together:
Task: "Create ShapSummaryChart.tsx in frontend/src/components/experiments/results/charts/"
Task: "Create ShapWaterfallChart.tsx in frontend/src/components/experiments/results/charts/"
Task: "Create PDPChart.tsx in frontend/src/components/experiments/results/charts/"
Task: "Create PDPComparisonChart.tsx in frontend/src/components/experiments/results/charts/"

# Launch all section components together (in parallel with charts):
Task: "Create ShapSummarySection.tsx in frontend/src/components/experiments/results/"
Task: "Create ShapWaterfallSection.tsx in frontend/src/components/experiments/results/"
Task: "Create PDPSection.tsx in frontend/src/components/experiments/results/"

# Then update phase component:
Task: "Update PhaseExplainability.tsx to compose all sections"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verification)
2. Complete Phase 2: Foundational (hooks for all phases)
3. Complete Phase 3: User Story 1 (Problem Location)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Hooks ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. **STOP and VALIDATE**: Test Problem Location phase independently
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Add User Story 5 → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 + User Story 2
   - Developer B: User Story 3 + User Story 4
   - Developer C: User Story 5
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Follow patterns from TryVsSuccessSection.tsx for all new sections
- Use indigo gradient for explanation collapsibles
- Use ChartErrorBoundary for all chart wrappers
