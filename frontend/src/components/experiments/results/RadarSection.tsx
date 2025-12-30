// frontend/src/components/experiments/results/RadarSection.tsx
// Section with Radar Comparison chart and explanation

import { useState } from 'react';
import { HelpCircle, Hexagon } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { ChartErrorBoundary } from '@/components/shared/ErrorBoundary';
import { RadarComparisonChart } from './charts/RadarComparisonChart';
import { useAnalysisRadarComparison } from '@/hooks/use-analysis-charts';

import { InsightSection } from './InsightSection';
interface RadarSectionProps {
  experimentId: string;
  hasClustering?: boolean;
}

export function RadarSection({ experimentId, hasClustering = true }: RadarSectionProps) {
  const [showExplanation, setShowExplanation] = useState(false);

  // Only fetch radar data when clustering exists
  const radar = useAnalysisRadarComparison(experimentId, hasClustering);

  const handleGenerateInsight = () => {
    if (!radar.data) return;
    generateInsight.mutate({
      chartType: 'radar',
      chartData: {
        clusters: radar.data.clusters,
        axis_labels: radar.data.axis_labels,
      },
    });
  };

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <CardTitle className="text-card-title flex items-center gap-2">
          <Hexagon className="h-4 w-4 text-slate-500" />
          Comparação de Perfis
        </CardTitle>
        <p className="text-meta">Compara os atributos médios de cada cluster</p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Explanation section - collapsible */}
        <Collapsible open={showExplanation} onOpenChange={setShowExplanation}>
          <div className="bg-gradient-to-r from-slate-50 to-indigo-50 border border-slate-200 rounded-lg p-3">
            <CollapsibleTrigger asChild>
              <Button
                variant="ghost"
                className="w-full flex items-center justify-between p-0 h-auto hover:bg-transparent"
              >
                <div className="flex items-center gap-2 text-indigo-700">
                  <HelpCircle className="h-4 w-4" />
                  <span className="text-sm font-medium">Como interpretar este gráfico?</span>
                </div>
                <span className="text-xs text-indigo-600">
                  {showExplanation ? 'Ocultar' : 'Ver explicação'}
                </span>
              </Button>
            </CollapsibleTrigger>

            <CollapsibleContent className="mt-3 space-y-3 text-sm text-slate-700">
              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">O que é um Gráfico Radar?</h4>
                <p className="text-xs">
                  O radar mostra múltiplos atributos em um só gráfico. Cada eixo representa um
                  atributo, e a <strong>área preenchida</strong> mostra o perfil de cada cluster.
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Como ler o gráfico?</h4>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li><strong>Área maior</strong>: Cluster com valores altos em múltiplos atributos</li>
                  <li><strong>Formato</strong>: Mostra em quais atributos o cluster se destaca</li>
                  <li><strong>Sobreposição</strong>: Onde clusters são similares</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Como usar?</h4>
                <p className="text-xs">
                  Compare os formatos dos clusters para identificar <strong>personas distintas</strong>.
                  Por exemplo, um cluster pode ter alta capacidade mas baixa confiança,
                  enquanto outro tem o padrão oposto.
                </p>
              </div>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Chart area with loading/error/empty states */}
        {radar.isLoading && (
          <div className="flex flex-col items-center justify-center gap-4" style={{ height: 450 }}>
            <Skeleton className="w-full h-full rounded-lg" />
          </div>
        )}

        {radar.isError && !radar.isLoading && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ height: 450 }}
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
              onClick={() => radar.refetch()}
              className="btn-secondary"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Tentar Novamente
            </Button>
          </div>
        )}

        {(!radar.data || !hasClustering) && !radar.isLoading && !radar.isError && (
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
                  : 'Gere clusters via K-Means primeiro para ver a comparação de perfis.'}
              </p>
            </div>
          </div>
        )}

        {!radar.isLoading && !radar.isError && radar.data && hasClustering && (
          <div style={{ minHeight: 450 }}>
            <ChartErrorBoundary chartName="Radar">
              <RadarComparisonChart data={radar.data} />
            </ChartErrorBoundary>
          </div>
        )}
        {/* AI-Generated Insights */}
        <InsightSection experimentId={experimentId} chartType="radar_comparison" />
      </CardContent>
    </Card>
  );
}
