// frontend/src/components/experiments/results/PhaseLocation.tsx
// Phase 2: Attribute Influence - Understanding how user characteristics affect outcomes
// Composes section components that each handle their own state and data fetching

import { ScatterSection } from './ScatterSection';
import { AttributeCorrelationSection } from './AttributeCorrelationSection';

interface PhaseLocationProps {
  experimentId: string;
}

export function PhaseLocation({ experimentId }: PhaseLocationProps) {
  return (
    <div className="space-y-6">
      {/* Row 1: Attribute Correlations - quick overview of important attributes */}
      <AttributeCorrelationSection experimentId={experimentId} />

      {/* Row 2: Scatter Chart - explore specific attribute correlations */}
      <ScatterSection experimentId={experimentId} />
    </div>
  );
}
