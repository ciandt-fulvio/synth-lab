/**
 * useMechanisms hook.
 *
 * React Query hooks for mechanism configuration and narrative generation.
 *
 * References:
 *   - API: src/services/mechanisms-api.ts
 *   - Types: src/types/mechanisms.ts
 */

import { useQuery, useMutation } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  listMechanisms,
  listFeatureTypes,
  generateNarrative,
} from '@/services/mechanisms-api';
import type { GenerateNarrativeRequest } from '@/types/mechanisms';

/**
 * Hook to fetch all mechanism definitions with their options.
 *
 * @returns Query result with mechanisms list
 */
export function useMechanisms() {
  return useQuery({
    queryKey: queryKeys.mechanisms.list(),
    queryFn: listMechanisms,
    staleTime: 5 * 60 * 1000, // 5 minutes - mechanisms rarely change
  });
}

/**
 * Hook to fetch all feature types.
 *
 * @returns Query result with feature types list
 */
export function useFeatureTypes() {
  return useQuery({
    queryKey: queryKeys.mechanisms.featureTypes(),
    queryFn: listFeatureTypes,
    staleTime: 5 * 60 * 1000, // 5 minutes - feature types rarely change
  });
}

/**
 * Hook to generate narrative with mechanism placeholders.
 *
 * Usage:
 *   const generateNarrative = useGenerateNarrative();
 *
 *   const handleGenerate = async () => {
 *     const result = await generateNarrative.mutateAsync({
 *       name: 'Pix via WhatsApp',
 *       hypothesis: 'Usuários preferem pagar pelo app',
 *       description: 'Descrição opcional',
 *     });
 *     setNarrativeData(result);
 *   };
 *
 * @returns Mutation object for narrative generation
 */
export function useGenerateNarrative() {
  return useMutation({
    mutationFn: (request: GenerateNarrativeRequest) => generateNarrative(request),
  });
}
