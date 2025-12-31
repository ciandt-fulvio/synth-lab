/**
 * ExplorationPreview page.
 *
 * Preview page for React Flow tree visualization.
 * Parallel to ExplorationDetail for A/B comparison.
 *
 * References:
 *   - Plan: Migration react-d3-tree to React Flow
 */

import { useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { FlaskConical, ExternalLink, TreeDeciduous } from 'lucide-react';

import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import { ExplorationTreeFlow } from '@/components/exploration/ExplorationTreeFlow';
import { ExplorationProgress } from '@/components/exploration/ExplorationProgress';
import { NodeDetailsPanel } from '@/components/exploration/NodeDetailsPanel';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  useExploration,
  useExplorationTree,
} from '@/hooks/use-exploration';
import type { ScenarioNode } from '@/types/exploration';

export default function ExplorationPreview() {
  const { id: experimentId, explorationId } = useParams<{
    id: string;
    explorationId: string;
  }>();

  // Data fetching (same hooks as ExplorationDetail)
  const { data: exploration, isLoading: isLoadingExploration } = useExploration(
    explorationId ?? ''
  );
  const { data: treeData, isLoading: isLoadingTree } = useExplorationTree(
    explorationId ?? ''
  );

  // Local state
  const [selectedNode, setSelectedNode] = useState<ScenarioNode | null>(null);
  const [isDetailsPanelOpen, setIsDetailsPanelOpen] = useState(false);

  // Computed values
  const winnerNodeId = useMemo(() => {
    if (!treeData?.nodes) return null;
    const winner = treeData.nodes.find((n) => n.node_status === 'winner');
    return winner?.id ?? null;
  }, [treeData?.nodes]);

  const parentNode = useMemo(() => {
    if (!selectedNode?.parent_id || !treeData?.nodes) return null;
    return treeData.nodes.find((n) => n.id === selectedNode.parent_id) ?? null;
  }, [selectedNode, treeData?.nodes]);

  // Handlers
  const handleNodeClick = (node: ScenarioNode) => {
    setSelectedNode(node);
    setIsDetailsPanelOpen(true);
  };

  // Loading state
  if (isLoadingExploration || isLoadingTree) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <SynthLabHeader
          subtitle="Preview: React Flow"
          backTo={`/experiments/${experimentId}/explorations/${explorationId}`}
        />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Skeleton className="h-24 w-full mb-6" />
          <Skeleton className="h-[500px] w-full" />
        </main>
      </div>
    );
  }

  // Error state
  if (!exploration || !treeData) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <SynthLabHeader
          subtitle="Preview"
          backTo={`/experiments/${experimentId}`}
        />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <p className="text-muted-foreground">Exploracao nao encontrada.</p>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader
        subtitle={
          <span className="flex items-center gap-2">
            <FlaskConical className="h-5 w-5 text-amber-500" />
            Preview: React Flow Tree
          </span>
        }
        backTo={`/experiments/${experimentId}/explorations/${explorationId}`}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Info banner */}
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FlaskConical className="h-5 w-5 text-amber-600" />
            <div>
              <p className="font-medium text-amber-900">
                Preview: Nova Visualizacao com React Flow
              </p>
              <p className="text-sm text-amber-700">
                Layout horizontal, nos em HTML, edges animados no caminho vencedor
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm" asChild>
            <Link
              to={`/experiments/${experimentId}/explorations/${explorationId}`}
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Ver Versao Atual
            </Link>
          </Button>
        </div>

        {/* Progress metrics */}
        <ExplorationProgress exploration={exploration} />

        {/* Tree visualization */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <TreeDeciduous className="h-5 w-5 text-indigo-600" />
            Arvore de Cenarios (React Flow)
          </h2>
          <ExplorationTreeFlow
            nodes={treeData.nodes}
            onNodeClick={handleNodeClick}
            selectedNodeId={selectedNode?.id}
            winnerNodeId={winnerNodeId}
          />
        </div>
      </main>

      {/* Node details panel */}
      <NodeDetailsPanel
        node={selectedNode}
        open={isDetailsPanelOpen}
        onOpenChange={setIsDetailsPanelOpen}
        parentNode={parentNode}
      />
    </div>
  );
}
