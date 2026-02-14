/**
 * QuantitativeAnalysisTab container component.
 *
 * Orchestrates the causal model + simulation workflow:
 * 1. Empty state → "Gerar Modelo" button
 * 2. Loading → spinner during LLM generation
 * 3. Model view → CausalDAGView + LikertAssertions side-by-side
 * 4. Simulate button → SimulationResults below model
 *
 * References:
 *   - Hooks: src/hooks/use-quantitative-analysis.ts
 *   - Components: CausalDAGView, LikertAssertions, SimulationResults
 */

import { useState, useCallback } from 'react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { BarChart3, Loader2, Play, RefreshCw, Sparkles } from 'lucide-react';
import {
  useCausalModel,
  useGenerateCausalModel,
  useUpdateEdgeSelections,
  useRunSimulation,
  useSimulationResults,
} from '@/hooks/use-quantitative-analysis';
import { CausalDAGView } from './CausalDAGView';
import { LikertAssertions } from './LikertAssertions';
import { SimulationResults } from './SimulationResults';

interface QuantitativeAnalysisTabProps {
  experimentId: string;
}

export function QuantitativeAnalysisTab({ experimentId }: QuantitativeAnalysisTabProps) {
  const [activeEdgeId, setActiveEdgeId] = useState<string | null>(null);

  const { data: model, isLoading, isError, error } = useCausalModel(experimentId);
  const generateMutation = useGenerateCausalModel();
  const updateMutation = useUpdateEdgeSelections(experimentId);
  const simulateMutation = useRunSimulation();
  const { data: simulationRun } = useSimulationResults(experimentId);

  const handleGenerate = () => {
    generateMutation.mutate(experimentId, {
      onSuccess: () => {
        toast.success('Modelo causal gerado com sucesso');
      },
      onError: (err) => {
        const message = err instanceof Error ? err.message : 'Erro ao gerar modelo';
        toast.error('Falha na geração', { description: message });
      },
    });
  };

  const handleSimulate = () => {
    simulateMutation.mutate(experimentId, {
      onSuccess: () => {
        toast.success('Simulação concluída');
      },
      onError: (err) => {
        const message = err instanceof Error ? err.message : 'Erro na simulação';
        toast.error('Falha na simulação', { description: message });
      },
    });
  };

  const handleSelectionsChange = useCallback(
    (selections: Record<string, number>) => {
      updateMutation.mutate(selections, {
        onError: (err) => {
          const message = err instanceof Error ? err.message : 'Erro ao salvar';
          toast.error('Erro ao salvar seleções', { description: message });
        },
      });
    },
    [updateMutation]
  );

  const handleEdgeClick = useCallback((edgeId: string) => {
    setActiveEdgeId((prev) => (prev === edgeId ? null : edgeId));
  }, []);

  const handleEdgeFocus = useCallback((edgeId: string | null) => {
    setActiveEdgeId(edgeId);
  }, []);

  // Loading state (initial fetch)
  if (isLoading) {
    return (
      <div className="text-center py-12">
        <Loader2 className="w-8 h-8 text-violet-500 mx-auto mb-3 animate-spin" />
        <p className="text-slate-500">Carregando modelo causal...</p>
      </div>
    );
  }

  // Error state (not 404 — real errors)
  if (isError && error && !error.message?.includes('404')) {
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

  // Empty state — no model yet or 404
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
          Gere um modelo causal (DAG) a partir do contexto do seu experimento.
          A IA criará nós, arestas e premissas para você calibrar.
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

  // Model loaded — show DAG + Likert + simulation
  return (
    <div className="space-y-6">
      {/* Model header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-slate-800">{model.label}</h3>
          <p className="text-sm text-slate-500">
            {model.nodes.length} nós, {model.edges.length} arestas
          </p>
        </div>
        <div className="flex items-center gap-2">
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
            Regenerar
          </Button>
          <Button
            size="sm"
            onClick={handleSimulate}
            disabled={simulateMutation.isPending}
            className="btn-primary"
          >
            {simulateMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                Simulando...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-1" />
                Simular
              </>
            )}
          </Button>
        </div>
      </div>

      {/* DAG + Likert side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* DAG visualization */}
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <CausalDAGView
            model={model}
            activeEdgeId={activeEdgeId}
            onEdgeClick={handleEdgeClick}
          />
        </div>

        {/* Likert assertions */}
        <div className="rounded-xl border border-slate-200 bg-white p-4 max-h-[500px] overflow-y-auto">
          <LikertAssertions
            edges={model.edges}
            activeEdgeId={activeEdgeId}
            onEdgeFocus={handleEdgeFocus}
            onSelectionsChange={handleSelectionsChange}
          />
        </div>
      </div>

      {/* Simulation results */}
      {simulateMutation.isPending && (
        <div className="text-center py-8 rounded-xl border border-slate-200 bg-white">
          <Loader2 className="w-8 h-8 text-indigo-500 mx-auto mb-3 animate-spin" />
          <p className="text-slate-600 font-medium">Executando simulação Monte Carlo...</p>
          <p className="text-sm text-slate-400 mt-1">Isso pode levar alguns segundos</p>
        </div>
      )}

      {simulationRun && !simulateMutation.isPending && (
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <SimulationResults run={simulationRun} />
        </div>
      )}
    </div>
  );
}
