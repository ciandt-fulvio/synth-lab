// src/hooks/use-sse.ts
// DEFERRED to next feature - SSE streaming implementation

import { useState, useEffect } from 'react';
import type { SSEEvent } from '@/types';

export function useSSE(execId: string, enabled: boolean = false) {
  const [messages, setMessages] = useState<SSEEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!enabled || !execId) return;

    // TODO: Implement EventSource connection in next feature
    console.log('SSE connection placeholder - to be implemented');

    // Placeholder implementation
    setIsConnected(false);
    setMessages([]);
    setError(null);

    return () => {
      // Cleanup
    };
  }, [execId, enabled]);

  return {
    messages,
    isConnected,
    error,
  };
}
