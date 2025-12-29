// frontend/src/components/experiments/results/index.ts
// Re-exports for experiment results components

// Phase containers
export { PhaseOverview } from './PhaseOverview';
export { PhaseLocation } from './PhaseLocation';
export { PhaseSegmentation } from './PhaseSegmentation';
export { PhaseEdgeCases } from './PhaseEdgeCases';
export { PhaseExplainability } from './PhaseExplainability';
export { PhaseInsights } from './PhaseInsights';

// Section components (Phase 2: Problem Location)
export { HeatmapSection } from './HeatmapSection';
export { BoxPlotSection } from './BoxPlotSection';
export { ScatterSection } from './ScatterSection';
export { TornadoSection } from './TornadoSection';
export { AttributeCorrelationSection } from './AttributeCorrelationSection';

// Section components (Phase 3: Segmentation)
export { ElbowSection } from './ElbowSection';
export { DendrogramSection } from './DendrogramSection';
export { RadarSection } from './RadarSection';

// Section components (Phase 4: Edge Cases)
export { ExtremeCasesSection } from './ExtremeCasesSection';
export { OutliersSection } from './OutliersSection';

// Section components (Phase 5: Explainability)
export { ShapSummarySection } from './ShapSummarySection';
export { ShapWaterfallSection } from './ShapWaterfallSection';
export { PDPSection } from './PDPSection';

// Section components (Phase 6: Insights)
export { InsightsListSection } from './InsightsListSection';
export { ExecutiveSummarySection } from './ExecutiveSummarySection';

// Chart components (re-exported from charts/)
export * from './charts';
