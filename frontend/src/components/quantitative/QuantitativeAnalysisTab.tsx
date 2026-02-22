/**
 * QuantitativeAnalysisTab container component.
 *
 * Orchestrates the enriched causal model workflow:
 * 1. Empty state -> "Gerar Modelo" button
 * 2. Loading -> spinner during LLM generation
 * 3. Model view -> CausalDAGView (left) + LikertAssertions (right)
 * 4. Simulate button at bottom -> triggers batch simulation
 *
 * References:
 *   - Hooks: src/hooks/use-quantitative-analysis.ts
 *   - Components: CausalDAGView, LikertAssertions
 */

import { useState, useCallback, useMemo } from 'react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { BarChart3, Loader2, Play, RefreshCw, Sparkles } from 'lucide-react';
import {
  useCausalModel,
  useGenerateCausalModel,
  useUpdateNodeSelections,
  useRunBatchSimulation,
  useSimulationResults,
} from '@/hooks/use-quantitative-analysis';
import { CausalDAGView } from './CausalDAGView';
import { LikertAssertions, buildCalibratableNodes } from './LikertAssertions';

interface QuantitativeAnalysisTabProps {
  experimentId: string;
}

export function QuantitativeAnalysisTab({ experimentId }: QuantitativeAnalysisTabProps) {
  const [activeNodeName, setActiveNodeName] = useState<string | null>(null);
  const [selectionsChanged, setSelectionsChanged] = useState(false);
  const [dagKey, setDagKey] = useState(0);

  const { data: model, isLoading, isError, error } = useCausalModel(experimentId);
  const generateMutation = useGenerateCausalModel();
  const nodeSelectionMutation = useUpdateNodeSelections(experimentId);
  const simulateMutation = useRunBatchSimulation();
  const { data: simulationRun } = useSimulationResults(experimentId);

  // Build calibratable nodes (interaction + outcome) for LikertAssertions
  const calibratableNodes = useMemo(
    () => buildCalibratableNodes(model?.node_metadata ?? null, model?.nodes),
    [model?.node_metadata, model?.nodes]
  );

  const handleGenerate = () => {
    generateMutation.mutate(experimentId, {
      onSuccess: () => {
        toast.success('Modelo causal gerado com sucesso');
        // Force full remount of Cytoscape after data settles
        setTimeout(() => setDagKey((k) => k + 1), 300);
      },
      onError: (err) => {
        const message = err instanceof Error ? err.message : 'Erro ao gerar modelo';
        toast.error('Falha na geração', { description: message });
      },
    });
  };

  const handleSimulate = () => {
    simulateMutation.mutate(experimentId, {
      onSuccess: (data) => {
        setSelectionsChanged(false);
        toast.success(
          `Batch concluído — ${data.n_scenarios} cenários simulados com ${data.n_synths} synths`
        );
      },
      onError: (err) => {
        const message = err instanceof Error ? err.message : 'Erro na simulação';
        toast.error('Falha na simulação', { description: message });
      },
    });
  };

  const handleNodeSelectionsChange = useCallback(
    (selections: Record<string, number>) => {
      setSelectionsChanged(true);
      nodeSelectionMutation.mutate(selections, {
        onError: (err) => {
          const message = err instanceof Error ? err.message : 'Erro ao salvar';
          toast.error('Erro ao salvar seleções', { description: message });
        },
      });
    },
    [nodeSelectionMutation]
  );

  const handleEdgeClick = useCallback((edgeId: string) => {
    setActiveNodeName((prev) => (prev === edgeId ? null : edgeId));
  }, []);

  const handleNodeClick = useCallback((nodeName: string) => {
    setActiveNodeName((prev) => (prev === nodeName ? null : nodeName));
  }, []);

  // Loading state
  if (isLoading) {
    return (
      <div className="text-center py-12">
        <Loader2 className="w-8 h-8 text-violet-500 mx-auto mb-3 animate-spin" />
        <p className="text-slate-500">Carregando modelo causal...</p>
      </div>
    );
  }

  // Error state
  const is404 = (error as any)?.status === 404 || error?.message?.includes('No causal model');
  if (isError && error && !is404) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="w-10 h-10 text-red-300 mx-auto mb-3" />
        <p className="text-red-600 font-medium mb-2">Erro ao carregar modelo</p>
        <p className="text-sm text-slate-500 mb-4">{error.message}</p>
        <Button variant="outline" size="sm" onClick={handleGenerate}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Tentar novamente
        </Button>
      </div>
    );
  }

  // Empty state
  if (!model) {
    return (
      <div className="text-center py-12">
        <div className="mx-auto w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-100 to-indigo-100 flex items-center justify-center mb-4">
          <Sparkles className="w-8 h-8 text-violet-500" />
        </div>
        <h3 className="text-lg font-semibold text-slate-800 mb-2">
          Modelagem Causal
        </h3>
        <p className="text-slate-500 max-w-md mx-auto mb-6">
          Para iniciar este experimento, clique no botão abaixo.
          A IA criará nós demográficos, sensitividades, características de produto, interações e premissas para calibrar.
        </p>
        <Button
          onClick={handleGenerate}
          disabled={generateMutation.isPending}
          className="btn-primary"
        >
          {generateMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Gerando modelo...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 mr-2" />
              Gerar Modelo Causal
            </>
          )}
        </Button>
      </div>
    );
  }

  // Model loaded — DAG (left) + Premissas Causais (right)
  return (
    <div className="space-y-6">
      {/* Model header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-slate-800">{model.label}</h3>
          <p className="text-sm text-slate-500">
            {model.nodes.length} nós, {model.edges.length} arestas
            {calibratableNodes.length > 0 && ` · ${calibratableNodes.length} premissas`}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleGenerate}
          disabled={generateMutation.isPending}
          className="text-slate-600"
        >
          {generateMutation.isPending ? (
            <Loader2 className="w-4 h-4 mr-1 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4 mr-1" />
          )}
          Gerar novamente
        </Button>
      </div>

      {/* 2-column layout: DAG (left) + Premissas (right) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* DAG visualization — left column */}
        <div className="rounded-xl border border-slate-200 bg-white p-4 flex flex-col h-[600px]">
          <CausalDAGView
            key={dagKey}
            model={model}
            activeEdgeId={activeNodeName}
            onEdgeClick={handleEdgeClick}
            onNodeClick={handleNodeClick}
          />
        </div>

        {/* Right column: Premissas Causais */}
        {calibratableNodes.length > 0 && (
          <div className="rounded-xl border border-slate-200 bg-white p-4 h-[600px] overflow-y-auto">
            <LikertAssertions
              nodes={calibratableNodes}
              activeNodeName={activeNodeName}
              onNodeActivate={setActiveNodeName}
              onSelectionsChange={handleNodeSelectionsChange}
            />
          </div>
        )}
      </div>

      {/* Simulate button */}
      {(!simulationRun || selectionsChanged) && (
        <div className="flex items-center justify-end pt-2 border-t border-slate-100">
          <Button
            onClick={handleSimulate}
            disabled={simulateMutation.isPending}
            className="btn-primary"
          >
            {simulateMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Simulando cenários...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                {simulationRun ? 'Simular novamente' : 'Simular'}
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
}
