// frontend/src/components/experiments/results/charts/ShapWaterfallChart.tsx
// Vertical waterfall chart showing SHAP contributions for a single synth

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ResponsiveContainer,
  ReferenceLine,
  Label,
} from 'recharts';
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

interface WaterfallDataPoint {
  name: string;
  value: number;
  base: number;
  contribution: number;
  isBase?: boolean;
  isPrediction?: boolean;
  isPositive?: boolean;
  displayValue: string;
}

export function ShapWaterfallChart({ data }: ShapWaterfallChartProps) {
  const { baseline_prediction, predicted_success_rate, contributions } = data;

  // Sort contributions by absolute SHAP value (descending)
  const sortedContributions = [...contributions].sort(
    (a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value)
  );

  // Build waterfall data with cumulative values
  const waterfallData: WaterfallDataPoint[] = [];

  // Base value
  waterfallData.push({
    name: 'Base',
    value: baseline_prediction,
    base: 0,
    contribution: baseline_prediction,
    isBase: true,
    isPositive: true,
    displayValue: baseline_prediction.toFixed(3),
  });

  // Contributions
  let cumulative = baseline_prediction;
  sortedContributions.forEach((item) => {
    const contributionValue = item.shap_value;
    const isPositive = contributionValue >= 0;

    waterfallData.push({
      name: formatFeatureName(item.feature_name),
      value: cumulative + contributionValue,
      base: isPositive ? cumulative : cumulative + contributionValue,
      contribution: Math.abs(contributionValue),
      isPositive,
      displayValue: `${isPositive ? '+' : ''}${contributionValue.toFixed(3)}`,
    });

    cumulative += contributionValue;
  });

  // Final prediction
  waterfallData.push({
    name: 'Predição',
    value: predicted_success_rate,
    base: 0,
    contribution: predicted_success_rate,
    isPrediction: true,
    isPositive: predicted_success_rate >= 0.5,
    displayValue: `${(predicted_success_rate * 100).toFixed(1)}%`,
  });

  // Custom label component
  const CustomLabel = (props: any) => {
    const { x, y, width, value, index } = props;
    const dataPoint = waterfallData[index];

    if (!dataPoint) return null;

    // Position label above bar
    const labelY = y - 8;
    const labelX = x + width / 2;

    return (
      <text
        x={labelX}
        y={labelY}
        fill={dataPoint.isPositive ? '#16a34a' : '#dc2626'}
        fontSize={11}
        fontWeight={dataPoint.isBase || dataPoint.isPrediction ? '700' : '600'}
        textAnchor="middle"
        dominantBaseline="bottom"
      >
        {dataPoint.displayValue}
      </text>
    );
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload[0]) return null;

    const dataPoint = payload[0].payload as WaterfallDataPoint;

    return (
      <div className="bg-white border border-slate-200 shadow-lg rounded-lg p-3">
        <p className="text-sm font-semibold text-slate-800 mb-1">{dataPoint.name}</p>
        {!dataPoint.isBase && !dataPoint.isPrediction && (
          <p className="text-xs text-slate-600">
            Contribuição: <span className={dataPoint.isPositive ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
              {dataPoint.displayValue}
            </span>
          </p>
        )}
        <p className="text-xs text-slate-600">
          Valor acumulado: <span className="font-medium text-slate-800">{dataPoint.value.toFixed(3)}</span>
        </p>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Vertical Waterfall Chart */}
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={waterfallData}
          margin={{ top: 30, right: 20, bottom: 60, left: 40 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />

          <XAxis
            dataKey="name"
            angle={-45}
            textAnchor="end"
            height={80}
            tick={{ fill: '#475569', fontSize: 11, fontWeight: 500 }}
            axisLine={{ stroke: '#cbd5e1' }}
          />

          <YAxis
            domain={[0, 'auto']}
            tick={{ fill: '#64748b', fontSize: 11 }}
            axisLine={{ stroke: '#cbd5e1' }}
            label={{
              value: 'Probabilidade',
              angle: -90,
              position: 'insideLeft',
              style: { fill: '#475569', fontSize: 12, fontWeight: 600 }
            }}
          />

          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(148, 163, 184, 0.1)' }} />

          {/* Reference line at 0.5 (50%) */}
          <ReferenceLine y={0.5} stroke="#94a3b8" strokeDasharray="4 4" strokeWidth={1.5}>
            <Label value="50%" position="right" fill="#64748b" fontSize={10} />
          </ReferenceLine>

          {/* Stacked bars to create waterfall effect */}
          <Bar dataKey="base" stackId="stack" fill="transparent" />
          <Bar dataKey="contribution" stackId="stack" label={<CustomLabel />} radius={[4, 4, 0, 0]}>
            {waterfallData.map((entry, index) => {
              let fill = '#22c55e'; // Default green

              if (entry.isBase) {
                fill = '#6366f1'; // Indigo for base
              } else if (entry.isPrediction) {
                fill = entry.isPositive ? '#16a34a' : '#dc2626'; // Dark green/red for prediction
              } else if (!entry.isPositive) {
                fill = '#ef4444'; // Red for negative contributions
              }

              return <Cell key={`cell-${index}`} fill={fill} fillOpacity={0.85} />;
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 text-sm pb-2">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-indigo-500" />
          <span className="text-slate-600 text-xs">Base</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-green-500" />
          <span className="text-slate-600 text-xs">Aumenta probabilidade</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-red-500" />
          <span className="text-slate-600 text-xs">Diminui probabilidade</span>
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
