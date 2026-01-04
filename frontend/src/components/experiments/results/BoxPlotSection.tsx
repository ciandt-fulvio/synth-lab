// frontend/src/components/experiments/results/BoxPlotSection.tsx
// Section with Box Plot chart, attribute selector, and explanation

import { useState } from 'react';
import { HelpCircle, BarChart2 } from 'lucide-react';
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
import { BoxPlotChart } from './charts/BoxPlotChart';
// import { useBoxPlotChart } from '@/hooks/use-simulation-charts'; // TODO: Box plot endpoint not yet migrated
import { useGenerateAnalysisChartInsight } from '@/hooks/use-insights';

interface BoxPlotSectionProps {
  simulationId: string;
}

const ATTRIBUTE_OPTIONS = [
  { value: 'capability_mean', label: 'Capacidade' },
  { value: 'trust_mean', label: 'Confiança' },
  { value: 'complexity', label: 'Complexidade' },
  { value: 'initial_effort', label: 'Esforço Inicial' },
  { value: 'perceived_risk', label: 'Risco Percebido' },
  { value: 'time_to_value', label: 'Tempo p/ Valor' },
];

export function BoxPlotSection({ simulationId }: BoxPlotSectionProps) {
  const [showExplanation, setShowExplanation] = useState(false);
  const [attribute, setAttribute] = useState('trust_mean');

  // TODO: Box plot endpoint not yet migrated to new analysis API
  // const boxPlot = useBoxPlotChart(simulationId, attribute);
  const boxPlot = { data: null, isLoading: false, isError: false, refetch: () => {} };
  const generateInsight = useGenerateAnalysisChartInsight(simulationId);

  const handleGenerateInsight = () => {
    if (!boxPlot.data) return;
    generateInsight.mutate({
      chartType: 'box_plot',
      chartData: {
        attribute,
        groups: boxPlot.data.groups,
      },
    });
  };

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <CardTitle className="text-card-title flex items-center gap-2">
          <BarChart2 className="h-4 w-4 text-slate-500" />
          Distribuição por Resultado
        </CardTitle>
        <p className="text-meta">Compara como um atributo varia entre os grupos de resultado</p>
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
                  O box plot mostra a <strong>distribuição</strong> de um atributo para cada grupo de resultado
                  (sucesso, falha, não tentou). A caixa representa onde estão 50% dos valores centrais.
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Como ler o gráfico?</h4>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li><strong>Linha central</strong>: Mediana (valor típico)</li>
                  <li><strong>Caixa</strong>: Intervalo interquartil (50% dos dados)</li>
                  <li><strong>Bigodes</strong>: Valores mínimo e máximo</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">O que procurar?</h4>
                <p className="text-xs">
                  Compare as medianas entre grupos. Se o grupo de <strong className="text-green-600">sucesso</strong>
                  {' '}tem mediana muito diferente do grupo de <strong className="text-red-600">falha</strong>,
                  esse atributo pode ser um bom preditor de resultado.
                </p>
              </div>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Controls */}
        <div className="bg-slate-50 rounded-lg p-3">
          <div className="flex flex-wrap gap-4 justify-center">
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-600">Atributo:</span>
              <Select value={attribute} onValueChange={setAttribute}>
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ATTRIBUTE_OPTIONS.map((opt) => (
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
        {boxPlot.isLoading && (
          <div className="flex flex-col items-center justify-center gap-4" style={{ height: 350 }}>
            <Skeleton className="w-full h-full rounded-lg" />
          </div>
        )}

        {boxPlot.isError && !boxPlot.isLoading && (
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
              onClick={() => boxPlot.refetch()}
              className="btn-secondary"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Tentar Novamente
            </Button>
          </div>
        )}

        {!boxPlot.data && !boxPlot.isLoading && !boxPlot.isError && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ height: 350 }}
          >
            <div className="icon-box-neutral">
              <BarChart2 className="h-6 w-6 text-slate-400" />
            </div>
            <div>
              <p className="text-body text-slate-500 font-medium mb-1">Sem Dados</p>
              <p className="text-meta">Nenhum dado disponível para este gráfico.</p>
            </div>
          </div>
        )}

        {!boxPlot.isLoading && !boxPlot.isError && boxPlot.data && (
          <div style={{ minHeight: 350 }}>
            <ChartErrorBoundary chartName="Box Plot">
              <BoxPlotChart data={boxPlot.data} />
            </ChartErrorBoundary>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
