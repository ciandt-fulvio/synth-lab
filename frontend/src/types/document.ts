/**
 * Document types for synth-lab.
 *
 * Types are specific to their source:
 * - exploration_*: Generated from exploration winning path
 * - research_*: Generated from interview research data
 * - executive_summary: Experiment-level summary combining all data
 */

export type DocumentType =
  | 'exploration_summary'
  | 'exploration_prfaq'
  | 'research_summary'
  | 'research_prfaq'
  | 'executive_summary';

export type DocumentStatus = 'pending' | 'generating' | 'completed' | 'failed' | 'partial';

/**
 * Full document with content.
 */
export interface ExperimentDocument {
  id: string;
  experiment_id: string;
  document_type: DocumentType;
  source_id?: string | null;
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
  source_id?: string | null;
  status: DocumentStatus;
  generated_at: string;
  model: string;
}

/**
 * Document availability status.
 */
export interface DocumentAvailability {
  // Exploration documents
  exploration_summary: { available: boolean; status: DocumentStatus | null };
  exploration_prfaq: { available: boolean; status: DocumentStatus | null };
  // Research documents (from interviews)
  research_summary: { available: boolean; status: DocumentStatus | null };
  research_prfaq: { available: boolean; status: DocumentStatus | null };
  // Experiment-level documents
  executive_summary: { available: boolean; status: DocumentStatus | null };
}

/**
 * Request to generate a document.
 */
export interface GenerateDocumentRequest {
  model?: string;
  source_id?: string;
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
  exploration_summary: 'Resumo da Exploração',
  exploration_prfaq: 'PR-FAQ da Exploração',
  research_summary: 'Resumo da Pesquisa',
  research_prfaq: 'PR-FAQ da Pesquisa',
  executive_summary: 'Resumo Executivo',
};

/**
 * Document type icons (Lucide React icon names).
 */
export const DOCUMENT_TYPE_ICONS: Record<DocumentType, string> = {
  exploration_summary: 'Network',
  exploration_prfaq: 'FileText',
  research_summary: 'Users',
  research_prfaq: 'Newspaper',
  executive_summary: 'Sparkles',
};
