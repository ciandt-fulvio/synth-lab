// frontend/src/components/experiments/results/TryVsSuccessSection.tsx
// Section with Adoption distribution chart, controls, and explanation

import { useState } from 'react';
import { HelpCircle, BarChart3 } from 'lucide-react';
import { TryVsSuccessChart } from './charts/TryVsSuccessChart';
import { useAnalysisTryVsSuccessChart } from '@/hooks/use-analysis-charts';
import { Slider } from '@/components/ui/slider';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { ChartErrorBoundary } from '@/components/shared/ErrorBoundary';
import { InsightSection } from './InsightSection';

interface TryVsSuccessSectionProps {
  experimentId: string;
}

export function TryVsSuccessSection({ experimentId }: TryVsSuccessSectionProps) {
  const [adoptionThreshold, setAdoptionThreshold] = useState(0.5);
  const [showExplanation, setShowExplanation] = useState(false);

  const tryVsSuccess = useAnalysisTryVsSuccessChart(
    experimentId,
    0.5, // attemptThreshold no longer used, pass default
    adoptionThreshold
  );

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <CardTitle className="text-card-title flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-slate-500" />
          Distribuição de Adoção
        </CardTitle>
        <p className="text-meta">Cada ponto é um synth posicionado pela sua taxa de adoção</p>
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
                  Cada ponto representa um <strong>synth individual</strong> e sua taxa de adoção.
                  A linha tracejada indica o limiar mínimo de adoção configurado.
                </p>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li><strong>Acima do limiar</strong>: Synths que adotaram a feature acima do mínimo esperado</li>
                  <li><strong>Abaixo do limiar</strong>: Synths com adoção abaixo do mínimo esperado</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Para que serve o parâmetro?</h4>
                <p className="text-xs">
                  O slider controla a linha divisória. Pense nela como:
                  "<strong>Qual o mínimo aceitável de adoção para considerar um synth como bom?</strong>"
                </p>
              </div>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Controls */}
        <div className="bg-slate-50 rounded-lg p-3">
          <div className="space-y-1.5">
            <div className="flex justify-between items-center">
              <label className="text-xs text-slate-600">Adoção mínima de</label>
              <span className="text-xs font-medium text-slate-800 bg-white px-2 py-0.5 rounded">
                {Math.round(adoptionThreshold * 100)}%
              </span>
            </div>
            <Slider
              value={[adoptionThreshold * 100]}
              onValueChange={(values) => setAdoptionThreshold(values[0] / 100)}
              min={10}
              max={90}
              step={5}
              className="w-full"
            />
          </div>
        </div>

        {/* Chart area with loading/error/empty states */}
        {tryVsSuccess.isLoading && (
          <div className="flex flex-col items-center justify-center gap-4" style={{ height: 400 }}>
            <Skeleton className="w-full h-full rounded-lg" />
          </div>
        )}

        {tryVsSuccess.isError && !tryVsSuccess.isLoading && (
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
              onClick={() => tryVsSuccess.refetch()}
              className="btn-secondary"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Tentar Novamente
            </Button>
          </div>
        )}

        {!tryVsSuccess.data && !tryVsSuccess.isLoading && !tryVsSuccess.isError && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ height: 400 }}
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

        {!tryVsSuccess.isLoading && !tryVsSuccess.isError && tryVsSuccess.data && (
          <div style={{ minHeight: 400 }}>
            <ChartErrorBoundary chartName="Distribuição de Adoção">
              <TryVsSuccessChart data={tryVsSuccess.data} />
            </ChartErrorBoundary>
          </div>
        )}

        {/* AI-Generated Insights */}
        <InsightSection experimentId={experimentId} chartType="try_vs_success" />
      </CardContent>
    </Card>
  );
}
