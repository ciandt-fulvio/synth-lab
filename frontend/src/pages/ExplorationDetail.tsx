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
import { Network, FileText } from 'lucide-react';
import { toast } from 'sonner';

import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import { ExplorationTreeFlow } from '@/components/exploration/ExplorationTreeFlow';
import { ExplorationProgress } from '@/components/exploration/ExplorationProgress';
import { NodeDetailsPanel } from '@/components/exploration/NodeDetailsPanel';
import { ExplorationDocumentCard } from '@/components/exploration/ExplorationDocumentCard';
import { Skeleton } from '@/components/ui/skeleton';
import {
  useExploration,
  useExplorationTree,
  useExplorationSummary,
  useExplorationPRFAQ,
  useGenerateExplorationSummary,
  useGenerateExplorationPRFAQ,
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

  // Completed statuses that allow document generation
  const COMPLETED_STATUSES = ['goal_achieved', 'depth_limit_reached', 'cost_limit_reached'];
  const canGenerateDocuments = exploration
    ? COMPLETED_STATUSES.includes(exploration.status)
    : false;

  // Document hooks
  const { data: summary, isLoading: isLoadingSummary } = useExplorationSummary(
    explorationId ?? '',
    canGenerateDocuments || !!explorationId
  );
  const { data: prfaq, isLoading: isLoadingPRFAQ } = useExplorationPRFAQ(
    explorationId ?? '',
    canGenerateDocuments || !!explorationId
  );

  // Document generation mutations
  const generateSummary = useGenerateExplorationSummary();
  const generatePRFAQ = useGenerateExplorationPRFAQ();

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

  const handleGenerateSummary = async () => {
    if (!explorationId) return;
    try {
      await generateSummary.mutateAsync(explorationId);
      toast.success('Resumo gerado com sucesso!');
    } catch (error) {
      toast.error('Erro ao gerar resumo', {
        description: error instanceof Error ? error.message : 'Tente novamente',
      });
    }
  };

  const handleGeneratePRFAQ = async () => {
    if (!explorationId) return;
    try {
      await generatePRFAQ.mutateAsync(explorationId);
      toast.success('PR-FAQ gerado com sucesso!');
    } catch (error) {
      toast.error('Erro ao gerar PR-FAQ', {
        description: error instanceof Error ? error.message : 'Tente novamente',
      });
    }
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

        {/* Document generation section */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <FileText className="h-5 w-5 text-indigo-600" />
            Documentos da Exploração
          </h2>
          <p className="text-sm text-slate-500 mb-6">
            Gere documentos com resumo e recomendações baseados no caminho vencedor da exploração.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <ExplorationDocumentCard
              documentType="exploration_summary"
              document={summary}
              isLoading={isLoadingSummary}
              isGenerating={generateSummary.isPending}
              canGenerate={canGenerateDocuments}
              onGenerate={handleGenerateSummary}
            />
            <ExplorationDocumentCard
              documentType="exploration_prfaq"
              document={prfaq}
              isLoading={isLoadingPRFAQ}
              isGenerating={generatePRFAQ.isPending}
              canGenerate={canGenerateDocuments && summary?.status === 'completed'}
              onGenerate={handleGeneratePRFAQ}
              disabledReason={
                canGenerateDocuments && summary?.status !== 'completed'
                  ? 'Gere o resumo primeiro para liberar o PR-FAQ'
                  : undefined
              }
            />
          </div>
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
