// frontend/src/components/experiments/results/PhaseInsights.tsx
// Phase 6: LLM Insights - AI-generated insights and executive summary
// TODO: Implement in Phase 8 (US6)

import { Lightbulb } from 'lucide-react';

interface PhaseInsightsProps {
  simulationId: string;
}

export function PhaseInsights({ simulationId }: PhaseInsightsProps) {
  return (
    <div className="p-8 rounded-xl border-2 border-dashed border-slate-200 bg-slate-50/50 text-center">
      <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3">
        <Lightbulb className="w-6 h-6 text-slate-400" />
      </div>
      <p className="text-slate-500 text-sm mb-1">
        Insights LLM
      </p>
      <p className="text-slate-400 text-xs">
        Em desenvolvimento - Insights gerados por IA e resumo executivo
      </p>
    </div>
  );
}
