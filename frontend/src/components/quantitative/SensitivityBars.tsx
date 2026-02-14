/**
 * SensitivityBars component.
 *
 * Horizontal bar chart showing per-edge sensitivity impact, sorted by impact desc.
 * Each bar shows the edge header and its impact on adoption rate.
 *
 * References:
 *   - Types: src/types/quantitative-analysis.ts (SensitivityItem)
 *   - Charts: recharts v2.15
 *   - Pattern: src/components/synths/DemographicCharts.tsx
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { SensitivityItem, Interpretation } from '@/types/quantitative-analysis';

const IMPACT_COLORS = [
  '#4f46e5', // indigo-600 (highest impact)
  '#6366f1', // indigo-500
  '#818cf8', // indigo-400
  '#a5b4fc', // indigo-300
  '#c7d2fe', // indigo-200
  '#e0e7ff', // indigo-100
];

interface SensitivityBarsProps {
  sensitivity: SensitivityItem[];
  interpretation?: Interpretation;
}

export function SensitivityBars({ sensitivity, interpretation }: SensitivityBarsProps) {
  const chartData = sensitivity.map((item) => ({
    ...item,
    // Truncate long headers for chart display
    shortHeader: item.header.length > 40 ? item.header.substring(0, 37) + '...' : item.header,
  }));

  const maxImpact = Math.max(...sensitivity.map((s) => s.impact), 1);

  return (
    <div className="space-y-4">
      {/* Chart */}
      <div style={{ height: Math.max(sensitivity.length * 48 + 40, 200) }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fontSize: 11 }}
              domain={[0, Math.ceil(maxImpact * 1.1)]}
              tickFormatter={(v: number) => `${v.toFixed(1)}pp`}
            />
            <YAxis
              dataKey="shortHeader"
              type="category"
              width={180}
              tick={{ fontSize: 11 }}
            />
            <Tooltip
              formatter={(value: number) => [`${value.toFixed(2)}pp`, 'Impacto']}
              labelFormatter={(_label: string, payload: Array<{ payload: SensitivityItem }>) => {
                const item = payload?.[0]?.payload;
                if (!item) return '';
                return `${item.header}\nBaixo: ${item.mean_low.toFixed(1)}% → Alto: ${item.mean_high.toFixed(1)}%`;
              }}
            />
            <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
              {chartData.map((_, index) => (
                <Cell
                  key={index}
                  fill={IMPACT_COLORS[Math.min(index, IMPACT_COLORS.length - 1)]}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Detail table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200">
              <th className="text-left py-2 px-3 text-xs font-medium text-slate-500">Premissa</th>
              <th className="text-right py-2 px-3 text-xs font-medium text-slate-500">Impacto</th>
              <th className="text-right py-2 px-3 text-xs font-medium text-slate-500">Cenário Baixo</th>
              <th className="text-right py-2 px-3 text-xs font-medium text-slate-500">Cenário Alto</th>
            </tr>
          </thead>
          <tbody>
            {sensitivity.map((item, i) => (
              <tr key={item.edge_id} className={i % 2 === 0 ? 'bg-slate-50/50' : ''}>
                <td className="py-2 px-3 text-slate-700">{item.header}</td>
                <td className="py-2 px-3 text-right font-medium text-slate-800">
                  {item.impact.toFixed(2)}pp
                </td>
                <td className="py-2 px-3 text-right text-slate-600">
                  {item.mean_low.toFixed(1)}%
                </td>
                <td className="py-2 px-3 text-right text-slate-600">
                  {item.mean_high.toFixed(1)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* AI Interpretation */}
      {interpretation && (
        <div className="rounded-lg bg-slate-50 border border-slate-200 p-4">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">
            Interpretação — Sensibilidade
          </p>
          <p className="text-sm text-slate-700 leading-relaxed">
            {interpretation.ai_text || interpretation.raw_text}
          </p>
        </div>
      )}
    </div>
  );
}
