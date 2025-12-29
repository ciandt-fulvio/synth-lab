// frontend/src/components/experiments/results/HeatmapSection.tsx
// Section with Failure Heatmap chart showing 3 fixed axis combinations

import { useState } from 'react';
import { HelpCircle, Grid3X3, Sparkles, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { ChartErrorBoundary } from '@/components/shared/ErrorBoundary';
import { FailureHeatmap } from './charts/FailureHeatmap';
import { useAnalysisFailureHeatmap } from '@/hooks/use-analysis-charts';
import { useGenerateAnalysisChartInsight } from '@/hooks/use-insights';

interface HeatmapSectionProps {
  experimentId: string;
}

// Fixed axis combinations for UX analysis
const HEATMAP_VIEWS = [
  {
    id: 'capability-trust',
    label: 'Capacidade × Confiança',
    shortLabel: 'Cap × Conf',
    xAxis: 'capability_mean',
    yAxis: 'trust_mean',
    description: 'Identifica usuários com baixa capacidade e/ou confiança que falham mais',
  },
  {
    id: 'friction-exploration',
    label: 'Tolerância a Atrito × Exploração',
    shortLabel: 'Atrito × Explor',
    xAxis: 'friction_tolerance_mean',
    yAxis: 'exploration_prob',
    description: 'Mostra como tolerância a dificuldades e propensão a explorar afetam falhas',
  },
  {
    id: 'time-expertise',
    label: 'Tempo Disponível × Expertise',
    shortLabel: 'Tempo × Expert',
    xAxis: 'time_availability',
    yAxis: 'domain_expertise',
    description: 'Revela se falta de tempo ou expertise contribuem para falhas',
  },
] as const;

function HeatmapView({
  experimentId,
  xAxis,
  yAxis,
  description,
}: {
  experimentId: string;
  xAxis: string;
  yAxis: string;
  description: string;
}) {
  const heatmap = useAnalysisFailureHeatmap(experimentId, xAxis, yAxis);
  const generateInsight = useGenerateAnalysisChartInsight(experimentId);

  const handleGenerateInsight = () => {
    if (!heatmap.data) return;
    generateInsight.mutate({
      chartType: 'failure_heatmap',
      chartData: {
        x_axis: xAxis,
        y_axis: yAxis,
        cells: heatmap.data.cells,
      },
    });
  };

  if (heatmap.isLoading) {
    return (
      <div className="flex flex-col items-center justify-center gap-4" style={{ height: 400 }}>
        <Skeleton className="w-full h-full rounded-lg" />
      </div>
    );
  }

  if (heatmap.isError) {
    return (
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
          onClick={() => heatmap.refetch()}
          className="btn-secondary"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Tentar Novamente
        </Button>
      </div>
    );
  }

  if (!heatmap.data) {
    return (
      <div
        className="flex flex-col items-center justify-center gap-4 text-center"
        style={{ height: 400 }}
      >
        <div className="icon-box-neutral">
          <Grid3X3 className="h-6 w-6 text-slate-400" />
        </div>
        <div>
          <p className="text-body text-slate-500 font-medium mb-1">Sem Dados</p>
          <p className="text-meta">Nenhum dado disponível para este gráfico.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* View description and insight button */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-600">{description}</p>
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
      </div>

      {/* Chart */}
      <div style={{ minHeight: 400 }}>
        <ChartErrorBoundary chartName="Mapa de Calor">
          <FailureHeatmap data={heatmap.data} />
        </ChartErrorBoundary>
      </div>
    </div>
  );
}

export function HeatmapSection({ experimentId }: HeatmapSectionProps) {
  const [showExplanation, setShowExplanation] = useState(false);
  const [activeView, setActiveView] = useState(HEATMAP_VIEWS[0].id);

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <div>
          <CardTitle className="text-card-title flex items-center gap-2">
            <Grid3X3 className="h-4 w-4 text-slate-500" />
            Mapa de Calor de Falhas
          </CardTitle>
          <p className="text-meta">
            Identifica regiões com alta taxa de falha em duas dimensões de perfil de usuário
          </p>
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
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">
                  O que este gráfico mostra?
                </h4>
                <p className="text-xs">
                  O mapa de calor divide os synths em uma grade baseada em{' '}
                  <strong>dois atributos de perfil</strong>. Cada célula mostra a taxa de falha
                  média dos synths naquela combinação de atributos.
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">Como ler as cores?</h4>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li>
                    <strong className="text-green-600">Verde</strong>: Baixa taxa de falha (bom!)
                  </li>
                  <li>
                    <strong className="text-amber-600">Amarelo/Laranja</strong>: Taxa de falha
                    moderada
                  </li>
                  <li>
                    <strong className="text-red-600">Vermelho</strong>: Alta taxa de falha
                    (problema!)
                  </li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">O que fazer com isso?</h4>
                <p className="text-xs">
                  Procure por <strong>regiões vermelhas</strong> - elas indicam combinações de
                  perfil onde os usuários falham mais. Isso ajuda a identificar{' '}
                  <strong>limiares</strong> ("a partir daqui quebra") e{' '}
                  <strong>regiões críticas</strong> do espaço de usuários.
                </p>
              </div>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Tabs for different views */}
        <Tabs value={activeView} onValueChange={setActiveView} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            {HEATMAP_VIEWS.map((view) => (
              <TabsTrigger key={view.id} value={view.id} className="text-xs sm:text-sm">
                {view.shortLabel}
              </TabsTrigger>
            ))}
          </TabsList>

          {HEATMAP_VIEWS.map((view) => (
            <TabsContent key={view.id} value={view.id} className="mt-4">
              <HeatmapView
                experimentId={experimentId}
                xAxis={view.xAxis}
                yAxis={view.yAxis}
                description={view.description}
              />
            </TabsContent>
          ))}
        </Tabs>
      </CardContent>
    </Card>
  );
}
