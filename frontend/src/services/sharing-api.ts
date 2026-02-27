/**
 * Sharing API service.
 *
 * API client for sharing experiments and synth groups.
 *
 * References:
 *   - Types: src/types/sharing.ts
 */

import { fetchAPI } from './api';
import type { ShareResultResponse, ShareListResponse } from '@/types/sharing';

/**
 * Share an experiment by email.
 */
export async function shareExperiment(
  experimentId: string,
  email: string,
): Promise<ShareResultResponse> {
  return fetchAPI<ShareResultResponse>(`/auth/experiments/${experimentId}/shares`, {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

/**
 * List all shares and pending invites for an experiment.
 */
export async function listExperimentShares(
  experimentId: string,
): Promise<ShareListResponse> {
  return fetchAPI<ShareListResponse>(`/auth/experiments/${experimentId}/shares`);
}

/**
 * Revoke experiment access by email.
 */
export async function revokeExperimentShare(
  experimentId: string,
  email: string,
): Promise<void> {
  return fetchAPI<void>(
    `/auth/experiments/${experimentId}/shares?email=${encodeURIComponent(email)}`,
    { method: 'DELETE' },
  );
}

/**
 * Share a synth group by email.
 */
export async function shareSynthGroup(
  synthGroupId: string,
  email: string,
): Promise<ShareResultResponse> {
  return fetchAPI<ShareResultResponse>(`/auth/synth-groups/${synthGroupId}/shares`, {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

/**
 * List all shares and pending invites for a synth group.
 */
export async function listSynthGroupShares(
  synthGroupId: string,
): Promise<ShareListResponse> {
  return fetchAPI<ShareListResponse>(`/auth/synth-groups/${synthGroupId}/shares`);
}

/**
 * Revoke synth group access by email.
 */
export async function revokeSynthGroupShare(
  synthGroupId: string,
  email: string,
): Promise<void> {
  return fetchAPI<void>(
    `/auth/synth-groups/${synthGroupId}/shares?email=${encodeURIComponent(email)}`,
    { method: 'DELETE' },
  );
}
