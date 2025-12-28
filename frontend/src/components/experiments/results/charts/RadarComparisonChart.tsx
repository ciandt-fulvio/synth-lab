// frontend/src/components/experiments/results/charts/RadarComparisonChart.tsx
// Radar chart comparing cluster profiles

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';
import type { RadarChart as RadarData } from '@/types/simulation';

interface RadarComparisonChartProps {
  data: RadarData;
}

// Generate distinct colors for clusters
const CLUSTER_COLORS = [
  '#6366f1', // indigo
  '#22c55e', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // violet
  '#06b6d4', // cyan
  '#ec4899', // pink
  '#84cc16', // lime
];

function formatAxisLabel(label: string): string {
  const labelMap: Record<string, string> = {
    capability_mean: 'Capacidade',
    trust_mean: 'Confiança',
    complexity: 'Complexidade',
    initial_effort: 'Esforço',
    perceived_risk: 'Risco',
    time_to_value: 'Tempo/Valor',
    openness: 'Abertura',
    conscientiousness: 'Consciência',
    extraversion: 'Extroversão',
    agreeableness: 'Amabilidade',
    neuroticism: 'Neuroticismo',
  };
  return labelMap[label] || label.replace(/_/g, ' ');
}

export function RadarComparisonChart({ data }: RadarComparisonChartProps) {
  const { axes, series } = data;

  // Transform data for Recharts radar format
  const chartData = axes.map((axis) => {
    const point: Record<string, unknown> = { axis: formatAxisLabel(axis) };
    series.forEach((s) => {
      const valueIndex = axes.indexOf(axis);
      point[s.name] = s.values[valueIndex];
    });
    return point;
  });

  return (
    <div className="space-y-4">
      {/* Chart */}
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={chartData}>
          <PolarGrid stroke="#e2e8f0" />
          <PolarAngleAxis
            dataKey="axis"
            tick={{ fontSize: 11, fill: '#64748b' }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 1]}
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            tickFormatter={(v) => v.toFixed(1)}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
            }}
            formatter={(value: number) => value.toFixed(3)}
          />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            formatter={(value) => (
              <span className="text-sm text-slate-600">{value}</span>
            )}
          />

          {series.map((s, index) => (
            <Radar
              key={s.name}
              name={s.name}
              dataKey={s.name}
              stroke={CLUSTER_COLORS[index % CLUSTER_COLORS.length]}
              fill={CLUSTER_COLORS[index % CLUSTER_COLORS.length]}
              fillOpacity={0.2}
              strokeWidth={2}
            />
          ))}
        </RadarChart>
      </ResponsiveContainer>

      {/* Cluster summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {series.map((s, index) => (
          <div
            key={s.name}
            className="p-3 bg-slate-50 rounded-lg text-center"
          >
            <div
              className="w-4 h-4 rounded-full mx-auto mb-2"
              style={{ backgroundColor: CLUSTER_COLORS[index % CLUSTER_COLORS.length] }}
            />
            <p className="text-sm font-medium text-slate-800">{s.name}</p>
            <p className="text-xs text-slate-500">
              {s.count} synths ({((s.count / data.total_synths) * 100).toFixed(0)}%)
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
