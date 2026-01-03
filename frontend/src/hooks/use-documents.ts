/**
 * React Query hooks for experiment documents.
 *
 * Provides data fetching and mutation hooks for documents.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import * as documentsApi from '@/services/documents-api';
import type { DocumentType } from '@/types/document';

/**
 * Hook to list all documents for an experiment.
 */
export function useDocuments(experimentId: string) {
  return useQuery({
    queryKey: queryKeys.documents.list(experimentId),
    queryFn: () => documentsApi.listDocuments(experimentId),
    enabled: !!experimentId,
  });
}

/**
 * Hook to check document availability for an experiment.
 * Automatically polls every second when any document is being generated.
 */
export function useDocumentAvailability(experimentId: string) {
  return useQuery({
    queryKey: queryKeys.documents.availability(experimentId),
    queryFn: () => documentsApi.checkAvailability(experimentId),
    enabled: !!experimentId,
    refetchInterval: (query) => {
      // Poll every second if any document is generating
      const data = query.state.data;
      if (data) {
        const hasGenerating = Object.values(data).some(
          (doc: any) => doc?.status === 'generating'
        );
        return hasGenerating ? 1000 : false;
      }
      return false;
    },
  });
}

/**
 * Hook to get a specific document.
 * Returns undefined (not error) when document doesn't exist (404).
 *
 * @param sourceId - Required for exploration/research documents (exploration_id or exec_id)
 */
export function useDocument(
  experimentId: string,
  documentType: DocumentType,
  sourceId?: string
) {
  return useQuery({
    queryKey: [...queryKeys.documents.detail(experimentId, documentType), sourceId],
    queryFn: async () => {
      try {
        return await documentsApi.getDocument(experimentId, documentType, sourceId);
      } catch (error) {
        // Treat 404 as "no document" instead of error
        if (error instanceof Error && error.message.includes('404')) {
          return undefined;
        }
        throw error;
      }
    },
    enabled: !!experimentId && !!documentType,
  });
}

/**
 * Hook to get document markdown content.
 *
 * @param sourceId - Required for exploration/research documents (exploration_id or exec_id)
 */
export function useDocumentMarkdown(
  experimentId: string,
  documentType: DocumentType,
  options?: { enabled?: boolean; sourceId?: string }
) {
  return useQuery({
    queryKey: [...queryKeys.documents.markdown(experimentId, documentType), options?.sourceId],
    queryFn: () => documentsApi.getDocumentMarkdown(experimentId, documentType, options?.sourceId),
    enabled: options?.enabled !== false && !!experimentId && !!documentType,
  });
}

/**
 * Hook to generate a document.
 */
export function useGenerateDocument(experimentId: string, documentType: DocumentType) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (model?: string) =>
      documentsApi.generateDocument(experimentId, documentType, model ? { model } : undefined),
    onSuccess: () => {
      // Invalidate related queries
      queryClient.invalidateQueries({
        queryKey: queryKeys.documents.list(experimentId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.documents.availability(experimentId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.documents.detail(experimentId, documentType),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.documents.markdown(experimentId, documentType),
      });
    },
  });
}

/**
 * Hook to delete a document.
 */
export function useDeleteDocument(experimentId: string, documentType: DocumentType) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => documentsApi.deleteDocument(experimentId, documentType),
    onSuccess: () => {
      // Invalidate related queries
      queryClient.invalidateQueries({
        queryKey: queryKeys.documents.list(experimentId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.documents.availability(experimentId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.documents.detail(experimentId, documentType),
      });
    },
  });
}
