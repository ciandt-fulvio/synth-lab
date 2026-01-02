/**
 * ExplorationDetail page.
 *
 * Displays exploration tree visualization using React Flow with node details.
 *
 * References:
 *   - Spec: specs/025-exploration-frontend/spec.md (US2, US3, US4, US5)
 */

import { useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { Network } from 'lucide-react';

import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import { ExplorationTreeFlow } from '@/components/exploration/ExplorationTreeFlow';
import { ExplorationProgress } from '@/components/exploration/ExplorationProgress';
import { NodeDetailsPanel } from '@/components/exploration/NodeDetailsPanel';
import { Skeleton } from '@/components/ui/skeleton';
import {
  useExploration,
  useExplorationTree,
} from '@/hooks/use-exploration';
import type { ScenarioNode } from '@/types/exploration';

export default function ExplorationDetail() {
  const { id: experimentId, explorationId } = useParams<{
    id: string;
    explorationId: string;
  }>();

  // Data fetching
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
          subtitle="Carregando exploração..."
          backTo={`/experiments/${experimentId}?tab=explorations`}
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
          subtitle="Exploração não encontrada"
          backTo={`/experiments/${experimentId}?tab=explorations`}
        />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <p className="text-muted-foreground">Exploração não encontrada.</p>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader
        subtitle={
          <span className="flex items-center gap-2">
            <Network className="h-5 w-5 text-indigo-600" />
            Exploração de Cenários
          </span>
        }
        backTo={`/experiments/${experimentId}?tab=explorations`}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Progress metrics */}
        <ExplorationProgress exploration={exploration} />

        {/* Tree visualization */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <Network className="h-5 w-5 text-indigo-600" />
            Árvore de Cenários
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
