// src/hooks/use-research.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  listExecutions,
  getExecution,
  getTranscripts,
  executeResearch,
} from '@/services/research-api';
import type {
  PaginationParams,
  ResearchExecuteRequest,
} from '@/types';

export function useResearchList(params?: PaginationParams) {
  return useQuery({
    queryKey: [...queryKeys.researchList, params],
    queryFn: () => listExecutions(params),
  });
}

export function useResearchDetail(execId: string) {
  return useQuery({
    queryKey: queryKeys.researchDetail(execId),
    queryFn: () => getExecution(execId),
    enabled: !!execId,
  });
}

export function useResearchTranscripts(execId: string, params?: PaginationParams) {
  return useQuery({
    queryKey: [...queryKeys.researchTranscripts(execId), params],
    queryFn: () => getTranscripts(execId, params),
    enabled: !!execId,
  });
}

export function useExecuteResearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ResearchExecuteRequest) => executeResearch(request),
    onSuccess: () => {
      // Invalidate research list to show the new execution
      queryClient.invalidateQueries({ queryKey: queryKeys.researchList });
    },
  });
}
