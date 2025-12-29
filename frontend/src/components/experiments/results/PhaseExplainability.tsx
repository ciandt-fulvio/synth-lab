// frontend/src/components/experiments/results/PhaseExplainability.tsx
// Phase 5: Deep Explanation - SHAP and PDP charts
// Composes section components for model explainability

import { ShapSummarySection } from './ShapSummarySection';
import { ShapWaterfallSection } from './ShapWaterfallSection';
import { PDPSection } from './PDPSection';

interface PhaseExplainabilityProps {
  experimentId: string;
}

export function PhaseExplainability({ experimentId }: PhaseExplainabilityProps) {
  return (
    <div className="space-y-6">
      {/* SHAP Summary: Global feature importance */}
      <ShapSummarySection experimentId={experimentId} />

      {/* SHAP Waterfall: Individual synth explanation */}
      <ShapWaterfallSection experimentId={experimentId} />

      {/* PDP: Partial Dependence Plots */}
      <PDPSection experimentId={experimentId} />
    </div>
  );
}
