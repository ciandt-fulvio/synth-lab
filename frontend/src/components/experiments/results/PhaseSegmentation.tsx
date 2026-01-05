// frontend/src/components/experiments/results/PhaseSegmentation.tsx
// Phase 3: Persona Segmentation - Automatic K-Means with PCA and Radar

import { useEffect } from 'react';
import { Loader2, Users } from 'lucide-react';
import {
  useAnalysisClustering,
  useAutoAnalysisClustering,
} from '@/hooks/use-analysis-charts';
import { RadarSection } from './RadarSection';
import { PCAScatterSection } from './PCAScatterSection';

interface PhaseSegmentationProps {
  experimentId: string;
}

export function PhaseSegmentation({ experimentId }: PhaseSegmentationProps) {
  // Fetch existing clustering data
  const clustering = useAnalysisClustering(experimentId);

  // Auto-clustering mutation
  const autoClustering = useAutoAnalysisClustering(experimentId);

  // Automatically trigger K-Means clustering when page loads (if not already present)
  useEffect(() => {
    const hasKMeans = clustering.data?.method === 'kmeans';
    if (!hasKMeans && !clustering.isLoading && !autoClustering.isPending) {
      autoClustering.mutate();
    }
  }, [clustering.data, clustering.isLoading, autoClustering]);

  const hasKMeansClustering = !!clustering.data && clustering.data.method === 'kmeans';
  const isAutoClusteringRunning = autoClustering.isPending;

  // Show loading state while auto-clustering is running
  if (isAutoClusteringRunning) {
    return (
      <div className="space-y-6">
        <div className="card p-8">
          <div className="flex flex-col items-center justify-center gap-4 text-center">
            <div className="icon-box-primary">
              <Users className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-800 mb-2">
                Executando Clustering Automático
              </h3>
              <p className="text-sm text-slate-600 mb-4">
                Detectando número ideal de clusters e agrupando synths...
              </p>
              <Loader2 className="h-8 w-8 animate-spin text-indigo-600 mx-auto" />
            </div>
            <div className="text-xs text-slate-500 max-w-md">
              <p>
                O sistema está executando o Método Elbow para detectar automaticamente o número
                ideal de clusters (K) e em seguida gerando os agrupamentos via K-Means.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* PCA Scatter (K-Means only) */}
      <PCAScatterSection experimentId={experimentId} hasClustering={hasKMeansClustering} />

      {/* Radar Comparison (K-Means only) */}
      <RadarSection experimentId={experimentId} hasClustering={hasKMeansClustering} />
    </div>
  );
}
