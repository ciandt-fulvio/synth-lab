/**
 * DAGValidationStep component for simulation wizard.
 *
 * Displays the generated DAG for user review with link to full editor.
 *
 * References:
 *   - Spec: specs/035-causal-simulation/spec.md
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ReactFlowProvider } from 'reactflow';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { DAGVisualization } from '@/components/simulation/DAGVisualization';
import { NodeDetailSheet } from '@/components/simulation/NodeDetailSheet';
import { ArrowRight, Edit2, Loader2, Network, AlertTriangle } from 'lucide-react';
import type { CausalDAG, Variable } from '@/types/causal-dag';
import type { Hypothesis, Relevance } from '@/types/hypothesis';
import { useUpdateHypothesis } from '@/hooks/use-simulations';

interface DAGValidationStepProps {
  simulationId: string;
  dag: CausalDAG | null;
  hypotheses?: Hypothesis[];
  isLoading: boolean;
  onConfirm: () => void;
  isConfirming: boolean;
  /** When true, hides edit/confirm buttons for reviewing completed steps */
  readOnly?: boolean;
}

/**
 * Step component for validating the generated DAG.
 */
export function DAGValidationStep({
  simulationId,
  dag,
  hypotheses,
  isLoading,
  onConfirm,
  isConfirming,
  readOnly = false,
}: DAGValidationStepProps) {
  const navigate = useNavigate();
  const [selectedVariable, setSelectedVariable] = useState<Variable | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const updateHypothesisMutation = useUpdateHypothesis();

  const selectedHypothesis = hypotheses?.find(
    (h) => h.variable_name === selectedVariable?.name
  ) ?? null;

  const handleEditNodeDetail = useCallback((variable: Variable) => {
    setSelectedVariable(variable);
    setSheetOpen(true);
  }, []);

  const handleSheetSave = useCallback(
    (data: { relevance: Relevance; range_min: number | null; range_max: number | null }) => {
      if (!selectedHypothesis) return;
      updateHypothesisMutation.mutate(
        {
          simulationId,
          hypothesisId: selectedHypothesis.id,
          data: {
            relevance: data.relevance,
            range_min: data.range_min,
            range_max: data.range_max,
          },
        },
        {
          onSuccess: () => {
            setSheetOpen(false);
            toast.success('Hipótese atualizada');
          },
          onError: (error) => {
            toast.error('Erro ao salvar', { description: String(error) });
          },
        }
      );
    },
    [selectedHypothesis, simulationId, updateHypothesisMutation]
  );

  const handleEditDAG = () => {
    navigate(`/simulations/${simulationId}/dag`);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (!dag) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 mx-auto text-amber-500 mb-4" />
        <h3 className="text-lg font-semibold text-slate-900 mb-2">Modelo não encontrado</h3>
        <p className="text-sm text-slate-600">
          O modelo causal ainda não foi gerado para esta simulação.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            {readOnly ? 'Modelo Causal' : 'Validar Modelo Causal'}
          </h2>
          {!readOnly && (
            <p className="text-sm text-slate-600 mt-1">
              Revise as relações de causa e efeito geradas. Você pode editar as variáveis e relações antes de continuar.
            </p>
          )}
        </div>
        {!readOnly && (
          <Button variant="outline" size="sm" onClick={handleEditDAG}>
            <Edit2 className="h-4 w-4 mr-1" />
            Editar Modelo
          </Button>
        )}
      </div>

      {/* DAG Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-slate-50 rounded-lg p-4 text-center">
          <Network className="h-5 w-5 mx-auto text-indigo-600 mb-2" />
          <p className="text-2xl font-bold text-slate-900">{dag.nodes?.length || 0}</p>
          <p className="text-xs text-slate-600">Variáveis</p>
        </div>
        <div className="bg-slate-50 rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-slate-900">{dag.edges?.length || 0}</p>
          <p className="text-xs text-slate-600">Relações</p>
        </div>
        <div className="bg-slate-50 rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-slate-900">v{dag.version || 1}</p>
          <p className="text-xs text-slate-600">Versão</p>
        </div>
      </div>

      {/* DAG Visualization */}
      <div className="border rounded-lg overflow-hidden bg-white">
        <div className="p-4 border-b bg-slate-50">
          <h3 className="text-sm font-medium text-slate-700">Grafo de Dependências</h3>
        </div>
        <div className="h-[400px]">
          <ReactFlowProvider>
            <DAGVisualization
              dag={dag}
              hypotheses={hypotheses}
              onEditNodeDetail={handleEditNodeDetail}
            />
          </ReactFlowProvider>
        </div>
      </div>

      {/* Assumptions and Risks */}
      {(dag.assumptions?.length > 0 || dag.risks?.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {dag.assumptions && dag.assumptions.length > 0 && (
            <div className="border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Suposições</h3>
              <ul className="space-y-2">
                {dag.assumptions.map((assumption, idx) => (
                  <li key={idx} className="text-sm text-slate-600">
                    <span className="font-medium text-slate-700">{assumption.assumption}</span>
                    <p className="text-xs text-slate-500 mt-1">{assumption.rationale}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {dag.risks && dag.risks.length > 0 && (
            <div className="border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Riscos Identificados</h3>
              <ul className="space-y-2">
                {dag.risks.map((risk, idx) => (
                  <li key={idx} className="text-sm text-slate-600">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          risk.impact === 'high'
                            ? 'bg-red-100 text-red-700'
                            : risk.impact === 'medium'
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        {risk.impact}
                      </span>
                      <span className="font-medium text-slate-700">{risk.risk}</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">{risk.mitigation}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {!readOnly && (
        <div className="flex justify-end pt-4 border-t">
          <Button onClick={onConfirm} disabled={isConfirming} className="btn-primary">
            {isConfirming ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Gerando Hipóteses...
              </>
            ) : (
              <>
                Confirmar e Gerar Hipóteses
                <ArrowRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      )}

      {/* Node detail sheet for editing relevance/range */}
      <NodeDetailSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        variable={selectedVariable}
        hypothesis={selectedHypothesis}
        onSave={handleSheetSave}
        isSaving={updateHypothesisMutation.isPending}
      />
    </div>
  );
}
