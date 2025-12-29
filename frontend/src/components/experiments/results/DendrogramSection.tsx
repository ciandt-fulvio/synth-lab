// frontend/src/components/experiments/results/DendrogramSection.tsx
// Section with Dendrogram chart for hierarchical clustering and explanation

import { useState } from 'react';
import { HelpCircle, GitBranch, Sparkles, Loader2 } from 'lucide-react';
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
import { DendrogramChart } from './charts/DendrogramChart';
import { useAnalysisDendrogram } from '@/hooks/use-analysis-charts';
import { useGenerateAnalysisChartInsight } from '@/hooks/use-insights';

interface DendrogramSectionProps {
  experimentId: string;
  onCutHeight?: (height: number) => void;
}

export function DendrogramSection({ experimentId, onCutHeight }: DendrogramSectionProps) {
  const [showExplanation, setShowExplanation] = useState(false);

  const dendrogram = useAnalysisDendrogram(experimentId);
  const generateInsight = useGenerateAnalysisChartInsight(experimentId);

  const handleGenerateInsight = () => {
    if (!dendrogram.data) return;
    generateInsight.mutate({
      chartType: 'dendrogram',
      chartData: {
        nodes: dendrogram.data.nodes,
        max_height: dendrogram.data.max_height,
      },
    });
  };

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-card-title flex items-center gap-2">
              <GitBranch className="h-4 w-4 text-slate-500" />
              Dendrograma
            </CardTitle>
            <p className="text-meta">Visualização hierárquica dos clusters - clique para definir altura de corte</p>
          </div>
          {dendrogram.data && (
            <Button
              onClick={handleGenerateInsight}
              disabled={generateInsight.isPending}
              variant="outline"
              size="sm"
              className="text-indigo-600 border-indigo-200 hover:bg-indigo-50"
            >
              {generateInsight.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4 mr-2" />
              )}
              Gerar Insight
            </Button>
          )}
        </div>
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
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">O que é um Dendrograma?</h4>
                <p className="text-xs">
                  Um dendrograma mostra como os synths são <strong>agrupados hierarquicamente</strong>.
                  Na base estão synths individuais; conforme subimos, eles se juntam em grupos cada vez maiores.
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Como ler o gráfico?</h4>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li><strong>Eixo vertical</strong>: Distância entre grupos (dissimilaridade)</li>
                  <li><strong>Ramos</strong>: Mostram quais synths pertencem ao mesmo grupo</li>
                  <li><strong>Altura do merge</strong>: Quanto menor, mais similares os synths</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Como usar?</h4>
                <p className="text-xs">
                  <strong>Clique em um nó</strong> para definir a altura de corte. Todos os ramos
                  cortados nessa altura formam clusters distintos. Cortes mais baixos criam mais
                  clusters (mais específicos), cortes mais altos criam menos clusters (mais gerais).
                </p>
              </div>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Chart area with loading/error/empty states */}
        {dendrogram.isLoading && (
          <div className="flex flex-col items-center justify-center gap-4" style={{ height: 400 }}>
            <Skeleton className="w-full h-full rounded-lg" />
          </div>
        )}

        {dendrogram.isError && !dendrogram.isLoading && (
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
              onClick={() => dendrogram.refetch()}
              className="btn-secondary"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Tentar Novamente
            </Button>
          </div>
        )}

        {!dendrogram.data && !dendrogram.isLoading && !dendrogram.isError && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ height: 400 }}
          >
            <div className="icon-box-neutral">
              <GitBranch className="h-6 w-6 text-slate-400" />
            </div>
            <div>
              <p className="text-body text-slate-500 font-medium mb-1">Sem Dados</p>
              <p className="text-meta">Nenhum dado disponível para este gráfico.</p>
            </div>
          </div>
        )}

        {!dendrogram.isLoading && !dendrogram.isError && dendrogram.data && (
          <div style={{ minHeight: 400 }}>
            <ChartErrorBoundary chartName="Dendrograma">
              <DendrogramChart data={dendrogram.data} onCutHeight={onCutHeight} />
            </ChartErrorBoundary>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
