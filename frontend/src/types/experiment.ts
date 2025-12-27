/**
 * T009 TypeScript types for Experiment.
 *
 * Types for experiment API request/response handling.
 *
 * References:
 *   - OpenAPI: specs/018-experiment-hub/contracts/openapi.yaml
 *   - Data model: specs/018-experiment-hub/data-model.md
 */

import type { PaginationMeta } from './common';

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

/**
 * Summary of a simulation linked to an experiment.
 */
export interface SimulationSummary {
  /** Simulation run ID */
  id: string;
  /** Scenario identifier (nullable) */
  scenario_id?: string | null;
  /** Simulation status */
  status: 'pending' | 'running' | 'completed' | 'failed';
  /** Whether insights are available */
  has_insights: boolean;
  /** Start timestamp */
  started_at: string;
  /** Completion timestamp */
  completed_at?: string | null;
  /** Aggregated score (0-100) */
  score?: number | null;
}

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
  /** Number of linked simulations */
  simulation_count: number;
  /** Number of linked interviews */
  interview_count: number;
  /** Creation timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at?: string | null;
}

/**
 * Full experiment details including linked simulations and interviews.
 */
export interface ExperimentDetail extends ExperimentSummary {
  /** Additional context */
  description?: string | null;
  /** Linked simulations */
  simulations: SimulationSummary[];
  /** Linked interviews */
  interviews: InterviewSummary[];
}

/**
 * Paginated list of experiment summaries.
 */
export interface PaginatedExperimentSummary {
  data: ExperimentSummary[];
  pagination: PaginationMeta;
}

/**
 * Dimension score configuration for scorecards.
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
