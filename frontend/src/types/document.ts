/**
 * Document types for synth-lab.
 *
 * Types for experiment documents: summary, prfaq, executive_summary.
 */

export type DocumentType = 'summary' | 'prfaq' | 'executive_summary';
export type DocumentStatus = 'pending' | 'generating' | 'completed' | 'failed' | 'partial';

/**
 * Full document with content.
 */
export interface ExperimentDocument {
  id: string;
  experiment_id: string;
  document_type: DocumentType;
  markdown_content: string;
  metadata?: Record<string, unknown>;
  generated_at: string;
  model: string;
  status: DocumentStatus;
  error_message?: string;
}

/**
 * Document summary for listing (without content).
 */
export interface ExperimentDocumentSummary {
  id: string;
  document_type: DocumentType;
  status: DocumentStatus;
  generated_at: string;
  model: string;
}

/**
 * Document availability status.
 */
export interface DocumentAvailability {
  summary: { available: boolean; status: DocumentStatus | null };
  prfaq: { available: boolean; status: DocumentStatus | null };
  executive_summary: { available: boolean; status: DocumentStatus | null };
}

/**
 * Request to generate a document.
 */
export interface GenerateDocumentRequest {
  model?: string;
}

/**
 * Response after starting document generation.
 */
export interface GenerateDocumentResponse {
  document_id: string | null;
  status: DocumentStatus;
  message: string;
}

/**
 * Document type display labels (Portuguese).
 */
export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  summary: 'Resumo da Pesquisa',
  prfaq: 'PR-FAQ',
  executive_summary: 'Resumo Executivo',
};

/**
 * Document type icons (Lucide React icon names).
 */
export const DOCUMENT_TYPE_ICONS: Record<DocumentType, string> = {
  summary: 'FileText',
  prfaq: 'Newspaper',
  executive_summary: 'Sparkles',
};
