// frontend/src/components/experiments/results/PhaseEdgeCases.tsx
// Phase 4: Edge Cases - Extreme cases and outliers tables
// Composes section components for interview candidate selection

import { ExtremeCasesSection } from './ExtremeCasesSection';
import { OutliersSection } from './OutliersSection';

interface PhaseEdgeCasesProps {
  experimentId: string;
}

export function PhaseEdgeCases({ experimentId }: PhaseEdgeCasesProps) {
  return (
    <div className="space-y-6">
      {/* Extreme Cases: worst failures, best successes, unexpected */}
      <ExtremeCasesSection experimentId={experimentId} />

      {/* Statistical Outliers with Isolation Forest */}
      <OutliersSection experimentId={experimentId} />
    </div>
  );
}
