// frontend/src/components/experiments/results/index.ts
// Re-exports for experiment results components

// Phase containers
export { PhaseOverview } from './PhaseOverview';
export { PhaseLocation } from './PhaseLocation';
export { PhaseSegmentation } from './PhaseSegmentation';
export { PhaseEdgeCases } from './PhaseEdgeCases';
export { PhaseInsights } from './PhaseInsights';

// Section components (Phase 2: Influência - moved from Phase 5)
export { ShapSummarySection } from './ShapSummarySection';
export { PDPSection } from './PDPSection';

// Section components (Legacy - keeping for now)
export { HeatmapSection } from './HeatmapSection';
export { BoxPlotSection } from './BoxPlotSection';

// Section components (Phase 3: Segmentation)
export { ElbowSection } from './ElbowSection';
export { DendrogramSection } from './DendrogramSection';
export { RadarSection } from './RadarSection';

// Section components (Phase 4: Edge Cases)
export { ExtremeCasesSection } from './ExtremeCasesSection';
export { OutliersSection } from './OutliersSection';
export { ShapWaterfallSection } from './ShapWaterfallSection';

// Section components (Phase 5: Insights)
export { InsightsListSection } from './InsightsListSection';
export { ExecutiveSummarySection } from './ExecutiveSummarySection';

// Chart components (re-exported from charts/)
export * from './charts';
