// frontend/src/components/experiments/results/index.ts
// Re-exports for experiment results components

// Phase containers
export { PhaseOverview } from './PhaseOverview';
export { PhaseLocation } from './PhaseLocation';
export { PhaseEdgeCases } from './PhaseEdgeCases';

// Section components (Phase 2: Influência)
export { ShapSummarySection } from './ShapSummarySection';

// Section components (Legacy - keeping for now)
export { HeatmapSection } from './HeatmapSection';
export { BoxPlotSection } from './BoxPlotSection';

// Section components (Phase 3: Edge Cases)
export { ExtremeCasesSection } from './ExtremeCasesSection';
export { OutliersSection } from './OutliersSection';
export { ShapWaterfallSection } from './ShapWaterfallSection';

// Chart components (re-exported from charts/)
export * from './charts';
