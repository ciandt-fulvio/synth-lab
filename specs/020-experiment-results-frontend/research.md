# Research: Experiment Results Frontend

**Feature**: 020-experiment-results-frontend
**Date**: 2025-12-28
**Status**: Complete

## Research Questions

### 1. Sankey Diagram Implementation with Recharts

**Decision**: Use Recharts native Sankey component

**Rationale**: Recharts includes a built-in Sankey component that supports the node-link structure needed. The backend already returns data in a compatible format with `nodes` and `links` arrays.

**Alternatives Considered**:
- **D3.js sankey-diagram**: More powerful but requires significant integration effort and doesn't match existing codebase patterns
- **react-d3-tree**: Designed for trees, not flow diagrams
- **Custom SVG**: Too much implementation overhead

**Implementation Notes**:
```typescript
import { Sankey, Layer, Rectangle, Label } from 'recharts';

// Backend returns: { nodes: [{name: string}], links: [{source: number, target: number, value: number}] }
// Recharts Sankey expects exactly this format
```

### 2. Dendrogram Visualization

**Decision**: Custom SVG component using hierarchical clustering data

**Rationale**: Recharts doesn't have a built-in dendrogram component. The backend returns `HierarchicalResult` with `dendrogram` field containing a tree structure (`DendrogramNode`). A custom React component with SVG paths will render the hierarchical tree.

**Alternatives Considered**:
- **react-d3-tree**: Could work but adds another dependency and has different styling conventions
- **Recharts Treemap**: Wrong visualization type (area-based, not tree lines)
- **D3.js dendrogram**: Good but requires D3 integration

**Implementation Notes**:
- Backend `DendrogramNode` has: `id`, `left`, `right`, `distance`, `synth_count`, `synth_ids`
- Render as recursive SVG tree with horizontal or vertical layout
- Use Tailwind colors for consistency (indigo/violet theme)

### 3. SHAP Waterfall Chart

**Decision**: Use Recharts horizontal BarChart with custom styling for positive/negative values

**Rationale**: SHAP waterfall charts show feature contributions as horizontal bars from a baseline. Recharts BarChart with `layout="vertical"` and conditional bar coloring (green for positive, red for negative) achieves this.

**Alternatives Considered**:
- **Custom SVG waterfall**: More control but more code
- **echarts**: Different library, inconsistent with codebase

**Implementation Notes**:
```typescript
// Backend ShapExplanation has: contributions: [{feature: string, value: number, shap_value: number}]
// Render as horizontal bars, sorted by |shap_value|
// Color: shap_value > 0 → green (positive contribution), < 0 → red (negative)
```

### 4. Radar Chart for Cluster Comparison

**Decision**: Use Recharts RadarChart component

**Rationale**: Recharts has a native RadarChart component that perfectly matches the cluster comparison use case. Backend returns `RadarChart` with `clusters` containing axis values.

**Implementation Notes**:
```typescript
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Legend } from 'recharts';

// Backend RadarChart has: clusters: [{cluster_id, label, data: [{axis, value}]}], axis_labels, baseline
```

### 5. Heatmap Visualization

**Decision**: Custom grid component using CSS Grid + Tailwind color intensity

**Rationale**: Recharts doesn't have a native heatmap component. A CSS Grid layout with color-coded cells (using Tailwind color palette with varying intensity) is simpler and more performant than SVG-based solutions.

**Alternatives Considered**:
- **Recharts ScatterChart with custom shapes**: Possible but hacky
- **D3.js heatmap**: Overkill for simple 2D grid
- **react-heatmap**: Additional dependency

**Implementation Notes**:
```typescript
// Backend FailureHeatmapChart has: cells: [{x_bin, y_bin, count, metric_value}], x_labels, y_labels
// Render as CSS Grid with color intensity based on metric_value (0-1 scale)
// Use slate/red gradient: higher failure = more red
```

### 6. Box Plot Chart

**Decision**: Custom SVG component or use Recharts ComposedChart with error bars

**Rationale**: Recharts doesn't have native box plot support. Use ComposedChart with custom error bars (Line + ReferenceLine) to simulate box plot appearance, or create a simple custom SVG component.

**Implementation Notes**:
- Backend box plot endpoint likely returns: min, q1, median, q3, max, outliers
- Render as vertical boxes with whiskers using SVG rect + line elements

### 7. State Management for Analysis Results

**Decision**: React Query with simulation-specific query keys

**Rationale**: Follows existing codebase patterns. Each chart/analysis type gets its own query key for independent caching and refetching.

**Implementation Notes**:
```typescript
// lib/query-keys.ts extensions
simulationCharts: {
  tryVsSuccess: (simId: string) => ['simulation', 'charts', 'try-vs-success', simId],
  distribution: (simId: string) => ['simulation', 'charts', 'distribution', simId],
  sankey: (simId: string) => ['simulation', 'charts', 'sankey', simId],
  // ... etc
},
simulationClustering: (simId: string) => ['simulation', 'clustering', simId],
simulationInsights: (simId: string) => ['simulation', 'insights', simId],
```

### 8. Loading/Error/Empty State Pattern

**Decision**: Create ChartContainer wrapper component

**Rationale**: All charts need consistent loading (skeleton), error (retry button), and empty states. A wrapper component ensures consistency and reduces code duplication.

**Implementation Notes**:
```typescript
interface ChartContainerProps {
  isLoading: boolean;
  isError: boolean;
  isEmpty: boolean;
  onRetry?: () => void;
  emptyMessage?: string;
  children: React.ReactNode;
}

// Usage:
<ChartContainer
  isLoading={query.isLoading}
  isError={query.isError}
  isEmpty={!data?.points?.length}
  onRetry={() => query.refetch()}
>
  <ActualChart data={data} />
</ChartContainer>
```

### 9. Phase Navigation Architecture

**Decision**: Extend existing AnalysisPhaseTabs component

**Rationale**: The component already exists at `frontend/src/components/experiments/AnalysisPhaseTabs.tsx` with the 6 phases defined. Simply integrate the phase content components.

**Implementation Notes**:
- AnalysisPhaseTabs already has: `ANALYSIS_PHASES` array with all 6 phases
- Need to add: `activePhase` state, `onPhaseChange` callback, render content based on phase
- Each phase component receives `simulationId` prop

### 10. Insight Generation UI Pattern

**Decision**: Follow ArtifactButton pattern from PRFAQ/Summary

**Rationale**: The existing ArtifactButton component handles generate/view/retry states which is exactly what's needed for LLM insights.

**Implementation Notes**:
- Use `ArtifactButton` for "Generate Insight" action per chart
- Display insight in a Card with caption, explanation, evidence list, recommendation
- Use MarkdownPopup for executive summary display

## Technology Decisions Summary

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Scatter/Line/Bar charts | Recharts native | Already installed, matches codebase |
| Pie chart | Recharts PieChart | Native support |
| Sankey diagram | Recharts Sankey | Native support |
| Radar chart | Recharts RadarChart | Native support |
| Dendrogram | Custom SVG component | No Recharts support |
| Heatmap | CSS Grid + color intensity | Simple, performant |
| Box plot | Custom SVG or ComposedChart | No native support |
| SHAP waterfall | Recharts BarChart horizontal | Adapted from bar chart |
| State management | React Query | Existing pattern |
| UI components | shadcn/ui + Tailwind | Existing design system |

## Dependencies

No new dependencies required. All visualizations can be implemented with:
- Recharts 2.12.7+ (already installed)
- shadcn/ui components (already installed)
- Tailwind CSS (already installed)
- React Query (already installed)

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Dendrogram rendering complexity | Start with simple horizontal layout, iterate |
| Heatmap color perception | Use established color scales (sequential reds) |
| Large dataset performance | Use React Query caching, pagination where available |
| Chart responsiveness | Use Recharts ResponsiveContainer consistently |
