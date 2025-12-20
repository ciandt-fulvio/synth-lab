// src/hooks/use-topics.ts

import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import { listTopics, getTopic } from '@/services/topics-api';
import type { PaginationParams } from '@/types';

export function useTopicsList(params?: PaginationParams) {
  return useQuery({
    queryKey: [...queryKeys.topicsList, params],
    queryFn: () => listTopics(params),
  });
}

export function useTopicDetail(topicName: string | null) {
  return useQuery({
    queryKey: queryKeys.topicDetail(topicName || ''),
    queryFn: () => getTopic(topicName!),
    enabled: !!topicName,
  });
}
