/**
 * VersionHistory component for displaying hypothesis version history.
 *
 * Table showing version timeline with actions to view and restore.
 *
 * References:
 *   - Types: types/hypothesis.ts
 */

import { Clock, Eye, GitCompare, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import type { HypothesisVersion } from '@/types/hypothesis';

interface VersionHistoryProps {
  /**
   * List of versions to display.
   */
  versions: HypothesisVersion[];

  /**
   * Currently active version.
   */
  currentVersion?: number;

  /**
   * Callback when view version is clicked.
   */
  onView?: (version: number) => void;

  /**
   * Callback when compare versions is clicked.
   */
  onCompare?: (version: number) => void;

  /**
   * Callback when restore version is clicked.
   */
  onRestore?: (version: number) => void;

  /**
   * Whether actions are disabled (loading state).
   */
  disabled?: boolean;
}

/**
 * Format date for display.
 */
function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

/**
 * Format relative time.
 */
function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffHours < 1) return 'Just now';
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(dateStr);
}

/**
 * VersionHistory component.
 *
 * @example
 * <VersionHistory
 *   versions={versions}
 *   currentVersion={3}
 *   onView={(v) => console.log('view', v)}
 * />
 */
export function VersionHistory({
  versions,
  currentVersion,
  onView,
  onCompare,
  onRestore,
  disabled = false,
}: VersionHistoryProps) {
  if (versions.length === 0) {
    return (
      <div className="text-center text-slate-500 py-8">
        <Clock className="h-8 w-8 mx-auto mb-2 text-slate-400" />
        <p>No saved versions yet</p>
        <p className="text-sm">Save your first version to track changes</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-slate-200 overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-slate-50">
            <TableHead className="w-[80px]">Version</TableHead>
            <TableHead>Name</TableHead>
            <TableHead className="hidden md:table-cell">Description</TableHead>
            <TableHead>Created</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {versions.map((version) => {
            const isCurrent = version.version === currentVersion;
            return (
              <TableRow
                key={version.version}
                className={isCurrent ? 'bg-indigo-50' : ''}
              >
                <TableCell>
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-slate-100 text-slate-700 text-sm font-medium">
                      {version.version}
                    </span>
                    {isCurrent && (
                      <span className="text-xs text-indigo-600 font-medium">
                        Current
                      </span>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <span className="font-medium text-slate-900">
                    {version.name || `Version ${version.version}`}
                  </span>
                </TableCell>
                <TableCell className="hidden md:table-cell">
                  <span className="text-sm text-slate-500 line-clamp-1">
                    {version.description || '-'}
                  </span>
                </TableCell>
                <TableCell>
                  <div className="flex flex-col">
                    <span className="text-sm text-slate-700">
                      {formatRelativeTime(version.created_at)}
                    </span>
                    <span className="text-xs text-slate-500">
                      {formatDate(version.created_at)}
                    </span>
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-1">
                    {onView && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onView(version.version)}
                        disabled={disabled}
                        className="h-8 w-8 p-0"
                        title="View version"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    )}
                    {onCompare && !isCurrent && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onCompare(version.version)}
                        disabled={disabled}
                        className="h-8 w-8 p-0"
                        title="Compare with current"
                      >
                        <GitCompare className="h-4 w-4" />
                      </Button>
                    )}
                    {onRestore && !isCurrent && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onRestore(version.version)}
                        disabled={disabled}
                        className="h-8 w-8 p-0 text-amber-600 hover:text-amber-700"
                        title="Restore version"
                      >
                        <RotateCcw className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
