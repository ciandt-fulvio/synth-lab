/**
 * SimulationResults page for exploring simulation evidence and insights.
 *
 * Displays percentiles, sensitivity analysis, failure modes, and clusters.
 *
 * References:
 *   - Spec: specs/035-causal-simulation/spec.md
 *   - Components: components/simulation/*
 */

import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import { PercentileChart } from '@/components/simulation/PercentileChart';
import { SensitivityChart } from '@/components/simulation/SensitivityChart';
import { FailureModeCard } from '@/components/simulation/FailureModeCard';
import { ClusterComparison } from '@/components/simulation/ClusterComparison';
import { InsightCard } from '@/components/simulation/InsightCard';
import { AuditTrailModal } from '@/components/simulation/AuditTrailModal';
import { TraceView } from '@/components/simulation/TraceView';
import { useEvidence } from '@/hooks/use-evidence';
import { useSimulationInsights, useInsightTrace } from '@/hooks/use-simulation-insights';
import {
  useSimulation,
  useSimulationAudit,
  useReplaySimulation,
  useExportAudit,
} from '@/hooks/use-simulations';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  BarChart3,
  AlertTriangle,
  Users,
  Lightbulb,
  RefreshCw,
  Loader2,
  FileJson,
} from 'lucide-react';
import { toast } from 'sonner';
import type { FailureMode, BehavioralCluster, InsightTrace } from '@/types/simulation-insight';

/**
 * SimulationResults page component.
 */
export default function SimulationResults() {
  const { id: simulationId } = useParams<{ id: string }>();

  // Data hooks
  const { data: simulation } = useSimulation(simulationId || '');
  const {
    data: evidence,
    isLoading: isLoadingEvidence,
    refetch: refetchEvidence,
  } = useEvidence(simulationId || '');
  const { data: insights, isLoading: isLoadingInsights } = useSimulationInsights(
    simulationId || ''
  );
  const { data: auditData, isLoading: isLoadingAudit } = useSimulationAudit(
    simulationId || ''
  );

  // Mutations
  const insightTraceMutation = useInsightTrace();
  const replayMutation = useReplaySimulation();
  const exportMutation = useExportAudit();

  // Local state
  const [selectedTab, setSelectedTab] = useState('overview');
  const [selectedFailureMode, setSelectedFailureMode] = useState<FailureMode | null>(null);
  const [selectedCluster, setSelectedCluster] = useState<BehavioralCluster | null>(null);
  const [selectedInsightTrace, setSelectedInsightTrace] = useState<InsightTrace | null>(null);
  const [showAuditModal, setShowAuditModal] = useState(false);
  const [exportPackage, setExportPackage] = useState<Record<string, unknown> | null>(null);

  const handleTraceClick = async (insightId: string) => {
    try {
      const trace = await insightTraceMutation.mutateAsync(insightId);
      setSelectedInsightTrace(trace);
    } catch (error) {
      console.error('Failed to fetch trace:', error);
    }
  };

  const handleExportAudit = async () => {
    if (!simulationId) return;
    try {
      const result = await exportMutation.mutateAsync(simulationId);
      setExportPackage(result.export_package);
      toast.success('Export package loaded');
    } catch (error) {
      console.error('Failed to export audit:', error);
      toast.error('Failed to export audit trail');
    }
  };

  const handleReplay = async () => {
    if (!simulationId) return;
    try {
      await replayMutation.mutateAsync(simulationId);
      toast.success('Simulation replayed successfully');
      refetchEvidence();
    } catch (error) {
      console.error('Failed to replay simulation:', error);
      toast.error('Failed to replay simulation');
    }
  };

  if (isLoadingEvidence) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <SynthLabHeader subtitle="Loading..." backTo={`/simulations/${simulationId}`} />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="card p-8 text-center">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-600 mx-auto mb-4" />
            <p className="text-slate-500">Computing simulation evidence...</p>
            <p className="text-sm text-slate-400 mt-2">This may take a moment</p>
          </div>
        </main>
      </div>
    );
  }

  if (!evidence) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <SynthLabHeader subtitle="No Results" backTo={`/simulations/${simulationId}`} />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="card p-8 text-center text-slate-500">
            No evidence available. Run the simulation first.
          </div>
        </main>
      </div>
    );
  }

  // Prepare percentile data for chart
  const percentileData = Object.entries(evidence.outcome_distributions).map(
    ([name, dist]) => ({
      name,
      p5: dist.p5,
      p25: dist.p25,
      p50: dist.p50,
      p75: dist.p75,
      p95: dist.p95,
      mean: dist.mean,
    })
  );

  // Prepare sensitivity data for chart
  const sensitivityData = evidence.variance_explained.map((vc) => ({
    variable: vc.variable_name,
    variance_explained: vc.variance_explained * 100,
  }));

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader
        subtitle={`Results - ${simulation?.question_text || 'Simulation'}`}
        backTo={`/simulations/${simulationId}`}
        actions={
          <div className="flex items-center gap-2">
            {auditData && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowAuditModal(true)}
              >
                <FileJson className="h-4 w-4 mr-2" />
                Audit Trail
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchEvidence()}
              disabled={isLoadingEvidence}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoadingEvidence ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        }
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={selectedTab} onValueChange={setSelectedTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="failures" className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Failure Modes ({evidence.failure_modes.length})
            </TabsTrigger>
            <TabsTrigger value="clusters" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Clusters ({evidence.clusters.length})
            </TabsTrigger>
            <TabsTrigger value="insights" className="flex items-center gap-2">
              <Lightbulb className="h-4 w-4" />
              Insights ({insights?.length || 0})
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="card p-4">
                <div className="text-sm text-slate-500">Outcomes</div>
                <div className="text-2xl font-semibold text-slate-900">
                  {Object.keys(evidence.outcome_distributions).length}
                </div>
              </div>
              <div className="card p-4">
                <div className="text-sm text-slate-500">Key Drivers</div>
                <div className="text-2xl font-semibold text-slate-900">
                  {evidence.variance_explained.filter((v) => v.variance_explained > 0.05).length}
                </div>
              </div>
              <div className="card p-4">
                <div className="text-sm text-slate-500">Failure Modes</div>
                <div className="text-2xl font-semibold text-slate-900">
                  {evidence.failure_modes.length}
                </div>
              </div>
              <div className="card p-4">
                <div className="text-sm text-slate-500">Clusters</div>
                <div className="text-2xl font-semibold text-slate-900">
                  {evidence.clusters.length}
                </div>
              </div>
            </div>

            {/* Percentile Chart */}
            <div className="card p-6">
              <h2 className="text-section-title mb-4">Outcome Distributions</h2>
              {percentileData.length > 0 ? (
                <PercentileChart data={percentileData} height={300} />
              ) : (
                <div className="text-center text-slate-500 py-8">
                  No outcome data available
                </div>
              )}
            </div>

            {/* Sensitivity Chart */}
            <div className="card p-6">
              <h2 className="text-section-title mb-4">Sensitivity Analysis</h2>
              {sensitivityData.length > 0 ? (
                <SensitivityChart data={sensitivityData} height={300} />
              ) : (
                <div className="text-center text-slate-500 py-8">
                  No sensitivity data available
                </div>
              )}
            </div>
          </TabsContent>

          {/* Failure Modes Tab */}
          <TabsContent value="failures" className="space-y-4">
            {evidence.failure_modes.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {evidence.failure_modes.map((fm) => (
                  <FailureModeCard
                    key={fm.id}
                    failureMode={fm}
                    onClick={() => setSelectedFailureMode(fm)}
                  />
                ))}
              </div>
            ) : (
              <div className="card p-8 text-center text-slate-500">
                No failure modes detected
              </div>
            )}
          </TabsContent>

          {/* Clusters Tab */}
          <TabsContent value="clusters">
            {evidence.clusters.length > 0 ? (
              <ClusterComparison
                clusters={evidence.clusters}
                onClusterClick={setSelectedCluster}
              />
            ) : (
              <div className="card p-8 text-center text-slate-500">
                No clusters detected
              </div>
            )}
          </TabsContent>

          {/* Insights Tab */}
          <TabsContent value="insights" className="space-y-4">
            {isLoadingInsights ? (
              <div className="card p-8 text-center">
                <Loader2 className="h-6 w-6 animate-spin text-indigo-600 mx-auto" />
              </div>
            ) : insights && insights.length > 0 ? (
              insights.map((insight) => (
                <InsightCard
                  key={insight.id}
                  insight={insight}
                  onTraceClick={() => handleTraceClick(insight.id)}
                />
              ))
            ) : (
              <div className="card p-8 text-center text-slate-500">
                No insights available
              </div>
            )}
          </TabsContent>
        </Tabs>
      </main>

      {/* Failure Mode Detail Dialog */}
      <Dialog
        open={selectedFailureMode !== null}
        onOpenChange={() => setSelectedFailureMode(null)}
      >
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Failure Mode Details</DialogTitle>
            <DialogDescription>
              {selectedFailureMode?.description}
            </DialogDescription>
          </DialogHeader>
          {selectedFailureMode && (
            <div className="space-y-4 py-4">
              <div>
                <h4 className="font-medium text-slate-900 mb-2">Conditions</h4>
                <ul className="space-y-1 text-sm">
                  {Object.entries(selectedFailureMode.pattern).map(
                    ([varName, condition]) => (
                      <li key={varName} className="flex justify-between">
                        <span className="text-slate-600">{varName}</span>
                        <span className="font-mono">
                          {condition.operator} {condition.value.toFixed(2)}
                        </span>
                      </li>
                    )
                  )}
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-slate-900 mb-2">Impact</h4>
                <ul className="space-y-1 text-sm">
                  {Object.entries(selectedFailureMode.outcome_threshold).map(
                    ([outName, threshold]) => (
                      <li key={outName} className="flex justify-between">
                        <span className="text-slate-600">{outName}</span>
                        <span className="font-mono">
                          {threshold.operator} {threshold.value.toFixed(2)}
                        </span>
                      </li>
                    )
                  )}
                </ul>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Frequency</span>
                <span className="font-medium">
                  {(selectedFailureMode.frequency * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Severity</span>
                <span className="font-medium capitalize">
                  {selectedFailureMode.severity}
                </span>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Cluster Detail Dialog */}
      <Dialog
        open={selectedCluster !== null}
        onOpenChange={() => setSelectedCluster(null)}
      >
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{selectedCluster?.label}</DialogTitle>
            <DialogDescription>
              {selectedCluster?.size} scenarios ({((selectedCluster?.percentage || 0) * 100).toFixed(1)}%)
            </DialogDescription>
          </DialogHeader>
          {selectedCluster && (
            <div className="space-y-4 py-4">
              <div>
                <h4 className="font-medium text-slate-900 mb-2">Centroid Values</h4>
                <ul className="space-y-1 text-sm max-h-40 overflow-y-auto">
                  {Object.entries(selectedCluster.centroid).map(([varName, value]) => (
                    <li key={varName} className="flex justify-between">
                      <span className="text-slate-600">{varName}</span>
                      <span className="font-mono">{value.toFixed(3)}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-slate-900 mb-2">Outcome Statistics</h4>
                <ul className="space-y-1 text-sm">
                  {Object.entries(selectedCluster.outcome_stats).map(
                    ([outName, stats]) => (
                      <li key={outName} className="flex justify-between">
                        <span className="text-slate-600">{outName}</span>
                        <span className="font-mono">
                          mean={stats.mean.toFixed(2)}, p50={stats.p50.toFixed(2)}
                        </span>
                      </li>
                    )
                  )}
                </ul>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Insight Trace Dialog */}
      <Dialog
        open={selectedInsightTrace !== null}
        onOpenChange={() => setSelectedInsightTrace(null)}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Insight Traceability</DialogTitle>
            <DialogDescription>
              Evidence supporting this insight
            </DialogDescription>
          </DialogHeader>
          {selectedInsightTrace && (
            <TraceView
              trace={selectedInsightTrace}
              insightTitle={
                insights?.find((i) => i.id === selectedInsightTrace.insight_id)?.title ||
                'Insight'
              }
              insightType={
                insights?.find((i) => i.id === selectedInsightTrace.insight_id)?.insight_type
              }
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Audit Trail Modal */}
      <AuditTrailModal
        open={showAuditModal}
        onOpenChange={(open) => {
          setShowAuditModal(open);
          if (!open) setExportPackage(null);
        }}
        audit={auditData || null}
        exportPackage={
          exportPackage
            ? {
                audit_id: auditData?.id || '',
                simulation_id: simulationId || '',
                export_package: exportPackage,
              }
            : null
        }
        onExport={handleExportAudit}
        onReplay={handleReplay}
        isLoading={exportMutation.isPending || replayMutation.isPending}
      />
    </div>
  );
}
