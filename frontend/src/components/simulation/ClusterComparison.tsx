/**
 * ClusterComparison component for comparing behavioral clusters.
 *
 * Side-by-side table showing cluster centroids and outcomes.
 *
 * References:
 *   - Types: types/simulation-insight.ts
 */

import { Users } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import type { BehavioralCluster } from '@/types/simulation-insight';

interface ClusterComparisonProps {
  /**
   * Clusters to compare.
   */
  clusters: BehavioralCluster[];

  /**
   * Optional variables to highlight.
   */
  highlightVariables?: string[];

  /**
   * Optional click handler for cluster drill-down.
   */
  onClusterClick?: (cluster: BehavioralCluster) => void;
}

/**
 * Format percentage for display.
 */
function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

/**
 * Format number for display.
 */
function formatNumber(value: number): string {
  if (Math.abs(value) < 0.01) return value.toExponential(2);
  if (Math.abs(value) < 1) return value.toFixed(3);
  if (Math.abs(value) < 100) return value.toFixed(2);
  return value.toFixed(0);
}

/**
 * Get all unique variable names from centroids.
 */
function getVariableNames(clusters: BehavioralCluster[]): string[] {
  const names = new Set<string>();
  clusters.forEach((cluster) => {
    Object.keys(cluster.centroid).forEach((name) => names.add(name));
  });
  return Array.from(names).sort();
}

/**
 * Get all unique outcome names from clusters.
 */
function getOutcomeNames(clusters: BehavioralCluster[]): string[] {
  const names = new Set<string>();
  clusters.forEach((cluster) => {
    Object.keys(cluster.outcome_stats).forEach((name) => names.add(name));
  });
  return Array.from(names).sort();
}

/**
 * ClusterComparison component.
 *
 * @example
 * <ClusterComparison
 *   clusters={clusters}
 *   onClusterClick={(c) => console.log(c.id)}
 * />
 */
export function ClusterComparison({
  clusters,
  highlightVariables = [],
  onClusterClick,
}: ClusterComparisonProps) {
  if (clusters.length === 0) {
    return (
      <div className="text-center text-slate-500 py-8">
        No clusters available
      </div>
    );
  }

  const variableNames = getVariableNames(clusters);
  const outcomeNames = getOutcomeNames(clusters);

  return (
    <div className="space-y-4">
      {/* Cluster Overview */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {clusters.map((cluster) => (
          <div
            key={cluster.id}
            className={`p-4 rounded-lg border bg-white ${
              onClusterClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''
            }`}
            onClick={() => onClusterClick?.(cluster)}
          >
            <div className="flex items-center gap-2 mb-2">
              <Users className="h-4 w-4 text-slate-500" />
              <span className="font-medium text-slate-900">{cluster.label}</span>
            </div>
            <div className="text-2xl font-semibold text-slate-900">
              {cluster.size}
            </div>
            <div className="text-sm text-slate-500">
              {formatPercent(cluster.percentage)} of scenarios
            </div>
          </div>
        ))}
      </div>

      {/* Centroid Comparison Table */}
      <div className="rounded-lg border border-slate-200 overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50">
              <TableHead className="w-[200px]">Variable</TableHead>
              {clusters.map((cluster) => (
                <TableHead key={cluster.id} className="text-center">
                  {cluster.label}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {variableNames.map((varName) => {
              const isHighlighted = highlightVariables.includes(varName);
              return (
                <TableRow
                  key={varName}
                  className={isHighlighted ? 'bg-indigo-50' : ''}
                >
                  <TableCell className="font-medium">
                    {varName}
                    {isHighlighted && (
                      <span className="ml-2 text-xs text-indigo-600">*</span>
                    )}
                  </TableCell>
                  {clusters.map((cluster) => (
                    <TableCell key={cluster.id} className="text-center font-mono">
                      {formatNumber(cluster.centroid[varName] ?? 0)}
                    </TableCell>
                  ))}
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      {/* Outcome Comparison Table */}
      {outcomeNames.length > 0 && (
        <div className="rounded-lg border border-slate-200 overflow-hidden">
          <div className="bg-slate-100 px-4 py-2 border-b border-slate-200">
            <h4 className="font-medium text-slate-900">Outcome Statistics</h4>
          </div>
          <Table>
            <TableHeader>
              <TableRow className="bg-slate-50">
                <TableHead className="w-[200px]">Outcome</TableHead>
                {clusters.map((cluster) => (
                  <TableHead key={cluster.id} className="text-center" colSpan={3}>
                    {cluster.label}
                  </TableHead>
                ))}
              </TableRow>
              <TableRow className="bg-slate-50/50">
                <TableHead></TableHead>
                {clusters.map((cluster) => (
                  <TableHead key={cluster.id} colSpan={3} className="p-0">
                    <div className="grid grid-cols-3 text-center text-xs">
                      <span className="px-2 py-1 border-r border-slate-200">Mean</span>
                      <span className="px-2 py-1 border-r border-slate-200">p50</span>
                      <span className="px-2 py-1">Std</span>
                    </div>
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {outcomeNames.map((outName) => (
                <TableRow key={outName}>
                  <TableCell className="font-medium">{outName}</TableCell>
                  {clusters.map((cluster) => {
                    const stats = cluster.outcome_stats[outName];
                    return (
                      <TableCell key={cluster.id} colSpan={3} className="p-0">
                        <div className="grid grid-cols-3 text-center font-mono text-sm">
                          <span className="px-2 py-2 border-r border-slate-100">
                            {stats ? formatNumber(stats.mean) : '-'}
                          </span>
                          <span className="px-2 py-2 border-r border-slate-100">
                            {stats ? formatNumber(stats.p50) : '-'}
                          </span>
                          <span className="px-2 py-2">
                            {stats ? formatNumber(stats.std) : '-'}
                          </span>
                        </div>
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
