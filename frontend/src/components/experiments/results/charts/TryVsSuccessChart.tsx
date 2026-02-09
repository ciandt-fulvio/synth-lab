// frontend/src/components/experiments/results/charts/TryVsSuccessChart.tsx
// Scatter chart showing adoption rate distribution with threshold line

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from 'recharts';
import type { TryVsSuccessChart as TryVsSuccessData } from '@/types/simulation';

interface TryVsSuccessChartProps {
  data: TryVsSuccessData;
}

// Category colors
const CATEGORY_COLORS = {
  above_threshold: '#22c55e', // Green - above adoption threshold
  below_threshold: '#94a3b8', // Slate - below adoption threshold
} as const;

function getCategoryColor(category: string): string {
  return CATEGORY_COLORS[category as keyof typeof CATEGORY_COLORS] || CATEGORY_COLORS.below_threshold;
}

function getCategoryLabel(category: string): string {
  const labels: Record<string, string> = {
    above_threshold: 'Acima do limiar',
    below_threshold: 'Abaixo do limiar',
  };
  return labels[category] || category;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: TryVsSuccessData['points'][0] & { index: number };
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null;

  const point = payload[0].payload;
  const categoryLabel = getCategoryLabel(point.category);
  const categoryColor = getCategoryColor(point.category);

  return (
    <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-3 text-sm">
      <div className="flex items-center gap-2 mb-2">
        <div
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: categoryColor }}
        />
        <span className="font-medium text-slate-800">{categoryLabel}</span>
      </div>
      <div className="space-y-1 text-slate-600">
        <p>Synth: <span className="font-medium">{point.synth_id}</span></p>
        <p>Taxa de Adoção: <span className="font-medium">{(point.adopted_rate * 100).toFixed(1)}%</span></p>
      </div>
    </div>
  );
}

export function TryVsSuccessChart({ data }: TryVsSuccessChartProps) {
  const { points, quadrant_thresholds, quadrant_counts, total_synths } = data;

  // Add index for x-axis positioning (each dot = 1 synth)
  const indexedPoints = points.map((p, i) => ({ ...p, index: i + 1 }));

  return (
    <div className="space-y-4">
      {/* Category Legend */}
      <div className="flex flex-wrap gap-4 justify-center">
        {Object.keys(quadrant_counts).map((category) => (
          <div key={category} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: getCategoryColor(category) }}
            />
            <span className="text-sm text-slate-600">
              {getCategoryLabel(category)} ({quadrant_counts[category as keyof typeof quadrant_counts]})
            </span>
          </div>
        ))}
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={350}>
        <ScatterChart
          margin={{ top: 20, right: 20, bottom: 40, left: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            type="number"
            dataKey="index"
            name="Synth"
            domain={[0, points.length + 1]}
            stroke="#64748b"
            fontSize={12}
            label={{
              value: 'Synth (índice)',
              position: 'insideBottom',
              offset: -10,
              style: { fontSize: 12, fill: '#64748b' },
            }}
          />
          <YAxis
            type="number"
            dataKey="adopted_rate"
            name="Taxa de Adoção"
            domain={[0, 1]}
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
            stroke="#64748b"
            fontSize={12}
            label={{
              value: 'Taxa de Adoção',
              angle: -90,
              position: 'insideLeft',
              style: { fontSize: 12, fill: '#64748b', textAnchor: 'middle' },
            }}
          />
          <Tooltip content={<CustomTooltip />} />

          {/* Reference line for adoption threshold */}
          <ReferenceLine
            y={quadrant_thresholds.y}
            stroke="#94a3b8"
            strokeDasharray="5 5"
            label={{
              value: 'Limiar de Adoção',
              position: 'right',
              style: { fontSize: 10, fill: '#94a3b8' },
            }}
          />

          {/* Scatter points */}
          <Scatter name="Synths" data={indexedPoints} fill="#8884d8">
            {indexedPoints.map((point, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getCategoryColor(point.category)}
                opacity={0.7}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>

      {/* Summary */}
      <div className="text-center text-sm text-slate-500">
        Total de {total_synths} synths analisados
      </div>
    </div>
  );
}
