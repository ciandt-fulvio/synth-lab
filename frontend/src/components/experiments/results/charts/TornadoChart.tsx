// frontend/src/components/experiments/results/charts/TornadoChart.tsx
// Tornado chart showing feature importance (horizontal bar chart)

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';
import type { TornadoChart as TornadoData } from '@/types/simulation';

interface TornadoChartProps {
  data: TornadoData;
}

function formatFeatureName(feature: string): string {
  const labelMap: Record<string, string> = {
    capability_mean: 'Capacidade',
    trust_mean: 'Confiança',
    complexity: 'Complexidade',
    initial_effort: 'Esforço Inicial',
    perceived_risk: 'Risco',
    time_to_value: 'Tempo p/ Valor',
    openness: 'Abertura',
    conscientiousness: 'Conscienciosidade',
    extraversion: 'Extroversão',
    agreeableness: 'Amabilidade',
    neuroticism: 'Neuroticismo',
  };
  return labelMap[feature] || feature.replace(/_/g, ' ');
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: TornadoData['features'][0];
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null;

  const feature = payload[0].payload;
  const isPositive = feature.importance >= 0;

  return (
    <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-3 text-sm">
      <p className="font-medium text-slate-800 mb-1">
        {formatFeatureName(feature.feature)}
      </p>
      <div className="space-y-1 text-slate-600">
        <p>
          Importância:{' '}
          <span className={`font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {isPositive ? '+' : ''}{(feature.importance * 100).toFixed(1)}%
          </span>
        </p>
        <p className="text-xs text-slate-500">
          {isPositive
            ? 'Aumenta a probabilidade de sucesso'
            : 'Diminui a probabilidade de sucesso'}
        </p>
      </div>
    </div>
  );
}

export function TornadoChart({ data }: TornadoChartProps) {
  const { features, baseline } = data;

  // Sort by absolute importance
  const sortedFeatures = [...features].sort(
    (a, b) => Math.abs(b.importance) - Math.abs(a.importance)
  );

  // Format for chart
  const chartData = sortedFeatures.map((f) => ({
    ...f,
    displayName: formatFeatureName(f.feature),
    // Scale importance for display (percentage)
    value: f.importance * 100,
  }));

  // Calculate domain for symmetric axis
  const maxAbs = Math.max(...chartData.map((d) => Math.abs(d.value)));
  const domain = [-Math.ceil(maxAbs), Math.ceil(maxAbs)];

  return (
    <div className="space-y-4">
      {/* Baseline info */}
      <div className="text-center">
        <span className="text-sm text-slate-600">
          Taxa Base de Sucesso:{' '}
          <span className="font-medium text-slate-800">
            {(baseline * 100).toFixed(1)}%
          </span>
        </span>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={Math.max(300, chartData.length * 40)}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 20, right: 40, bottom: 20, left: 120 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
          <XAxis
            type="number"
            domain={domain}
            tickFormatter={(v) => `${v > 0 ? '+' : ''}${v}%`}
            stroke="#64748b"
            fontSize={12}
          />
          <YAxis
            type="category"
            dataKey="displayName"
            width={110}
            stroke="#64748b"
            fontSize={12}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine x={0} stroke="#64748b" strokeWidth={1} />
          <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={30}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.value >= 0 ? '#22c55e' : '#ef4444'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-3 rounded bg-green-500" />
          <span className="text-slate-600">Aumenta Sucesso</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-3 rounded bg-red-500" />
          <span className="text-slate-600">Diminui Sucesso</span>
        </div>
      </div>

      {/* Interpretation */}
      <div className="text-center text-xs text-slate-500">
        Valores mostram o impacto de cada atributo na probabilidade de sucesso
      </div>
    </div>
  );
}
