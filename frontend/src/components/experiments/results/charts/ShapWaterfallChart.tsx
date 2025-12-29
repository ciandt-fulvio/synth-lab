// frontend/src/components/experiments/results/charts/ShapWaterfallChart.tsx
// Vertical waterfall chart showing SHAP contributions for a single synth
// Redesigned for clarity with vertical bars and clean data presentation

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
  LabelList,
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
  value: number; // Cumulative value to display
  contribution: number; // The change from previous step
  isBase?: boolean;
  isPrediction?: boolean;
  isPositive?: boolean;
  displayValue: string;
  cumulativeValue: number;
}

export function ShapWaterfallChart({ data }: ShapWaterfallChartProps) {
  const { baseline_prediction, predicted_success_rate, contributions } = data;

  // Sort contributions by absolute SHAP value (descending)
  const sortedContributions = [...contributions].sort(
    (a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value)
  );

  // Build waterfall data
  const waterfallData: WaterfallDataPoint[] = [];

  // Base value
  waterfallData.push({
    name: 'Base',
    value: baseline_prediction,
    contribution: baseline_prediction,
    isBase: true,
    isPositive: true,
    displayValue: (baseline_prediction * 100).toFixed(1) + '%',
    cumulativeValue: baseline_prediction,
  });

  // Contributions
  let cumulative = baseline_prediction;
  sortedContributions.forEach((item) => {
    const contributionValue = item.shap_value;
    const isPositive = contributionValue >= 0;

    cumulative += contributionValue;

    waterfallData.push({
      name: formatFeatureName(item.feature_name),
      value: cumulative,
      contribution: contributionValue,
      isPositive,
      displayValue: `${isPositive ? '+' : ''}${(contributionValue * 100).toFixed(1)}%`,
      cumulativeValue: cumulative,
    });
  });

  // Add prediction marker
  waterfallData.push({
    name: 'Predição',
    value: cumulative,
    contribution: 0,
    isPrediction: true,
    isPositive: cumulative >= baseline_prediction,
    displayValue: (cumulative * 100).toFixed(1) + '%',
    cumulativeValue: cumulative,
  });

  const finalPrediction = cumulative;

  // Find min/max for Y-axis domain
  const allValues = waterfallData.map((d) => d.value);
  const minValue = Math.min(...allValues, 0);
  const maxValue = Math.max(...allValues, 1);
  const yDomain = [Math.max(0, minValue - 0.1), Math.min(1, maxValue + 0.1)];

  // Custom label component for bar tops
  const CustomLabel = (props: any) => {
    const { x, y, width, value, index } = props;
    const dataPoint = waterfallData[index];

    if (!dataPoint) return null;

    // Position label above bar
    const labelY = y - 8;
    const labelX = x + width / 2;

    let color = '#64748b';
    if (dataPoint.isBase) color = '#6366f1';
    else if (dataPoint.isPrediction) color = '#8b5cf6';
    else if (dataPoint.isPositive) color = '#16a34a';
    else color = '#dc2626';

    return (
      <text
        x={labelX}
        y={labelY}
        fill={color}
        fontSize={11}
        fontWeight={dataPoint.isBase || dataPoint.isPrediction ? '700' : '600'}
        textAnchor="middle"
        dominantBaseline="bottom"
      >
        {dataPoint.isBase || dataPoint.isPrediction
          ? dataPoint.displayValue
          : dataPoint.displayValue}
      </text>
    );
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload[0]) return null;

    const dataPoint = payload[0].payload as WaterfallDataPoint;

    return (
      <div className="bg-white/95 backdrop-blur-sm border-2 border-slate-200 shadow-xl rounded-lg p-3.5">
        <p className="text-sm font-bold text-slate-900 mb-2 tracking-tight">
          {dataPoint.name}
        </p>
        {!dataPoint.isBase && !dataPoint.isPrediction && (
          <p className="text-xs text-slate-600 mb-1">
            Contribuição:{' '}
            <span
              className={`font-semibold ${
                dataPoint.isPositive ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {dataPoint.displayValue}
            </span>
          </p>
        )}
        <p className="text-xs text-slate-600">
          Acumulado:{' '}
          <span className="font-semibold text-slate-900">
            {(dataPoint.cumulativeValue * 100).toFixed(1)}%
          </span>
        </p>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Waterfall Chart */}
      <ResponsiveContainer width="100%" height={450}>
        <BarChart
          data={waterfallData}
          margin={{ top: 40, right: 30, bottom: 80, left: 60 }}
          barCategoryGap="20%"
        >
          {/* Clean grid */}
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#e2e8f0"
            vertical={false}
            opacity={0.6}
          />

          {/* X-axis with angled labels */}
          <XAxis
            dataKey="name"
            angle={-45}
            textAnchor="end"
            height={100}
            interval={0}
            tick={{
              fill: '#475569',
              fontSize: 12,
              fontWeight: 600,
            }}
            axisLine={{ stroke: '#cbd5e1', strokeWidth: 2 }}
            tickLine={{ stroke: '#cbd5e1' }}
          />

          {/* Y-axis */}
          <YAxis
            domain={yDomain}
            tick={{ fill: '#64748b', fontSize: 12, fontWeight: 500 }}
            axisLine={{ stroke: '#cbd5e1', strokeWidth: 2 }}
            tickLine={{ stroke: '#cbd5e1' }}
            tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
            label={{
              value: 'Probabilidade de Sucesso',
              angle: -90,
              position: 'insideLeft',
              style: {
                fill: '#334155',
                fontSize: 13,
                fontWeight: 700,
                letterSpacing: '-0.02em',
              },
            }}
          />

          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(99, 102, 241, 0.08)' }} />

          {/* Reference line at 50% threshold */}
          <ReferenceLine y={0.5} stroke="#94a3b8" strokeDasharray="5 5" strokeWidth={2}>
            <Label
              value="50% (limiar)"
              position="right"
              fill="#64748b"
              fontSize={11}
              fontWeight="600"
              offset={10}
            />
          </ReferenceLine>

          {/* Bars */}
          <Bar dataKey="value" radius={[6, 6, 0, 0]} label={<CustomLabel />}>
            {waterfallData.map((entry, index) => {
              let fill = '#22c55e'; // Green for positive
              let opacity = 0.9;
              let strokeWidth = 0;
              let stroke = 'none';

              if (entry.isBase) {
                fill = '#6366f1'; // Indigo for base
                opacity = 1;
                strokeWidth = 3;
                stroke = '#4f46e5';
              } else if (entry.isPrediction) {
                fill = '#8b5cf6'; // Purple for prediction
                opacity = 1;
                strokeWidth = 3;
                stroke = '#7c3aed';
              } else if (!entry.isPositive) {
                fill = '#ef4444'; // Red for negative
                opacity = 0.9;
              }

              return (
                <Cell
                  key={`cell-${index}`}
                  fill={fill}
                  fillOpacity={opacity}
                  stroke={stroke}
                  strokeWidth={strokeWidth}
                />
              );
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Enhanced Legend */}
      <div className="flex items-center justify-center gap-8 text-sm pb-2 border-t border-slate-200 pt-4">
        <div className="flex items-center gap-2.5">
          <div className="w-4 h-4 rounded-md bg-indigo-500 border-2 border-indigo-700 shadow-sm" />
          <span className="text-slate-700 text-sm font-medium">Base</span>
        </div>
        <div className="flex items-center gap-2.5">
          <div className="w-4 h-4 rounded-md bg-green-500 shadow-sm" />
          <span className="text-slate-700 text-sm font-medium">Aumenta (+)</span>
        </div>
        <div className="flex items-center gap-2.5">
          <div className="w-4 h-4 rounded-md bg-red-500 shadow-sm" />
          <span className="text-slate-700 text-sm font-medium">Diminui (−)</span>
        </div>
        <div className="flex items-center gap-2.5">
          <div className="w-4 h-4 rounded-md bg-purple-500 border-2 border-purple-700 shadow-sm" />
          <span className="text-slate-700 text-sm font-medium">Predição</span>
        </div>
      </div>

      {/* Explanation text */}
      {data.explanation_text && (
        <div className="p-4 bg-gradient-to-r from-indigo-50 to-violet-50 border-l-4 border-indigo-400 rounded-r-lg">
          <p className="text-sm text-indigo-900 leading-relaxed">{data.explanation_text}</p>
        </div>
      )}
    </div>
  );
}
