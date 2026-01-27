/**
 * AuditTrailModal component for viewing simulation audit trail.
 *
 * Expandable JSON viewer with export functionality.
 *
 * References:
 *   - Backend: api/routers/simulations.py
 */

import { useState } from 'react';
import {
  Download,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Clock,
  Hash,
  FileJson,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface AuditTrail {
  id: string;
  simulation_id: string;
  question: string;
  random_seed: number;
  n_worlds: number;
  dag_version: number;
  n_hypotheses: number;
  n_failure_modes: number;
  n_clusters: number;
  n_insights: number;
  created_at: string;
}

interface ExportPackage {
  audit_id: string;
  simulation_id: string;
  export_package: Record<string, unknown>;
}

interface AuditTrailModalProps {
  /**
   * Whether modal is open.
   */
  open: boolean;

  /**
   * Callback when modal is closed.
   */
  onOpenChange: (open: boolean) => void;

  /**
   * Audit trail data.
   */
  audit: AuditTrail | null;

  /**
   * Export package data (if fetched).
   */
  exportPackage?: ExportPackage | null;

  /**
   * Callback to fetch export package.
   */
  onExport?: () => void;

  /**
   * Callback to replay simulation.
   */
  onReplay?: () => void;

  /**
   * Whether export/replay is loading.
   */
  isLoading?: boolean;
}

/**
 * Format date for display.
 */
function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString();
}

/**
 * CollapsibleSection for expandable JSON viewing.
 */
function CollapsibleSection({
  title,
  data,
  defaultExpanded = false,
}: {
  title: string;
  data: unknown;
  defaultExpanded?: boolean;
}) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden">
      <button
        className="w-full flex items-center justify-between p-3 bg-slate-50 hover:bg-slate-100 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="font-medium text-slate-700">{title}</span>
        {isExpanded ? (
          <ChevronDown className="h-4 w-4 text-slate-500" />
        ) : (
          <ChevronRight className="h-4 w-4 text-slate-500" />
        )}
      </button>
      {isExpanded && (
        <div className="p-3 bg-slate-900 overflow-x-auto">
          <pre className="text-sm text-slate-200 font-mono">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

/**
 * AuditTrailModal component.
 *
 * @example
 * <AuditTrailModal
 *   open={showAudit}
 *   onOpenChange={setShowAudit}
 *   audit={auditData}
 *   onExport={handleExport}
 *   onReplay={handleReplay}
 * />
 */
export function AuditTrailModal({
  open,
  onOpenChange,
  audit,
  exportPackage,
  onExport,
  onReplay,
  isLoading = false,
}: AuditTrailModalProps) {
  const handleDownload = () => {
    if (!exportPackage) return;

    const blob = new Blob([JSON.stringify(exportPackage.export_package, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-${audit?.simulation_id || 'unknown'}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (!audit) {
    return null;
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileJson className="h-5 w-5 text-indigo-600" />
            Audit Trail
          </DialogTitle>
          <DialogDescription>
            Complete reproducibility record for this simulation
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3 bg-slate-50 rounded-lg">
              <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
                <Hash className="h-3 w-3" />
                Seed
              </div>
              <div className="font-mono font-medium">{audit.random_seed}</div>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg">
              <div className="text-slate-500 text-xs mb-1">Worlds</div>
              <div className="font-medium">{audit.n_worlds}</div>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg">
              <div className="text-slate-500 text-xs mb-1">DAG Version</div>
              <div className="font-medium">v{audit.dag_version}</div>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg">
              <div className="text-slate-500 text-xs mb-1">Hypotheses</div>
              <div className="font-medium">{audit.n_hypotheses}</div>
            </div>
          </div>

          {/* Question */}
          <div className="p-3 bg-slate-50 rounded-lg">
            <div className="text-slate-500 text-xs mb-1">Question</div>
            <div className="text-sm text-slate-800">{audit.question}</div>
          </div>

          {/* Timestamp */}
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Clock className="h-4 w-4" />
            Created: {formatDate(audit.created_at)}
          </div>

          {/* Results Summary */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 border border-amber-200 bg-amber-50 rounded-lg">
              <div className="text-amber-700 text-xs mb-1">Failure Modes</div>
              <div className="font-semibold text-amber-800">
                {audit.n_failure_modes}
              </div>
            </div>
            <div className="p-3 border border-blue-200 bg-blue-50 rounded-lg">
              <div className="text-blue-700 text-xs mb-1">Clusters</div>
              <div className="font-semibold text-blue-800">
                {audit.n_clusters}
              </div>
            </div>
            <div className="p-3 border border-green-200 bg-green-50 rounded-lg">
              <div className="text-green-700 text-xs mb-1">Insights</div>
              <div className="font-semibold text-green-800">
                {audit.n_insights}
              </div>
            </div>
          </div>

          {/* Export Package Details (if available) */}
          {exportPackage && (
            <div className="space-y-2">
              <h4 className="font-medium text-slate-900">Export Package</h4>
              <CollapsibleSection
                title="DAG Snapshot"
                data={exportPackage.export_package.dag}
              />
              <CollapsibleSection
                title="Hypotheses"
                data={exportPackage.export_package.hypotheses}
              />
              <CollapsibleSection
                title="Evidence Summary"
                data={exportPackage.export_package.evidence_summary}
              />
              <CollapsibleSection
                title="Insights"
                data={exportPackage.export_package.insights}
              />
            </div>
          )}
        </div>

        <DialogFooter className="flex-wrap gap-2">
          {onExport && !exportPackage && (
            <Button
              variant="outline"
              onClick={onExport}
              disabled={isLoading}
            >
              <FileJson className="h-4 w-4 mr-2" />
              Load Full Details
            </Button>
          )}
          {exportPackage && (
            <Button variant="outline" onClick={handleDownload}>
              <Download className="h-4 w-4 mr-2" />
              Download JSON
            </Button>
          )}
          {onReplay && (
            <Button
              onClick={onReplay}
              disabled={isLoading}
              className="btn-primary"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Replay Simulation
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
