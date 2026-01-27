/**
 * PercentileChart component for outcome distribution visualization.
 *
 * Displays box plot with p5, p25, p50, p75, p95 percentiles.
 *
 * References:
 *   - Spec: specs/035-causal-simulation/spec.md
 *   - Data: services/simulations-api.ts (PercentileDistribution)
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { PercentileDistribution } from '@/services/simulations-api';

interface PercentileChartProps {
  /**
   * Outcome distributions keyed by variable name.
   */
  distributions: Record<string, PercentileDistribution>;

  /**
   * Chart height in pixels.
   */
  height?: number;
}

/**
 * Custom tooltip for percentile chart.
 */
function PercentileTooltip({ active, payload }: any) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const data = payload[0].payload;

  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-lg p-3 space-y-2">
      <p className="font-semibold text-slate-900">{data.variable}</p>
      <div className="space-y-1 text-sm">
        <div className="flex justify-between gap-4">
          <span className="text-slate-600">P5 (min):</span>
          <span className="font-mono font-medium">{data.p5.toFixed(2)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-600">P25:</span>
          <span className="font-mono font-medium">{data.p25.toFixed(2)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-600">P50 (median):</span>
          <span className="font-mono font-medium text-indigo-700">{data.p50.toFixed(2)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-600">P75:</span>
          <span className="font-mono font-medium">{data.p75.toFixed(2)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-600">P95 (max):</span>
          <span className="font-mono font-medium">{data.p95.toFixed(2)}</span>
        </div>
        <div className="flex justify-between gap-4 pt-2 border-t border-slate-200">
          <span className="text-slate-600">Range:</span>
          <span className="font-mono font-medium">{(data.p95 - data.p5).toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
}

/**
 * PercentileChart component.
 *
 * Displays box plot visualization of outcome distributions.
 *
 * @example
 * <PercentileChart
 *   distributions={{
 *     "adoption_rate": { p5: 0.1, p25: 0.3, p50: 0.5, p75: 0.7, p95: 0.9 }
 *   }}
 * />
 */
export function PercentileChart({
  distributions,
  height = 400,
}: PercentileChartProps) {
  // Transform data for Recharts
  const data = Object.entries(distributions).map(([variable, dist]) => ({
    variable,
    p5: dist.p5,
    p25: dist.p25,
    p50: dist.p50,
    p75: dist.p75,
    p95: dist.p95,
    // For stacked bar visualization
    lowerWhisker: dist.p25 - dist.p5,
    lowerBox: dist.p50 - dist.p25,
    upperBox: dist.p75 - dist.p50,
    upperWhisker: dist.p95 - dist.p75,
  }));

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500">
        No distribution data available
      </div>
    );
  }

  // Colors for box plot segments
  const colors = {
    whisker: '#cbd5e1', // slate-300
    box: '#818cf8',     // indigo-400
    median: '#4f46e5',  // indigo-600
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-section-title">Outcome Distributions</h3>
        <div className="flex items-center gap-4 text-xs text-slate-600">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: colors.whisker }} />
            <span>P5-P25, P75-P95</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: colors.box }} />
            <span>P25-P75 (IQR)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: colors.median }} />
            <span>Median (P50)</span>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="variable"
            angle={-45}
            textAnchor="end"
            height={80}
            tick={{ fill: '#64748b', fontSize: 12 }}
          />
          <YAxis
            tick={{ fill: '#64748b', fontSize: 12 }}
            label={{
              value: 'Value',
              angle: -90,
              position: 'insideLeft',
              style: { fill: '#64748b', fontSize: 12 },
            }}
          />
          <Tooltip content={<PercentileTooltip />} />

          {/* Stacked bars for box plot */}
          <Bar dataKey="p5" stackId="box" fill="transparent" />
          <Bar dataKey="lowerWhisker" stackId="box" fill={colors.whisker} />
          <Bar dataKey="lowerBox" stackId="box" fill={colors.box} />
          <Bar dataKey="upperBox" stackId="box" fill={colors.box} />
          <Bar dataKey="upperWhisker" stackId="box" fill={colors.whisker} />
        </BarChart>
      </ResponsiveContainer>

      {/* Summary statistics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.map((item) => (
          <div key={item.variable} className="card p-4">
            <h4 className="text-card-title mb-2">{item.variable}</h4>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-600">Median:</span>
                <span className="font-mono font-medium">{item.p50.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Range:</span>
                <span className="font-mono text-slate-700">
                  {item.p5.toFixed(2)} - {item.p95.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
