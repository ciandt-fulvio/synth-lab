// src/services/topics-api.ts

import { fetchAPI } from './api';
import type {
  PaginatedResponse,
  PaginationParams,
  TopicSummary,
  TopicDetail,
} from '@/types';

export async function listTopics(
  params?: PaginationParams
): Promise<PaginatedResponse<TopicSummary>> {
  const queryParams = new URLSearchParams();

  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.offset) queryParams.append('offset', params.offset.toString());

  const query = queryParams.toString();
  const endpoint = query ? `/topics/list?${query}` : '/topics/list';

  return fetchAPI<PaginatedResponse<TopicSummary>>(endpoint);
}

export async function getTopic(topicName: string): Promise<TopicDetail> {
  return fetchAPI<TopicDetail>(`/topics/${encodeURIComponent(topicName)}`);
}
