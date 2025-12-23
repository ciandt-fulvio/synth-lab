// src/hooks/use-synth-chat.ts
//
// Purpose: Hook for managing chat state with a synth.
// Handles message history, sending messages with streaming responses, and loading states.
//
// Related:
// - chat-api.ts: API client for chat endpoint (streaming)
// - SynthChatDialog: Main consumer of this hook

import { useState, useCallback, useRef } from 'react';
import { sendChatMessageStream } from '@/services/chat-api';
import type { ChatMessage } from '@/types/chat';

interface UseSynthChatParams {
  synthId: string;
  synthName: string;
  synthAge?: number;
  execId: string;
}

interface UseSynthChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (message: string) => void;
  clearError: () => void;
  clearMessages: () => void;
}

/**
 * Hook for managing chat state with a synth.
 *
 * Features:
 * - Maintains message history in session state
 * - Handles streaming messages from the API
 * - Manages loading and error states
 * - Auto-adds user messages optimistically
 * - Updates synth response in real-time as chunks arrive
 *
 * @param params - Synth and execution IDs for API calls
 * @returns Chat state and actions
 */
export function useSynthChat({
  synthId,
  execId,
}: UseSynthChatParams): UseSynthChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Ref to track current streaming content
  const streamingContentRef = useRef('');

  // Send a message with streaming response
  const sendMessage = useCallback(
    (message: string) => {
      if (!message.trim() || isLoading) return;

      // Add user message optimistically
      const userMessage: ChatMessage = {
        role: 'user',
        content: message,
        timestamp: new Date().toISOString(),
      };

      // Add placeholder for synth response
      const synthPlaceholder: ChatMessage = {
        role: 'synth',
        content: '',
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage, synthPlaceholder]);
      setError(null);
      setIsLoading(true);
      streamingContentRef.current = '';

      // Build chat history for API (excluding the current user message and placeholder)
      const chatHistory = messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp,
      }));

      // Send streaming request
      sendChatMessageStream(
        synthId,
        {
          exec_id: execId,
          message: message,
          chat_history: chatHistory,
        },
        // onChunk: Update the synth message with accumulated content
        (chunk: string) => {
          streamingContentRef.current += chunk;
          setMessages((prev) => {
            const updated = [...prev];
            // Update the last message (synth placeholder)
            if (updated.length > 0) {
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                content: streamingContentRef.current,
              };
            }
            return updated;
          });
        },
        // onComplete: Mark loading as complete
        () => {
          setIsLoading(false);
        },
        // onError: Handle errors
        (err: Error) => {
          setError(err.message || 'Erro ao enviar mensagem. Tente novamente.');
          setIsLoading(false);
          // Remove the empty synth placeholder on error
          setMessages((prev) => {
            if (prev.length > 0 && prev[prev.length - 1].content === '') {
              return prev.slice(0, -1);
            }
            return prev;
          });
        }
      );
    },
    [synthId, execId, messages, isLoading]
  );

  // Clear error state
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Clear all messages (reset chat)
  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearError,
    clearMessages,
  };
}
