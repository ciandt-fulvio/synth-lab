// frontend/src/components/experiments/results/charts/ScatterCorrelationChart.tsx
// Scatter plot showing correlation between two variables with trendline

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Line,
  ComposedChart,
} from 'recharts';
import type { ScatterCorrelationChart as ScatterData, ScatterPoint } from '@/types/simulation';

interface ScatterCorrelationChartProps {
  data: ScatterData;
}

function formatAxisLabel(label: string): string {
  const labelMap: Record<string, string> = {
    capability_mean: 'Capacidade Média',
    trust_mean: 'Confiança Média',
    success_rate: 'Taxa de Sucesso',
    failed_rate: 'Taxa de Falha',
    complexity: 'Complexidade',
    initial_effort: 'Esforço Inicial',
    perceived_risk: 'Risco Percebido',
    time_to_value: 'Tempo p/ Valor',
  };
  return labelMap[label] || label.replace(/_/g, ' ');
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: { x: number; y: number; synth_id: string };
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null;

  const point = payload[0].payload;

  return (
    <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-3 text-sm">
      <div className="font-medium text-slate-800 mb-2">Synth: {point.synth_id}</div>
      <div className="space-y-1 text-slate-600">
        <p>
          X: <span className="font-medium">{point.x.toFixed(3)}</span>
        </p>
        <p>
          Y: <span className="font-medium">{point.y.toFixed(3)}</span>
        </p>
      </div>
    </div>
  );
}

export function ScatterCorrelationChart({ data }: ScatterCorrelationChartProps) {
  const { points, x_axis, y_axis, trendline, correlation } = data;

  // Transform points to use x/y for recharts
  const chartPoints = points.map((p) => ({
    x: p.x_value,
    y: p.y_value,
    synth_id: p.synth_id,
  }));

  // Get correlation value (pearson_r)
  const correlationValue = correlation?.pearson_r ?? 0;
  const isSignificant = correlation?.is_significant ?? false;

  return (
    <div className="space-y-4">
      {/* Correlation indicator */}
      <div className="flex items-center justify-center gap-2">
        <span className="text-sm text-slate-600">Correlação:</span>
        <span
          className={`text-lg font-bold ${
            Math.abs(correlationValue) > 0.7
              ? 'text-green-600'
              : Math.abs(correlationValue) > 0.4
                ? 'text-amber-600'
                : 'text-slate-500'
          }`}
        >
          r = {correlationValue.toFixed(3)}
        </span>
        <span className="text-xs text-slate-400">
          (
          {Math.abs(correlationValue) > 0.7
            ? 'forte'
            : Math.abs(correlationValue) > 0.4
              ? 'moderada'
              : 'fraca'}
          )
        </span>
        {isSignificant && (
          <span className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
            p {'<'} 0.05
          </span>
        )}
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={350}>
        <ComposedChart margin={{ top: 20, right: 20, bottom: 40, left: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            type="number"
            dataKey="x"
            name={formatAxisLabel(x_axis)}
            stroke="#64748b"
            fontSize={12}
            domain={['dataMin', 'dataMax']}
            label={{
              value: formatAxisLabel(x_axis),
              position: 'insideBottom',
              offset: -10,
              style: { fontSize: 12, fill: '#64748b' },
            }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name={formatAxisLabel(y_axis)}
            stroke="#64748b"
            fontSize={12}
            domain={['dataMin', 'dataMax']}
            label={{
              value: formatAxisLabel(y_axis),
              angle: -90,
              position: 'insideLeft',
              style: { fontSize: 12, fill: '#64748b', textAnchor: 'middle' },
            }}
          />
          <Tooltip content={<CustomTooltip />} />

          {/* Trendline */}
          {trendline && trendline.length >= 2 && (
            <Line
              type="linear"
              dataKey="y"
              data={trendline}
              stroke="#6366f1"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              isAnimationActive={false}
            />
          )}

          {/* Scatter points */}
          <Scatter name="Synths" data={chartPoints} fill="#6366f1" opacity={0.6} />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-indigo-500" />
          <span className="text-slate-600">Synths ({points.length})</span>
        </div>
        {trendline && trendline.length > 0 && (
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-indigo-500 border-dashed" />
            <span className="text-slate-600">Tendência</span>
          </div>
        )}
      </div>

      {/* R-squared info */}
      {correlation && (
        <p className="text-center text-xs text-slate-400">
          R² = {correlation.r_squared.toFixed(3)} (a linha de tendência explica{' '}
          {(correlation.r_squared * 100).toFixed(1)}% da variância)
        </p>
      )}
    </div>
  );
}
