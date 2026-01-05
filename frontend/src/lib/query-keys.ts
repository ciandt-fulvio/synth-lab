/**
 * Centralized query keys for React Query.
 *
 * This ensures consistent cache invalidation across the application.
 */

export const queryKeys = {
  // Experiments
  experimentsList: ['experiments'] as const,
  experimentDetail: (id: string) => ['experiments', id] as const,

  // Synths
  synthsList: ['synths'] as const,
  synthDetail: (id: string) => ['synths', id] as const,

  // Synth Groups
  synthGroupsList: ['synth-groups'] as const,
  synthGroupDetail: (id: string) => ['synth-groups', id] as const,

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

  // Analysis (experiment-based)
  analysis: {
    tryVsSuccess: (experimentId: string) => ['analysis', experimentId, 'try-vs-success'] as const,
    distribution: (experimentId: string) => ['analysis', experimentId, 'distribution'] as const,
    failureHeatmap: (experimentId: string) => ['analysis', experimentId, 'failure-heatmap'] as const,
    scatter: (experimentId: string) => ['analysis', experimentId, 'scatter'] as const,
    clusters: (experimentId: string) => ['analysis', experimentId, 'clusters'] as const,
    elbow: (experimentId: string) => ['analysis', experimentId, 'elbow'] as const,
    radarComparison: (experimentId: string) => ['analysis', experimentId, 'radar-comparison'] as const,
    pcaScatter: (experimentId: string) => ['analysis', experimentId, 'pca-scatter'] as const,
    extremeCases: (experimentId: string) => ['analysis', experimentId, 'extreme-cases'] as const,
    outliers: (experimentId: string) => ['analysis', experimentId, 'outliers'] as const,
    shapSummary: (experimentId: string) => ['analysis', experimentId, 'shap-summary'] as const,
    shapExplanation: (experimentId: string, synthId: string) => ['analysis', experimentId, 'shap', synthId] as const,
    pdp: (experimentId: string, feature: string) => ['analysis', experimentId, 'pdp', feature] as const,
    pdpComparison: (experimentId: string) => ['analysis', experimentId, 'pdp-comparison'] as const,
    insights: (experimentId: string) => ['analysis', experimentId, 'insights'] as const,
    sankeyFlow: (experimentId: string) => ['analysis', experimentId, 'sankey-flow'] as const,
  },

  // Simulation (simulation-based, legacy)
  simulation: {
    tryVsSuccess: (simulationId: string) => ['simulation', simulationId, 'try-vs-success'] as const,
    distribution: (simulationId: string) => ['simulation', simulationId, 'distribution'] as const,
    failureHeatmap: (simulationId: string) => ['simulation', simulationId, 'failure-heatmap'] as const,
    scatter: (simulationId: string) => ['simulation', simulationId, 'scatter'] as const,
    boxPlot: (simulationId: string) => ['simulation', simulationId, 'box-plot'] as const,
    clusters: (simulationId: string) => ['simulation', simulationId, 'clusters'] as const,
    elbow: (simulationId: string) => ['simulation', simulationId, 'elbow'] as const,
    clusterRadar: (simulationId: string, clusterId: number) => ['simulation', simulationId, 'cluster-radar', clusterId] as const,
    radarComparison: (simulationId: string) => ['simulation', simulationId, 'radar-comparison'] as const,
    extremeCases: (simulationId: string) => ['simulation', simulationId, 'extreme-cases'] as const,
    outliers: (simulationId: string) => ['simulation', simulationId, 'outliers'] as const,
    shapSummary: (simulationId: string) => ['simulation', simulationId, 'shap-summary'] as const,
    shapExplanation: (simulationId: string, synthId: string) => ['simulation', simulationId, 'shap', synthId] as const,
    pdp: (simulationId: string, feature: string) => ['simulation', simulationId, 'pdp', feature] as const,
    pdpComparison: (simulationId: string) => ['simulation', simulationId, 'pdp-comparison'] as const,
    insights: (simulationId: string) => ['simulation', simulationId, 'insights'] as const,
  },

  // Explorations
  explorationsList: (experimentId: string) => ['explorations', 'list', experimentId] as const,
  explorationDetail: (id: string) => ['explorations', 'detail', id] as const,
  explorationTree: (id: string) => ['explorations', 'tree', id] as const,
  explorationWinningPath: (id: string) => ['explorations', 'winning-path', id] as const,
  actionCatalog: ['explorations', 'catalog'] as const,

  // Exploration Documents
  explorationDocuments: {
    summary: (explorationId: string) => ['explorations', explorationId, 'documents', 'summary'] as const,
    prfaq: (explorationId: string) => ['explorations', explorationId, 'documents', 'prfaq'] as const,
  },

  // Documents
  documents: {
    list: (experimentId: string) => ['documents', experimentId, 'list'] as const,
    availability: (experimentId: string) => ['documents', experimentId, 'availability'] as const,
    detail: (experimentId: string, documentType: string) => ['documents', experimentId, documentType] as const,
    markdown: (experimentId: string, documentType: string) => ['documents', experimentId, documentType, 'markdown'] as const,
  },
};
