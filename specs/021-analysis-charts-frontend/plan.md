# Implementation Plan: Analysis Charts Frontend Integration

**Branch**: `021-analysis-charts-frontend` | **Date**: 2025-12-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/021-analysis-charts-frontend/spec.md`

## Summary

Frontend implementation of remaining quantitative analysis chart phases (2-6) for experiment results visualization. The feature extends the existing Phase 1 (Overview) implementation by adding Problem Location, Segmentation, Edge Cases, Explainability, and LLM Insights phases. Following established patterns from TryVsSuccessSection and existing chart components.

## Technical Context

**Language/Version**: TypeScript 5.5.3 (frontend)
**Primary Dependencies**: React 18.3.1, TanStack React Query 5.56+, Recharts 2.12.7+, shadcn/ui (Radix UI), Tailwind CSS 3.4+
**Storage**: N/A (data from backend API)
**Testing**: Component tests with React Testing Library, E2E with Playwright
**Target Platform**: Web browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (frontend only)
**Performance Goals**: Charts render within 2 seconds, interactive controls respond immediately
**Constraints**: Reuse existing API endpoints from `/simulation/simulations/{id}` path, follow design system from `frontend/CLAUDE.md`
**Scale/Scope**: 5 phase containers, ~15 chart components, ~10 hooks

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| VII. Architecture Frontend | ✅ PASS | Pages only compose components, components pure (props→JSX), hooks encapsulate React Query, services call API, query keys centralized |
| V. Simplicity | ✅ PASS | Reusing existing patterns from TryVsSuccessSection, ChartContainer, established hooks |
| VI. Language | ✅ PASS | Code in English, UI text in Portuguese (following existing patterns) |
| I. TDD/BDD | ⚠️ DEFERRED | Frontend tests will be written after component implementation (visual testing focus) |

## Project Structure

### Documentation (this feature)

```text
specs/021-analysis-charts-frontend/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (frontend types)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API contracts already exist)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/
│   │   └── experiments/
│   │       └── results/
│   │           ├── PhaseLocation.tsx        # Exists - needs completion
│   │           ├── PhaseSegmentation.tsx    # Exists - needs completion
│   │           ├── PhaseEdgeCases.tsx       # Placeholder - needs implementation
│   │           ├── PhaseExplainability.tsx  # Placeholder - needs implementation
│   │           ├── PhaseInsights.tsx        # Placeholder - needs implementation
│   │           ├── HeatmapSection.tsx       # NEW - with controls + explanation
│   │           ├── BoxPlotSection.tsx       # NEW - with controls + explanation
│   │           ├── ScatterSection.tsx       # NEW - with controls + explanation
│   │           ├── TornadoSection.tsx       # NEW - with explanation
│   │           ├── ElbowSection.tsx         # NEW - K-Means optimization
│   │           ├── DendrogramSection.tsx    # NEW - Hierarchical clustering
│   │           ├── RadarSection.tsx         # NEW - Cluster comparison
│   │           ├── ExtremeCasesSection.tsx  # NEW - Edge case tables
│   │           ├── OutliersSection.tsx      # NEW - Outlier detection
│   │           ├── ShapSummarySection.tsx   # NEW - Global SHAP
│   │           ├── ShapWaterfallSection.tsx # NEW - Individual SHAP
│   │           ├── PDPSection.tsx           # NEW - Partial dependence
│   │           ├── InsightsListSection.tsx  # NEW - Generated insights
│   │           ├── ExecutiveSummarySection.tsx # NEW - LLM summary
│   │           └── charts/
│   │               ├── ShapSummaryChart.tsx # NEW
│   │               ├── ShapWaterfallChart.tsx # NEW
│   │               ├── PDPChart.tsx          # NEW
│   │               └── PDPComparisonChart.tsx # NEW
│   ├── hooks/
│   │   ├── use-simulation-charts.ts  # Exists - needs Phase 2 hooks
│   │   ├── use-clustering.ts         # Exists - complete
│   │   ├── use-edge-cases.ts         # NEW
│   │   ├── use-explainability.ts     # NEW
│   │   └── use-insights.ts           # NEW
│   ├── services/
│   │   └── simulation-api.ts         # Exists - has all API functions
│   ├── types/
│   │   └── simulation.ts             # Exists - has all types
│   └── lib/
│       └── query-keys.ts             # Exists - has all keys
```

**Structure Decision**: Frontend-only feature extending existing experiment results visualization. Follows established web application structure with components, hooks, services, and types directories.

## Complexity Tracking

> No constitution violations requiring justification. Implementation follows established patterns.

## Design Patterns from TryVsSuccessSection

### Section Component Pattern (from TryVsSuccessSection.tsx)
Each chart should be wrapped in a Section component that includes:
1. **Card container** with consistent styling
2. **CardHeader** with title + icon + description
3. **Collapsible explanation** with indigo gradient background
4. **Controls section** (sliders, selects) with slate-50 background
5. **Chart area** with loading/error/empty states
6. **ChartErrorBoundary** wrapper for resilience

### Color Palette (from TryVsSuccessChart.tsx)
```typescript
// Quadrant/status colors
const COLORS = {
  ok: '#22c55e',           // Green - success
  discovery_issue: '#3b82f6', // Blue - low engagement
  usability_issue: '#ef4444', // Red - high failure
  low_value: '#f59e0b',    // Amber - low value
};

// Outcome colors
const OUTCOME_COLORS = {
  success: '#22c55e',
  failed: '#ef4444',
  did_not_try: '#94a3b8',
};
```

### Control Patterns
- **Sliders**: For threshold values (attempt rate, success rate, contamination)
- **Selects**: For axis/attribute selection with translated labels
- **Tabs**: For method selection (K-Means vs Hierarchical)

### Loading/Error/Empty States
Use ChartContainer component with consistent states:
```tsx
<ChartContainer
  title="Title"
  description="Description"
  isLoading={query.isLoading}
  isError={query.isError}
  isEmpty={!query.data}
  onRetry={() => query.refetch()}
  height={400}
>
  {query.data && <Chart data={query.data} />}
</ChartContainer>
```

## API Endpoint Mapping

### Current (simulation-based)
- `/simulation/simulations/{id}/charts/*`

### Target (experiment-based)
- `/experiments/{id}/analysis/charts/*`

### Implementation Strategy
1. Phase 2 (Location) already uses simulation-based hooks - keep for now
2. Add experiment-based hooks for phases 4-6 (new endpoints needed)
3. Backend needs new endpoints: `/experiments/{id}/analysis/extreme-cases`, `/experiments/{id}/analysis/outliers`, etc.

**Note**: Backend API for phases 4-6 currently returns TODO placeholders. Frontend should:
1. Implement UI with empty states
2. Be ready to connect when backend is implemented
3. Use existing simulation-api.ts functions where available

## Phase Implementation Order

1. **Phase 2: Location** - Complete (charts exist, need section wrappers with explanations)
2. **Phase 3: Segmentation** - Mostly complete (needs explanation collapsibles)
3. **Phase 4: Edge Cases** - Implement ExtremeCasesSection + OutliersSection
4. **Phase 5: Explainability** - Implement SHAP + PDP sections
5. **Phase 6: Insights** - Implement InsightsListSection + ExecutiveSummarySection

## Key Implementation Notes

### Hooks Pattern
```typescript
export function useExtremeCases(simulationId: string, nPerCategory = 10, enabled = true) {
  return useQuery({
    queryKey: [...queryKeys.simulation.extremeCases(simulationId), nPerCategory],
    queryFn: () => getExtremeCases(simulationId, nPerCategory),
    enabled: !!simulationId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}
```

### Explanation Collapsible Pattern
```tsx
<Collapsible open={showExplanation} onOpenChange={setShowExplanation}>
  <div className="bg-gradient-to-r from-slate-50 to-indigo-50 border border-slate-200 rounded-lg p-3">
    <CollapsibleTrigger asChild>
      <Button variant="ghost" className="w-full...">
        <HelpCircle className="h-4 w-4" />
        <span>Como interpretar este gráfico?</span>
      </Button>
    </CollapsibleTrigger>
    <CollapsibleContent className="mt-3 space-y-3 text-sm text-slate-700">
      {/* Explanation content */}
    </CollapsibleContent>
  </div>
</Collapsible>
```

### Slider Control Pattern
```tsx
<div className="bg-slate-50 rounded-lg p-3">
  <div className="space-y-1.5">
    <div className="flex justify-between items-center">
      <label className="text-xs text-slate-600">Label</label>
      <span className="text-xs font-medium text-slate-800 bg-white px-2 py-0.5 rounded">
        {Math.round(value * 100)}%
      </span>
    </div>
    <Slider
      value={[value * 100]}
      onValueChange={(values) => setValue(values[0] / 100)}
      min={10}
      max={90}
      step={5}
    />
  </div>
</div>
```
