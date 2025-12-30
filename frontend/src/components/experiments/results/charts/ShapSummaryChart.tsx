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
} from 'recharts';
import type { ShapSummary } from '@/types/simulation';
import { formatFeatureName } from '@/lib/observable-labels';

interface ShapSummaryChartProps {
  data: ShapSummary;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: {
      feature: string;
      displayName: string;
      importance: number;
    };
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null;

  const d = payload[0].payload;

  return (
    <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-3 text-sm">
      <p className="font-medium text-slate-800 mb-1">{d.displayName}</p>
      <div className="text-slate-600">
        <p>Importância SHAP: <span className="font-medium text-indigo-600">{d.importance.toFixed(4)}</span></p>
      </div>
    </div>
  );
}

export function ShapSummaryChart({ data }: ShapSummaryChartProps) {
  // Convert feature_importances dict to array for charting
  const chartData = Object.entries(data.feature_importances || {}).map(([feature, importance]) => ({
    feature,
    displayName: formatFeatureName(feature),
    importance,
  }));

  // Sort by importance descending
  chartData.sort((a, b) => b.importance - a.importance);

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500">
        Sem dados de importância de features
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Model quality indicator */}
      <div className="flex items-center justify-between px-2">
        <span className="text-xs text-slate-500">
          Qualidade do modelo: R² = {(data.model_score * 100).toFixed(1)}%
        </span>
        <span className="text-xs text-slate-500">
          {data.total_synths} synths analisados
        </span>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={Math.max(250, chartData.length * 40)}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 10, right: 30, left: 160, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
          <XAxis
            type="number"
            stroke="#64748b"
            fontSize={11}
            tickFormatter={(v) => v.toFixed(3)}
          />
          <YAxis
            type="category"
            dataKey="displayName"
            stroke="#64748b"
            fontSize={11}
            width={150}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar
            dataKey="importance"
            fill="#6366f1"
            radius={[0, 4, 4, 0]}
            maxBarSize={28}
          />
        </BarChart>
      </ResponsiveContainer>

      {/* Top features summary */}
      {data.top_features && data.top_features.length > 0 && (
        <div className="text-center p-3 bg-indigo-50 rounded-lg border border-indigo-100">
          <span className="text-sm text-indigo-700">
            Features mais influentes:{' '}
            <span className="font-medium">
              {data.top_features.slice(0, 5).map(formatFeatureName).join(', ')}
            </span>
          </span>
        </div>
      )}
    </div>
  );
}
