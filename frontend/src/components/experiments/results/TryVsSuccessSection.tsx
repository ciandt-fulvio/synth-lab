// frontend/src/components/experiments/results/TryVsSuccessSection.tsx
// Section with Try vs Success chart, controls, and explanation

import { useState } from 'react';
import { Info, HelpCircle, BarChart3 } from 'lucide-react';
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
  const [attemptThreshold, setAttemptThreshold] = useState(0.5);
  const [successThreshold, setSuccessThreshold] = useState(0.5);
  const [showExplanation, setShowExplanation] = useState(false);

  const tryVsSuccess = useAnalysisTryVsSuccessChart(
    experimentId,
    attemptThreshold,
    successThreshold
  );

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <CardTitle className="text-card-title flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-slate-500" />
          Tentativa vs Sucesso
        </CardTitle>
        <p className="text-meta">Cada ponto é um synth posicionado pela sua taxa de tentativa e sucesso</p>
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
                  Cada ponto representa um <strong>synth individual</strong>. Diferente do gráfico de
                  Distribuição (que mostra médias), aqui vemos onde cada synth se posiciona em duas dimensões:
                </p>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li><strong>Eixo X (Taxa de Tentativa)</strong>: Do total de simulacoes de um synth, qual % das vezes ele tentou usar a feature</li>
                  <li><strong>Eixo Y (Taxa de Sucesso)</strong>: Apenas entre as vezes que tentou, qual % das vezes teve sucesso</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">O que são os quadrantes?</h4>
                <p className="text-xs mb-2">
                  As linhas tracejadas dividem o gráfico em 4 quadrantes:
                </p>
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-green-100 p-2 rounded-lg">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
                      <span className="font-medium text-green-800 text-xs">OK</span>
                    </div>
                    <p className="text-green-700 text-xs leading-tight">
                      Tenta bastante + Tem alto sucesso. É a situacao ideal!
                    </p>
                  </div>
                  <div className="bg-blue-100 p-2 rounded-lg">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                      <span className="font-medium text-blue-800 text-xs">Descoberta</span>
                    </div>
                    <p className="text-blue-700 text-xs leading-tight">
                      Baixa tentativa + Alto sucesso. Não descobrem a feature.
                    </p>
                  </div>
                  <div className="bg-red-100 p-2 rounded-lg">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
                      <span className="font-medium text-red-800 text-xs">Usabilidade</span>
                    </div>
                    <p className="text-red-700 text-xs leading-tight">
                      Tenta bastante + Tem pouco sucesso. Talvez está complexo para usar.
                    </p>
                  </div>
                  <div className="bg-amber-100 p-2 rounded-lg">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <div className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                      <span className="font-medium text-amber-800 text-xs">Baixo Valor</span>
                    </div>
                    <p className="text-amber-700 text-xs leading-tight">
                      Tenta pouco + Tem pouco sucesso. Feature irrelevante para o synth?
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Para que servem os parâmetros?</h4>
                <p className="text-xs">
                  Os sliders controlam as linhas divisórias
                </p>
                <p className="text-xs mt-1">
                  Pense nelas como: "Qual o <strong>mínimo aceitável de tentativa e sucesso para considerar um synth como bom?</strong>"
                </p>
              </div>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Controls */}
        <div className="bg-slate-50 rounded-lg p-3">

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <label className="text-xs text-slate-600">Tentar no minimo</label>
                <span className="text-xs font-medium text-slate-800 bg-white px-2 py-0.5 rounded">
                  {Math.round(attemptThreshold * 100)}%
                </span>
              </div>
              <Slider
                value={[attemptThreshold * 100]}
                onValueChange={(values) => setAttemptThreshold(values[0] / 100)}
                min={10}
                max={90}
                step={5}
                className="w-full"
              />
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <label className="text-xs text-slate-600">Sucesso minimo de</label>
                <span className="text-xs font-medium text-slate-800 bg-white px-2 py-0.5 rounded">
                  {Math.round(successThreshold * 100)}%
                </span>
              </div>
              <Slider
                value={[successThreshold * 100]}
                onValueChange={(values) => setSuccessThreshold(values[0] / 100)}
                min={10}
                max={90}
                step={5}
                className="w-full"
              />
            </div>
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
            <ChartErrorBoundary chartName="Tentativa vs Sucesso">
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
