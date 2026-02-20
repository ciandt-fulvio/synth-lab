/**
 * Chat API client for synth conversation.
 *
 * Handles communication with the chat endpoint for sending messages
 * to synths and receiving responses, including streaming support.
 */

import { ChatRequest, ChatResponse } from '@/types/chat';
import { fetchAPI } from './api';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

/**
 * Send a message to a synth and get their response (non-streaming).
 *
 * @param synthId - The ID of the synth to chat with
 * @param request - The chat request containing the message and history
 * @returns The synth's response
 */
export async function sendChatMessage(
  synthId: string,
  request: ChatRequest
): Promise<ChatResponse> {
  return fetchAPI<ChatResponse>(`/synths/${synthId}/chat`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Send a message to a synth and receive a streaming response.
 *
 * @param synthId - The ID of the synth to chat with
 * @param request - The chat request containing the message and history
 * @param onChunk - Callback invoked for each text chunk received
 * @param onComplete - Callback invoked when streaming completes
 * @param onError - Callback invoked if an error occurs
 */
export async function sendChatMessageStream(
  synthId: string,
  request: ChatRequest,
  onChunk: (chunk: string) => void,
  onComplete: () => void,
  onError: (error: Error) => void
): Promise<void> {
  try {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    const token = localStorage.getItem('auth_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/synths/${synthId}/chat/stream`, {
      method: 'POST',
      credentials: 'include',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      if (response.status === 401 && !window.location.pathname.startsWith('/login')) {
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
        return;
      }
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `Chat request failed: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Parse SSE lines from buffer
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6); // Remove 'data: ' prefix

          // Check for special markers
          if (data === '[DONE]') {
            onComplete();
            return;
          }

          if (data.startsWith('[ERROR]')) {
            throw new Error(data.slice(8)); // Remove '[ERROR] ' prefix
          }

          // Normal text chunk
          onChunk(data);
        }
      }
    }

    // Process any remaining buffer
    if (buffer.startsWith('data: ')) {
      const data = buffer.slice(6);
      if (data !== '[DONE]' && !data.startsWith('[ERROR]')) {
        onChunk(data);
      }
    }

    onComplete();
  } catch (error) {
    onError(error instanceof Error ? error : new Error('Unknown streaming error'));
  }
}
