// frontend/src/components/experiments/results/PhaseOverview.tsx
// Phase 1: Overview - aggregates Distribution and TryVsSuccess charts

import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { Users, PlayCircle, Calendar, FlaskConical, PieChart, Sparkles, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { ChartErrorBoundary } from '@/components/shared/ErrorBoundary';
import { OutcomeDistributionChart } from './charts/OutcomeDistributionChart';
import { TryVsSuccessSection } from './TryVsSuccessSection';
import { useAnalysisDistributionChart } from '@/hooks/use-analysis-charts';
import { useGenerateAnalysisChartInsight } from '@/hooks/use-insights';
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
      <Card className="card">
        <CardHeader className="pb-2">
          <CardTitle className="text-card-title flex items-center gap-2">
            <PieChart className="h-4 w-4 text-slate-500" />
            Distribuição de Resultados
          </CardTitle>
          <p className="text-meta">Proporção média de synths que tiveram sucesso, falharam ou não tentaram</p>
        </CardHeader>
        <CardContent>
          {/* Loading state */}
          {distribution.isLoading && (
            <div className="flex flex-col items-center justify-center gap-4" style={{ height: 400 }}>
              <Skeleton className="w-full h-full rounded-lg" />
            </div>
          )}

          {/* Error state */}
          {distribution.isError && !distribution.isLoading && (
            <div
              className="flex flex-col items-center justify-center gap-4 text-center"
              style={{ height: 400 }}
            >
              <div className="icon-box-neutral">
                <AlertCircle className="h-6 w-6 text-red-500" />
              </div>
              <div>
                <p className="text-body text-red-600 font-medium mb-1">Erro</p>
                <p className="text-meta">Erro ao carregar os dados. Tente novamente.</p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => distribution.refetch()}
                className="btn-secondary"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Tentar Novamente
              </Button>
            </div>
          )}

          {/* Empty state */}
          {!distribution.data && !distribution.isLoading && !distribution.isError && (
            <div
              className="flex flex-col items-center justify-center gap-4 text-center"
              style={{ height: 400 }}
            >
              <div className="icon-box-neutral">
                <PieChart className="h-6 w-6 text-slate-400" />
              </div>
              <div>
                <p className="text-body text-slate-500 font-medium mb-1">Sem Dados</p>
                <p className="text-meta">Nenhum dado disponível para este gráfico.</p>
              </div>
            </div>
          )}

          {/* Chart */}
          {!distribution.isLoading && !distribution.isError && distribution.data && (
            <div style={{ minHeight: 400 }}>
              <ChartErrorBoundary chartName="Distribuição de Resultados">
                <OutcomeDistributionChart data={distribution.data} />
              </ChartErrorBoundary>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Row 2: Try vs Success with explanation and controls */}
      <TryVsSuccessSection experimentId={experimentId} />
    </div>
  );
}
