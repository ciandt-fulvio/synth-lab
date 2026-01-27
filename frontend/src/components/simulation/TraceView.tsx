/**
 * TraceView component for visualizing insight traceability.
 *
 * Shows the path from insight → evidence → variables.
 *
 * References:
 *   - Types: types/simulation-insight.ts
 */

import { ArrowRight, Database, BarChart2, Lightbulb, Info } from 'lucide-react';
import type { InsightTrace } from '@/types/simulation-insight';

interface TraceViewProps {
  /**
   * Insight trace data.
   */
  trace: InsightTrace;

  /**
   * Insight title for context.
   */
  insightTitle?: string;

  /**
   * Insight type for styling.
   */
  insightType?: string;
}

/**
 * Format number for display.
 */
function formatNumber(value: number): string {
  if (Math.abs(value) < 0.01) return value.toExponential(2);
  return value.toFixed(3);
}

/**
 * TraceNode component for individual trace step.
 */
function TraceNode({
  icon: Icon,
  title,
  children,
  className = '',
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`p-4 rounded-lg border ${className}`}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className="h-4 w-4" />
        <span className="font-medium text-sm">{title}</span>
      </div>
      <div className="text-sm">{children}</div>
    </div>
  );
}

/**
 * TraceView component.
 *
 * @example
 * <TraceView
 *   trace={insightTrace}
 *   insightTitle="High price sensitivity"
 * />
 */
export function TraceView({
  trace,
  insightTitle = 'Insight',
  insightType = 'recommendation',
}: TraceViewProps) {
  const hasStatisticalSupport =
    Object.keys(trace.statistical_support).length > 0;
  const hasAffectedWorlds = trace.affected_worlds.length > 0;
  const hasEvidenceRefs = Object.keys(trace.evidence_references).length > 0;

  return (
    <div className="space-y-4">
      {/* Trace Header */}
      <div className="text-center text-sm text-slate-500">
        Traceability Path
      </div>

      {/* Visual Trace Path */}
      <div className="flex flex-col md:flex-row items-stretch gap-2 md:gap-4">
        {/* Insight */}
        <TraceNode
          icon={Lightbulb}
          title="Insight"
          className="flex-1 bg-green-50 border-green-200"
        >
          <div className="text-green-800 font-medium">{insightTitle}</div>
          <div className="text-xs text-green-600 mt-1 capitalize">
            {insightType.replace('_', ' ')}
          </div>
        </TraceNode>

        <ArrowRight className="hidden md:block h-5 w-5 text-slate-300 self-center flex-shrink-0" />

        {/* Evidence */}
        <TraceNode
          icon={BarChart2}
          title="Evidence"
          className="flex-1 bg-blue-50 border-blue-200"
        >
          {hasEvidenceRefs ? (
            <ul className="space-y-1 text-blue-800">
              {Object.entries(trace.evidence_references).map(([key, value]) => (
                <li key={key} className="flex justify-between">
                  <span className="text-blue-600">{key}:</span>
                  <span className="font-mono">{String(value)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <span className="text-blue-600">No evidence references</span>
          )}
        </TraceNode>

        <ArrowRight className="hidden md:block h-5 w-5 text-slate-300 self-center flex-shrink-0" />

        {/* Worlds */}
        <TraceNode
          icon={Database}
          title="Scenarios"
          className="flex-1 bg-slate-50 border-slate-200"
        >
          {hasAffectedWorlds ? (
            <div className="text-slate-800">
              <span className="font-semibold">{trace.affected_worlds.length}</span>{' '}
              affected scenarios
            </div>
          ) : (
            <span className="text-slate-500">No specific scenarios</span>
          )}
        </TraceNode>
      </div>

      {/* Statistical Support */}
      {hasStatisticalSupport && (
        <div className="p-4 bg-indigo-50 rounded-lg border border-indigo-200">
          <div className="flex items-center gap-2 mb-3">
            <Info className="h-4 w-4 text-indigo-600" />
            <span className="font-medium text-indigo-800">Statistical Support</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(trace.statistical_support).map(([key, value]) => (
              <div key={key} className="bg-white p-2 rounded border border-indigo-100">
                <div className="text-xs text-indigo-600">{key}</div>
                <div className="font-mono font-semibold text-indigo-800">
                  {formatNumber(value)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Affected World IDs (collapsed) */}
      {hasAffectedWorlds && trace.affected_worlds.length <= 20 && (
        <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
          <div className="text-xs text-slate-500 mb-2">Affected Scenario IDs</div>
          <div className="flex flex-wrap gap-1">
            {trace.affected_worlds.map((worldId) => (
              <span
                key={worldId}
                className="px-2 py-0.5 bg-slate-200 rounded text-xs font-mono text-slate-700"
              >
                {worldId}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Summary for many worlds */}
      {hasAffectedWorlds && trace.affected_worlds.length > 20 && (
        <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 text-center">
          <span className="text-slate-600">
            {trace.affected_worlds.length} scenarios support this insight
          </span>
        </div>
      )}
    </div>
  );
}
