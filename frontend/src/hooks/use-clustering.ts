// frontend/src/hooks/use-clustering.ts
// React Query hooks for clustering operations

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  getClustering,
  createClustering,
  getElbowData,
  getDendrogram,
  getClusterRadar,
  getRadarComparison,
  cutDendrogram,
} from '@/services/simulation-api';
import type { ClusterRequest, CutDendrogramRequest } from '@/types/simulation';

export function useClustering(simulationId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.simulation.clusters(simulationId),
    queryFn: () => getClustering(simulationId),
    enabled: !!simulationId && enabled,
    staleTime: 10 * 60 * 1000, // 10 minutes (clustering is expensive)
  });
}

export function useCreateClustering(simulationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ClusterRequest) => createClustering(simulationId, request),
    onSuccess: () => {
      // Invalidate clustering-related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.simulation.clusters(simulationId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.simulation.elbow(simulationId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.simulation.radarComparison(simulationId) });
    },
  });
}

export function useElbowData(simulationId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.simulation.elbow(simulationId),
    queryFn: () => getElbowData(simulationId),
    enabled: !!simulationId && enabled,
    staleTime: 10 * 60 * 1000,
  });
}

export function useDendrogram(simulationId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.simulation.dendrogram(simulationId),
    queryFn: () => getDendrogram(simulationId),
    enabled: !!simulationId && enabled,
    staleTime: 10 * 60 * 1000,
  });
}

export function useClusterRadar(
  simulationId: string,
  clusterId: number,
  enabled = true
) {
  return useQuery({
    queryKey: queryKeys.simulation.clusterRadar(simulationId, clusterId),
    queryFn: () => getClusterRadar(simulationId, clusterId),
    enabled: !!simulationId && clusterId >= 0 && enabled,
    staleTime: 10 * 60 * 1000,
  });
}

export function useRadarComparison(simulationId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.simulation.radarComparison(simulationId),
    queryFn: () => getRadarComparison(simulationId),
    enabled: !!simulationId && enabled,
    staleTime: 10 * 60 * 1000,
  });
}

export function useCutDendrogram(simulationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CutDendrogramRequest) => cutDendrogram(simulationId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.simulation.clusters(simulationId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.simulation.dendrogram(simulationId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.simulation.radarComparison(simulationId) });
    },
  });
}
