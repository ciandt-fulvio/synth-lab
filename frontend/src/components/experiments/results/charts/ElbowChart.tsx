// frontend/src/components/experiments/results/charts/ElbowChart.tsx
// Elbow chart for determining optimal number of clusters

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot,
} from 'recharts';
import type { ElbowDataPoint } from '@/types/simulation';

interface ElbowChartProps {
  data: ElbowDataPoint[];
  suggestedK?: number;
  onSelectK?: (k: number) => void;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: ElbowDataPoint;
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null;

  const point = payload[0].payload;
  return (
    <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-3 text-sm">
      <p className="font-medium text-slate-800 mb-1">K = {point.k}</p>
      <div className="space-y-1 text-slate-600">
        <p>Inércia: <span className="font-medium">{point.inertia.toFixed(2)}</span></p>
        {point.silhouette !== undefined && (
          <p>Silhouette: <span className="font-medium">{point.silhouette.toFixed(3)}</span></p>
        )}
      </div>
    </div>
  );
}

export function ElbowChart({ data, suggestedK, onSelectK }: ElbowChartProps) {
  // Find the suggested point
  const suggestedPoint = suggestedK
    ? data.find((d) => d.k === suggestedK)
    : undefined;

  return (
    <div className="space-y-4">
      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={data}
          margin={{ top: 20, right: 30, bottom: 20, left: 60 }}
          onClick={(e) => {
            if (e && e.activePayload && onSelectK) {
              const k = e.activePayload[0]?.payload?.k;
              if (k) onSelectK(k);
            }
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="k"
            stroke="#64748b"
            fontSize={12}
            label={{
              value: 'Número de Clusters (K)',
              position: 'insideBottom',
              offset: -10,
              style: { fontSize: 12, fill: '#64748b' },
            }}
          />
          <YAxis
            dataKey="inertia"
            stroke="#64748b"
            fontSize={12}
            label={{
              value: 'Inércia',
              angle: -90,
              position: 'insideLeft',
              style: { fontSize: 12, fill: '#64748b', textAnchor: 'middle' },
            }}
          />
          <Tooltip content={<CustomTooltip />} />

          {/* Inertia line */}
          <Line
            type="monotone"
            dataKey="inertia"
            stroke="#6366f1"
            strokeWidth={2}
            dot={{ r: 4, fill: '#6366f1' }}
            activeDot={{ r: 6, fill: '#4f46e5' }}
          />

          {/* Suggested K point */}
          {suggestedPoint && (
            <ReferenceDot
              x={suggestedPoint.k}
              y={suggestedPoint.inertia}
              r={8}
              fill="#22c55e"
              stroke="#16a34a"
              strokeWidth={2}
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      {/* Suggested K indicator */}
      {suggestedK && (
        <div className="flex items-center justify-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="w-4 h-4 rounded-full bg-green-500" />
          <span className="text-sm text-green-800">
            K recomendado: <span className="font-bold">{suggestedK}</span> clusters
          </span>
        </div>
      )}

      {/* Instructions */}
      <p className="text-center text-xs text-slate-500">
        Clique em um ponto para selecionar o número de clusters
      </p>
    </div>
  );
}
