/**
 * HypothesisEditor page for editing hypothesis parameters.
 *
 * Allows users to view, edit, and version hypothesis distributions.
 *
 * References:
 *   - Spec: specs/035-causal-simulation/spec.md
 *   - Components: components/simulation/Hypothesis*
 */

import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import { HypothesisTable } from '@/components/simulation/HypothesisTable';
import { VersionSelector } from '@/components/simulation/VersionSelector';
import { useHypothesisEditor, useHypothesesAtVersion } from '@/hooks/use-hypotheses';
import { useSimulation } from '@/hooks/use-simulations';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Save,
  History,
  GitCompare,
  Loader2,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { toast } from 'sonner';
import type { HypothesisUpdateRequest } from '@/types/hypothesis';

/**
 * HypothesisEditor page component.
 */
export default function HypothesisEditor() {
  const { id: simulationId } = useParams<{ id: string }>();

  // Data hooks
  const { data: simulation } = useSimulation(simulationId || '');
  const {
    hypotheses,
    versions,
    isLoading,
    isLoadingVersions,
    updateHypothesis,
    saveVersion,
    compareVersions,
    isUpdating,
    isSavingVersion,
    comparisonResult,
  } = useHypothesisEditor(simulationId || '');

  const hypothesesAtVersionMutation = useHypothesesAtVersion();

  // Local state
  const [showSaveVersion, setShowSaveVersion] = useState(false);
  const [showVersionHistory, setShowVersionHistory] = useState(false);
  const [showCompare, setShowCompare] = useState(false);
  const [versionName, setVersionName] = useState('');
  const [versionDescription, setVersionDescription] = useState('');
  const [compareFrom, setCompareFrom] = useState<number | undefined>();
  const [compareTo, setCompareTo] = useState<number | undefined>();
  const [viewingVersion, setViewingVersion] = useState<number | undefined>();
  const [versionHypotheses, setVersionHypotheses] = useState<typeof hypotheses | null>(null);

  const handleUpdate = (variableName: string, request: HypothesisUpdateRequest) => {
    updateHypothesis(variableName, request);
    toast.success(`Atualizado ${variableName}`);
  };

  const handleSaveVersion = () => {
    if (!versionName.trim()) {
      toast.error('Nome da versão é obrigatório');
      return;
    }

    saveVersion({
      name: versionName.trim(),
      description: versionDescription.trim() || undefined,
    });
    toast.success('Versão salva');
    setShowSaveVersion(false);
    setVersionName('');
    setVersionDescription('');
  };

  const handleCompare = () => {
    if (compareFrom === undefined || compareTo === undefined) {
      toast.error('Selecione ambas as versões para comparar');
      return;
    }

    compareVersions({
      version_from: compareFrom,
      version_to: compareTo,
    });
  };

  const handleViewVersion = async (version: number) => {
    if (!simulationId) return;

    setViewingVersion(version);
    try {
      const result = await hypothesesAtVersionMutation.mutateAsync({
        simulationId,
        version,
      });
      setVersionHypotheses(result);
    } catch {
      toast.error('Erro ao carregar versão');
      setViewingVersion(undefined);
    }
  };

  const handleBackToLatest = () => {
    setViewingVersion(undefined);
    setVersionHypotheses(null);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <SynthLabHeader subtitle="Carregando..." backTo={`/simulations/${simulationId}`} />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="card p-8 text-center text-slate-500">Carregando hipóteses...</div>
        </main>
      </div>
    );
  }

  const displayHypotheses = viewingVersion !== undefined ? versionHypotheses : hypotheses;
  const currentVersion = hypotheses?.[0]?.version ?? 1;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader
        subtitle={`Editor de Hipóteses - ${simulation?.question_text || 'Simulação'}`}
        backTo={`/simulations/${simulationId}`}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowCompare(true)}
              disabled={!versions || versions.length < 2}
            >
              <GitCompare className="h-4 w-4 mr-2" />
              Comparar
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowVersionHistory(true)}
            >
              <History className="h-4 w-4 mr-2" />
              Histórico ({versions?.length || 0})
            </Button>
            <Button
              size="sm"
              onClick={() => setShowSaveVersion(true)}
              disabled={isSavingVersion}
              className="btn-primary"
            >
              {isSavingVersion ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              Salvar Versão
            </Button>
          </div>
        }
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Version Banner */}
        {viewingVersion !== undefined && (
          <div className="mb-6 bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-amber-600" />
              <span className="text-amber-800">
                Visualizando versão {viewingVersion} (somente leitura)
              </span>
            </div>
            <Button variant="outline" size="sm" onClick={handleBackToLatest}>
              Voltar para Atual (v{currentVersion})
            </Button>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="card p-4">
            <div className="text-sm text-slate-500">Variáveis</div>
            <div className="text-2xl font-semibold text-slate-900">
              {displayHypotheses?.length || 0}
            </div>
          </div>
          <div className="card p-4">
            <div className="text-sm text-slate-500">Versão Atual</div>
            <div className="text-2xl font-semibold text-slate-900">
              v{viewingVersion ?? currentVersion}
            </div>
          </div>
          <div className="card p-4">
            <div className="text-sm text-slate-500">Versões Salvas</div>
            <div className="text-2xl font-semibold text-slate-900">
              {versions?.length || 0}
            </div>
          </div>
          <div className="card p-4">
            <div className="text-sm text-slate-500">Status</div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <span className="text-green-700 font-medium">Pronto</span>
            </div>
          </div>
        </div>

        {/* Hypothesis Table */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-section-title">Parâmetros de Distribuição</h2>
            {versions && versions.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-500">Ir para versão:</span>
                <VersionSelector
                  versions={versions}
                  value={viewingVersion ?? currentVersion}
                  onChange={handleViewVersion}
                  disabled={hypothesesAtVersionMutation.isPending}
                />
              </div>
            )}
          </div>

          {displayHypotheses && displayHypotheses.length > 0 ? (
            <HypothesisTable
              hypotheses={displayHypotheses}
              onUpdate={handleUpdate}
              readOnly={viewingVersion !== undefined}
              isUpdating={isUpdating}
            />
          ) : (
            <div className="text-center text-slate-500 py-8">
              Nenhuma hipótese disponível. Execute uma simulação para gerar hipóteses.
            </div>
          )}
        </div>
      </main>

      {/* Save Version Dialog */}
      <Dialog open={showSaveVersion} onOpenChange={setShowSaveVersion}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Salvar Versão de Hipóteses</DialogTitle>
            <DialogDescription>
              Salve os parâmetros atuais das hipóteses como uma versão nomeada para referência futura.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Nome da Versão</Label>
              <Input
                value={versionName}
                onChange={(e) => setVersionName(e.target.value)}
                placeholder="ex: Baseline, Otimista, Conservadora"
              />
            </div>
            <div className="space-y-2">
              <Label>Descrição (opcional)</Label>
              <Textarea
                value={versionDescription}
                onChange={(e) => setVersionDescription(e.target.value)}
                placeholder="Descreva as mudanças nesta versão..."
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSaveVersion(false)}>
              Cancelar
            </Button>
            <Button onClick={handleSaveVersion} disabled={!versionName.trim()}>
              Salvar Versão
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Version History Dialog */}
      <Dialog open={showVersionHistory} onOpenChange={setShowVersionHistory}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Histórico de Versões</DialogTitle>
            <DialogDescription>
              Visualize e restaure versões anteriores das hipóteses.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2 max-h-80 overflow-y-auto py-4">
            {versions?.map((version) => (
              <div
                key={version.version}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  version.version === (viewingVersion ?? currentVersion)
                    ? 'bg-indigo-50 border-indigo-200'
                    : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
                }`}
                onClick={() => {
                  handleViewVersion(version.version);
                  setShowVersionHistory(false);
                }}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium">v{version.version}</span>
                    {version.name && (
                      <span className="ml-2 text-slate-600">- {version.name}</span>
                    )}
                    {version.version === currentVersion && (
                      <span className="ml-2 text-xs text-indigo-600">(atual)</span>
                    )}
                  </div>
                  <span className="text-xs text-slate-500">
                    {new Date(version.created_at).toLocaleString()}
                  </span>
                </div>
                {version.description && (
                  <p className="text-sm text-slate-500 mt-1">{version.description}</p>
                )}
              </div>
            ))}
            {(!versions || versions.length === 0) && (
              <div className="text-center text-slate-500 py-4">
                Nenhuma versão salva ainda
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowVersionHistory(false)}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Compare Versions Dialog */}
      <Dialog open={showCompare} onOpenChange={setShowCompare}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Comparar Versões</DialogTitle>
            <DialogDescription>
              Compare os parâmetros das hipóteses entre duas versões.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Versão Base</Label>
                {versions && (
                  <VersionSelector
                    versions={versions}
                    value={compareFrom}
                    onChange={setCompareFrom}
                    placeholder="Selecione a versão base..."
                  />
                )}
              </div>
              <div className="space-y-2">
                <Label>Comparar com</Label>
                {versions && (
                  <VersionSelector
                    versions={versions}
                    value={compareTo}
                    onChange={setCompareTo}
                    placeholder="Selecione a versão para comparar..."
                  />
                )}
              </div>
            </div>

            <Button
              onClick={handleCompare}
              disabled={compareFrom === undefined || compareTo === undefined}
              className="w-full"
            >
              Comparar
            </Button>

            {/* Comparison Results */}
            {comparisonResult && (
              <div className="mt-4 space-y-2">
                <h4 className="font-medium text-slate-900">Resultados da Comparação</h4>
                {comparisonResult.changes.length === 0 ? (
                  <div className="text-slate-500 text-sm">Nenhuma diferença encontrada</div>
                ) : (
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {comparisonResult.changes.map((change, i) => (
                      <div
                        key={i}
                        className="p-3 rounded-lg bg-slate-50 border border-slate-200"
                      >
                        <div className="font-medium text-slate-900">
                          {change.variable_name}
                        </div>
                        <div className="text-sm text-slate-600 mt-1">
                          <span className="text-red-600">
                            {change.field}: {JSON.stringify(change.old_value)}
                          </span>
                          {' → '}
                          <span className="text-green-600">
                            {JSON.stringify(change.new_value)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCompare(false)}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
