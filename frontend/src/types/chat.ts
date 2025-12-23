/**
 * Chat types for synth conversation after interview.
 *
 * These types support the chat feature where users can converse with
 * synths after viewing their interview transcripts.
 */

export interface ChatMessage {
  role: 'user' | 'synth';
  content: string;
  timestamp: string; // ISO 8601
}

export interface ChatRequest {
  exec_id: string;
  message: string;
  chat_history: ChatMessage[];
}

export interface ChatResponse {
  message: string;
  timestamp: string;
}

export interface ChatSession {
  synthId: string;
  execId: string;
  synthName: string;
  synthAge?: number;
  messages: ChatMessage[];
  isLoading: boolean;
  error?: string;
}
