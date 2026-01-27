/**
 * DAGEditor - Simplified fullscreen causal DAG editor.
 *
 * Clean interface focused on the graph visualization with top toolbar for actions.
 */

import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { ReactFlowProvider } from 'reactflow';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import { DAGVisualization } from '@/components/simulation/DAGVisualization';
import { useSimulation } from '@/hooks/use-simulations';
import { useDAGEditor } from '@/hooks/use-dag';
import { Button } from '@/components/ui/button';
import {
  CheckCircle2,
  AlertCircle,
  History,
  Loader2,
  Info,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import type { Variable, Edge } from '@/types/causal-dag';

export default function DAGEditor() {
  const { id: simulationId } = useParams<{ id: string }>();

  // Data hooks
  const { data: simulation } = useSimulation(simulationId || '');
  const {
    dag,
    versions,
    isLoading,
    addNode,
    removeNode,
    addEdge,
    removeEdge,
    validateDAG,
    savePositions,
    isUpdating,
    isValidating,
    validationResult,
  } = useDAGEditor(simulationId || '');

  // Local state
  const [showVersions, setShowVersions] = useState(false);
  const [showInfo, setShowInfo] = useState(false);

  const handleAddEdge = (edge: Edge) => {
    addEdge(edge);
    toast.success('Relação adicionada');
  };

  const handleRemoveEdge = (source: string, target: string) => {
    removeEdge(source, target);
    toast.success('Relação removida');
  };

  const handleValidate = () => {
    if (!dag) return;
    validateDAG({ nodes: dag.nodes, edges: dag.edges });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <SynthLabHeader subtitle="Carregando..." backTo={`/simulations/${simulationId}`} />
        <main className="flex items-center justify-center h-[80vh]">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        </main>
      </div>
    );
  }

  if (!dag) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <SynthLabHeader subtitle="Não Encontrado" backTo={`/simulations/${simulationId}`} />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="card p-8 text-center text-slate-500">Modelo não encontrado</div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader
        subtitle="Modelo Causal"
        backTo={`/simulations/${simulationId}`}
        actions={
          <div className="flex items-center gap-2">
            {/* Info button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowInfo(true)}
            >
              <Info className="h-4 w-4" />
            </Button>

            {/* Versions button */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowVersions(true)}
            >
              <History className="h-4 w-4 mr-2" />
              v{dag.version}
            </Button>

            {/* Validate button */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleValidate}
              disabled={isValidating}
              className={
                validationResult
                  ? validationResult.valid
                    ? 'border-green-500 text-green-700'
                    : 'border-red-500 text-red-700'
                  : ''
              }
            >
              {isValidating ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : validationResult?.valid ? (
                <CheckCircle2 className="h-4 w-4 mr-2" />
              ) : validationResult ? (
                <AlertCircle className="h-4 w-4 mr-2" />
              ) : (
                <CheckCircle2 className="h-4 w-4 mr-2" />
              )}
              Validar
            </Button>
          </div>
        }
      />

      {/* Fullscreen DAG */}
      <main className="h-[calc(100vh-80px)]">
        <ReactFlowProvider>
          <DAGVisualization
            dag={dag}
            editable={false}
            onAddEdge={handleAddEdge}
            onDeleteEdge={handleRemoveEdge}
            onSavePositions={savePositions}
            height="100%"
          />
        </ReactFlowProvider>
      </main>

      {/* Validation Errors Toast */}
      {validationResult && !validationResult.valid && (
        <div className="fixed bottom-6 right-6 max-w-md bg-white border-2 border-red-500 rounded-lg shadow-xl p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h4 className="font-semibold text-red-800 mb-1">Modelo Inválido</h4>
              <ul className="text-sm text-red-700 space-y-1">
                {validationResult.errors.slice(0, 3).map((error, i) => (
                  <li key={i} className="flex items-start gap-1">
                    <span className="text-red-500">•</span>
                    <span>{error}</span>
                  </li>
                ))}
                {validationResult.errors.length > 3 && (
                  <li className="text-red-600 font-medium">
                    +{validationResult.errors.length - 3} more errors
                  </li>
                )}
              </ul>
            </div>
            <button
              onClick={() => validateDAG({ nodes: [], edges: [] })}
              className="text-slate-400 hover:text-slate-600"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Version History Dialog */}
      <Dialog open={showVersions} onOpenChange={setShowVersions}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Histórico de Versões</DialogTitle>
            <DialogDescription>
              Versões anteriores do modelo causal
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2 max-h-80 overflow-y-auto py-4">
            {versions?.map((version) => (
              <div
                key={version.version}
                className={`p-3 rounded-lg border transition-colors ${
                  version.version === dag.version
                    ? 'bg-indigo-50 border-indigo-200'
                    : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-semibold text-slate-900">
                      Versão {version.version}
                    </span>
                    {version.version === dag.version && (
                      <span className="ml-2 text-xs font-medium text-indigo-600 bg-indigo-100 px-2 py-0.5 rounded">
                        atual
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-slate-500">
                    {new Date(version.created_at).toLocaleDateString('pt-BR')}
                  </span>
                </div>
                <p className="text-sm text-slate-600 mt-1">
                  {version.node_count} variáveis • {version.edge_count} relações
                </p>
              </div>
            ))}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowVersions(false)}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Info Dialog */}
      <Dialog open={showInfo} onOpenChange={setShowInfo}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Modelo Causal - Informações</DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div>
              <h4 className="font-semibold text-slate-900 mb-2">Estrutura</h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-slate-50 rounded p-3">
                  <div className="text-2xl font-bold text-slate-900">{dag.nodes.length}</div>
                  <div className="text-xs text-slate-600">Variáveis</div>
                </div>
                <div className="bg-slate-50 rounded p-3">
                  <div className="text-2xl font-bold text-slate-900">{dag.edges.length}</div>
                  <div className="text-xs text-slate-600">Relações</div>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-semibold text-slate-900 mb-2">Tipos de Variáveis</h4>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-sm bg-emerald-500" />
                  <span className="text-sm text-slate-700">
                    <strong>Input:</strong> Variáveis de entrada/intervenção
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-sm bg-blue-500" />
                  <span className="text-sm text-slate-700">
                    <strong>Process:</strong> Variáveis intermediárias
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-sm bg-violet-500" />
                  <span className="text-sm text-slate-700">
                    <strong>Output:</strong> Variáveis de resultado
                  </span>
                </div>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowInfo(false)}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
