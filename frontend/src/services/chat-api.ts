/**
 * Chat API client for synth conversation.
 *
 * Handles communication with the chat endpoint for sending messages
 * to synths and receiving responses.
 */

import { ChatRequest, ChatResponse } from '@/types/chat';

const API_BASE = '/api';

/**
 * Send a message to a synth and get their response.
 *
 * @param synthId - The ID of the synth to chat with
 * @param request - The chat request containing the message and history
 * @returns The synth's response
 */
export async function sendChatMessage(
  synthId: string,
  request: ChatRequest
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/synths/${synthId}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Chat request failed: ${response.status}`);
  }

  return response.json();
}
