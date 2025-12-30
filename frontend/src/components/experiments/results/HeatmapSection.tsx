// frontend/src/components/experiments/results/HeatmapSection.tsx
// Failure Heatmap section with professional view switching

import { useState } from 'react';
import { AlertCircle, RefreshCw, Info } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { ChartErrorBoundary } from '@/components/shared/ErrorBoundary';
import { FailureHeatmap } from './charts/FailureHeatmap';
import { useAnalysisFailureHeatmap } from '@/hooks/use-analysis-charts';

interface HeatmapSectionProps {
  experimentId: string;
}

// Analysis perspectives for the heatmap - only observable attributes
const PERSPECTIVES = [
  {
    id: 'tech-experience',
    name: 'Tecnologia vs Experiência',
    xAxis: 'digital_literacy',
    yAxis: 'similar_tool_experience',
    insight: 'Usuários com baixa familiaridade tecnológica e pouca experiência tendem a falhar mais',
  },
  {
    id: 'knowledge-time',
    name: 'Conhecimento vs Tempo',
    xAxis: 'domain_expertise',
    yAxis: 'time_availability',
    insight: 'Falta de conhecimento do assunto ou tempo disponível podem causar falhas',
  },
  {
    id: 'tech-physical',
    name: 'Tecnologia vs Físico',
    xAxis: 'digital_literacy',
    yAxis: 'motor_ability',
    insight: 'Limitações físicas combinadas com baixa familiaridade tecnológica afetam o sucesso',
  },
] as const;

function HeatmapContent({
  experimentId,
  perspective,
}: {
  experimentId: string;
  perspective: (typeof PERSPECTIVES)[number];
}) {
  const heatmap = useAnalysisFailureHeatmap(experimentId, perspective.xAxis, perspective.yAxis);

  const handleGenerateInsight = () => {
    if (!heatmap.data) return;
    generateInsight.mutate({
      chartType: 'failure_heatmap',
      chartData: {
        x_axis: perspective.xAxis,
        y_axis: perspective.yAxis,
        cells: heatmap.data.cells,
      },
    });
  };

  if (heatmap.isLoading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-4 w-48 bg-slate-200 rounded" />
        <Skeleton className="w-full aspect-square max-w-md mx-auto rounded-lg" />
        <div className="h-3 w-32 bg-slate-200 rounded mx-auto" />
      </div>
    );
  }

  if (heatmap.isError) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-12 h-12 rounded-full bg-red-50 flex items-center justify-center mb-3">
          <AlertCircle className="h-6 w-6 text-red-500" />
        </div>
        <p className="text-sm text-slate-600 mb-1">Erro ao carregar dados</p>
        <p className="text-xs text-slate-400 mb-4">Não foi possível buscar o mapa de calor</p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => heatmap.refetch()}
          className="text-xs"
        >
          <RefreshCw className="h-3 w-3 mr-1.5" />
          Tentar novamente
        </Button>
      </div>
    );
  }

  if (!heatmap.data || heatmap.data.cells.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mb-3">
          <Info className="h-5 w-5 text-slate-400" />
        </div>
        <p className="text-sm text-slate-500">Nenhum dado disponível</p>
        <p className="text-xs text-slate-400">Execute uma análise para ver o mapa de calor</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Insight hint */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500 italic">💡 {perspective.insight}</p>
        <Button
          onClick={handleGenerateInsight}
          disabled={generateInsight.isPending}
          variant="ghost"
          size="sm"
          className="text-xs text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 h-7 px-2"
        >
          {generateInsight.isPending ? (
            <Loader2 className="h-3 w-3 mr-1.5 animate-spin" />
          ) : (
            <Sparkles className="h-3 w-3 mr-1.5" />
          )}
          Gerar análise IA
        </Button>
      </div>

      {/* Chart */}
      <ChartErrorBoundary chartName="Mapa de Calor">
        <FailureHeatmap data={heatmap.data} />
      </ChartErrorBoundary>
    </div>
  );
}

export function HeatmapSection({ experimentId }: HeatmapSectionProps) {
  const [activeId, setActiveId] = useState(PERSPECTIVES[0].id);
  const activePerspective = PERSPECTIVES.find((p) => p.id === activeId) || PERSPECTIVES[0];

  return (
    <Card className="overflow-hidden border-slate-200">
      {/* Header with view switcher */}
      <div className="bg-gradient-to-r from-slate-50 to-white border-b border-slate-100 px-5 py-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-800">
              Mapa de Calor de Falhas
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Visualize onde os usuários falham com base em seus atributos
            </p>
          </div>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button className="p-1.5 rounded-md hover:bg-slate-100 transition-colors">
                  <Info className="h-4 w-4 text-slate-400" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="left" className="max-w-xs text-xs">
                <p className="font-medium mb-1">Como interpretar</p>
                <p className="text-slate-400">
                  Cada célula mostra a taxa de falha para usuários com aquela combinação de atributos.
                  Cores mais quentes (laranja/vermelho) indicam maior taxa de falha.
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        {/* Segmented control for perspectives */}
        <div className="mt-4">
          <div className="inline-flex p-0.5 bg-slate-100 rounded-lg">
            {PERSPECTIVES.map((perspective) => (
              <button
                key={perspective.id}
                onClick={() => setActiveId(perspective.id)}
                className={`
                  px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-200
                  ${
                    activeId === perspective.id
                      ? 'bg-white text-slate-800 shadow-sm'
                      : 'text-slate-500 hover:text-slate-700'
                  }
                `}
              >
                {perspective.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <CardContent className="p-5">
        <HeatmapContent experimentId={experimentId} perspective={activePerspective} />
      </CardContent>
    </Card>
  );
}
