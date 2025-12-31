/**
 * ExplorationDetail page.
 *
 * Displays exploration tree visualization with node details and winning path.
 *
 * References:
 *   - Spec: specs/025-exploration-frontend/spec.md (US2, US3, US4, US5)
 */

import { useState, useMemo, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import {
  useExploration,
  useExplorationTree,
  useWinningPath,
} from '@/hooks/use-exploration';
import { ExplorationTree } from '@/components/exploration/ExplorationTree';
import { NodeDetailsPanel } from '@/components/exploration/NodeDetailsPanel';
import { ExplorationProgress } from '@/components/exploration/ExplorationProgress';
import { WinningPathPanel } from '@/components/exploration/WinningPathPanel';
import type { ScenarioNode } from '@/types/exploration';
import { ArrowLeft, TreeDeciduous, Trophy } from 'lucide-react';

export default function ExplorationDetail() {
  const { id: experimentId, explorationId } = useParams<{
    id: string;
    explorationId: string;
  }>();
  const navigate = useNavigate();

  // State
  const [selectedNode, setSelectedNode] = useState<ScenarioNode | null>(null);
  const [isDetailsPanelOpen, setIsDetailsPanelOpen] = useState(false);
  const [showWinningPath, setShowWinningPath] = useState(false);

  // Data fetching
  const { data: exploration, isLoading: isLoadingExploration } = useExploration(
    explorationId ?? ''
  );
  const { data: treeData, isLoading: isLoadingTree } = useExplorationTree(
    explorationId ?? ''
  );
  const { data: winningPath } = useWinningPath(explorationId ?? '');

  // Find parent node for delta calculation
  const parentNode = useMemo(() => {
    if (!selectedNode?.parent_id || !treeData?.nodes) return null;
    return treeData.nodes.find((n) => n.id === selectedNode.parent_id) || null;
  }, [selectedNode, treeData?.nodes]);

  // Find winner node ID
  const winnerNodeId = useMemo(() => {
    if (!treeData?.nodes) return null;
    const winner = treeData.nodes.find((n) => n.node_status === 'winner');
    return winner?.id || null;
  }, [treeData?.nodes]);

  // Show toast when exploration completes
  useEffect(() => {
    if (exploration?.status === 'goal_achieved' && winningPath) {
      toast.success('Meta atingida!', {
        description: 'A exploração encontrou um cenário vencedor.',
      });
    }
  }, [exploration?.status, winningPath]);

  // Handle node click
  const handleNodeClick = (node: ScenarioNode) => {
    setSelectedNode(node);
    setIsDetailsPanelOpen(true);
  };

  // Handle winning path step click
  const handlePathStepClick = (depth: number) => {
    const node = treeData?.nodes.find((n) => n.depth === depth);
    if (node) {
      setSelectedNode(node);
      setIsDetailsPanelOpen(true);
    }
  };

  // Loading state
  if (isLoadingExploration) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <SynthLabHeader
          subtitle="Carregando exploração..."
          backTo={`/experiments/${experimentId}`}
        />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Skeleton className="h-24 w-full mb-6" />
          <Skeleton className="h-[500px] w-full" />
        </main>
      </div>
    );
  }

  // Error state
  if (!exploration) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <SynthLabHeader
          subtitle="Exploração não encontrada"
          backTo={`/experiments/${experimentId}`}
        />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center py-12">
            <p className="text-muted-foreground">
              A exploração solicitada não foi encontrada.
            </p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => navigate(`/experiments/${experimentId}`)}
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Voltar ao Experimento
            </Button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader
        subtitle={
          <div className="flex items-center gap-2">
            <TreeDeciduous className="h-5 w-5 text-indigo-600" />
            <span>Exploração de Cenários</span>
          </div>
        }
        backTo={`/experiments/${experimentId}`}
        actions={
          winningPath && (
            <Button
              variant={showWinningPath ? 'default' : 'outline'}
              onClick={() => setShowWinningPath(!showWinningPath)}
              className={showWinningPath ? 'btn-primary' : ''}
            >
              <Trophy className="mr-2 h-4 w-4" />
              {showWinningPath ? 'Ocultar Caminho' : 'Ver Caminho Vencedor'}
            </Button>
          )
        }
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Progress Indicators */}
        <ExplorationProgress exploration={exploration} className="mb-8" />

        {/* Main Content Grid */}
        <div className={`grid gap-6 ${showWinningPath && winningPath ? 'lg:grid-cols-3' : ''}`}>
          {/* Tree Visualization */}
          <div className={showWinningPath && winningPath ? 'lg:col-span-2' : ''}>
            <div className="card p-4">
              <h2 className="text-section-title mb-4 flex items-center gap-2">
                <TreeDeciduous className="h-5 w-5 text-indigo-600" />
                Árvore de Cenários
              </h2>

              {isLoadingTree ? (
                <Skeleton className="h-[500px] w-full" />
              ) : treeData?.nodes && treeData.nodes.length > 0 ? (
                <ExplorationTree
                  nodes={treeData.nodes}
                  onNodeClick={handleNodeClick}
                  selectedNodeId={selectedNode?.id}
                  winnerNodeId={winnerNodeId}
                />
              ) : (
                <div className="flex items-center justify-center h-[500px] bg-slate-50 rounded-lg border">
                  <p className="text-muted-foreground">
                    Nenhum nó na árvore ainda
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Winning Path Panel */}
          {showWinningPath && winningPath && (
            <WinningPathPanel
              path={winningPath}
              onStepClick={handlePathStepClick}
            />
          )}
        </div>
      </main>

      {/* Node Details Panel */}
      <NodeDetailsPanel
        node={selectedNode}
        open={isDetailsPanelOpen}
        onOpenChange={setIsDetailsPanelOpen}
        parentNode={parentNode}
      />
    </div>
  );
}
