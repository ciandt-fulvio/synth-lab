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
import type { FeatureMechanisms } from './simulation';

// =============================================================================
// Scorecard Types (Embedded)
// =============================================================================

/**
 * Embedded scorecard data within an experiment.
 *
 * Legacy dimensions (complexity, initial_effort, perceived_risk, time_to_value)
 * were removed in 040 — simulation uses only mechanisms.
 */
export interface ScorecardData {
  /** Name of the feature */
  feature_name: string;
  /** Feature description */
  description_text: string;
  /** Usage scenario */
  use_scenario?: string;
  /** LLM-generated justification */
  justification?: string;
  /** Impact hypotheses */
  impact_hypotheses?: string[];
  /** Feature mechanisms for simulation (038-mechanism-based-simulation) */
  mechanisms?: FeatureMechanisms;
  /** Category tags for the feature */
  feature_types?: string[];
}

// =============================================================================
// Analysis Types (1:1 Relationship)
// =============================================================================

/**
 * Aggregated outcomes from analysis.
 */
export interface AggregatedOutcomes {
  /** Proportion that adopted (0-1) */
  adopted_rate: number;
  /** Proportion that did not adopt (0-1) */
  not_adopted_rate: number;
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
  /** Total turns across all transcripts */
  total_turns: number;
  /** Whether summary is available */
  has_summary: boolean;
  /** Whether PR-FAQ is available */
  has_prfaq: boolean;
  /** Additional context text (if provided) */
  additional_context: string | null;
  /** Start timestamp */
  started_at: string;
  /** Completion timestamp */
  completed_at?: string | null;
}

/**
 * Request to create an automatic interview with extreme cases.
 */
export interface AutoInterviewRequest {
  /** Number of turns for the interview (fixed at 4) */
  num_turns: number;
}

/**
 * Response from creating an automatic interview.
 */
export interface AutoInterviewResponse {
  /** Created interview ID */
  interview_id: string;
  /** Parent experiment ID */
  experiment_id: string;
  /** Synth IDs included in the interview (top 5 + bottom 5) */
  synth_ids: string[];
  /** Number of turns */
  num_turns: number;
  /** Interview status */
  status: 'pending' | 'running' | 'generating_summary' | 'completed' | 'failed';
  /** Creation timestamp */
  created_at: string;
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
  /** ID of the synth group to use for this experiment (required) */
  synth_group_id: string;
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
  /** Feature mechanisms for simulation (038-mechanism-based-simulation) */
  mechanisms?: FeatureMechanisms;
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
  /** ID of the synth group used for this experiment */
  synth_group_id: string;
  /** Name of the synth group used for this experiment */
  synth_group_name: string;
  /** Whether scorecard is filled */
  has_scorecard: boolean;
  /** Whether analysis exists */
  has_analysis: boolean;
  /** Whether interview guide is configured */
  has_interview_guide: boolean;
  /** Number of linked interviews */
  interview_count: number;
  /** Tag names associated with this experiment */
  tags: string[];
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
  /** ID of the synth group used for this experiment */
  synth_group_id: string;
  /** Name of the synth group used for this experiment */
  synth_group_name: string;
  /** Embedded scorecard data */
  scorecard_data?: ScorecardData | null;
  /** Whether scorecard is filled */
  has_scorecard: boolean;
  /** Whether interview guide is configured */
  has_interview_guide: boolean;
  /** Tag names associated with this experiment */
  tags: string[];
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

