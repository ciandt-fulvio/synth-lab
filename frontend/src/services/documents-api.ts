/**
 * Documents API client for synth-lab.
 *
 * API calls for experiment documents (summary, prfaq, executive_summary).
 */

import { fetchAPI } from './api';
import type {
  DocumentAvailability,
  DocumentType,
  ExperimentDocument,
  ExperimentDocumentSummary,
  GenerateDocumentRequest,
  GenerateDocumentResponse,
} from '@/types/document';

/**
 * List all documents for an experiment.
 */
export async function listDocuments(
  experimentId: string
): Promise<ExperimentDocumentSummary[]> {
  return fetchAPI(`/experiments/${experimentId}/documents`);
}

/**
 * Check document availability for an experiment.
 */
export async function checkAvailability(
  experimentId: string
): Promise<DocumentAvailability> {
  return fetchAPI(`/experiments/${experimentId}/documents/availability`);
}

/**
 * Get a specific document by type.
 *
 * @param sourceId - Required for exploration/research documents (exploration_id or exec_id)
 */
export async function getDocument(
  experimentId: string,
  documentType: DocumentType,
  sourceId?: string
): Promise<ExperimentDocument> {
  const queryParams = sourceId ? `?source_id=${sourceId}` : '';
  return fetchAPI(`/experiments/${experimentId}/documents/${documentType}${queryParams}`);
}

/**
 * Get document markdown content only.
 *
 * @param sourceId - Required for exploration/research documents (exploration_id or exec_id)
 */
export async function getDocumentMarkdown(
  experimentId: string,
  documentType: DocumentType,
  sourceId?: string
): Promise<string> {
  const queryParams = sourceId ? `?source_id=${sourceId}` : '';
  const response = await fetch(
    `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/experiments/${experimentId}/documents/${documentType}/markdown${queryParams}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch document: ${response.statusText}`);
  }
  return response.text();
}

/**
 * Start document generation.
 *
 * @param sourceId - Required for exploration/research documents (exploration_id or exec_id)
 */
export async function generateDocument(
  experimentId: string,
  documentType: DocumentType,
  request?: GenerateDocumentRequest
): Promise<GenerateDocumentResponse> {
  return fetchAPI(`/experiments/${experimentId}/documents/${documentType}/generate`, {
    method: 'POST',
    body: JSON.stringify(request || {}),
  });
}

/**
 * Delete a document.
 *
 * @param sourceId - Required for exploration/research documents (exploration_id or exec_id)
 */
export async function deleteDocument(
  experimentId: string,
  documentType: DocumentType,
  sourceId?: string
): Promise<{ deleted: boolean; document_type: string }> {
  const queryParams = sourceId ? `?source_id=${sourceId}` : '';
  return fetchAPI(`/experiments/${experimentId}/documents/${documentType}${queryParams}`, {
    method: 'DELETE',
  });
}
