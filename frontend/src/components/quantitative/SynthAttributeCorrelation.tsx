/**
 * SynthAttributeCorrelation component.
 *
 * Horizontal bar chart showing Pearson r correlation between each synth
 * attribute and adoption probability. Bars colored green (positive) / red
 * (negative), ordered by absolute value.
 *
 * References:
 *   - Types: src/types/quantitative-analysis.ts (SynthAttributeCorrelation)
 *   - Hook: useSynthAttributeInsights
 */

import { Loader2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer } from 'recharts';
import { useSynthAttributeInsights } from '@/hooks/use-quantitative-analysis';

interface SynthAttributeCorrelationProps {
  experimentId: string;
}

export function SynthAttributeCorrelation({ experimentId }: SynthAttributeCorrelationProps) {
  const { data, isLoading } = useSynthAttributeInsights(experimentId);

  if (isLoading) {
    return (
      <div className="text-center py-6">
        <Loader2 className="w-5 h-5 text-violet-500 mx-auto animate-spin" />
      </div>
    );
  }

  if (!data || data.correlations.length === 0) return null;

  // Recharts horizontal bar needs data ordered so that largest bars are at top.
  // We reverse so the largest |r| ends up at top of horizontal chart.
  const chartData = [...data.correlations].reverse().map((c) => ({
    label: c.label,
    r: c.r_value,
    abs_r: Math.abs(c.r_value),
    is_positive: c.is_positive,
  }));

  const maxAbs = Math.max(...chartData.map((d) => Math.abs(d.r)), 0.01);
  const domain = [-maxAbs * 1.15, maxAbs * 1.15];

  return (
    <div>
      <h3 className="text-base font-semibold text-slate-800 mb-1">
        Atributos que Influenciam a Adoção
      </h3>
      <p className="text-sm text-slate-500 mb-4">
        Correlação de Pearson r entre cada atributo do synth e p(adoção).{' '}
        <span className="text-emerald-600 font-medium">Verde = favorece adoção</span>
        {' · '}
        <span className="text-red-500 font-medium">Vermelho = reduz adoção</span>
      </p>

      <div style={{ height: chartData.length * 36 + 32 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 4, right: 24, left: 8, bottom: 4 }}
            barCategoryGap="30%"
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
            <XAxis
              type="number"
              domain={domain}
              tickFormatter={(v) => v.toFixed(2)}
              tick={{ fontSize: 10 }}
              tickCount={7}
            />
            <YAxis
              type="category"
              dataKey="label"
              width={120}
              tick={{ fontSize: 11, fill: '#475569' }}
            />
            <ReferenceLine x={0} stroke="#94a3b8" strokeWidth={1.5} />
            <Bar dataKey="r" radius={[0, 3, 3, 0]} isAnimationActive={false}>
              {chartData.map((entry, index) => (
                <Cell
                  key={index}
                  fill={entry.is_positive ? '#10b981' : '#ef4444'}
                  opacity={0.8 + 0.2 * (entry.abs_r / maxAbs)}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend footnote */}
      <p className="text-xs text-slate-400 mt-2">
        r próximo de ±1 indica forte correlação linear. r ≈ 0 indica sem relação linear.
      </p>
    </div>
  );
}
