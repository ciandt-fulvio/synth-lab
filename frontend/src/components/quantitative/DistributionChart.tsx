/**
 * DistributionChart component.
 *
 * Renders a histogram of Monte Carlo simulation results with stats overlay.
 * Shows mean, median, p10/p90 reference lines and AI interpretation below.
 *
 * References:
 *   - Types: src/types/quantitative-analysis.ts
 *   - Charts: recharts v2.15
 *   - Pattern: src/components/synths/DemographicCharts.tsx
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import type { SimulationStats, Interpretation } from '@/types/quantitative-analysis';

const HISTOGRAM_BINS = 20;
const BAR_COLOR = '#4f46e5'; // indigo-600

interface DistributionChartProps {
  distribution: number[];
  stats: SimulationStats;
  interpretation?: Interpretation;
}

function buildHistogram(distribution: number[], bins: number) {
  if (distribution.length === 0) return [];

  const min = Math.min(...distribution);
  const max = Math.max(...distribution);
  const range = max - min || 1;
  const binWidth = range / bins;

  const buckets = Array.from({ length: bins }, (_, i) => ({
    label: `${(min + i * binWidth).toFixed(1)}%`,
    rangeStart: min + i * binWidth,
    rangeEnd: min + (i + 1) * binWidth,
    count: 0,
  }));

  for (const value of distribution) {
    let idx = Math.floor((value - min) / binWidth);
    if (idx >= bins) idx = bins - 1;
    buckets[idx].count++;
  }

  return buckets;
}

export function DistributionChart({ distribution, stats, interpretation }: DistributionChartProps) {
  const histogram = buildHistogram(distribution, HISTOGRAM_BINS);

  return (
    <div className="space-y-4">
      {/* Stats summary */}
      <div className="grid grid-cols-5 gap-3">
        <StatCard label="Média" value={`${stats.mean.toFixed(1)}%`} />
        <StatCard label="Mediana" value={`${stats.median.toFixed(1)}%`} />
        <StatCard label="Desvio" value={`${stats.std.toFixed(1)}%`} />
        <StatCard label="P10" value={`${stats.p10.toFixed(1)}%`} />
        <StatCard label="P90" value={`${stats.p90.toFixed(1)}%`} />
      </div>

      {/* Histogram */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={histogram} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 10 }}
              interval={Math.ceil(HISTOGRAM_BINS / 8)}
            />
            <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
            <ReferenceLine
              x={findClosestBin(histogram, stats.mean)}
              stroke="#059669"
              strokeWidth={2}
              strokeDasharray="4 4"
              label={{ value: 'Média', fill: '#059669', fontSize: 10, position: 'top' }}
            />
            <ReferenceLine
              x={findClosestBin(histogram, stats.p10)}
              stroke="#d97706"
              strokeWidth={1.5}
              strokeDasharray="3 3"
              label={{ value: 'P10', fill: '#d97706', fontSize: 10, position: 'top' }}
            />
            <ReferenceLine
              x={findClosestBin(histogram, stats.p90)}
              stroke="#d97706"
              strokeWidth={1.5}
              strokeDasharray="3 3"
              label={{ value: 'P90', fill: '#d97706', fontSize: 10, position: 'top' }}
            />
            <Bar dataKey="count" fill={BAR_COLOR} radius={[2, 2, 0, 0]} opacity={0.85} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* AI Interpretation */}
      {interpretation && (
        <div className="rounded-lg bg-slate-50 border border-slate-200 p-4">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">
            Interpretação — Distribuição
          </p>
          <p className="text-sm text-slate-700 leading-relaxed">
            {interpretation.ai_text || interpretation.raw_text}
          </p>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-center">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-lg font-semibold text-slate-800">{value}</p>
    </div>
  );
}

function findClosestBin(
  histogram: { label: string; rangeStart: number; rangeEnd: number }[],
  value: number
): string | undefined {
  for (const bin of histogram) {
    if (value >= bin.rangeStart && value < bin.rangeEnd) {
      return bin.label;
    }
  }
  // Fallback to last bin
  return histogram[histogram.length - 1]?.label;
}
