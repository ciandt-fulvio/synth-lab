// frontend/src/components/experiments/results/charts/ScatterCorrelationChart.tsx
// Scatter plot showing correlation between two variables with optional trendline

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import type { ScatterCorrelationChart as ScatterData } from '@/types/simulation';

interface ScatterCorrelationChartProps {
  data: ScatterData;
}

// Outcome colors
const OUTCOME_COLORS = {
  success: '#22c55e',
  failed: '#ef4444',
  did_not_try: '#94a3b8',
} as const;

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
    payload: ScatterData['points'][0];
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null;

  const point = payload[0].payload;
  const outcomeColor = OUTCOME_COLORS[point.outcome as keyof typeof OUTCOME_COLORS] || '#64748b';

  return (
    <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-3 text-sm">
      <div className="flex items-center gap-2 mb-2">
        <div
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: outcomeColor }}
        />
        <span className="font-medium text-slate-800 capitalize">
          {point.outcome === 'did_not_try' ? 'Não Tentou' : point.outcome === 'success' ? 'Sucesso' : 'Falhou'}
        </span>
      </div>
      <div className="space-y-1 text-slate-600">
        <p>X: <span className="font-medium">{point.x.toFixed(3)}</span></p>
        <p>Y: <span className="font-medium">{point.y.toFixed(3)}</span></p>
      </div>
    </div>
  );
}

export function ScatterCorrelationChart({ data }: ScatterCorrelationChartProps) {
  const { points, x_axis, y_axis, trendline, correlation } = data;

  // Group points by outcome for different colors
  const successPoints = points.filter((p) => p.outcome === 'success');
  const failedPoints = points.filter((p) => p.outcome === 'failed');
  const didNotTryPoints = points.filter((p) => p.outcome === 'did_not_try');

  // Calculate trendline endpoints if available
  const trendlinePoints = trendline
    ? [
        { x: Math.min(...points.map((p) => p.x)), y: trendline.intercept + trendline.slope * Math.min(...points.map((p) => p.x)) },
        { x: Math.max(...points.map((p) => p.x)), y: trendline.intercept + trendline.slope * Math.max(...points.map((p) => p.x)) },
      ]
    : [];

  return (
    <div className="space-y-4">
      {/* Correlation indicator */}
      {correlation !== undefined && (
        <div className="flex items-center justify-center gap-2">
          <span className="text-sm text-slate-600">Correlação:</span>
          <span
            className={`text-lg font-bold ${
              Math.abs(correlation) > 0.7
                ? 'text-green-600'
                : Math.abs(correlation) > 0.4
                ? 'text-amber-600'
                : 'text-slate-500'
            }`}
          >
            r = {correlation.toFixed(3)}
          </span>
          <span className="text-xs text-slate-400">
            ({Math.abs(correlation) > 0.7 ? 'forte' : Math.abs(correlation) > 0.4 ? 'moderada' : 'fraca'})
          </span>
        </div>
      )}

      {/* Chart */}
      <ResponsiveContainer width="100%" height={350}>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 40, left: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            type="number"
            dataKey="x"
            name={formatAxisLabel(x_axis)}
            stroke="#64748b"
            fontSize={12}
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
            label={{
              value: formatAxisLabel(y_axis),
              angle: -90,
              position: 'insideLeft',
              style: { fontSize: 12, fill: '#64748b', textAnchor: 'middle' },
            }}
          />
          <Tooltip content={<CustomTooltip />} />

          {/* Trendline */}
          {trendline && trendlinePoints.length === 2 && (
            <ReferenceLine
              segment={[
                { x: trendlinePoints[0].x, y: trendlinePoints[0].y },
                { x: trendlinePoints[1].x, y: trendlinePoints[1].y },
              ]}
              stroke="#6366f1"
              strokeWidth={2}
              strokeDasharray="5 5"
            />
          )}

          {/* Success points */}
          <Scatter
            name="Sucesso"
            data={successPoints}
            fill={OUTCOME_COLORS.success}
            opacity={0.7}
          />

          {/* Failed points */}
          <Scatter
            name="Falhou"
            data={failedPoints}
            fill={OUTCOME_COLORS.failed}
            opacity={0.7}
          />

          {/* Did not try points */}
          <Scatter
            name="Não Tentou"
            data={didNotTryPoints}
            fill={OUTCOME_COLORS.did_not_try}
            opacity={0.7}
          />
        </ScatterChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: OUTCOME_COLORS.success }} />
          <span className="text-slate-600">Sucesso</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: OUTCOME_COLORS.failed }} />
          <span className="text-slate-600">Falhou</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: OUTCOME_COLORS.did_not_try }} />
          <span className="text-slate-600">Não Tentou</span>
        </div>
        {trendline && (
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-indigo-500" style={{ borderStyle: 'dashed' }} />
            <span className="text-slate-600">Tendência</span>
          </div>
        )}
      </div>
    </div>
  );
}
