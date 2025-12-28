// frontend/src/components/experiments/results/PhaseLocation.tsx
// Phase 2: Problem Location - Heatmap, BoxPlot, Scatter, Tornado charts

import { useState } from 'react';
import { ChartContainer } from '@/components/shared/ChartContainer';
import { FailureHeatmap } from './charts/FailureHeatmap';
import { BoxPlotChart } from './charts/BoxPlotChart';
import { ScatterCorrelationChart } from './charts/ScatterCorrelationChart';
import { TornadoChart } from './charts/TornadoChart';
import {
  useFailureHeatmap,
  useBoxPlotChart,
  useScatterCorrelation,
  useTornadoChart,
} from '@/hooks/use-simulation-charts';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface PhaseLocationProps {
  simulationId: string;
}

const AXIS_OPTIONS = [
  { value: 'capability_mean', label: 'Capacidade' },
  { value: 'trust_mean', label: 'Confiança' },
  { value: 'complexity', label: 'Complexidade' },
  { value: 'initial_effort', label: 'Esforço Inicial' },
  { value: 'perceived_risk', label: 'Risco Percebido' },
  { value: 'time_to_value', label: 'Tempo p/ Valor' },
];

export function PhaseLocation({ simulationId }: PhaseLocationProps) {
  // State for configurable chart axes
  const [heatmapXAxis, setHeatmapXAxis] = useState('capability_mean');
  const [heatmapYAxis, setHeatmapYAxis] = useState('trust_mean');
  const [boxPlotAttr, setBoxPlotAttr] = useState('trust_mean');
  const [scatterXAxis, setScatterXAxis] = useState('trust_mean');
  const [scatterYAxis, setScatterYAxis] = useState('success_rate');

  // Fetch data
  const heatmap = useFailureHeatmap(simulationId, heatmapXAxis, heatmapYAxis);
  const boxPlot = useBoxPlotChart(simulationId, boxPlotAttr);
  const scatter = useScatterCorrelation(simulationId, scatterXAxis, scatterYAxis);
  const tornado = useTornadoChart(simulationId);

  return (
    <div className="space-y-6">
      {/* Row 1: Failure Heatmap */}
      <ChartContainer
        title="Mapa de Calor de Falhas"
        description="Identifica regiões com alta taxa de falha em duas dimensões"
        isLoading={heatmap.isLoading}
        isError={heatmap.isError}
        isEmpty={!heatmap.data}
        onRetry={() => heatmap.refetch()}
        height={400}
      >
        <div className="space-y-4">
          {/* Axis selectors */}
          <div className="flex flex-wrap gap-4 justify-center">
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-600">Eixo X:</span>
              <Select value={heatmapXAxis} onValueChange={setHeatmapXAxis}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {AXIS_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-600">Eixo Y:</span>
              <Select value={heatmapYAxis} onValueChange={setHeatmapYAxis}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {AXIS_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          {heatmap.data && <FailureHeatmap data={heatmap.data} />}
        </div>
      </ChartContainer>

      {/* Row 2: Two columns - Box Plot + Scatter */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Box Plot */}
        <ChartContainer
          title="Distribuição por Resultado"
          description="Compara a distribuição de um atributo entre grupos de resultado"
          isLoading={boxPlot.isLoading}
          isError={boxPlot.isError}
          isEmpty={!boxPlot.data}
          onRetry={() => boxPlot.refetch()}
          height={350}
        >
          <div className="space-y-4">
            <div className="flex items-center gap-2 justify-center">
              <span className="text-sm text-slate-600">Atributo:</span>
              <Select value={boxPlotAttr} onValueChange={setBoxPlotAttr}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {AXIS_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {boxPlot.data && <BoxPlotChart data={boxPlot.data} />}
          </div>
        </ChartContainer>

        {/* Scatter Correlation */}
        <ChartContainer
          title="Correlação"
          description="Visualiza a relação entre dois atributos"
          isLoading={scatter.isLoading}
          isError={scatter.isError}
          isEmpty={!scatter.data}
          onRetry={() => scatter.refetch()}
          height={350}
        >
          <div className="space-y-4">
            <div className="flex flex-wrap gap-4 justify-center">
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-600">X:</span>
                <Select value={scatterXAxis} onValueChange={setScatterXAxis}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {AXIS_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-600">Y:</span>
                <Select value={scatterYAxis} onValueChange={setScatterYAxis}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="success_rate">Taxa Sucesso</SelectItem>
                    <SelectItem value="failed_rate">Taxa Falha</SelectItem>
                    {AXIS_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            {scatter.data && <ScatterCorrelationChart data={scatter.data} />}
          </div>
        </ChartContainer>
      </div>

      {/* Row 3: Tornado Chart */}
      <ChartContainer
        title="Importância dos Atributos"
        description="Mostra o impacto de cada atributo na probabilidade de sucesso"
        isLoading={tornado.isLoading}
        isError={tornado.isError}
        isEmpty={!tornado.data}
        onRetry={() => tornado.refetch()}
        height={400}
      >
        {tornado.data && <TornadoChart data={tornado.data} />}
      </ChartContainer>
    </div>
  );
}
