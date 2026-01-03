// src/hooks/use-research.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  listExecutions,
  getExecution,
  getTranscripts,
  executeResearch,
  getResearchSummary,
  getResearchPRFAQ,
  generateResearchSummary,
  generateResearchPRFAQ,
  deleteResearchSummary,
  deleteResearchPRFAQ,
} from '@/services/research-api';
import type {
  PaginationParams,
  ResearchExecuteRequest,
} from '@/types';
import type { ExperimentDocument } from '@/types/document';

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

// =============================================================================
// Research Document Hooks
// =============================================================================

/**
 * Get research summary document.
 * Returns null if not generated yet.
 */
export function useResearchSummary(execId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.researchDocuments.summary(execId),
    queryFn: () => getResearchSummary(execId),
    enabled: enabled && !!execId,
    retry: false, // 404 expected for new executions
  });
}

/**
 * Generate research summary document.
 */
export function useGenerateResearchSummary() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (execId: string) => generateResearchSummary(execId),
    onSuccess: (document: ExperimentDocument, execId: string) => {
      // Update cache with new document
      queryClient.setQueryData(
        queryKeys.researchDocuments.summary(execId),
        document
      );
    },
  });
}

/**
 * Delete research summary document.
 */
export function useDeleteResearchSummary() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (execId: string) => deleteResearchSummary(execId),
    onSuccess: (_: void, execId: string) => {
      // Clear cache
      queryClient.setQueryData(
        queryKeys.researchDocuments.summary(execId),
        null
      );
    },
  });
}

/**
 * Get research PRFAQ document.
 * Returns null if not generated yet.
 */
export function useResearchPRFAQ(execId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.researchDocuments.prfaq(execId),
    queryFn: () => getResearchPRFAQ(execId),
    enabled: enabled && !!execId,
    retry: false, // 404 expected for new executions
  });
}

/**
 * Generate research PRFAQ document.
 */
export function useGenerateResearchPRFAQ() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (execId: string) => generateResearchPRFAQ(execId),
    onSuccess: (document: ExperimentDocument, execId: string) => {
      // Update cache with new document
      queryClient.setQueryData(
        queryKeys.researchDocuments.prfaq(execId),
        document
      );
    },
  });
}

/**
 * Delete research PRFAQ document.
 */
export function useDeleteResearchPRFAQ() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (execId: string) => deleteResearchPRFAQ(execId),
    onSuccess: (_: void, execId: string) => {
      // Clear cache
      queryClient.setQueryData(
        queryKeys.researchDocuments.prfaq(execId),
        null
      );
    },
  });
}
