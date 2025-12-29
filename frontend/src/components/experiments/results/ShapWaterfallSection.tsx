// frontend/src/components/experiments/results/ShapWaterfallSection.tsx
// Section with SHAP Waterfall chart for individual synth explanation

import { useState } from 'react';
import { HelpCircle, Activity, Sparkles, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { ChartErrorBoundary } from '@/components/shared/ErrorBoundary';
import { ShapWaterfallChart } from './charts/ShapWaterfallChart';
import { useAnalysisShapExplanation, useAnalysisExtremeCases } from '@/hooks/use-analysis-charts';
import { useGenerateAnalysisChartInsight } from '@/hooks/use-insights';

interface ShapWaterfallSectionProps {
  experimentId: string;
}

export function ShapWaterfallSection({ experimentId }: ShapWaterfallSectionProps) {
  const [showExplanation, setShowExplanation] = useState(false);
  const [selectedSynthId, setSelectedSynthId] = useState<string>('');

  // Get extreme cases to populate the synth selector
  const extremeCases = useAnalysisExtremeCases(experimentId, 5);

  // Get SHAP explanation for selected synth
  const shapExplanation = useAnalysisShapExplanation(experimentId, selectedSynthId, !!selectedSynthId);
  const generateInsight = useGenerateAnalysisChartInsight(experimentId);

  const handleGenerateInsight = () => {
    if (!shapExplanation.data) return;
    generateInsight.mutate({
      chartType: 'shap_explanation',
      chartData: {
        synth_id: selectedSynthId,
        base_value: shapExplanation.data.base_value,
        prediction: shapExplanation.data.prediction,
        contributions: shapExplanation.data.contributions,
      },
    });
  };

  // Build synth options from extreme cases
  const synthOptions: Array<{ id: string; label: string; type: string }> = [];
  if (extremeCases.data) {
    extremeCases.data.worst_failures.forEach((s) => {
      synthOptions.push({ id: s.synth_id, label: `${s.synth_id.substring(0, 8)}...`, type: 'Pior Falha' });
    });
    extremeCases.data.best_successes.forEach((s) => {
      synthOptions.push({ id: s.synth_id, label: `${s.synth_id.substring(0, 8)}...`, type: 'Melhor Sucesso' });
    });
    extremeCases.data.unexpected_cases.slice(0, 3).forEach((s) => {
      synthOptions.push({ id: s.synth_id, label: `${s.synth_id.substring(0, 8)}...`, type: 'Inesperado' });
    });
  }

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-card-title flex items-center gap-2">
              <Activity className="h-4 w-4 text-slate-500" />
              Explicação Individual (SHAP Waterfall)
            </CardTitle>
            <p className="text-meta">Como cada atributo contribuiu para o resultado de um synth específico</p>
          </div>
          {shapExplanation.data && (
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
                  <span className="text-sm font-medium">Como ler este gráfico?</span>
                </div>
                <span className="text-xs text-indigo-600">
                  {showExplanation ? 'Ocultar' : 'Ver explicação'}
                </span>
              </Button>
            </CollapsibleTrigger>

            <CollapsibleContent className="mt-3 space-y-3 text-sm text-slate-700">
              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">O que é um gráfico Waterfall?</h4>
                <p className="text-xs">
                  O waterfall mostra como a predição é construída a partir de uma <strong>base</strong>
                  (probabilidade média de sucesso) adicionando ou subtraindo a contribuição de cada atributo.
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Como ler?</h4>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li><strong>Base</strong>: Probabilidade inicial antes de considerar os atributos</li>
                  <li><strong className="text-green-600">Barras verdes</strong>: Atributos que aumentam a probabilidade</li>
                  <li><strong className="text-red-600">Barras vermelhas</strong>: Atributos que diminuem a probabilidade</li>
                  <li><strong>Predição final</strong>: Soma de todas as contribuições</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Por que selecionar um synth?</h4>
                <p className="text-xs">
                  Cada synth tem uma história única. Entender <strong>por que</strong> um synth
                  específico falhou ou teve sucesso ajuda a criar intervenções mais eficazes.
                </p>
              </div>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Synth selector */}
        <div className="bg-slate-50 rounded-lg p-4">
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-600">Selecione um synth:</span>
            <Select value={selectedSynthId} onValueChange={setSelectedSynthId}>
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Escolha um synth..." />
              </SelectTrigger>
              <SelectContent>
                {extremeCases.isLoading && (
                  <SelectItem value="loading" disabled>Carregando...</SelectItem>
                )}
                {synthOptions.map((opt) => (
                  <SelectItem key={opt.id} value={opt.id}>
                    <span className="flex items-center gap-2">
                      <span className={`text-xs px-1.5 py-0.5 rounded ${
                        opt.type === 'Pior Falha' ? 'bg-red-100 text-red-700' :
                        opt.type === 'Melhor Sucesso' ? 'bg-green-100 text-green-700' :
                        'bg-amber-100 text-amber-700'
                      }`}>
                        {opt.type}
                      </span>
                      <span className="font-mono text-xs">{opt.label}</span>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* No selection state */}
        {!selectedSynthId && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ height: 350 }}
          >
            <div className="icon-box-neutral">
              <Activity className="h-6 w-6 text-slate-400" />
            </div>
            <div>
              <p className="text-body text-slate-500 font-medium mb-1">Selecione um Synth</p>
              <p className="text-meta">Escolha um synth acima para ver a explicação detalhada.</p>
            </div>
          </div>
        )}

        {/* Loading state */}
        {selectedSynthId && shapExplanation.isLoading && (
          <div className="flex flex-col items-center justify-center gap-4" style={{ height: 350 }}>
            <Skeleton className="w-full h-full rounded-lg" />
          </div>
        )}

        {/* Error state */}
        {selectedSynthId && shapExplanation.isError && !shapExplanation.isLoading && (
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
              onClick={() => shapExplanation.refetch()}
              className="btn-secondary"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Tentar Novamente
            </Button>
          </div>
        )}

        {/* Chart */}
        {selectedSynthId && !shapExplanation.isLoading && !shapExplanation.isError && shapExplanation.data && (
          <div style={{ minHeight: 350 }}>
            <ChartErrorBoundary chartName="SHAP Waterfall">
              <ShapWaterfallChart data={shapExplanation.data} />
            </ChartErrorBoundary>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
