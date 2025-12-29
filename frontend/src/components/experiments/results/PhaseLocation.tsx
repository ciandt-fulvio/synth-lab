// frontend/src/components/experiments/results/PhaseLocation.tsx
// Phase 2: Problem Location - Attribute importance, Heatmap, Scatter, Tornado charts
// Composes section components that each handle their own state and data fetching

import { HeatmapSection } from './HeatmapSection';
import { ScatterSection } from './ScatterSection';
import { TornadoSection } from './TornadoSection';
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

      {/* Row 3: Failure Heatmap */}
      <HeatmapSection experimentId={experimentId} />

      {/* Row 4: Tornado Chart */}
      <TornadoSection experimentId={experimentId} />
    </div>
  );
}
