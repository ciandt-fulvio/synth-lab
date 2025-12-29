// frontend/src/components/experiments/results/charts/PDPChart.tsx
// Line chart showing Partial Dependence Plot for a single feature

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  ComposedChart,
} from 'recharts';
import type { PDPResult } from '@/types/simulation';

interface PDPChartProps {
  data: PDPResult;
}

function formatFeatureName(feature: string): string {
  const labelMap: Record<string, string> = {
    capability_mean: 'Capacidade',
    trust_mean: 'Confiança',
    complexity: 'Complexidade',
    initial_effort: 'Esforço Inicial',
    perceived_risk: 'Risco',
    time_to_value: 'Tempo p/ Valor',
  };
  return labelMap[feature] || feature.replace(/_/g, ' ');
}

const EFFECT_TYPE_LABELS = {
  linear: { label: 'Linear', color: 'text-blue-600', bg: 'bg-blue-100' },
  monotonic: { label: 'Monotônico', color: 'text-green-600', bg: 'bg-green-100' },
  nonlinear: { label: 'Não Linear', color: 'text-amber-600', bg: 'bg-amber-100' },
  threshold: { label: 'Com Threshold', color: 'text-purple-600', bg: 'bg-purple-100' },
};

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: {
      feature_value: number;
      avg_prediction: number;
      std_prediction?: number;
    };
  }>;
  feature: string;
}

function CustomTooltip({ active, payload, feature }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null;

  const d = payload[0].payload;
  return (
    <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-3 text-sm">
      <p className="font-medium text-slate-800 mb-1">{formatFeatureName(feature)}</p>
      <div className="space-y-1 text-slate-600">
        <p>Valor: <span className="font-medium">{d.feature_value.toFixed(2)}</span></p>
        <p>Predição: <span className="font-medium">{(d.avg_prediction * 100).toFixed(1)}%</span></p>
        {d.std_prediction !== undefined && (
          <p>Desvio: <span className="font-medium">±{(d.std_prediction * 100).toFixed(1)}%</span></p>
        )}
      </div>
    </div>
  );
}

export function PDPChart({ data }: PDPChartProps) {
  const { feature, points, effect_type, effect_strength } = data;

  const effectStyle = EFFECT_TYPE_LABELS[effect_type] || EFFECT_TYPE_LABELS.linear;

  // Prepare chart data with confidence band if available
  const chartData = points.map((p) => ({
    ...p,
    upper: p.std_prediction ? p.avg_prediction + p.std_prediction : p.avg_prediction,
    lower: p.std_prediction ? p.avg_prediction - p.std_prediction : p.avg_prediction,
  }));

  const hasStd = points.some((p) => p.std_prediction !== undefined);

  return (
    <div className="space-y-4">
      {/* Effect summary */}
      <div className="flex items-center justify-center gap-4">
        <span className={`text-xs px-2 py-1 rounded-full ${effectStyle.bg} ${effectStyle.color}`}>
          {effectStyle.label}
        </span>
        <span className="text-sm text-slate-600">
          Força do efeito:{' '}
          <span className={`font-bold ${effect_strength > 0.5 ? 'text-green-600' : 'text-slate-500'}`}>
            {(effect_strength * 100).toFixed(0)}%
          </span>
        </span>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={chartData} margin={{ top: 20, right: 30, bottom: 40, left: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="feature_value"
            stroke="#64748b"
            fontSize={12}
            tickFormatter={(v) => v.toFixed(2)}
            label={{
              value: formatFeatureName(feature),
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
          <Tooltip content={<CustomTooltip feature={feature} />} />

          {/* Confidence band */}
          {hasStd && (
            <Area
              type="monotone"
              dataKey="upper"
              stroke="none"
              fill="#6366f1"
              fillOpacity={0.1}
            />
          )}
          {hasStd && (
            <Area
              type="monotone"
              dataKey="lower"
              stroke="none"
              fill="#ffffff"
              fillOpacity={1}
            />
          )}

          {/* Main line */}
          <Line
            type="monotone"
            dataKey="avg_prediction"
            stroke="#6366f1"
            strokeWidth={3}
            dot={{ r: 4, fill: '#6366f1' }}
            activeDot={{ r: 6, fill: '#4f46e5' }}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Interpretation */}
      <div className="text-center text-xs text-slate-500">
        {effect_type === 'linear' && 'Relação aproximadamente linear entre a feature e a probabilidade de sucesso'}
        {effect_type === 'monotonic' && 'Quanto maior o valor, maior (ou menor) a probabilidade de sucesso'}
        {effect_type === 'nonlinear' && 'Relação complexa - o efeito varia dependendo do valor da feature'}
        {effect_type === 'threshold' && 'Existe um ponto de corte onde o comportamento muda significativamente'}
      </div>
    </div>
  );
}
