/**
 * ProductImpactChart component.
 *
 * Horizontal bar chart comparing adoption rates at high vs low
 * calibration per product attribute.
 *
 * References:
 *   - Types: src/types/quantitative-analysis.ts (ScenarioRunResult)
 *   - Charts: recharts v2.15
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  LabelList,
} from 'recharts';
import type { ScenarioRunResult } from '@/types/quantitative-analysis';

interface ProductImpactChartProps {
  scenarios: ScenarioRunResult[];
}

interface ProductImpact {
  name: string;
  impact: number;
  meanHigh: number;
  meanLow: number;
}

function computeProductImpacts(scenarios: ScenarioRunResult[]): ProductImpact[] {
  if (scenarios.length === 0) return [];

  const productNodes = new Set<string>();
  for (const s of scenarios) {
    for (const key of Object.keys(s.product_values)) {
      productNodes.add(key);
    }
  }

  const impacts: ProductImpact[] = [];

  for (const node of productNodes) {
    const highScenarios = scenarios.filter((s) => s.product_values[node] === 'high');
    const lowScenarios = scenarios.filter((s) => s.product_values[node] === 'low');

    if (highScenarios.length === 0 || lowScenarios.length === 0) continue;

    const meanHigh =
      highScenarios.reduce((sum, s) => sum + s.stats.mean, 0) / highScenarios.length;
    const meanLow =
      lowScenarios.reduce((sum, s) => sum + s.stats.mean, 0) / lowScenarios.length;

    impacts.push({
      name: node,
      impact: Math.round((meanHigh - meanLow) * 10) / 10,
      meanHigh: Math.round(meanHigh * 10) / 10,
      meanLow: Math.round(meanLow * 10) / 10,
    });
  }

  return impacts.sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact));
}

export function ProductImpactChart({ scenarios }: ProductImpactChartProps) {
  const impacts = computeProductImpacts(scenarios);

  if (impacts.length === 0) return null;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <h3 className="text-base font-semibold text-slate-800 mb-1">
        Quanto cada atributo de produto influencia a adoção?
      </h3>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-slate-500">
          Taxa média de adoção com cada atributo no nível máximo vs. mínimo
        </p>
        <div className="flex items-center gap-4 text-xs text-slate-500 shrink-0 ml-4">
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-3 h-3 rounded-sm bg-red-400" />
            Nível baixo
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-3 h-3 rounded-sm bg-emerald-400" />
            Nível alto
          </span>
        </div>
      </div>

      <div style={{ height: Math.max(impacts.length * 56 + 60, 180) }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={impacts}
            layout="vertical"
            margin={{ top: 5, right: 60, left: 10, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fontSize: 11 }}
              tickFormatter={(v: number) => `${v.toFixed(0)}%`}
              domain={[0, 'auto']}
            />
            <YAxis
              dataKey="name"
              type="category"
              width={200}
              tick={{ fontSize: 11, fill: '#475569' }}
            />
            <Bar
              dataKey="meanLow"
              fill="#f87171"
              radius={[0, 4, 4, 0]}
              barSize={16}
              isAnimationActive={false}
            >
              <LabelList
                dataKey="meanLow"
                position="right"
                formatter={(v: number) => `${v.toFixed(1)}%`}
                style={{ fontSize: 10, fill: '#dc2626' }}
              />
            </Bar>
            <Bar
              dataKey="meanHigh"
              fill="#34d399"
              radius={[0, 4, 4, 0]}
              barSize={16}
              isAnimationActive={false}
            >
              <LabelList
                dataKey="meanHigh"
                position="right"
                formatter={(v: number) => `${v.toFixed(1)}%`}
                style={{ fontSize: 10, fill: '#059669' }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
