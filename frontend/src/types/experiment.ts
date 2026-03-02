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
  /** Synth selection strategy (random, propensos, resistentes, indecisos, sensiveis) */
  synth_selection_type: string | null;
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
  /** ID of the synth group used for this experiment */
  synth_group_id: string;
  /** Name of the synth group used for this experiment */
  synth_group_name: string;
  /** Whether interview guide is configured */
  has_interview_guide: boolean;
  /** Number of linked interviews */
  interview_count: number;
  /** Number of uploaded materials */
  materials_count: number;
  /** Whether simulation batches exist */
  has_simulation: boolean;
  /** Whether quantitative analysis (simulation runs) exist */
  has_quanti: boolean;
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
  /** Whether interview guide is configured */
  has_interview_guide: boolean;
  /** Tag names associated with this experiment */
  tags: string[];
  /** Creation timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at?: string | null;
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

