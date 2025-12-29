// frontend/src/components/experiments/results/charts/PDPChart.tsx
// Line chart showing Partial Dependence Plot for a single feature

import {
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

const EFFECT_TYPE_LABELS: Record<string, { label: string; color: string; bg: string }> = {
  monotonic_increasing: { label: 'Crescente', color: 'text-green-600', bg: 'bg-green-100' },
  monotonic_decreasing: { label: 'Decrescente', color: 'text-red-600', bg: 'bg-red-100' },
  non_linear: { label: 'Não Linear', color: 'text-amber-600', bg: 'bg-amber-100' },
  flat: { label: 'Sem Efeito', color: 'text-slate-600', bg: 'bg-slate-100' },
};

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: {
      feature_value: number;
      predicted_success: number;
      confidence_lower?: number;
      confidence_upper?: number;
    };
  }>;
  featureDisplayName: string;
}

function CustomTooltip({ active, payload, featureDisplayName }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null;

  const d = payload[0].payload;
  return (
    <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-3 text-sm">
      <p className="font-medium text-slate-800 mb-1">{featureDisplayName}</p>
      <div className="space-y-1 text-slate-600">
        <p>Valor: <span className="font-medium">{d.feature_value.toFixed(2)}</span></p>
        <p>Predição: <span className="font-medium text-indigo-600">{(d.predicted_success * 100).toFixed(1)}%</span></p>
      </div>
    </div>
  );
}

export function PDPChart({ data }: PDPChartProps) {
  const { feature_name, feature_display_name, pdp_values, effect_type, effect_strength, baseline_value } = data;

  const effectStyle = EFFECT_TYPE_LABELS[effect_type] || EFFECT_TYPE_LABELS.flat;

  // Prepare chart data with confidence band if available
  const chartData = pdp_values.map((p) => ({
    feature_value: p.feature_value,
    predicted_success: p.predicted_success,
    confidence_lower: p.confidence_lower,
    confidence_upper: p.confidence_upper,
  }));

  const hasConfidence = pdp_values.some((p) => p.confidence_lower !== undefined);

  return (
    <div className="space-y-4">
      {/* Effect summary */}
      <div className="flex items-center justify-center gap-4">
        <span className={`text-xs px-2 py-1 rounded-full ${effectStyle.bg} ${effectStyle.color}`}>
          {effectStyle.label}
        </span>
        <span className="text-sm text-slate-600">
          Força do efeito:{' '}
          <span className={`font-bold ${effect_strength > 0.1 ? 'text-indigo-600' : 'text-slate-500'}`}>
            {(effect_strength * 100).toFixed(1)}%
          </span>
        </span>
        <span className="text-xs text-slate-400">
          Baseline: {baseline_value.toFixed(2)}
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
              value: feature_display_name,
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
          <Tooltip content={<CustomTooltip featureDisplayName={feature_display_name} />} />

          {/* Confidence band */}
          {hasConfidence && (
            <Area
              type="monotone"
              dataKey="confidence_upper"
              stroke="none"
              fill="#6366f1"
              fillOpacity={0.1}
            />
          )}
          {hasConfidence && (
            <Area
              type="monotone"
              dataKey="confidence_lower"
              stroke="none"
              fill="#ffffff"
              fillOpacity={1}
            />
          )}

          {/* Main line */}
          <Line
            type="monotone"
            dataKey="predicted_success"
            stroke="#6366f1"
            strokeWidth={3}
            dot={{ r: 4, fill: '#6366f1' }}
            activeDot={{ r: 6, fill: '#4f46e5' }}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Interpretation */}
      <div className="text-center text-xs text-slate-500">
        {effect_type === 'monotonic_increasing' && 'Quanto maior o valor, maior a probabilidade de sucesso'}
        {effect_type === 'monotonic_decreasing' && 'Quanto maior o valor, menor a probabilidade de sucesso'}
        {effect_type === 'non_linear' && 'Relação complexa - o efeito varia dependendo do valor da feature'}
        {effect_type === 'flat' && 'Esta feature tem pouco impacto na probabilidade de sucesso'}
      </div>
    </div>
  );
}
