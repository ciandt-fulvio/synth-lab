/**
 * VersionComparison component for comparing hypothesis versions.
 *
 * Diff table showing changed parameters between two versions.
 *
 * References:
 *   - Types: types/hypothesis.ts
 */

import { ArrowRight, Minus, Plus, RefreshCw } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface VersionChange {
  variable_name: string;
  field: string;
  old_value: unknown;
  new_value: unknown;
}

interface VersionComparisonProps {
  /**
   * Version number of the base (from).
   */
  fromVersion: number;

  /**
   * Version number of the compare (to).
   */
  toVersion: number;

  /**
   * List of changes between versions.
   */
  changes: VersionChange[];

  /**
   * Whether comparison is loading.
   */
  isLoading?: boolean;
}

/**
 * Format value for display.
 */
function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'number') {
    if (Math.abs(value) < 0.01) return value.toExponential(2);
    return value.toFixed(3);
  }
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

/**
 * Get change type for styling.
 */
function getChangeType(oldVal: unknown, newVal: unknown): 'added' | 'removed' | 'modified' {
  if (oldVal === null || oldVal === undefined) return 'added';
  if (newVal === null || newVal === undefined) return 'removed';
  return 'modified';
}

/**
 * VersionComparison component.
 *
 * @example
 * <VersionComparison
 *   fromVersion={1}
 *   toVersion={2}
 *   changes={changes}
 * />
 */
export function VersionComparison({
  fromVersion,
  toVersion,
  changes,
  isLoading = false,
}: VersionComparisonProps) {
  if (isLoading) {
    return (
      <div className="text-center text-slate-500 py-8">
        <RefreshCw className="h-8 w-8 mx-auto mb-2 animate-spin text-slate-400" />
        <p>Comparing versions...</p>
      </div>
    );
  }

  if (changes.length === 0) {
    return (
      <div className="text-center text-slate-500 py-8 bg-green-50 rounded-lg border border-green-200">
        <p className="text-green-700 font-medium">No differences found</p>
        <p className="text-sm text-green-600">
          Version {fromVersion} and {toVersion} have identical parameters
        </p>
      </div>
    );
  }

  // Group changes by variable
  const changesByVariable = changes.reduce<Record<string, VersionChange[]>>(
    (acc, change) => {
      if (!acc[change.variable_name]) {
        acc[change.variable_name] = [];
      }
      acc[change.variable_name].push(change);
      return acc;
    },
    {}
  );

  return (
    <div className="space-y-4">
      {/* Summary Header */}
      <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
        <div className="flex items-center gap-4">
          <div className="text-center">
            <div className="text-xs text-slate-500">From</div>
            <div className="font-semibold text-lg">v{fromVersion}</div>
          </div>
          <ArrowRight className="h-5 w-5 text-slate-400" />
          <div className="text-center">
            <div className="text-xs text-slate-500">To</div>
            <div className="font-semibold text-lg">v{toVersion}</div>
          </div>
        </div>
        <div className="text-sm text-slate-600">
          {changes.length} change{changes.length !== 1 ? 's' : ''} across{' '}
          {Object.keys(changesByVariable).length} variable
          {Object.keys(changesByVariable).length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Changes by Variable */}
      {Object.entries(changesByVariable).map(([varName, varChanges]) => (
        <div
          key={varName}
          className="rounded-lg border border-slate-200 overflow-hidden"
        >
          <div className="bg-slate-100 px-4 py-2 border-b border-slate-200">
            <span className="font-medium text-slate-900">{varName}</span>
            <span className="ml-2 text-sm text-slate-500">
              {varChanges.length} change{varChanges.length !== 1 ? 's' : ''}
            </span>
          </div>
          <Table>
            <TableHeader>
              <TableRow className="bg-slate-50">
                <TableHead className="w-[150px]">Field</TableHead>
                <TableHead>Previous (v{fromVersion})</TableHead>
                <TableHead></TableHead>
                <TableHead>Current (v{toVersion})</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {varChanges.map((change, index) => {
                const changeType = getChangeType(change.old_value, change.new_value);
                return (
                  <TableRow key={index}>
                    <TableCell className="font-medium text-slate-700">
                      {change.field}
                    </TableCell>
                    <TableCell>
                      <div
                        className={`inline-flex items-center gap-1 px-2 py-1 rounded text-sm ${
                          changeType === 'removed'
                            ? 'bg-red-100 text-red-800'
                            : changeType === 'modified'
                            ? 'bg-amber-100 text-amber-800'
                            : 'text-slate-500'
                        }`}
                      >
                        {changeType === 'removed' && (
                          <Minus className="h-3 w-3" />
                        )}
                        <span className="font-mono">
                          {formatValue(change.old_value)}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <ArrowRight className="h-4 w-4 text-slate-400 mx-auto" />
                    </TableCell>
                    <TableCell>
                      <div
                        className={`inline-flex items-center gap-1 px-2 py-1 rounded text-sm ${
                          changeType === 'added'
                            ? 'bg-green-100 text-green-800'
                            : changeType === 'modified'
                            ? 'bg-green-100 text-green-800'
                            : 'text-slate-500'
                        }`}
                      >
                        {changeType === 'added' && <Plus className="h-3 w-3" />}
                        <span className="font-mono">
                          {formatValue(change.new_value)}
                        </span>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      ))}
    </div>
  );
}
