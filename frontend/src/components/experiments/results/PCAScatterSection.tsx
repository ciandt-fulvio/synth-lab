// frontend/src/components/experiments/results/PCAScatterSection.tsx
// PCA Scatter section with explanation and insight generation

import { useState } from 'react';
import { HelpCircle, Hexagon, AlertCircle, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Skeleton } from '@/components/ui/skeleton';
import { ChartErrorBoundary } from '@/components/shared/ErrorBoundary';
import { PCAScatterChart } from './charts/PCAScatterChart';
import { useAnalysisPCAScatter } from '@/hooks/use-analysis-charts';

import { InsightSection } from './InsightSection';
interface PCAScatterSectionProps {
  experimentId: string;
  hasClustering?: boolean;
}

export function PCAScatterSection({
  experimentId,
  hasClustering = true,
}: PCAScatterSectionProps) {
  const [showExplanation, setShowExplanation] = useState(false);

  const scatter = useAnalysisPCAScatter(experimentId, hasClustering);

  const handleGenerateInsight = () => {
    if (!scatter.data) return;
    generateInsight.mutate({
      chartType: 'pca_scatter',
      chartData: {
        total_variance: scatter.data.total_variance,
        n_points: scatter.data.points.length,
      },
    });
  };

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <CardTitle className="text-card-title flex items-center gap-2">
          <Hexagon className="h-4 w-4 text-slate-500" />
          Visualização de Clusters (PCA)
        </CardTitle>
        <p className="text-meta">Projeção 2D dos synths coloridos por cluster</p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Explanation */}
        <Collapsible open={showExplanation} onOpenChange={setShowExplanation}>
          <div className="bg-gradient-to-r from-slate-50 to-indigo-50 border border-slate-200 rounded-lg p-3">
            <CollapsibleTrigger asChild>
              <Button
                variant="ghost"
                className="w-full flex items-center justify-between p-0 h-auto hover:bg-transparent"
              >
                <div className="flex items-center gap-2 text-indigo-700">
                  <HelpCircle className="h-4 w-4" />
                  <span className="text-sm font-medium">O que é PCA?</span>
                </div>
                <span className="text-xs text-indigo-600">
                  {showExplanation ? 'Ocultar' : 'Ver explicação'}
                </span>
              </Button>
            </CollapsibleTrigger>

            <CollapsibleContent className="mt-3 space-y-3 text-sm text-slate-700">
              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Por que usar PCA?</h4>
                <p className="text-xs">
                  PCA (Principal Component Analysis) reduz múltiplos atributos para 2 dimensões,
                  permitindo visualizar a <strong>separação natural dos clusters</strong> em um
                  gráfico 2D.
                </p>
              </div>
              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Como ler o gráfico?</h4>
                <p className="text-xs">
                  Cada ponto é um synth. <strong>Cores</strong> indicam clusters (mesmas do Radar).
                  Quanto mais <strong>separados</strong> os grupos de cores, melhor a qualidade do
                  clustering.
                </p>
              </div>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Loading */}
        {scatter.isLoading && (
          <div className="flex justify-center" style={{ height: 450 }}>
            <Skeleton className="w-full h-full rounded-lg" />
          </div>
        )}

        {/* Error */}
        {scatter.isError && !scatter.isLoading && (
          <div
            className="flex flex-col items-center justify-center gap-4"
            style={{ height: 450 }}
          >
            <div className="icon-box-neutral">
              <AlertCircle className="h-6 w-6 text-red-500" />
            </div>
            <div className="text-center">
              <p className="text-body text-red-600 font-medium mb-1">Erro</p>
              <p className="text-meta">Erro ao carregar dados. Tente novamente.</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => scatter.refetch()}
              className="btn-secondary"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Tentar Novamente
            </Button>
          </div>
        )}

        {/* Empty */}
        {(!scatter.data || !hasClustering) && !scatter.isLoading && !scatter.isError && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ height: 450 }}
          >
            <div className="icon-box-neutral">
              <Hexagon className="h-6 w-6 text-slate-400" />
            </div>
            <div>
              <p className="text-body text-slate-500 font-medium mb-1">
                {hasClustering ? 'Sem Dados' : 'K-Means Necessário'}
              </p>
              <p className="text-meta">
                {hasClustering
                  ? 'Nenhum dado disponível para este gráfico.'
                  : 'Execute o clustering K-Means primeiro.'}
              </p>
            </div>
          </div>
        )}

        {/* Chart */}
        {!scatter.isLoading && !scatter.isError && scatter.data && hasClustering && (
          <div style={{ minHeight: 450 }}>
            <ChartErrorBoundary chartName="PCA Scatter">
              <PCAScatterChart data={scatter.data} />
            </ChartErrorBoundary>
          </div>
        )}
        {/* AI-Generated Insights */}
        <InsightSection experimentId={experimentId} chartType="pca_scatter" />
      </CardContent>
    </Card>
  );
}
