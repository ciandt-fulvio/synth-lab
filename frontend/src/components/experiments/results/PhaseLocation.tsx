// frontend/src/components/experiments/results/PhaseLocation.tsx
// Phase 2: Influência - Understanding how features influence outcomes
// Shows SHAP Summary for global importance

import { ShapSummarySection } from './ShapSummarySection';

interface PhaseLocationProps {
  experimentId: string;
}

export function PhaseLocation({ experimentId }: PhaseLocationProps) {
  return (
    <div className="space-y-6">
      {/* SHAP Summary: Global feature importance */}
      <ShapSummarySection experimentId={experimentId} />
    </div>
  );
}
