/**
 * TypeScript types for Experiment (Refactored).
 *
 * Types for experiment API request/response handling.
 * Updated to match spec 019-experiment-refactor.
 *
 * References:
 *   - Spec: specs/019-experiment-refactor/spec.md
 *   - Data model: specs/019-experiment-refactor/data-model.md
 */

import type { PaginationMeta } from './common';

// =============================================================================
// Scorecard Types (Embedded)
// =============================================================================

/**
 * Scorecard dimension with score and optional metadata.
 */
export interface ScorecardDimension {
  /** Score value in [0,1] */
  score: number;
  /** Rules applied to derive score */
  rules_applied?: string[];
  /** Lower bound for uncertainty */
  lower_bound?: number;
  /** Upper bound for uncertainty */
  upper_bound?: number;
}

/**
 * Embedded scorecard data within an experiment.
 */
export interface ScorecardData {
  /** Name of the feature */
  feature_name: string;
  /** Feature description */
  description_text: string;
  /** Usage scenario */
  use_scenario?: string;
  /** Complexity dimension */
  complexity: ScorecardDimension;
  /** Initial effort dimension */
  initial_effort: ScorecardDimension;
  /** Perceived risk dimension */
  perceived_risk: ScorecardDimension;
  /** Time to value dimension */
  time_to_value: ScorecardDimension;
  /** LLM-generated justification */
  justification?: string;
  /** Impact hypotheses */
  impact_hypotheses?: string[];
}

// =============================================================================
// Analysis Types (1:1 Relationship)
// =============================================================================

/**
 * Aggregated outcomes from analysis.
 */
export interface AggregatedOutcomes {
  /** Proportion that did not try (0-1) */
  did_not_try_rate: number;
  /** Proportion that tried but failed (0-1) */
  failed_rate: number;
  /** Proportion that succeeded (0-1) */
  success_rate: number;
}

/**
 * Summary of analysis linked to an experiment (1:1 relationship).
 */
export interface AnalysisSummary {
  /** Analysis run ID */
  id: string;
  /** Simulation ID for chart endpoints (uses analysis ID) */
  simulation_id: string;
  /** Analysis status */
  status: 'pending' | 'running' | 'completed' | 'failed';
  /** Start timestamp */
  started_at: string;
  /** Completion timestamp */
  completed_at?: string | null;
  /** Number of synths analyzed */
  total_synths: number;
  /** Number of Monte Carlo executions per synth */
  n_executions: number;
  /** Time taken to run the analysis in seconds */
  execution_time_seconds?: number | null;
  /** Aggregated outcomes from analysis */
  aggregated_outcomes?: AggregatedOutcomes | null;
}

// =============================================================================
// Interview Types (N:1 Relationship)
// =============================================================================

/**
 * Summary of an interview linked to an experiment.
 */
export interface InterviewSummary {
  /** Execution ID */
  exec_id: string;
  /** Research topic name */
  topic_name: string;
  /** Interview status */
  status: 'pending' | 'running' | 'generating_summary' | 'completed' | 'failed';
  /** Number of synths interviewed */
  synth_count: number;
  /** Whether summary is available */
  has_summary: boolean;
  /** Whether PR-FAQ is available */
  has_prfaq: boolean;
  /** Start timestamp */
  started_at: string;
  /** Completion timestamp */
  completed_at?: string | null;
}

// =============================================================================
// Experiment Request Types
// =============================================================================

/**
 * Request schema for creating a new experiment.
 */
export interface ExperimentCreate {
  /** Short name of the feature (max 100 chars) */
  name: string;
  /** Description of the hypothesis to test (max 500 chars) */
  hypothesis: string;
  /** Additional context, links, references (max 2000 chars) */
  description?: string;
  /** Optional scorecard data to create with experiment */
  scorecard_data?: ScorecardData;
}

/**
 * Request schema for updating an experiment.
 */
export interface ExperimentUpdate {
  /** Short name of the feature (max 100 chars) */
  name?: string;
  /** Description of the hypothesis to test (max 500 chars) */
  hypothesis?: string;
  /** Additional context, links, references (max 2000 chars) */
  description?: string;
}

// =============================================================================
// Experiment Response Types
// =============================================================================

/**
 * Summary of an experiment for list display.
 */
export interface ExperimentSummary {
  /** Experiment ID (exp_[a-f0-9]{8}) */
  id: string;
  /** Short name of the feature */
  name: string;
  /** Hypothesis description */
  hypothesis: string;
  /** Additional context */
  description?: string | null;
  /** Whether scorecard is filled */
  has_scorecard: boolean;
  /** Whether analysis exists */
  has_analysis: boolean;
  /** Whether interview guide is configured */
  has_interview_guide: boolean;
  /** Number of linked interviews */
  interview_count: number;
  /** Creation timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at?: string | null;
}

/**
 * Full experiment details including linked analysis and interviews.
 */
export interface ExperimentDetail {
  /** Experiment ID (exp_[a-f0-9]{8}) */
  id: string;
  /** Short name of the feature */
  name: string;
  /** Hypothesis description */
  hypothesis: string;
  /** Additional context */
  description?: string | null;
  /** Embedded scorecard data */
  scorecard_data?: ScorecardData | null;
  /** Whether scorecard is filled */
  has_scorecard: boolean;
  /** Whether interview guide is configured */
  has_interview_guide: boolean;
  /** Creation timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at?: string | null;
  /** Linked analysis (1:1 relationship) */
  analysis?: AnalysisSummary | null;
  /** Linked interviews (N:1 relationship) */
  interviews: InterviewSummary[];
  /** Number of linked interviews */
  interview_count: number;
}

/**
 * Paginated list of experiment summaries.
 */
export interface PaginatedExperimentSummary {
  data: ExperimentSummary[];
  pagination: PaginationMeta;
}

// =============================================================================
// Scorecard API Types (Legacy - for backward compatibility)
// =============================================================================

/**
 * Dimension score configuration for scorecards.
 * @deprecated Use ScorecardDimension instead
 */
export interface DimensionCreate {
  /** Score value in [0,1] */
  score: number;
  /** Rules applied to derive score */
  rules_applied?: string[];
  /** Minimum uncertainty bound */
  min_uncertainty?: number;
  /** Maximum uncertainty bound */
  max_uncertainty?: number;
}

/**
 * Request schema for creating a scorecard linked to an experiment.
 * @deprecated Use PUT /experiments/{id}/scorecard with ScorecardData instead
 */
export interface ScorecardCreate {
  /** Name of the feature */
  feature_name: string;
  /** Usage scenario */
  use_scenario: string;
  /** Feature description */
  description_text: string;
  /** List of evaluators */
  evaluators?: string[];
  /** Media URLs for feature description */
  description_media_urls?: string[];
  /** Complexity dimension */
  complexity?: DimensionCreate;
  /** Initial effort dimension */
  initial_effort?: DimensionCreate;
  /** Perceived risk dimension */
  perceived_risk?: DimensionCreate;
  /** Time to value dimension */
  time_to_value?: DimensionCreate;
}

/**
 * Response schema for a created scorecard.
 * @deprecated Use ExperimentDetail.scorecard_data instead
 */
export interface ScorecardResponse {
  /** Scorecard ID (8 char alphanumeric) */
  id: string;
  /** Parent experiment ID */
  experiment_id: string | null;
  /** Feature name */
  feature_name: string;
  /** Usage scenario */
  use_scenario: string;
  /** Feature description */
  description_text: string;
  /** Complexity score [0,1] */
  complexity_score: number;
  /** Initial effort score [0,1] */
  initial_effort_score: number;
  /** Perceived risk score [0,1] */
  perceived_risk_score: number;
  /** Time to value score [0,1] */
  time_to_value_score: number;
  /** LLM-generated justification */
  justification: string | null;
  /** Impact hypotheses */
  impact_hypotheses: string[];
  /** Creation timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at: string | null;
}

// =============================================================================
// AI Estimation Types
// =============================================================================

/**
 * AI-generated dimension estimate.
 */
export interface DimensionEstimate {
  /** Estimated score value in [0,1] */
  score: number;
  /** Brief justification for the score */
  justification?: string;
  /** Minimum uncertainty bound */
  lower_bound?: number;
  /** Maximum uncertainty bound */
  upper_bound?: number;
}

/**
 * Response from AI scorecard estimation.
 */
export interface ScorecardEstimateResponse {
  complexity: DimensionEstimate;
  initial_effort: DimensionEstimate;
  perceived_risk: DimensionEstimate;
  time_to_value: DimensionEstimate;
  justification?: string;
  impact_hypotheses?: string[];
}
