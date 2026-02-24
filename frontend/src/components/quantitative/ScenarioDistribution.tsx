/**
 * ScenarioDistribution component.
 *
 * Shows a single histogram of adoption rates across all scenarios,
 * with reference lines for P10, mean, and P90.
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
  Tooltip,
  ReferenceLine,
} from 'recharts';
import type { ScenarioRunResult } from '@/types/quantitative-analysis';

const HISTOGRAM_BINS = 60;

interface ScenarioDistributionProps {
  scenarios: ScenarioRunResult[];
}

interface BinData {
  label: string;
  rangeStart: number;
  count: number;
}

function buildHistogram(values: number[], bins: number): BinData[] {
  if (values.length === 0) return [];

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const binWidth = range / bins;

  const buckets: BinData[] = Array.from({ length: bins }, (_, i) => ({
    label: `${(min + i * binWidth).toFixed(1)}%`,
    rangeStart: min + i * binWidth,
    count: 0,
  }));

  for (const v of values) {
    let idx = Math.floor((v - min) / binWidth);
    if (idx >= bins) idx = bins - 1;
    buckets[idx].count++;
  }

  return buckets;
}

function percentile(sorted: number[], p: number): number {
  const idx = (p / 100) * (sorted.length - 1);
  const lo = Math.floor(idx);
  const hi = Math.ceil(idx);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (idx - lo);
}

function closestBinLabel(value: number, buckets: BinData[]): string {
  let best = buckets[0];
  let bestDist = Math.abs(value - buckets[0].rangeStart);
  for (const b of buckets) {
    const d = Math.abs(value - b.rangeStart);
    if (d < bestDist) { bestDist = d; best = b; }
  }
  return best.label;
}

export function ScenarioDistribution({ scenarios }: ScenarioDistributionProps) {
  if (scenarios.length === 0) return null;

  const sorted = [...scenarios.map((s) => s.stats.mean)].sort((a, b) => a - b);
  const histogram = buildHistogram(sorted, HISTOGRAM_BINS);

  const mean = sorted.reduce((a, b) => a + b, 0) / sorted.length;
  const p10 = percentile(sorted, 10);
  const p90 = percentile(sorted, 90);

  const meanLabel = closestBinLabel(mean, histogram);
  const p10Label  = closestBinLabel(p10,  histogram);
  const p90Label  = closestBinLabel(p90,  histogram);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <h3 className="text-base font-semibold text-slate-800 mb-1">Distribuição dos Cenários</h3>
      <p className="text-sm text-slate-500 mb-2">
        {scenarios.length} cenários · {sorted[0].toFixed(1)}%–{sorted[sorted.length - 1].toFixed(1)}%
      </p>

      {/* Legend */}
      <div className="flex items-center gap-4 mb-3 text-xs text-slate-500">
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-5 border-t-2 border-dashed border-amber-400" />
          P10 {p10.toFixed(1)}%
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-5 border-t-2 border-violet-600" />
          Média {mean.toFixed(1)}%
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-5 border-t-2 border-dashed border-emerald-500" />
          P90 {p90.toFixed(1)}%
        </span>
      </div>

      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={histogram} margin={{ top: 4, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 10 }}
              interval={Math.ceil(HISTOGRAM_BINS / 8)}
            />
            <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
            <Tooltip
              contentStyle={{
                fontSize: 12,
                borderRadius: 8,
                border: '1px solid #e2e8f0',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
              formatter={(value: number) => [value, 'Cenários']}
            />
            <Bar
              dataKey="count"
              fill="#6366f1"
              opacity={0.8}
              radius={[2, 2, 0, 0]}
              isAnimationActive={false}
            />
            <ReferenceLine
              x={p10Label}
              stroke="#f59e0b"
              strokeWidth={2}
              strokeDasharray="4 3"
              label={{ value: 'P10', position: 'top', fontSize: 10, fill: '#f59e0b' }}
            />
            <ReferenceLine
              x={meanLabel}
              stroke="#6366f1"
              strokeWidth={2}
              label={{ value: 'Média', position: 'top', fontSize: 10, fill: '#6366f1' }}
            />
            <ReferenceLine
              x={p90Label}
              stroke="#10b981"
              strokeWidth={2}
              strokeDasharray="4 3"
              label={{ value: 'P90', position: 'top', fontSize: 10, fill: '#10b981' }}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
