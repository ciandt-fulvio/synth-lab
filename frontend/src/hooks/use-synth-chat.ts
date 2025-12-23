// src/hooks/use-synth-chat.ts
//
// Purpose: Hook for managing chat state with a synth.
// Handles message history, sending messages, and loading states.
//
// Related:
// - chat-api.ts: API client for chat endpoint
// - SynthChatDialog: Main consumer of this hook

import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { sendChatMessage } from '@/services/chat-api';
import type { ChatMessage, ChatSession } from '@/types/chat';

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
 * - Handles sending messages to the API
 * - Manages loading and error states
 * - Auto-adds user messages optimistically
 *
 * @param params - Synth and execution IDs for API calls
 * @returns Chat state and actions
 */
export function useSynthChat({
  synthId,
  synthName,
  synthAge,
  execId,
}: UseSynthChatParams): UseSynthChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Mutation for sending chat messages
  const mutation = useMutation({
    mutationFn: async (userMessage: string) => {
      // Build chat history for API (excluding the current message we're adding)
      const chatHistory = messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp,
      }));

      return sendChatMessage(synthId, {
        exec_id: execId,
        message: userMessage,
        chat_history: chatHistory,
      });
    },
    onSuccess: (response, userMessage) => {
      // Add synth's response to messages
      const synthMessage: ChatMessage = {
        role: 'synth',
        content: response.message,
        timestamp: response.timestamp,
      };
      setMessages((prev) => [...prev, synthMessage]);
      setError(null);
    },
    onError: (err: Error) => {
      setError(err.message || 'Erro ao enviar mensagem. Tente novamente.');
    },
  });

  // Send a message
  const sendMessage = useCallback(
    (message: string) => {
      if (!message.trim()) return;

      // Add user message optimistically
      const userMessage: ChatMessage = {
        role: 'user',
        content: message,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setError(null);

      // Send to API
      mutation.mutate(message);
    },
    [mutation]
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
    isLoading: mutation.isPending,
    error,
    sendMessage,
    clearError,
    clearMessages,
  };
}
