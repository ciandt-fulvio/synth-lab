// frontend/src/hooks/use-outliers.ts
// React Query hooks for edge cases and outlier detection

import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import { getAnalysisExtremeCases, getAnalysisOutliers } from '@/services/experiments-api';

export function useExtremeCases(
  experimentId: string,
  nPerCategory = 10,
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.analysis.extremeCases(experimentId), nPerCategory],
    queryFn: () => getAnalysisExtremeCases(experimentId, nPerCategory),
    enabled: !!experimentId && enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useOutliers(
  experimentId: string,
  contamination = 0.1,
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.analysis.outliers(experimentId), contamination],
    queryFn: () => getAnalysisOutliers(experimentId, contamination),
    enabled: !!experimentId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}
