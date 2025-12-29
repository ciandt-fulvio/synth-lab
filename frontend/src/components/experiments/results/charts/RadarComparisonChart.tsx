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

function formatAxisLabel(label: string): string {
  const labelMap: Record<string, string> = {
    'Capability Mean': 'Capacidade',
    'Trust Mean': 'Confiança',
    'Friction Tolerance Mean': 'Tolerância',
    capability_mean: 'Capacidade',
    trust_mean: 'Confiança',
    friction_tolerance_mean: 'Tolerância',
    complexity: 'Complexidade',
    initial_effort: 'Esforço',
    perceived_risk: 'Risco',
    time_to_value: 'Tempo/Valor',
  };
  return labelMap[label] || label.replace(/_/g, ' ');
}

export function RadarComparisonChart({ data }: RadarComparisonChartProps) {
  const { clusters, axis_labels } = data;

  // Transform data for Recharts radar format
  // Each point in chartData represents one axis with values from all clusters
  const chartData = axis_labels.map((axisLabel, axisIndex) => {
    const point: Record<string, unknown> = { axis: formatAxisLabel(axisLabel) };
    clusters.forEach((cluster) => {
      // Use normalized value (0-1 scale) for radar chart
      const axisData = cluster.axes[axisIndex];
      point[cluster.label] = axisData?.normalized ?? 0;
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
            formatter={(value: number) => value.toFixed(2)}
          />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            formatter={(value) => (
              <span className="text-sm text-slate-600">{value}</span>
            )}
          />

          {clusters.map((cluster) => (
            <Radar
              key={cluster.cluster_id}
              name={cluster.label}
              dataKey={cluster.label}
              stroke={cluster.color}
              fill={cluster.color}
              fillOpacity={0.2}
              strokeWidth={2}
            />
          ))}
        </RadarChart>
      </ResponsiveContainer>

      {/* Cluster summary */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {clusters.map((cluster) => (
          <div
            key={cluster.cluster_id}
            className="p-3 bg-slate-50 rounded-lg text-center"
          >
            <div
              className="w-4 h-4 rounded-full mx-auto mb-2"
              style={{ backgroundColor: cluster.color }}
            />
            <p className="text-sm font-medium text-slate-800">{cluster.label}</p>
            <p className="text-xs text-slate-500">
              Taxa de sucesso: {(cluster.success_rate * 100).toFixed(0)}%
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
