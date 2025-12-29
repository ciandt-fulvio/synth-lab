// frontend/src/components/experiments/results/PhaseEdgeCases.tsx
// Phase 4: Edge Cases - Extreme cases and outliers with click-to-explain
// Click on any card to see SHAP Waterfall explanation

import { useState } from 'react';
import { ExtremeCasesSection } from './ExtremeCasesSection';
import { OutliersSection } from './OutliersSection';
import { ShapWaterfallSection } from './ShapWaterfallSection';

interface PhaseEdgeCasesProps {
  experimentId: string;
}

export function PhaseEdgeCases({ experimentId }: PhaseEdgeCasesProps) {
  const [selectedSynthId, setSelectedSynthId] = useState<string | null>(null);

  const handleSynthClick = (synthId: string) => {
    setSelectedSynthId(synthId);
  };

  return (
    <div className="space-y-6">
      {/* Extreme Cases: worst failures, best successes */}
      <ExtremeCasesSection
        experimentId={experimentId}
        onSynthClick={handleSynthClick}
        selectedSynthId={selectedSynthId}
      />

      {/* SHAP Waterfall: Individual synth explanation (click-to-explain) */}
      {selectedSynthId && (
        <ShapWaterfallSection
          experimentId={experimentId}
          selectedSynthId={selectedSynthId}
        />
      )}

      {/* Statistical Outliers with Isolation Forest */}
      <OutliersSection
        experimentId={experimentId}
        onSynthClick={handleSynthClick}
        selectedSynthId={selectedSynthId}
      />
    </div>
  );
}
