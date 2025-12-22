// src/hooks/use-sse.ts
// Custom React hook for Server-Sent Events (SSE) connection management
//
// Purpose: Manages EventSource lifecycle, connection state, and event listeners
// for real-time interview message streaming from /api/research/{exec_id}/stream
//
// Related:
// - Backend SSE endpoint: src/synth_lab/api/research.py (stream_interview_messages)
// - Event types: specs/014-live-interview-cards/contracts/sse-events.yaml
// - Type definitions: src/types/sse-events.ts

import { useEffect, useRef, useState } from 'react';
import type { InterviewMessageEvent } from '@/types/sse-events';

/**
 * Hook for managing Server-Sent Events connection to interview stream.
 *
 * @param execId - Research execution ID to stream messages from
 * @param enabled - Whether to establish SSE connection (false = disconnected)
 * @param onMessage - Callback invoked when 'message' event received
 * @returns Connection state (isConnected, error)
 *
 * @example
 * const { isConnected, error } = useSSE(
 *   'exec-123',
 *   true,
 *   (event) => console.log('Message:', event.text)
 * );
 */
export function useSSE(
  execId: string,
  enabled: boolean,
  onMessage: (event: InterviewMessageEvent) => void
): {
  isConnected: boolean;
  error: Error | null;
} {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // Don't connect if disabled or no execId
    if (!enabled || !execId) {
      setIsConnected(false);
      return;
    }

    // Create EventSource connection
    const url = `/api/research/${execId}/stream`;
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    // Connection opened
    eventSource.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    // Connection error
    eventSource.onerror = () => {
      setIsConnected(false);
      setError(new Error('SSE connection failed'));
      eventSource.close();
    };

    // Listen for 'message' events
    eventSource.addEventListener('message', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as InterviewMessageEvent;
        onMessage(data);
      } catch (err) {
        console.error('Failed to parse SSE message:', err);
      }
    });

    // Cleanup on unmount or dependency change
    return () => {
      eventSource.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    };
  }, [execId, enabled, onMessage]);

  return { isConnected, error };
}
