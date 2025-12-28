// frontend/src/components/experiments/results/PhaseExplainability.tsx
// Phase 5: Deep Explanation - SHAP and PDP charts
// TODO: Implement in Phase 7 (US5)

import { Microscope } from 'lucide-react';

interface PhaseExplainabilityProps {
  simulationId: string;
}

export function PhaseExplainability({ simulationId }: PhaseExplainabilityProps) {
  return (
    <div className="p-8 rounded-xl border-2 border-dashed border-slate-200 bg-slate-50/50 text-center">
      <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3">
        <Microscope className="w-6 h-6 text-slate-400" />
      </div>
      <p className="text-slate-500 text-sm mb-1">
        Aprofundamento (Explicabilidade)
      </p>
      <p className="text-slate-400 text-xs">
        Em desenvolvimento - SHAP Waterfall, Summary e PDP
      </p>
    </div>
  );
}
