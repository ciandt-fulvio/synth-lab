// src/types/sse-events.ts
// SSE Event Type Definitions for Live Interview Cards
//
// This file defines TypeScript interfaces for Server-Sent Events (SSE)
// received from the /research/{exec_id}/stream endpoint.
//
// Backend Source: src/synth_lab/models/events.py (InterviewMessageEvent)
// API Documentation: specs/014-live-interview-cards/contracts/sse-events.yaml

/**
 * Event representing a single message in an interview (interviewer or interviewee turn).
 * Sent via SSE with event type "message".
 */
export interface InterviewMessageEvent {
  // Event metadata
  event_type: 'message';
  exec_id: string;

  // Interview identification
  synth_id: string;
  turn_number: number;

  // Message content
  speaker: 'Interviewer' | 'Interviewee';
  text: string; // May contain JSON-formatted response, requires extractMessageText()

  // Timing
  timestamp: string; // ISO 8601 datetime string
  is_replay: boolean; // true for historical messages, false for new live messages
}

/**
 * Event signaling that all interviews in an execution have finished transcription.
 * Sent via SSE with event type "transcription_completed".
 */
export interface TranscriptionCompletedEvent {
  successful_count: number; // Number of interviews completed successfully
  failed_count: number; // Number of interviews that failed
}

/**
 * Event signaling that all processing (interviews + summary generation) has finished.
 * Sent via SSE with event type "execution_completed".
 * Empty payload - event type itself is the signal.
 */
export interface ExecutionCompletedEvent {
  // Empty object
}

/**
 * Union type for all possible SSE event types
 */
export type SSEEventType =
  | 'message'
  | 'transcription_completed'
  | 'execution_completed';

/**
 * Component prop types for Live Interview Cards
 */

export interface LiveInterviewCardProps {
  // Identifiers
  execId: string;
  synthId: string;

  // Message data
  messages: InterviewMessageEvent[];

  // Interaction
  onClick: (synthId: string) => void;
}

export interface LiveInterviewGridProps {
  execId: string; // Research execution to display interviews for
}

/**
 * State structure for aggregated messages by synth
 * Keys: Synth IDs (UUIDs)
 * Values: Arrays of InterviewMessageEvent in chronological order
 */
export interface LiveInterviewMessages {
  [synthId: string]: InterviewMessageEvent[];
}

/**
 * State returned by the useSSE hook
 */
export interface SSEHookState {
  // Connection status
  isConnected: boolean; // true when EventSource.readyState === OPEN
  error: Error | null; // Error if connection fails

  // Event handlers (set by consumer)
  onMessage?: (event: InterviewMessageEvent) => void;
  onTranscriptionCompleted?: (data: TranscriptionCompletedEvent) => void;
  onExecutionCompleted?: () => void;
}

/**
 * State returned by the useLiveInterviews hook
 */
export interface LiveInterviewsHookState {
  // Aggregated messages
  messagesBySynth: LiveInterviewMessages;

  // Connection status (from SSE hook)
  isConnected: boolean;
  error: Error | null;

  // Derived data
  synthIds: string[]; // Array of synth IDs (keys of messagesBySynth)
}
