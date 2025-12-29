// frontend/src/components/experiments/results/charts/ShapWaterfallChart.tsx
// Waterfall chart showing SHAP contributions for a single synth

import type { ShapExplanation } from '@/types/simulation';

interface ShapWaterfallChartProps {
  data: ShapExplanation;
}

function formatFeatureName(feature: string): string {
  const labelMap: Record<string, string> = {
    capability_mean: 'Capacidade',
    trust_mean: 'Confiança',
    friction_tolerance_mean: 'Tolerância',
    exploration_prob: 'Exploração',
    digital_literacy: 'Lit. Digital',
    similar_tool_experience: 'Exp. Similar',
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

export function ShapWaterfallChart({ data }: ShapWaterfallChartProps) {
  const { baseline_prediction, predicted_success_rate, contributions } = data;

  // Sort contributions by absolute SHAP value
  const sortedContributions = [...contributions].sort(
    (a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value)
  );

  // Calculate cumulative values for waterfall
  let cumulative = baseline_prediction;
  const waterfallData = sortedContributions.map((c) => {
    const start = cumulative;
    cumulative += c.shap_value;
    return {
      ...c,
      start,
      end: cumulative,
      isPositive: c.shap_value >= 0,
    };
  });

  // Find max extent for scaling
  const allValues = [baseline_prediction, predicted_success_rate, ...waterfallData.flatMap((w) => [w.start, w.end])];
  const minVal = Math.min(...allValues);
  const maxVal = Math.max(...allValues);
  const range = maxVal - minVal || 1;

  // SVG dimensions
  const width = 600;
  const height = Math.max(250, waterfallData.length * 35 + 100);
  const margin = { top: 40, right: 80, bottom: 40, left: 120 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const barHeight = Math.min(25, (plotHeight - 60) / (waterfallData.length + 2));

  // Scale function
  const scaleX = (val: number) => margin.left + ((val - minVal) / range) * plotWidth;

  return (
    <div className="space-y-4">
      {/* SVG Waterfall */}
      <div className="flex justify-center overflow-x-auto">
        <svg width={width} height={height} className="bg-slate-50 rounded-lg">
          {/* Base value row */}
          <g transform={`translate(0, ${margin.top})`}>
            <text
              x={margin.left - 10}
              y={barHeight / 2}
              textAnchor="end"
              dominantBaseline="middle"
              fontSize={11}
              fill="#64748b"
            >
              Base
            </text>
            <circle
              cx={scaleX(baseline_prediction)}
              cy={barHeight / 2}
              r={6}
              fill="#6366f1"
            />
            <text
              x={scaleX(baseline_prediction) + 12}
              y={barHeight / 2}
              dominantBaseline="middle"
              fontSize={11}
              fill="#64748b"
            >
              {baseline_prediction.toFixed(3)}
            </text>
          </g>

          {/* Contribution bars */}
          {waterfallData.map((item, index) => {
            const y = margin.top + (index + 1) * (barHeight + 5);
            const x1 = scaleX(item.start);
            const x2 = scaleX(item.end);
            const barX = Math.min(x1, x2);
            const barWidth = Math.abs(x2 - x1);

            return (
              <g key={item.feature_name} transform={`translate(0, ${y})`}>
                {/* Feature label */}
                <text
                  x={margin.left - 10}
                  y={barHeight / 2}
                  textAnchor="end"
                  dominantBaseline="middle"
                  fontSize={11}
                  fill="#334155"
                >
                  {formatFeatureName(item.feature_name)}
                </text>

                {/* Connector line from previous */}
                <line
                  x1={x1}
                  y1={-5}
                  x2={x1}
                  y2={barHeight / 2}
                  stroke="#94a3b8"
                  strokeDasharray="2 2"
                />

                {/* Bar */}
                <rect
                  x={barX}
                  y={0}
                  width={Math.max(barWidth, 2)}
                  height={barHeight}
                  fill={item.isPositive ? '#22c55e' : '#ef4444'}
                  rx={3}
                  opacity={0.8}
                />

                {/* Value label */}
                <text
                  x={x2 + (item.isPositive ? 8 : -8)}
                  y={barHeight / 2}
                  textAnchor={item.isPositive ? 'start' : 'end'}
                  dominantBaseline="middle"
                  fontSize={10}
                  fill={item.isPositive ? '#16a34a' : '#dc2626'}
                  fontWeight="500"
                >
                  {item.isPositive ? '+' : ''}{item.shap_value.toFixed(3)}
                </text>

                {/* Feature value */}
                <text
                  x={width - margin.right + 10}
                  y={barHeight / 2}
                  dominantBaseline="middle"
                  fontSize={10}
                  fill="#94a3b8"
                >
                  ({item.feature_value.toFixed(2)})
                </text>
              </g>
            );
          })}

          {/* Final prediction row */}
          <g transform={`translate(0, ${margin.top + (waterfallData.length + 1) * (barHeight + 5) + 10})`}>
            <text
              x={margin.left - 10}
              y={barHeight / 2}
              textAnchor="end"
              dominantBaseline="middle"
              fontSize={11}
              fontWeight="600"
              fill="#334155"
            >
              Predição
            </text>
            <circle
              cx={scaleX(predicted_success_rate)}
              cy={barHeight / 2}
              r={8}
              fill={predicted_success_rate >= 0.5 ? '#22c55e' : '#ef4444'}
            />
            <text
              x={scaleX(predicted_success_rate) + 14}
              y={barHeight / 2}
              dominantBaseline="middle"
              fontSize={12}
              fontWeight="600"
              fill={predicted_success_rate >= 0.5 ? '#16a34a' : '#dc2626'}
            >
              {(predicted_success_rate * 100).toFixed(1)}%
            </text>
          </g>
        </svg>
      </div>

      {/* Summary */}
      <div className="flex items-center justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-3 rounded bg-green-500" />
          <span className="text-slate-600">Aumenta probabilidade</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-3 rounded bg-red-500" />
          <span className="text-slate-600">Diminui probabilidade</span>
        </div>
      </div>

      {/* Explanation text */}
      {data.explanation_text && (
        <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
          <p className="text-sm text-indigo-800">{data.explanation_text}</p>
        </div>
      )}
    </div>
  );
}
