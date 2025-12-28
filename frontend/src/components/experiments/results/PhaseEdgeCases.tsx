// frontend/src/components/experiments/results/PhaseEdgeCases.tsx
// Phase 4: Edge Cases - Extreme cases and outliers tables
// TODO: Implement in Phase 6 (US4)

import { UserCheck } from 'lucide-react';

interface PhaseEdgeCasesProps {
  simulationId: string;
}

export function PhaseEdgeCases({ simulationId }: PhaseEdgeCasesProps) {
  return (
    <div className="p-8 rounded-xl border-2 border-dashed border-slate-200 bg-slate-50/50 text-center">
      <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3">
        <UserCheck className="w-6 h-6 text-slate-400" />
      </div>
      <p className="text-slate-500 text-sm mb-1">
        Casos Especiais
      </p>
      <p className="text-slate-400 text-xs">
        Em desenvolvimento - Tabelas de casos extremos e outliers
      </p>
    </div>
  );
}
