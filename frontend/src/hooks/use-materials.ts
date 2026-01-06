/**
 * React Query hooks for experiment materials.
 *
 * Provides data fetching and mutation hooks for materials.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import * as materialsApi from '@/services/materials-api';
import type { MaterialType } from '@/types/material';
import { useState, useCallback } from 'react';

/**
 * Hook to list all materials for an experiment.
 */
export function useMaterials(experimentId: string) {
  return useQuery({
    queryKey: queryKeys.materials.list(experimentId),
    queryFn: () => materialsApi.listMaterials(experimentId),
    enabled: !!experimentId,
  });
}

/**
 * Hook to get material limits for an experiment.
 */
export function useMaterialLimits(experimentId: string) {
  return useQuery({
    queryKey: queryKeys.materials.limits(experimentId),
    queryFn: () => materialsApi.getMaterialLimits(experimentId),
    enabled: !!experimentId,
  });
}

/**
 * Hook to get a specific material.
 */
export function useMaterial(experimentId: string, materialId: string) {
  return useQuery({
    queryKey: queryKeys.materials.detail(experimentId, materialId),
    queryFn: () => materialsApi.getMaterial(experimentId, materialId),
    enabled: !!experimentId && !!materialId,
  });
}

/**
 * Hook to get presigned view URL for a material.
 */
export function useMaterialViewUrl(experimentId: string, materialId: string) {
  return useQuery({
    queryKey: queryKeys.materials.viewUrl(experimentId, materialId),
    queryFn: () => materialsApi.getViewUrl(experimentId, materialId),
    enabled: !!experimentId && !!materialId,
    // URLs expire, so refetch periodically
    staleTime: 30 * 60 * 1000, // 30 minutes
    refetchInterval: 45 * 60 * 1000, // 45 minutes
  });
}

/**
 * Hook to upload a material with progress tracking.
 */
export function useUploadMaterial(experimentId: string) {
  const queryClient = useQueryClient();
  const [progress, setProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState<boolean>(false);

  const mutation = useMutation({
    mutationFn: async ({
      file,
      materialType,
    }: {
      file: File;
      materialType: MaterialType;
    }) => {
      setIsUploading(true);
      setProgress(0);
      try {
        return await materialsApi.uploadMaterial(
          experimentId,
          file,
          materialType,
          setProgress
        );
      } finally {
        setIsUploading(false);
      }
    },
    onSuccess: () => {
      // Invalidate materials list and limits
      queryClient.invalidateQueries({
        queryKey: queryKeys.materials.list(experimentId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.materials.limits(experimentId),
      });
    },
  });

  return {
    ...mutation,
    progress,
    isUploading,
    resetProgress: () => setProgress(0),
  };
}

/**
 * Hook to upload multiple materials.
 */
export function useUploadMaterials(experimentId: string) {
  const queryClient = useQueryClient();
  const [uploads, setUploads] = useState<
    Map<string, { progress: number; status: 'pending' | 'uploading' | 'completed' | 'error'; error?: string }>
  >(new Map());

  const uploadFiles = useCallback(
    async (files: File[], materialType: MaterialType) => {
      // Initialize upload states
      const newUploads = new Map(uploads);
      for (const file of files) {
        newUploads.set(file.name, { progress: 0, status: 'pending' });
      }
      setUploads(newUploads);

      const results: { file: File; success: boolean; error?: string }[] = [];

      for (const file of files) {
        try {
          setUploads((prev) => {
            const next = new Map(prev);
            next.set(file.name, { progress: 0, status: 'uploading' });
            return next;
          });

          await materialsApi.uploadMaterial(experimentId, file, materialType, (progress) => {
            setUploads((prev) => {
              const next = new Map(prev);
              next.set(file.name, { progress, status: 'uploading' });
              return next;
            });
          });

          setUploads((prev) => {
            const next = new Map(prev);
            next.set(file.name, { progress: 100, status: 'completed' });
            return next;
          });

          results.push({ file, success: true });
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Upload failed';
          setUploads((prev) => {
            const next = new Map(prev);
            next.set(file.name, { progress: 0, status: 'error', error: message });
            return next;
          });
          results.push({ file, success: false, error: message });
        }
      }

      // Invalidate queries
      queryClient.invalidateQueries({
        queryKey: queryKeys.materials.list(experimentId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.materials.limits(experimentId),
      });

      return results;
    },
    [experimentId, queryClient, uploads]
  );

  const clearUploads = useCallback(() => {
    setUploads(new Map());
  }, []);

  return {
    uploads,
    uploadFiles,
    clearUploads,
  };
}

/**
 * Hook to reorder materials.
 */
export function useReorderMaterials(experimentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (materialIds: string[]) =>
      materialsApi.reorderMaterials(experimentId, { material_ids: materialIds }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.materials.list(experimentId),
      });
    },
  });
}

/**
 * Hook to delete a material.
 */
export function useDeleteMaterial(experimentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (materialId: string) =>
      materialsApi.deleteMaterial(experimentId, materialId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.materials.list(experimentId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.materials.limits(experimentId),
      });
    },
  });
}

/**
 * Hook to retry description generation.
 */
export function useRetryDescription(experimentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (materialId: string) =>
      materialsApi.retryDescription(experimentId, materialId),
    onSuccess: (_, materialId) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.materials.list(experimentId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.materials.detail(experimentId, materialId),
      });
    },
  });
}
