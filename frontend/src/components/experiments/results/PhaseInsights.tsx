// frontend/src/components/experiments/results/PhaseInsights.tsx
// Phase 6: LLM Insights - AI-generated insights and executive summary
// Composes section components for LLM-powered analysis

import { InsightsListSection } from './InsightsListSection';
import { ExecutiveSummarySection } from './ExecutiveSummarySection';

interface PhaseInsightsProps {
  experimentId: string;
}

export function PhaseInsights({ experimentId }: PhaseInsightsProps) {
  return (
    <div className="space-y-6">
      {/* Executive Summary first for stakeholder focus */}
      <ExecutiveSummarySection experimentId={experimentId} />

      {/* Individual insights list */}
      <InsightsListSection experimentId={experimentId} />
    </div>
  );
}
