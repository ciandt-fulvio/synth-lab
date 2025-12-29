// frontend/src/components/experiments/results/charts/PCAScatterChart.tsx
// PCA 2D scatter plot with cluster colors

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
  ResponsiveContainer,
} from 'recharts';
import type { PCAScatterChart as ChartData } from '@/types/simulation';

interface PCAScatterChartProps {
  data: ChartData;
}

export function PCAScatterChart({ data }: PCAScatterChartProps) {
  const { points, explained_variance, total_variance } = data;

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.[0]) return null;
    const point = payload[0].payload;
    return (
      <div className="bg-white p-3 rounded-lg shadow-lg border border-slate-200">
        <p className="text-xs font-mono text-slate-600 mb-2">
          {point.synth_id.substring(0, 12)}...
        </p>
        <div className="space-y-1 text-xs">
          <p>
            <strong>Cluster:</strong> {point.cluster_label}
          </p>
          <p>
            <strong>PC1:</strong> {point.x.toFixed(3)}
          </p>
          <p>
            <strong>PC2:</strong> {point.y.toFixed(3)}
          </p>
        </div>
      </div>
    );
  };

  // Extract unique clusters for legend
  const clusters = Array.from(
    new Map(
      points.map((p) => [p.cluster_id, { label: p.cluster_label, color: p.color }])
    ).values()
  );

  return (
    <div className="space-y-4">
      {/* Variance info */}
      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3">
        <p className="text-sm text-indigo-800">
          <strong>Variância Explicada:</strong> PC1 = {(explained_variance[0] * 100).toFixed(1)}%,
          PC2 = {(explained_variance[1] * 100).toFixed(1)}% (Total:{' '}
          {(total_variance * 100).toFixed(1)}%)
        </p>
        <p className="text-xs text-indigo-600 mt-1">
          PCA reduz todos os atributos para 2 dimensões, preservando{' '}
          {(total_variance * 100).toFixed(0)}% da variação.
        </p>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={450}>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            type="number"
            dataKey="x"
            name="PC1"
            stroke="#64748b"
            tick={{ fontSize: 12 }}
            label={{
              value: 'Componente Principal 1',
              position: 'bottom',
              fontSize: 12,
            }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name="PC2"
            stroke="#64748b"
            tick={{ fontSize: 12 }}
            label={{
              value: 'Componente Principal 2',
              angle: -90,
              position: 'left',
              fontSize: 12,
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="top"
            height={36}
            content={() => (
              <div className="flex items-center justify-center gap-4 mb-2">
                {clusters.map((cluster) => (
                  <div key={cluster.label} className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: cluster.color }}
                    />
                    <span className="text-xs text-slate-600">{cluster.label}</span>
                  </div>
                ))}
              </div>
            )}
          />
          <Scatter name="Synths" data={points}>
            {points.map((point) => (
              <Cell key={point.synth_id} fill={point.color} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
