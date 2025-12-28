// frontend/src/components/experiments/results/PhaseOverview.tsx
// Phase 1: Overview - aggregates Distribution and TryVsSuccess charts

import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { Users, PlayCircle, Calendar, FlaskConical } from 'lucide-react';
import { ChartContainer } from '@/components/shared/ChartContainer';
import { OutcomeDistributionChart } from './charts/OutcomeDistributionChart';
import { TryVsSuccessSection } from './TryVsSuccessSection';
import { useAnalysisDistributionChart } from '@/hooks/use-analysis-charts';
import type { AnalysisSummary } from '@/types/experiment';

interface PhaseOverviewProps {
  experimentId: string;
  analysis?: AnalysisSummary | null;
}

// Simulation Summary Component
function SimulationSummary({ analysis }: { analysis: AnalysisSummary }) {
  const completedDate = analysis.completed_at
    ? format(new Date(analysis.completed_at), "dd/MM/yyyy", { locale: ptBR })
    : null;
  const completedTime = analysis.completed_at
    ? format(new Date(analysis.completed_at), "HH:mm", { locale: ptBR })
    : null;

  const totalSimulations = analysis.total_synths * analysis.n_executions;

  return (
    <div className="bg-gradient-to-r from-slate-50 to-indigo-50 border border-slate-200 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <div className="p-2 bg-indigo-100 rounded-lg">
          <FlaskConical className="h-5 w-5 text-indigo-600" />
        </div>
        <div>
          <h3 className="font-semibold text-slate-800">Resumo da Simulação</h3>
          <p className="text-xs text-slate-500">Análise Monte Carlo concluída</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Synths Analyzed */}
        <div className="bg-white rounded-lg p-3 border border-slate-100">
          <div className="flex items-center gap-2 mb-1">
            <Users className="h-4 w-4 text-slate-400" />
            <span className="text-xs text-slate-500">Synths</span>
          </div>
          <p className="text-xl font-bold text-slate-800">
            {analysis.total_synths.toLocaleString('pt-BR')}
          </p>
        </div>

        {/* Executions per Synth */}
        <div className="bg-white rounded-lg p-3 border border-slate-100">
          <div className="flex items-center gap-2 mb-1">
            <PlayCircle className="h-4 w-4 text-slate-400" />
            <span className="text-xs text-slate-500">Execuções/Synth</span>
          </div>
          <p className="text-xl font-bold text-slate-800">
            {analysis.n_executions.toLocaleString('pt-BR')}
          </p>
        </div>

        {/* Total Simulations */}
        <div className="bg-white rounded-lg p-3 border border-slate-100">
          <div className="flex items-center gap-2 mb-1">
            <FlaskConical className="h-4 w-4 text-slate-400" />
            <span className="text-xs text-slate-500">Total Simulações</span>
          </div>
          <p className="text-xl font-bold text-indigo-600">
            {totalSimulations.toLocaleString('pt-BR')}
          </p>
        </div>

        {/* Execution Date/Time */}
        <div className="bg-white rounded-lg p-3 border border-slate-100">
          <div className="flex items-center gap-2 mb-1">
            <Calendar className="h-4 w-4 text-slate-400" />
            <span className="text-xs text-slate-500">Executada em</span>
          </div>
          {completedDate ? (
            <div>
              <p className="text-xl font-bold text-slate-800">{completedDate}</p>
              <p className="text-xs text-slate-500">às {completedTime}</p>
            </div>
          ) : (
            <p className="text-xl font-bold text-slate-800">-</p>
          )}
        </div>
      </div>
    </div>
  );
}

export function PhaseOverview({ experimentId, analysis }: PhaseOverviewProps) {
  const distribution = useAnalysisDistributionChart(experimentId);

  return (
    <div className="space-y-6">
      {/* Row 0: Simulation Summary */}
      {analysis && analysis.status === 'completed' && (
        <SimulationSummary analysis={analysis} />
      )}

      {/* Row 1: Distribution (main highlight) */}
      <ChartContainer
        title="Distribuição de Resultados"
        description="Proporção média de synths que tiveram sucesso, falharam ou não tentaram"
        isLoading={distribution.isLoading}
        isError={distribution.isError}
        isEmpty={!distribution.data}
        onRetry={() => distribution.refetch()}
        height={400}
      >
        {distribution.data && (
          <OutcomeDistributionChart data={distribution.data} />
        )}
      </ChartContainer>

      {/* Row 2: Try vs Success with explanation and controls */}
      <TryVsSuccessSection experimentId={experimentId} />
    </div>
  );
}
