// frontend/src/components/experiments/results/charts/ShapSummaryChart.tsx
// Bar chart showing global feature importance from SHAP

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { ShapSummary } from '@/types/simulation';

interface ShapSummaryChartProps {
  data: ShapSummary;
}

const DIRECTION_COLORS = {
  positive: '#22c55e', // green-500
  negative: '#ef4444', // red-500
  mixed: '#f59e0b', // amber-500
};

function formatFeatureName(feature: string): string {
  const labelMap: Record<string, string> = {
    capability_mean: 'Capacidade',
    trust_mean: 'Confiança',
    complexity: 'Complexidade',
    initial_effort: 'Esforço Inicial',
    perceived_risk: 'Risco',
    time_to_value: 'Tempo p/ Valor',
    openness: 'Abertura',
    conscientiousness: 'Consciência',
    extraversion: 'Extroversão',
    agreeableness: 'Amabilidade',
    neuroticism: 'Neuroticismo',
  };
  return labelMap[feature] || feature.replace(/_/g, ' ');
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: {
      feature: string;
      importance: number;
      direction: string;
    };
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null;

  const d = payload[0].payload;
  const directionText = {
    positive: 'Aumenta sucesso',
    negative: 'Diminui sucesso',
    mixed: 'Efeito misto',
  }[d.direction as keyof typeof DIRECTION_COLORS] || 'Desconhecido';

  return (
    <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-3 text-sm">
      <p className="font-medium text-slate-800 mb-1">{formatFeatureName(d.feature)}</p>
      <div className="space-y-1 text-slate-600">
        <p>Importância: <span className="font-medium">{d.importance.toFixed(3)}</span></p>
        <p>Direção: <span className="font-medium">{directionText}</span></p>
      </div>
    </div>
  );
}

export function ShapSummaryChart({ data }: ShapSummaryChartProps) {
  const chartData = data.feature_importance.map((fi) => ({
    feature: fi.feature,
    displayName: formatFeatureName(fi.feature),
    importance: fi.mean_abs_shap,
    direction: fi.direction,
  }));

  // Sort by importance descending
  chartData.sort((a, b) => b.importance - a.importance);

  return (
    <div className="space-y-4">
      {/* Chart */}
      <ResponsiveContainer width="100%" height={Math.max(300, chartData.length * 35)}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 10, right: 30, left: 100, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
          <XAxis
            type="number"
            stroke="#64748b"
            fontSize={12}
            tickFormatter={(v) => v.toFixed(2)}
          />
          <YAxis
            type="category"
            dataKey="displayName"
            stroke="#64748b"
            fontSize={12}
            width={90}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="importance" radius={[0, 4, 4, 0]} maxBarSize={25}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={DIRECTION_COLORS[entry.direction as keyof typeof DIRECTION_COLORS] || DIRECTION_COLORS.mixed}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-3 rounded" style={{ backgroundColor: DIRECTION_COLORS.positive }} />
          <span className="text-slate-600">Aumenta Sucesso</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-3 rounded" style={{ backgroundColor: DIRECTION_COLORS.negative }} />
          <span className="text-slate-600">Diminui Sucesso</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-3 rounded" style={{ backgroundColor: DIRECTION_COLORS.mixed }} />
          <span className="text-slate-600">Efeito Misto</span>
        </div>
      </div>

      {/* Top features summary */}
      {data.top_features && data.top_features.length > 0 && (
        <div className="text-center p-3 bg-slate-50 rounded-lg">
          <span className="text-sm text-slate-600">
            Features mais importantes:{' '}
            <span className="font-medium text-slate-800">
              {data.top_features.map(formatFeatureName).join(', ')}
            </span>
          </span>
        </div>
      )}
    </div>
  );
}
