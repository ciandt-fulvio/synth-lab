// frontend/src/components/experiments/results/ScatterSection.tsx
// Section with Scatter Correlation chart, axis selectors, and explanation

import { useState } from 'react';
import { HelpCircle, ScatterChart as ScatterIcon } from 'lucide-react';
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
import { ScatterCorrelationChart } from './charts/ScatterCorrelationChart';
import { useAnalysisScatterCorrelation } from '@/hooks/use-analysis-charts';

interface ScatterSectionProps {
  experimentId: string;
}

// Same 9 synth attributes as AttributeCorrelationChart
const X_AXIS_OPTIONS = [
  { value: 'capability_mean', label: 'Capacidade Média' },
  { value: 'trust_mean', label: 'Confiança Média' },
  { value: 'friction_tolerance_mean', label: 'Tolerância a Atrito' },
  { value: 'exploration_prob', label: 'Propensão a Explorar' },
  { value: 'digital_literacy', label: 'Literacia Digital' },
  { value: 'similar_tool_experience', label: 'Experiência Similar' },
  { value: 'motor_ability', label: 'Habilidade Motora' },
  { value: 'time_availability', label: 'Tempo Disponível' },
  { value: 'domain_expertise', label: 'Expertise no Domínio' },
];

// Only attempt and success rates
const Y_AXIS_OPTIONS = [
  { value: 'attempt_rate', label: 'Taxa de Tentativa' },
  { value: 'success_rate', label: 'Taxa de Sucesso' },
];

export function ScatterSection({ experimentId }: ScatterSectionProps) {
  const [showExplanation, setShowExplanation] = useState(false);
  const [xAxis, setXAxis] = useState('capability_mean');
  const [yAxis, setYAxis] = useState('success_rate');

  const scatter = useAnalysisScatterCorrelation(experimentId, xAxis, yAxis);

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <div>
          <CardTitle className="text-card-title flex items-center gap-2">
            <ScatterIcon className="h-4 w-4 text-slate-500" />
            Correlação de Atributos
          </CardTitle>
          <p className="text-meta">Visualiza a relação entre dois atributos e identifica padrões</p>
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
                  Cada ponto representa um synth. A posição mostra os valores de dois atributos.
                  As cores indicam o resultado (sucesso, falha, não tentou).
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">O que é correlação?</h4>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li><strong>r ≈ 1</strong>: Correlação positiva forte (quando X aumenta, Y aumenta)</li>
                  <li><strong>r ≈ -1</strong>: Correlação negativa forte (quando X aumenta, Y diminui)</li>
                  <li><strong>r ≈ 0</strong>: Sem correlação (variáveis independentes)</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">O que procurar?</h4>
                <p className="text-xs">
                  Procure por <strong>agrupamentos de cores</strong>. Se pontos verdes (sucesso)
                  estão concentrados em uma região e vermelhos (falha) em outra, você encontrou
                  um padrão importante.
                </p>
              </div>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Controls */}
        <div className="bg-slate-50 rounded-lg p-3">
          <div className="flex flex-wrap gap-4 justify-center">
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-600">Eixo X:</span>
              <Select value={xAxis} onValueChange={setXAxis}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {X_AXIS_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-600">Eixo Y:</span>
              <Select value={yAxis} onValueChange={setYAxis}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Y_AXIS_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Chart area with loading/error/empty states */}
        {scatter.isLoading && (
          <div className="flex flex-col items-center justify-center gap-4" style={{ height: 400 }}>
            <Skeleton className="w-full h-full rounded-lg" />
          </div>
        )}

        {scatter.isError && !scatter.isLoading && (
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
              onClick={() => scatter.refetch()}
              className="btn-secondary"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Tentar Novamente
            </Button>
          </div>
        )}

        {!scatter.data && !scatter.isLoading && !scatter.isError && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ height: 400 }}
          >
            <div className="icon-box-neutral">
              <ScatterIcon className="h-6 w-6 text-slate-400" />
            </div>
            <div>
              <p className="text-body text-slate-500 font-medium mb-1">Sem Dados</p>
              <p className="text-meta">Nenhum dado disponível para este gráfico.</p>
            </div>
          </div>
        )}

        {!scatter.isLoading && !scatter.isError && scatter.data && (
          <div style={{ minHeight: 400 }}>
            <ChartErrorBoundary chartName="Correlação">
              <ScatterCorrelationChart data={scatter.data} />
            </ChartErrorBoundary>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
