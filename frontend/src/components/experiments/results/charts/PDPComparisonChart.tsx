// frontend/src/components/experiments/results/charts/PDPComparisonChart.tsx
// Multi-line chart comparing PDP curves across features

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import type { PDPComparison } from '@/types/simulation';
import { formatFeatureName } from '@/lib/observable-labels';

interface PDPComparisonChartProps {
  data: PDPComparison;
}

const FEATURE_COLORS = [
  '#6366f1', // indigo
  '#22c55e', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // violet
  '#06b6d4', // cyan
];

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    dataKey: string;
    value: number;
    color: string;
  }>;
  label?: number;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-3 text-sm">
      <p className="font-medium text-slate-800 mb-2">Valor normalizado: {label?.toFixed(2)}</p>
      <div className="space-y-1">
        {payload.map((entry) => (
          <div key={entry.dataKey} className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-slate-600">{formatFeatureName(entry.dataKey)}:</span>
            <span className="font-medium text-slate-800">{(entry.value * 100).toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function PDPComparisonChart({ data }: PDPComparisonChartProps) {
  const { pdps, feature_ranking } = data;

  // Normalize x-axis to 0-1 range for comparison
  // Each PDP has different feature_range, so we normalize to percentiles
  const normalizedData: Array<Record<string, number>> = [];

  // Use the first PDP's number of points as reference
  const numPoints = pdps[0]?.points.length || 20;

  for (let i = 0; i < numPoints; i++) {
    const point: Record<string, number> = { x: i / (numPoints - 1) };
    pdps.forEach((pdp) => {
      if (pdp.points[i]) {
        point[pdp.feature] = pdp.points[i].avg_prediction;
      }
    });
    normalizedData.push(point);
  }

  return (
    <div className="space-y-4">
      {/* Feature ranking */}
      {feature_ranking && feature_ranking.length > 0 && (
        <div className="flex items-center justify-center gap-2 flex-wrap">
          <span className="text-sm text-slate-500">Ranking:</span>
          {feature_ranking.map((feature, index) => (
            <span
              key={feature}
              className="text-xs px-2 py-1 rounded-full"
              style={{
                backgroundColor: `${FEATURE_COLORS[index % FEATURE_COLORS.length]}20`,
                color: FEATURE_COLORS[index % FEATURE_COLORS.length],
              }}
            >
              {index + 1}. {formatFeatureName(feature)}
            </span>
          ))}
        </div>
      )}

      {/* Chart */}
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={normalizedData} margin={{ top: 20, right: 30, bottom: 40, left: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="x"
            stroke="#64748b"
            fontSize={12}
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
            label={{
              value: 'Valor da Feature (normalizado)',
              position: 'insideBottom',
              offset: -10,
              style: { fontSize: 12, fill: '#64748b' },
            }}
          />
          <YAxis
            stroke="#64748b"
            fontSize={12}
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
            label={{
              value: 'Prob. Sucesso',
              angle: -90,
              position: 'insideLeft',
              style: { fontSize: 12, fill: '#64748b', textAnchor: 'middle' },
            }}
            domain={[0, 1]}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            formatter={(value) => (
              <span className="text-sm text-slate-600">{formatFeatureName(value)}</span>
            )}
          />

          {pdps.map((pdp, index) => (
            <Line
              key={pdp.feature}
              type="monotone"
              dataKey={pdp.feature}
              stroke={FEATURE_COLORS[index % FEATURE_COLORS.length]}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      {/* Effect types summary */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {pdps.map((pdp, index) => (
          <div
            key={pdp.feature}
            className="p-2 rounded-lg border"
            style={{
              borderColor: `${FEATURE_COLORS[index % FEATURE_COLORS.length]}40`,
              backgroundColor: `${FEATURE_COLORS[index % FEATURE_COLORS.length]}10`,
            }}
          >
            <div className="flex items-center gap-2 mb-1">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: FEATURE_COLORS[index % FEATURE_COLORS.length] }}
              />
              <span className="text-xs font-medium text-slate-700">
                {formatFeatureName(pdp.feature)}
              </span>
            </div>
            <div className="text-xs text-slate-500">
              {pdp.effect_type === 'linear' && 'Efeito linear'}
              {pdp.effect_type === 'monotonic' && 'Efeito monotônico'}
              {pdp.effect_type === 'nonlinear' && 'Efeito não linear'}
              {pdp.effect_type === 'threshold' && 'Efeito com threshold'}
              {' · '}
              Força: {(pdp.effect_strength * 100).toFixed(0)}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
