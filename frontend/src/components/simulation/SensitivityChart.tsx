/**
 * SensitivityChart component for variance decomposition visualization.
 *
 * Displays bar chart showing variance explained (R²) by each variable.
 *
 * References:
 *   - Spec: specs/035-causal-simulation/spec.md
 *   - Service: services/simulation/evidence_calculator_service.py
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
import { TrendingUp, AlertTriangle } from 'lucide-react';

interface SensitivityChartProps {
  /**
   * Variance explained (R²) keyed by variable name.
   * Values should be between 0 and 1.
   */
  varianceExplained: Record<string, number>;

  /**
   * Chart height in pixels.
   */
  height?: number;

  /**
   * Threshold for highlighting high-impact variables.
   */
  highlightThreshold?: number;
}

/**
 * Custom tooltip for sensitivity chart.
 */
function SensitivityTooltip({ active, payload }: any) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const data = payload[0].payload;
  const percentage = (data.variance * 100).toFixed(1);
  const isHighImpact = data.variance >= 0.3;

  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-lg p-3">
      <p className="font-semibold text-slate-900 mb-2">{data.variable}</p>
      <div className="space-y-1 text-sm">
        <div className="flex items-center gap-2">
          <span className="text-slate-600">Variance Explained (R²):</span>
          <span className="font-mono font-medium text-indigo-700">{percentage}%</span>
        </div>
        {isHighImpact && (
          <div className="flex items-center gap-2 text-amber-700 pt-2 border-t border-slate-200">
            <AlertTriangle className="h-3.5 w-3.5" />
            <span className="text-xs">High impact variable</span>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * SensitivityChart component.
 *
 * Displays variance decomposition as horizontal bar chart.
 *
 * @example
 * <SensitivityChart
 *   varianceExplained={{
 *     "price": 0.45,
 *     "marketing_spend": 0.32,
 *     "season": 0.15
 *   }}
 * />
 */
export function SensitivityChart({
  varianceExplained,
  height = 400,
  highlightThreshold = 0.3,
}: SensitivityChartProps) {
  // Transform and sort data by variance (descending)
  const data = Object.entries(varianceExplained)
    .map(([variable, variance]) => ({
      variable,
      variance,
      percentage: variance * 100,
    }))
    .sort((a, b) => b.variance - a.variance);

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500">
        No sensitivity data available
      </div>
    );
  }

  // Identify high-impact variables
  const highImpactCount = data.filter((d) => d.variance >= highlightThreshold).length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-section-title">Sensitivity Analysis</h3>
          <p className="text-sm text-slate-600 mt-1">
            Variance explained by each variable (R²)
          </p>
        </div>
        {highImpactCount > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 rounded-lg border border-amber-200">
            <TrendingUp className="h-4 w-4 text-amber-700" />
            <span className="text-sm font-medium text-amber-900">
              {highImpactCount} high-impact variable{highImpactCount > 1 ? 's' : ''}
            </span>
          </div>
        )}
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 20, right: 30, left: 120, bottom: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            type="number"
            domain={[0, 1]}
            tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
            tick={{ fill: '#64748b', fontSize: 12 }}
          />
          <YAxis
            type="category"
            dataKey="variable"
            width={110}
            tick={{ fill: '#64748b', fontSize: 12 }}
          />
          <Tooltip content={<SensitivityTooltip />} />
          <Bar dataKey="variance" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.variance >= highlightThreshold ? '#f59e0b' : '#818cf8'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Key insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Top driver */}
        {data.length > 0 && (
          <div className="card p-4 border-l-4 border-indigo-500">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-4 w-4 text-indigo-600" />
              <h4 className="text-card-title">Top Driver</h4>
            </div>
            <p className="text-sm text-slate-600 mb-2">{data[0].variable}</p>
            <p className="text-2xl font-bold text-indigo-700">
              {data[0].percentage.toFixed(1)}%
            </p>
            <p className="text-xs text-slate-500 mt-1">variance explained</p>
          </div>
        )}

        {/* Combined impact of top 3 */}
        {data.length >= 3 && (
          <div className="card p-4 border-l-4 border-violet-500">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-4 w-4 text-violet-600" />
              <h4 className="text-card-title">Top 3 Combined</h4>
            </div>
            <p className="text-sm text-slate-600 mb-2">
              {data.slice(0, 3).map((d) => d.variable).join(', ')}
            </p>
            <p className="text-2xl font-bold text-violet-700">
              {data
                .slice(0, 3)
                .reduce((sum, d) => sum + d.percentage, 0)
                .toFixed(1)}%
            </p>
            <p className="text-xs text-slate-500 mt-1">variance explained</p>
          </div>
        )}
      </div>

      {/* High-impact variables list */}
      {highImpactCount > 0 && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 p-4">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="h-4 w-4 text-amber-700" />
            <h4 className="font-semibold text-amber-900">High-Impact Variables</h4>
          </div>
          <p className="text-sm text-amber-800 mb-3">
            These variables explain ≥{highlightThreshold * 100}% of variance. Focus interventions
            here for maximum impact.
          </p>
          <ul className="space-y-2">
            {data
              .filter((d) => d.variance >= highlightThreshold)
              .map((d) => (
                <li key={d.variable} className="flex items-center justify-between">
                  <span className="text-sm font-medium text-amber-900">{d.variable}</span>
                  <span className="text-sm font-mono text-amber-700">
                    {d.percentage.toFixed(1)}%
                  </span>
                </li>
              ))}
          </ul>
        </div>
      )}
    </div>
  );
}
