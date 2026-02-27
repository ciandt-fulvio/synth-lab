/**
 * Centralized query keys for React Query.
 *
 * This ensures consistent cache invalidation across the application.
 */

export const queryKeys = {
  // Tags
  tags: () => ['tags'] as const,

  // Experiments
  experiments: () => ['experiments'] as const,
  experimentsList: ['experiments'] as const,
  experimentDetail: (id: string) => ['experiments', id] as const,

  // Synths
  synthsList: ['synths'] as const,
  synthDetail: (id: string) => ['synths', id] as const,

  // Synth Groups
  synthGroupsList: ['synth-groups'] as const,
  synthGroupDetail: (id: string) => ['synth-groups', id] as const,
  synthGroupStatistics: (id: string) => ['synth-groups', id, 'statistics'] as const,

  // Research
  researchList: ['research'] as const,
  researchDetail: (execId: string) => ['research', execId] as const,
  researchTranscripts: (execId: string) => ['research', execId, 'transcripts'] as const,
  researchTranscript: (execId: string, synthId: string) => ['research', execId, 'transcripts', synthId] as const,
  autoInterview: (experimentId: string) => ['auto-interview', experimentId] as const,

  // Research Documents
  researchDocuments: {
    summary: (execId: string) => ['research', execId, 'documents', 'summary'] as const,
    prfaq: (execId: string) => ['research', execId, 'documents', 'prfaq'] as const,
  },

  // Documents
  documents: {
    list: (experimentId: string) => ['documents', experimentId, 'list'] as const,
    availability: (experimentId: string) => ['documents', experimentId, 'availability'] as const,
    detail: (experimentId: string, documentType: string) => ['documents', experimentId, documentType] as const,
    markdown: (experimentId: string, documentType: string) => ['documents', experimentId, documentType, 'markdown'] as const,
  },

  // Quantitative Analysis
  quantitativeAnalysis: {
    model: (experimentId: string) => ['quantitative-analysis', experimentId, 'model'] as const,
    results: (experimentId: string) => ['quantitative-analysis', experimentId, 'results'] as const,
    report: (experimentId: string) => ['quantitative-analysis', experimentId, 'report'] as const,
  },

  // Sharing
  experimentShares: (experimentId: string) => ['experiments', experimentId, 'shares'] as const,
  synthGroupShares: (synthGroupId: string) => ['synth-groups', synthGroupId, 'shares'] as const,

  // Materials
  materials: {
    list: (experimentId: string) => ['materials', experimentId, 'list'] as const,
    limits: (experimentId: string) => ['materials', experimentId, 'limits'] as const,
    detail: (experimentId: string, materialId: string) => ['materials', experimentId, materialId] as const,
    viewUrl: (experimentId: string, materialId: string) => ['materials', experimentId, materialId, 'view-url'] as const,
  },
};
