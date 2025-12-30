// frontend/src/components/experiments/results/ShapSummarySection.tsx
// Section with SHAP Summary chart and explanation

import { useState } from 'react';
import { HelpCircle, BarChart3 } from 'lucide-react';
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
import { ShapSummaryChart } from './charts/ShapSummaryChart';
import { useAnalysisShapSummary } from '@/hooks/use-analysis-charts';

interface ShapSummarySectionProps {
  experimentId: string;
}

export function ShapSummarySection({ experimentId }: ShapSummarySectionProps) {
  const [showExplanation, setShowExplanation] = useState(false);

  const shapSummary = useAnalysisShapSummary(experimentId);

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <CardTitle className="text-card-title flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-slate-500" />
          Importância de Features (SHAP)
        </CardTitle>
        <p className="text-meta">Quanto cada atributo contribui para o sucesso ou falha</p>
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
                  <span className="text-sm font-medium">O que é SHAP?</span>
                </div>
                <span className="text-xs text-indigo-600">
                  {showExplanation ? 'Ocultar' : 'Ver explicação'}
                </span>
              </Button>
            </CollapsibleTrigger>

            <CollapsibleContent className="mt-3 space-y-3 text-sm text-slate-700">
              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">O que é SHAP?</h4>
                <p className="text-xs">
                  SHAP (SHapley Additive exPlanations) é uma técnica de explicabilidade que
                  mede a <strong>contribuição real</strong> de cada atributo para a predição
                  de sucesso ou falha. É baseado em teoria dos jogos.
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Como ler o gráfico?</h4>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li><strong>Barras maiores</strong>: Atributos mais importantes para o resultado</li>
                  <li><strong className="text-green-600">Verde</strong>: Valores altos aumentam sucesso</li>
                  <li><strong className="text-red-600">Vermelho</strong>: Valores altos diminuem sucesso</li>
                  <li><strong className="text-amber-600">Amarelo</strong>: Efeito depende do contexto</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Por que usar SHAP?</h4>
                <p className="text-xs">
                  Diferente de correlação simples, SHAP considera as <strong>interações</strong>
                  entre atributos. Dois atributos podem ter baixa correlação individual mas
                  forte efeito combinado.
                </p>
              </div>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Loading state */}
        {shapSummary.isLoading && (
          <div className="flex flex-col items-center justify-center gap-4" style={{ height: 350 }}>
            <Skeleton className="w-full h-full rounded-lg" />
          </div>
        )}

        {/* Error state */}
        {shapSummary.isError && !shapSummary.isLoading && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ height: 350 }}
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
              onClick={() => shapSummary.refetch()}
              className="btn-secondary"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Tentar Novamente
            </Button>
          </div>
        )}

        {/* Empty state */}
        {!shapSummary.data && !shapSummary.isLoading && !shapSummary.isError && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ height: 350 }}
          >
            <div className="icon-box-neutral">
              <BarChart3 className="h-6 w-6 text-slate-400" />
            </div>
            <div>
              <p className="text-body text-slate-500 font-medium mb-1">Sem Dados</p>
              <p className="text-meta">Nenhum dado disponível para este gráfico.</p>
            </div>
          </div>
        )}

        {/* Chart */}
        {!shapSummary.isLoading && !shapSummary.isError && shapSummary.data && (
          <div style={{ minHeight: 350 }}>
            <ChartErrorBoundary chartName="SHAP Summary">
              <ShapSummaryChart data={shapSummary.data} />
            </ChartErrorBoundary>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
