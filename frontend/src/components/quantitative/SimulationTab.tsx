/**
 * SimulationTab container component.
 *
 * Displays simulation results and provides manual interview guide generation.
 * Simulation is triggered from the Análise Quanti tab.
 *
 * References:
 *   - Hooks: src/hooks/use-quantitative-analysis.ts
 *   - Components: SimulationResults
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Loader2, Activity, FileText, BarChart3 } from 'lucide-react';
import {
  useSimulationResults,
} from '@/hooks/use-quantitative-analysis';
import { SimulationResults } from './SimulationResults';

interface SimulationTabProps {
  experimentId: string;
  onGenerateGuide?: () => void;
}

export function SimulationTab({ experimentId, onGenerateGuide }: SimulationTabProps) {
  const { data: simulationRun, isLoading } = useSimulationResults(experimentId);
  const [showStubDialog, setShowStubDialog] = useState(false);

  // Loading
  if (isLoading) {
    return (
      <div className="text-center py-12">
        <Loader2 className="w-8 h-8 text-violet-500 mx-auto mb-3 animate-spin" />
        <p className="text-slate-500">Carregando resultados...</p>
      </div>
    );
  }

  // No results yet
  if (!simulationRun) {
    return (
      <div className="text-center py-12">
        <Activity className="w-10 h-10 text-slate-300 mx-auto mb-3" />
        <p className="text-slate-500">
          Nenhuma simulação realizada ainda.
        </p>
        <p className="text-sm text-slate-400 mt-1">
          Execute a simulação na aba &quot;Análise Quanti&quot;.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Results */}
      <SimulationResults run={simulationRun} />

      {/* Action buttons — bottom */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
        <Button
          size="sm"
          variant="outline"
          onClick={() => setShowStubDialog(true)}
        >
          <BarChart3 className="w-4 h-4 mr-1" />
          Gerar Resumo da Simulação
        </Button>
        <Button
          size="sm"
          onClick={onGenerateGuide}
          className="btn-primary"
        >
          <FileText className="w-4 h-4 mr-1" />
          Gerar roteiro de entrevista
        </Button>
      </div>

      {/* Stub dialog for "Gerar Resumo da Simulação" */}
      <Dialog open={showStubDialog} onOpenChange={setShowStubDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-violet-600" />
              Resumo da Simulação
            </DialogTitle>
          </DialogHeader>
          <div className="text-center py-8">
            <p className="text-slate-500 text-sm">Em desenvolvimento</p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
