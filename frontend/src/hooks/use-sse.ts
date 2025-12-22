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
  const onMessageRef = useRef(onMessage);

  // Keep onMessage ref updated
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    // Don't connect if disabled or no execId
    if (!enabled || !execId) {
      setIsConnected(false);
      return;
    }

    let eventSource: EventSource | null = null;

    try {
      // Create EventSource connection
      const url = `/api/research/${execId}/stream`;
      console.log('[useSSE] Connecting to:', url);
      eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      // Connection opened
      eventSource.onopen = () => {
        console.log('[useSSE] Connected');
        setIsConnected(true);
        setError(null);
      };

      // Connection error
      eventSource.onerror = (event) => {
        console.error('[useSSE] Connection error:', event);
        setIsConnected(false);
        setError(new Error('SSE connection failed'));
        if (eventSource) {
          eventSource.close();
        }
      };

      // Listen for 'message' events
      eventSource.addEventListener('message', (event: MessageEvent) => {
        try {
          console.log('[useSSE] Message received:', event.data);
          const data = JSON.parse(event.data) as InterviewMessageEvent;
          onMessageRef.current(data);
        } catch (err) {
          console.error('[useSSE] Failed to parse SSE message:', err);
        }
      });
    } catch (err) {
      console.error('[useSSE] Failed to create EventSource:', err);
      setError(err instanceof Error ? err : new Error('Failed to create EventSource'));
      setIsConnected(false);
    }

    // Cleanup on unmount or dependency change
    return () => {
      if (eventSource) {
        console.log('[useSSE] Disconnecting');
        eventSource.close();
        eventSourceRef.current = null;
        setIsConnected(false);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [execId, enabled]);

  return { isConnected, error };
}
