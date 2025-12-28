// src/types/research.ts

export type ExecutionStatus =
  | 'pending'
  | 'running'
  | 'generating_summary'
  | 'completed'
  | 'failed';

export interface ResearchExecutionSummary {
  exec_id: string;
  experiment_id: string | null;
  topic_name: string;
  status: ExecutionStatus;
  synth_count: number;
  started_at: string; // ISO datetime
  completed_at: string | null;
}

export interface ResearchExecutionDetail extends ResearchExecutionSummary {
  successful_count: number;
  failed_count: number;
  model: string;
  max_turns: number;
  summary_available: boolean;
  prfaq_available: boolean;
}

export interface Message {
  speaker: string;
  text: string;
  internal_notes?: string | null;
}

export interface TranscriptSummary {
  synth_id: string;
  synth_name: string | null;
  turn_count: number;
  timestamp: string;
  status: string;
}

export interface TranscriptDetail extends TranscriptSummary {
  exec_id: string;
  messages: Message[];
}

export interface ResearchExecuteRequest {
  topic_name: string;
  experiment_id?: string | null;
  synth_ids?: string[] | null;
  synth_count?: number | null;
  max_turns?: number; // default: 6
  max_concurrent?: number; // default: 10
  model?: string; // default: 'gpt-4o-mini'
  generate_summary?: boolean; // default: true
}

/**
 * Request for creating an interview from an experiment.
 * Experiment_id is taken from the URL path.
 * Topic comes from the experiment's interview guide.
 */
export interface InterviewCreateRequest {
  additional_context?: string | null;
  synth_ids?: string[] | null;
  synth_count?: number | null;
  max_turns?: number; // default: 6
  generate_summary?: boolean; // default: true
}

export interface ResearchExecuteResponse {
  exec_id: string;
  status: ExecutionStatus;
  topic_name: string;
  synth_count: number;
  started_at: string;
}
