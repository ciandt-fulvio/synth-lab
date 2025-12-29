// frontend/src/components/experiments/results/PhaseSegmentation.tsx
// Phase 3: Persona Segmentation - Elbow, Radar, Dendrogram charts
// Composes section components with clustering controls

import { useState } from 'react';
import { HelpCircle, Play, Scissors, Loader2, Users } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  useAnalysisClustering,
  useCreateAnalysisClustering,
  useCutAnalysisDendrogram,
} from '@/hooks/use-analysis-charts';
import { ElbowSection } from './ElbowSection';
import { DendrogramSection } from './DendrogramSection';
import { RadarSection } from './RadarSection';

interface PhaseSegmentationProps {
  experimentId: string;
}

export function PhaseSegmentation({ experimentId }: PhaseSegmentationProps) {
  const [clusterMethod, setClusterMethod] = useState<'kmeans' | 'hierarchical'>('kmeans');
  const [numClusters, setNumClusters] = useState(3);
  const [cutHeight, setCutHeight] = useState<number | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);

  // Fetch existing clustering data
  const clustering = useAnalysisClustering(experimentId);

  // Mutations
  const createClustering = useCreateAnalysisClustering(experimentId);
  const cutDendrogramMutation = useCutAnalysisDendrogram(experimentId);

  const handleCreateClustering = () => {
    createClustering.mutate({
      method: clusterMethod,
      n_clusters: clusterMethod === 'kmeans' ? numClusters : undefined,
    });
  };

  const handleCutDendrogram = (height: number) => {
    setCutHeight(height);
    cutDendrogramMutation.mutate({ cut_height: height });
  };

  const handleSelectK = (k: number) => {
    setNumClusters(k);
  };

  const hasClustering = clustering.data !== null;
  const isLoading = createClustering.isPending || cutDendrogramMutation.isPending;

  return (
    <div className="space-y-6">
      {/* Clustering Controls Card */}
      <Card className="card">
        <CardHeader className="pb-2">
          <CardTitle className="text-card-title flex items-center gap-2">
            <Users className="h-4 w-4 text-slate-500" />
            Configuração de Clustering
          </CardTitle>
          <p className="text-meta">Configure e execute o agrupamento de synths em personas</p>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Explanation section - collapsible */}
          <Collapsible open={showExplanation} onOpenChange={setShowExplanation}>
            <div className="bg-gradient-to-r from-slate-50 to-indigo-50 border border-slate-200 rounded-lg p-3">
              <CollapsibleTrigger asChild>
                <Button
                  variant="ghost"
                  className="w-full flex items-center justify-between p-0 h-auto hover:bg-transparent"
                >
                  <div className="flex items-center gap-2 text-indigo-700">
                    <HelpCircle className="h-4 w-4" />
                    <span className="text-sm font-medium">O que é clustering?</span>
                  </div>
                  <span className="text-xs text-indigo-600">
                    {showExplanation ? 'Ocultar' : 'Ver explicação'}
                  </span>
                </Button>
              </CollapsibleTrigger>

              <CollapsibleContent className="mt-3 space-y-3 text-sm text-slate-700">
                <div>
                  <h4 className="font-semibold text-slate-800 mb-1 text-sm">Por que agrupar synths?</h4>
                  <p className="text-xs">
                    Clustering agrupa synths similares em <strong>personas</strong>. Isso ajuda a entender
                    os diferentes perfis de usuários e como cada grupo se comporta diferente.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-slate-800 mb-1 text-sm">K-Means vs Hierárquico</h4>
                  <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                    <li><strong>K-Means</strong>: Você escolhe quantos clusters (K). Rápido e simples.</li>
                    <li><strong>Hierárquico</strong>: Mostra a estrutura de agrupamento. Você corta onde quiser.</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-slate-800 mb-1 text-sm">Quantos clusters escolher?</h4>
                  <p className="text-xs">
                    Use o <strong>Método Elbow</strong> (K-Means) ou o <strong>Dendrograma</strong> (Hierárquico)
                    para decidir. Geralmente 3-5 clusters são suficientes para criar personas úteis.
                  </p>
                </div>
              </CollapsibleContent>
            </div>
          </Collapsible>

          {/* Clustering Method Tabs */}
          <Tabs value={clusterMethod} onValueChange={(v) => setClusterMethod(v as 'kmeans' | 'hierarchical')}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="kmeans">K-Means</TabsTrigger>
              <TabsTrigger value="hierarchical">Hierárquico</TabsTrigger>
            </TabsList>

            <TabsContent value="kmeans" className="space-y-4 pt-4">
              <div className="flex items-end gap-4">
                <div className="flex-1">
                  <Label htmlFor="numClusters">Número de Clusters (K)</Label>
                  <Input
                    id="numClusters"
                    type="number"
                    min={2}
                    max={10}
                    value={numClusters}
                    onChange={(e) => setNumClusters(parseInt(e.target.value) || 3)}
                    className="mt-1"
                  />
                </div>
                <Button
                  onClick={handleCreateClustering}
                  disabled={isLoading}
                  className="btn-primary"
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4 mr-2" />
                  )}
                  Gerar Clusters
                </Button>
              </div>
              <p className="text-xs text-slate-500">
                Use o gráfico Elbow abaixo para determinar o número ideal de clusters
              </p>
            </TabsContent>

            <TabsContent value="hierarchical" className="space-y-4 pt-4">
              <div className="flex items-end gap-4">
                <div className="flex-1">
                  <Label>Altura de Corte</Label>
                  <p className="text-sm text-slate-500 mt-1">
                    {cutHeight ? `Corte em h=${cutHeight.toFixed(2)}` : 'Clique no dendrograma para definir'}
                  </p>
                </div>
                <Button
                  onClick={() => cutHeight && handleCutDendrogram(cutHeight)}
                  disabled={isLoading || !cutHeight}
                  className="btn-primary"
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Scissors className="w-4 h-4 mr-2" />
                  )}
                  Cortar Dendrograma
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Elbow Chart (for K-Means) */}
      {clusterMethod === 'kmeans' && (
        <ElbowSection
          experimentId={experimentId}
          suggestedK={3}
          onSelectK={handleSelectK}
        />
      )}

      {/* Dendrogram (for Hierarchical) */}
      {clusterMethod === 'hierarchical' && (
        <DendrogramSection
          experimentId={experimentId}
          onCutHeight={setCutHeight}
        />
      )}

      {/* Radar Comparison (shows when clusters exist) */}
      <RadarSection
        experimentId={experimentId}
        hasClustering={hasClustering}
      />
    </div>
  );
}
