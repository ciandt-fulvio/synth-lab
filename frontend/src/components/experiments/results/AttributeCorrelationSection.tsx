// frontend/src/components/experiments/results/AttributeCorrelationSection.tsx
// Section showing correlation of synth attributes with attempt and success rates

import { useState } from 'react';
import { BarChart3, HelpCircle, Sparkles, Loader2, AlertCircle, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Skeleton } from '@/components/ui/skeleton';
import { ChartErrorBoundary } from '@/components/shared/ErrorBoundary';
import { AttributeCorrelationChart } from './charts/AttributeCorrelationChart';
import { useAnalysisAttributeCorrelations } from '@/hooks/use-analysis-charts';
import { useGenerateAnalysisChartInsight } from '@/hooks/use-insights';

interface AttributeCorrelationSectionProps {
  experimentId: string;
}

export function AttributeCorrelationSection({ experimentId }: AttributeCorrelationSectionProps) {
  const [showExplanation, setShowExplanation] = useState(false);

  const correlations = useAnalysisAttributeCorrelations(experimentId);
  const generateInsight = useGenerateAnalysisChartInsight(experimentId);

  const handleGenerateInsight = () => {
    if (!correlations.data) return;
    generateInsight.mutate({
      chartType: 'attribute_correlations',
      chartData: {
        correlations: correlations.data.correlations,
        total_synths: correlations.data.total_synths,
      },
    });
  };

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-card-title flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-slate-500" />
              Importância dos Atributos
            </CardTitle>
            <p className="text-meta">
              Quais características dos usuários mais influenciam tentativa e sucesso
            </p>
          </div>
          {correlations.data && (
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
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">O que este gráfico mostra?</h4>
                <p className="text-xs">
                  Mostra a correlação de Pearson entre cada atributo dos synths e duas métricas:
                  a taxa de tentativa (quem tentou usar) e a taxa de sucesso (quem conseguiu).
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">O que significam as barras?</h4>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li><strong>Barras azuis (positivas)</strong>: Quando o atributo aumenta, a métrica também aumenta</li>
                  <li><strong>Barras vermelhas (negativas)</strong>: Quando o atributo aumenta, a métrica diminui</li>
                  <li><strong>Barras cinzas</strong>: Correlação não estatisticamente significativa</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">O que procurar?</h4>
                <p className="text-xs">
                  Atributos com correlações fortes (barras longas) e significativas (coloridas)
                  são os mais importantes para prever comportamento. Use isso para identificar
                  quais características de usuários priorizar.
                </p>
              </div>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Loading state */}
        {correlations.isLoading && (
          <div className="flex flex-col items-center justify-center gap-4" style={{ height: 400 }}>
            <Skeleton className="w-full h-full rounded-lg" />
          </div>
        )}

        {/* Error state */}
        {correlations.isError && !correlations.isLoading && (
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
              onClick={() => correlations.refetch()}
              className="btn-secondary"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Tentar Novamente
            </Button>
          </div>
        )}

        {/* Empty state */}
        {!correlations.data && !correlations.isLoading && !correlations.isError && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ height: 400 }}
          >
            <div className="icon-box-neutral">
              <BarChart3 className="h-6 w-6 text-slate-400" />
            </div>
            <div>
              <p className="text-body text-slate-500 font-medium mb-1">Sem Dados</p>
              <p className="text-meta">Nenhum dado disponível. Execute uma análise primeiro.</p>
            </div>
          </div>
        )}

        {/* Chart */}
        {!correlations.isLoading && !correlations.isError && correlations.data && (
          <ChartErrorBoundary chartName="Correlação de Atributos">
            <AttributeCorrelationChart data={correlations.data} />
          </ChartErrorBoundary>
        )}
      </CardContent>
    </Card>
  );
}
