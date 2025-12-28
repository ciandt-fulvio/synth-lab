// frontend/src/components/experiments/results/PhaseSegmentation.tsx
// Phase 3: Persona Segmentation - Elbow, Radar, Dendrogram charts

import { useState } from 'react';
import { ChartContainer } from '@/components/shared/ChartContainer';
import { ElbowChart } from './charts/ElbowChart';
import { RadarComparisonChart } from './charts/RadarComparisonChart';
import { DendrogramChart } from './charts/DendrogramChart';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  useClustering,
  useCreateClustering,
  useElbowData,
  useDendrogram,
  useRadarComparison,
  useCutDendrogram,
} from '@/hooks/use-clustering';
import { Loader2, Play, Scissors } from 'lucide-react';

interface PhaseSegmentationProps {
  simulationId: string;
}

export function PhaseSegmentation({ simulationId }: PhaseSegmentationProps) {
  const [clusterMethod, setClusterMethod] = useState<'kmeans' | 'hierarchical'>('kmeans');
  const [numClusters, setNumClusters] = useState(3);
  const [cutHeight, setCutHeight] = useState<number | null>(null);

  // Fetch existing clustering data
  const clustering = useClustering(simulationId);
  const elbow = useElbowData(simulationId);
  const dendrogram = useDendrogram(simulationId);
  const radarComparison = useRadarComparison(simulationId);

  // Mutations
  const createClustering = useCreateClustering(simulationId);
  const cutDendrogramMutation = useCutDendrogram(simulationId);

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
      {/* Clustering Controls */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-4">
          Configuração de Clustering
        </h3>

        <Tabs value={clusterMethod} onValueChange={(v) => setClusterMethod(v as 'kmeans' | 'hierarchical')}>
          <TabsList className="grid w-full grid-cols-2 mb-4">
            <TabsTrigger value="kmeans">K-Means</TabsTrigger>
            <TabsTrigger value="hierarchical">Hierárquico</TabsTrigger>
          </TabsList>

          <TabsContent value="kmeans" className="space-y-4">
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

          <TabsContent value="hierarchical" className="space-y-4">
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
      </div>

      {/* Elbow Chart (for K-Means) */}
      {clusterMethod === 'kmeans' && (
        <ChartContainer
          title="Método Elbow"
          description="Ajuda a determinar o número ideal de clusters observando onde a curva 'dobra'"
          isLoading={elbow.isLoading}
          isError={elbow.isError}
          isEmpty={!elbow.data || elbow.data.length === 0}
          onRetry={() => elbow.refetch()}
          height={350}
        >
          {elbow.data && (
            <ElbowChart
              data={elbow.data}
              suggestedK={3} // Could be calculated from data
              onSelectK={handleSelectK}
            />
          )}
        </ChartContainer>
      )}

      {/* Dendrogram (for Hierarchical) */}
      {clusterMethod === 'hierarchical' && (
        <ChartContainer
          title="Dendrograma"
          description="Visualização hierárquica dos clusters - clique para definir altura de corte"
          isLoading={dendrogram.isLoading}
          isError={dendrogram.isError}
          isEmpty={!dendrogram.data}
          onRetry={() => dendrogram.refetch()}
          height={420}
        >
          {dendrogram.data && (
            <DendrogramChart
              data={dendrogram.data}
              onCutHeight={setCutHeight}
            />
          )}
        </ChartContainer>
      )}

      {/* Radar Comparison (shows when clusters exist) */}
      <ChartContainer
        title="Comparação de Perfis"
        description="Compara os atributos médios de cada cluster"
        isLoading={radarComparison.isLoading}
        isError={radarComparison.isError}
        isEmpty={!radarComparison.data || !hasClustering}
        emptyMessage={hasClustering ? 'Nenhum dado de comparação' : 'Gere clusters primeiro para ver a comparação'}
        onRetry={() => radarComparison.refetch()}
        height={450}
      >
        {radarComparison.data && (
          <RadarComparisonChart data={radarComparison.data} />
        )}
      </ChartContainer>
    </div>
  );
}
