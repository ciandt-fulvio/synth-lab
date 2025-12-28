// frontend/src/components/experiments/results/charts/TryVsSuccessChart.tsx
// Scatter chart showing Try vs Success quadrant analysis

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

// Quadrant colors (matching API quadrant names)
const QUADRANT_COLORS = {
  ok: '#22c55e', // Green - high try, high success
  discovery_issue: '#3b82f6', // Blue - low try, high success (need better discovery)
  usability_issue: '#ef4444', // Red - high try, low success (usability problem)
  low_value: '#f59e0b', // Amber/Gold - low try, low success (low perceived value)
} as const;

function getQuadrantColor(quadrant: string): string {
  return QUADRANT_COLORS[quadrant as keyof typeof QUADRANT_COLORS] || QUADRANT_COLORS.low_value;
}

function getQuadrantLabel(quadrant: string): string {
  const labels: Record<string, string> = {
    ok: 'OK',
    discovery_issue: 'Problema de Descoberta',
    usability_issue: 'Problema de Usabilidade',
    low_value: 'Baixo Valor',
  };
  return labels[quadrant] || quadrant;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: TryVsSuccessData['points'][0];
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null;

  const point = payload[0].payload;
  const quadrantLabel = getQuadrantLabel(point.quadrant);
  const quadrantColor = getQuadrantColor(point.quadrant);

  return (
    <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-3 text-sm">
      <div className="flex items-center gap-2 mb-2">
        <div
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: quadrantColor }}
        />
        <span className="font-medium text-slate-800">{quadrantLabel}</span>
      </div>
      <div className="space-y-1 text-slate-600">
        <p>Synth: <span className="font-medium">{point.synth_id}</span></p>
        <p>Taxa de Tentativa: <span className="font-medium">{(point.attempt_rate * 100).toFixed(1)}%</span></p>
        <p>Taxa de Sucesso: <span className="font-medium">{(point.success_rate * 100).toFixed(1)}%</span></p>
      </div>
    </div>
  );
}

export function TryVsSuccessChart({ data }: TryVsSuccessChartProps) {
  const { points, quadrant_thresholds, quadrant_counts, total_synths } = data;

  return (
    <div className="space-y-4">
      {/* Quadrant Legend */}
      <div className="flex flex-wrap gap-4 justify-center">
        {Object.keys(quadrant_counts).map((quadrant) => (
          <div key={quadrant} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: getQuadrantColor(quadrant) }}
            />
            <span className="text-sm text-slate-600">
              {getQuadrantLabel(quadrant)}
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
            dataKey="attempt_rate"
            name="Taxa de Tentativa"
            domain={[0, 1]}
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
            stroke="#64748b"
            fontSize={12}
            label={{
              value: 'Taxa de Tentativa',
              position: 'insideBottom',
              offset: -10,
              style: { fontSize: 12, fill: '#64748b' },
            }}
          />
          <YAxis
            type="number"
            dataKey="success_rate"
            name="Taxa de Sucesso"
            domain={[0, 1]}
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
            stroke="#64748b"
            fontSize={12}
            label={{
              value: 'Taxa de Sucesso',
              angle: -90,
              position: 'insideLeft',
              style: { fontSize: 12, fill: '#64748b', textAnchor: 'middle' },
            }}
          />
          <Tooltip content={<CustomTooltip />} />

          {/* Reference lines for thresholds */}
          <ReferenceLine
            x={quadrant_thresholds.x}
            stroke="#94a3b8"
            strokeDasharray="5 5"
            label={{
              value: 'Limite Tentativa',
              position: 'top',
              style: { fontSize: 10, fill: '#94a3b8' },
            }}
          />
          <ReferenceLine
            y={quadrant_thresholds.y}
            stroke="#94a3b8"
            strokeDasharray="5 5"
            label={{
              value: 'Limite Sucesso',
              position: 'right',
              style: { fontSize: 10, fill: '#94a3b8' },
            }}
          />

          {/* Scatter points */}
          <Scatter name="Synths" data={points} fill="#8884d8">
            {points.map((point, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getQuadrantColor(point.quadrant)}
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
