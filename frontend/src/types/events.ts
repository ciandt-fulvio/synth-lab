// src/types/events.ts

export interface InterviewMessageEvent {
  event_type: 'message';
  exec_id: string;
  synth_id: string;
  turn_number: number;
  speaker: string;
  text: string;
  timestamp: string;
  is_replay: boolean;
}

export interface TranscriptionCompletedEvent {
  event_type: 'transcription_completed';
  successful_count: number;
  failed_count: number;
}

export interface ExecutionCompletedEvent {
  event_type: 'execution_completed';
}

export type SSEEvent =
  | InterviewMessageEvent
  | TranscriptionCompletedEvent
  | ExecutionCompletedEvent;
