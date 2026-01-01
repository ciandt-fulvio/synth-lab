// src/services/prfaq-api.ts

import { fetchAPI } from './api';
import type {
  PRFAQSummary,
  PRFAQGenerateRequest,
  PRFAQGenerateResponse,
} from '@/types';

export async function getPrfaq(execId: string): Promise<PRFAQSummary> {
  return fetchAPI<PRFAQSummary>(`/prfaq/${execId}`);
}

export async function generatePrfaq(
  request: PRFAQGenerateRequest
): Promise<PRFAQGenerateResponse> {
  return fetchAPI<PRFAQGenerateResponse>('/prfaq/generate', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}
