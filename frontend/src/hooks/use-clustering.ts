// frontend/src/hooks/use-clustering.ts
// React Query hooks for experiment analysis clustering operations

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  getAnalysisClustering,
  createAnalysisClustering,
  getAnalysisElbow,
  getAnalysisRadarComparison,
} from '@/services/experiments-api';
import type { ClusterRequest } from '@/types/simulation';

export function useClustering(experimentId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.analysis.clusters(experimentId),
    queryFn: () => getAnalysisClustering(experimentId),
    enabled: !!experimentId && enabled,
    staleTime: 10 * 60 * 1000, // 10 minutes (clustering is expensive)
  });
}

export function useCreateClustering(experimentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ClusterRequest) => createAnalysisClustering(experimentId, request),
    onSuccess: () => {
      // Invalidate clustering-related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.analysis.clusters(experimentId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.analysis.elbow(experimentId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.analysis.radarComparison(experimentId) });
    },
  });
}

export function useElbowData(experimentId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.analysis.elbow(experimentId),
    queryFn: () => getAnalysisElbow(experimentId),
    enabled: !!experimentId && enabled,
    staleTime: 10 * 60 * 1000,
  });
}

export function useRadarComparison(experimentId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.analysis.radarComparison(experimentId),
    queryFn: () => getAnalysisRadarComparison(experimentId),
    enabled: !!experimentId && enabled,
    staleTime: 10 * 60 * 1000,
  });
}
