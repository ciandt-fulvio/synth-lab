// frontend/src/components/experiments/results/charts/FailureHeatmap.tsx
// Heatmap showing failure rates across two dimensions

import type { FailureHeatmapChart } from '@/types/simulation';

interface FailureHeatmapProps {
  data: FailureHeatmapChart;
}

// Color scale for the heatmap (green to red)
function getHeatColor(value: number): string {
  // value is between 0 and 1
  if (value < 0.2) return 'bg-green-100 text-green-800';
  if (value < 0.4) return 'bg-green-200 text-green-800';
  if (value < 0.5) return 'bg-yellow-100 text-yellow-800';
  if (value < 0.6) return 'bg-amber-200 text-amber-800';
  if (value < 0.7) return 'bg-orange-200 text-orange-800';
  if (value < 0.8) return 'bg-red-200 text-red-800';
  return 'bg-red-400 text-white';
}

function formatAxisLabel(label: string): string {
  const labelMap: Record<string, string> = {
    capability_mean: 'Capacidade',
    trust_mean: 'Confiança',
    complexity: 'Complexidade',
    initial_effort: 'Esforço Inicial',
    perceived_risk: 'Risco Percebido',
    time_to_value: 'Tempo p/ Valor',
  };
  return labelMap[label] || label;
}

export function FailureHeatmap({ data }: FailureHeatmapProps) {
  const { cells, x_axis, y_axis, x_bins, y_bins, metric } = data;

  // Get unique bin labels
  const xLabels = [...new Set(cells.map((c) => c.x_bin))].sort((a, b) => a - b);
  const yLabels = [...new Set(cells.map((c) => c.y_bin))].sort((a, b) => b - a); // Reverse for visual display

  // Create a lookup map for cells
  const cellMap = new Map<string, typeof cells[0]>();
  cells.forEach((cell) => {
    cellMap.set(`${cell.x_bin}-${cell.y_bin}`, cell);
  });

  return (
    <div className="space-y-4">
      {/* Axis labels */}
      <div className="flex justify-between text-sm text-slate-600">
        <span>Eixo X: {formatAxisLabel(x_axis)}</span>
        <span>Eixo Y: {formatAxisLabel(y_axis)}</span>
      </div>

      {/* Heatmap grid */}
      <div className="overflow-x-auto">
        <div className="inline-block min-w-full">
          {/* Y-axis label */}
          <div className="flex">
            <div className="w-16 flex items-center justify-center">
              <span
                className="text-xs text-slate-500 font-medium transform -rotate-90 whitespace-nowrap"
                style={{ writingMode: 'vertical-rl' }}
              >
                {formatAxisLabel(y_axis)}
              </span>
            </div>

            {/* Grid */}
            <div className="flex-1">
              <div
                className="grid gap-1"
                style={{
                  gridTemplateColumns: `repeat(${xLabels.length}, minmax(60px, 1fr))`,
                }}
              >
                {yLabels.map((yBin) =>
                  xLabels.map((xBin) => {
                    const cell = cellMap.get(`${xBin}-${yBin}`);
                    const value = cell?.value ?? 0;
                    const count = cell?.count ?? 0;

                    return (
                      <div
                        key={`${xBin}-${yBin}`}
                        className={`
                          aspect-square rounded-lg flex flex-col items-center justify-center
                          transition-all hover:scale-105 cursor-default
                          ${getHeatColor(value)}
                        `}
                        title={`${formatAxisLabel(x_axis)}: ${xBin}, ${formatAxisLabel(y_axis)}: ${yBin}\n${metric}: ${(value * 100).toFixed(1)}%\nSynths: ${count}`}
                      >
                        <span className="text-lg font-bold">
                          {(value * 100).toFixed(0)}%
                        </span>
                        <span className="text-xs opacity-70">n={count}</span>
                      </div>
                    );
                  })
                )}
              </div>

              {/* X-axis label */}
              <div className="text-center mt-2">
                <span className="text-xs text-slate-500 font-medium">
                  {formatAxisLabel(x_axis)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-2 text-xs text-slate-600">
        <span>Baixo</span>
        <div className="flex gap-0.5">
          <div className="w-6 h-4 bg-green-100 rounded-sm" />
          <div className="w-6 h-4 bg-green-200 rounded-sm" />
          <div className="w-6 h-4 bg-yellow-100 rounded-sm" />
          <div className="w-6 h-4 bg-amber-200 rounded-sm" />
          <div className="w-6 h-4 bg-orange-200 rounded-sm" />
          <div className="w-6 h-4 bg-red-200 rounded-sm" />
          <div className="w-6 h-4 bg-red-400 rounded-sm" />
        </div>
        <span>Alto</span>
      </div>

      {/* Summary */}
      <p className="text-center text-sm text-slate-500">
        Métrica: Taxa de {metric === 'failed_rate' ? 'Falha' : metric}
      </p>
    </div>
  );
}
