// src/hooks/use-synths.ts

import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import { listSynths, getSynth } from '@/services/synths-api';
import type { SynthsListParams } from '@/types';

export function useSynthsList(params?: SynthsListParams) {
  return useQuery({
    queryKey: [...queryKeys.synthsList, params],
    queryFn: () => listSynths(params),
  });
}

export function useSynthDetail(synthId: string | null) {
  return useQuery({
    queryKey: queryKeys.synthDetail(synthId || ''),
    queryFn: () => getSynth(synthId!),
    enabled: !!synthId,
  });
}
