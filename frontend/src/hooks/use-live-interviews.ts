// src/hooks/use-live-interviews.ts
// Custom React hook for aggregating live interview messages by synth_id
//
// Purpose: Consumes useSSE hook and organizes messages into a dictionary
// keyed by synth_id, enabling multi-interview monitoring in LiveInterviewGrid
//
// Related:
// - useSSE hook: src/hooks/use-sse.ts
// - Type definitions: src/types/sse-events.ts
// - Component usage: src/components/interviews/LiveInterviewGrid.tsx

import { useCallback, useState } from 'react';
import { useSSE } from './use-sse';
import type {
  InterviewMessageEvent,
  LiveInterviewMessages,
  LiveInterviewsHookState,
} from '@/types/sse-events';

/**
 * Hook for managing live interview messages aggregated by synth_id.
 *
 * Establishes SSE connection and maintains a dictionary of messages
 * where each key is a synth_id and value is an array of messages
 * in chronological order.
 *
 * @param execId - Research execution ID to stream messages from
 * @returns State with messagesBySynth, synthIds, connection status
 *
 * @example
 * const { messagesBySynth, synthIds, isConnected } = useLiveInterviews('exec-123');
 *
 * // Render cards for each synth
 * synthIds.map(synthId => (
 *   <LiveInterviewCard
 *     key={synthId}
 *     synthId={synthId}
 *     messages={messagesBySynth[synthId]}
 *   />
 * ))
 */
export function useLiveInterviews(execId: string): LiveInterviewsHookState {
  const [messagesBySynth, setMessagesBySynth] = useState<LiveInterviewMessages>({});

  // Callback to handle incoming messages
  const handleMessage = useCallback((event: InterviewMessageEvent) => {
    setMessagesBySynth((prev) => {
      const synthId = event.synth_id;
      const existingMessages = prev[synthId] || [];

      return {
        ...prev,
        [synthId]: [...existingMessages, event],
      };
    });
  }, []);

  // Establish SSE connection
  const { isConnected, error } = useSSE(execId, true, handleMessage);

  // Derive synthIds from messagesBySynth keys
  const synthIds = Object.keys(messagesBySynth);

  return {
    messagesBySynth,
    synthIds,
    isConnected,
    error,
  };
}
