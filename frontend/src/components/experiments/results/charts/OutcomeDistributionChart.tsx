// frontend/src/components/experiments/results/charts/OutcomeDistributionChart.tsx
// Pie chart showing outcome distribution (success, failed, did not try)

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import type { OutcomeDistributionChart as DistributionData } from '@/types/simulation';

interface OutcomeDistributionChartProps {
  data: DistributionData;
}

// Outcome colors
const OUTCOME_COLORS = {
  success: '#22c55e', // Green
  failed: '#ef4444', // Red
  did_not_try: '#f59e0b', // Amber/Gold - important: not gray!
} as const;

const OUTCOME_LABELS = {
  success: 'Sucesso',
  failed: 'Falhou',
  did_not_try: 'Não Tentou',
} as const;

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: {
      name: string;
      value: number;
      fill: string;
    };
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null;

  const item = payload[0].payload;
  return (
    <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-3 text-sm">
      <div className="flex items-center gap-2">
        <div
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: item.fill }}
        />
        <span className="font-medium text-slate-800">{item.name}</span>
      </div>
      <p className="text-slate-600 mt-1">
        {item.value.toFixed(1)}%
      </p>
    </div>
  );
}

interface CustomLegendProps {
  payload?: Array<{
    value: string;
    color: string;
  }>;
}

function CustomLegend({ payload }: CustomLegendProps) {
  if (!payload) return null;

  return (
    <div className="flex justify-center gap-6 mt-4">
      {payload.map((entry, index) => (
        <div key={`legend-${index}`} className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-sm text-slate-600">{entry.value}</span>
        </div>
      ))}
    </div>
  );
}

export function OutcomeDistributionChart({ data }: OutcomeDistributionChartProps) {
  const { summary, total_synths } = data;

  // Transform data for pie chart using summary averages
  const pieData = [
    {
      name: OUTCOME_LABELS.success,
      value: summary.avg_success * 100,
      fill: OUTCOME_COLORS.success,
    },
    {
      name: OUTCOME_LABELS.failed,
      value: summary.avg_failed * 100,
      fill: OUTCOME_COLORS.failed,
    },
    {
      name: OUTCOME_LABELS.did_not_try,
      value: summary.avg_did_not_try * 100,
      fill: OUTCOME_COLORS.did_not_try,
    },
  ].filter((item) => item.value > 0);

  return (
    <div className="space-y-4">
      {/* Big success number */}
      <div className="text-center">
        <span className="text-5xl font-bold text-green-600">
          {(summary.avg_success * 100).toFixed(0)}%
        </span>
        <p className="text-sm text-slate-500 mt-1">Taxa de Sucesso Média</p>
      </div>

      {/* Pie chart */}
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={pieData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={2}
            dataKey="value"
            animationBegin={0}
            animationDuration={800}
          >
            {pieData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend content={<CustomLegend />} />
        </PieChart>
      </ResponsiveContainer>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4 text-center">
        <div className="p-3 bg-green-50 rounded-lg">
          <p className="text-2xl font-bold text-green-600">
            {(summary.avg_success * 100).toFixed(1)}%
          </p>
          <p className="text-xs text-green-700">Sucesso</p>
        </div>
        <div className="p-3 bg-red-50 rounded-lg">
          <p className="text-2xl font-bold text-red-600">
            {(summary.avg_failed * 100).toFixed(1)}%
          </p>
          <p className="text-xs text-red-700">Falharam</p>
        </div>
        <div className="p-3 bg-amber-50 rounded-lg">
          <p className="text-2xl font-bold text-amber-600">
            {(summary.avg_did_not_try * 100).toFixed(1)}%
          </p>
          <p className="text-xs text-amber-700">Não Tentaram</p>
        </div>
      </div>

      {/* Total */}
      <p className="text-center text-sm text-slate-500">
        Total de {total_synths} synths analisados
      </p>
    </div>
  );
}
