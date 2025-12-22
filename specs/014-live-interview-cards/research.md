# Research: Live Interview Cards Display

**Feature**: 014-live-interview-cards
**Date**: 2025-12-21
**Status**: Phase 0 Complete

## Purpose

This document consolidates research findings to resolve technical unknowns identified in the implementation plan. All decisions, rationales, and alternatives are documented to inform Phase 1 design and implementation.

## Research Questions

### 1. SSE Best Practices in React

**Question**: How to handle EventSource reconnection, error states, and cleanup in React? What are common pitfalls with SSE in modern browsers?

#### Decision

Implement EventSource management using React useEffect with proper cleanup, automatic reconnection with exponential backoff, and readyState monitoring.

#### Rationale

- **Native EventSource API**: Modern browsers (Chrome, Firefox, Safari, Edge) have excellent built-in support - no library needed
- **React Lifecycle**: useEffect provides natural lifecycle management (connection on mount, cleanup on unmount)
- **Auto-Reconnect**: EventSource automatically reconnects on connection loss, but manual handling needed for error states
- **Readiness Detection**: readyState enum (CONNECTING=0, OPEN=1, CLOSED=2) enables connection status monitoring

#### Implementation Pattern

```typescript
// Recommended pattern from research
useEffect(() => {
  if (!enabled || !execId) return;

  const url = getStreamUrl(execId);
  const eventSource = new EventSource(url);

  // Connection lifecycle handlers
  eventSource.onopen = () => {
    setIsConnected(true);
    setReconnectAttempts(0); // Reset backoff on successful connection
  };

  eventSource.onerror = (error) => {
    setIsConnected(false);

    // EventSource auto-reconnects on network issues
    // Only handle fatal errors (close and show error state)
    if (eventSource.readyState === EventSource.CLOSED) {
      setError(new Error('SSE connection closed'));
    }
  };

  // Event listeners for each event type
  eventSource.addEventListener('message', (e) => {
    const event = JSON.parse(e.data);
    handleMessageEvent(event);
  });

  eventSource.addEventListener('transcription_completed', (e) => {
    const data = JSON.parse(e.data);
    handleTranscriptionCompleted(data);
  });

  eventSource.addEventListener('execution_completed', () => {
    eventSource.close(); // Clean close when execution finishes
  });

  // Cleanup on unmount or dependency change
  return () => {
    eventSource.close();
  };
}, [execId, enabled]);
```

#### Common Pitfalls (Documented for Avoidance)

1. **Memory Leaks**: Forgetting to close EventSource in cleanup → Always call `eventSource.close()` in useEffect return
2. **Duplicate Connections**: Re-running effect without proper dependencies → Include all dependencies in useEffect array
3. **Error Handling**: Not checking readyState before operations → Always verify connection state
4. **CORS Issues**: EventSource requires proper CORS headers → Backend already configured correctly
5. **Browser Tab Backgrounding**: Some browsers throttle SSE when tab inactive → Acceptable trade-off, reconnects when tab active

#### Alternatives Considered

- **Socket.IO Library**: Rejected - overkill for one-way streaming, adds 100KB+ bundle size
- **WebSocket**: Rejected - bidirectional when we only need server→client, more complex protocol
- **React Query with Polling**: Rejected per spec - inefficient, higher latency than SSE

#### References

- MDN EventSource API: https://developer.mozilla.org/en-US/docs/Web/API/EventSource
- SSE Specification: https://html.spec.whatwg.org/multipage/server-sent-events.html
- React Hook Patterns: https://react.dev/reference/react/useEffect

---

### 2. Auto-Scroll to Newest Messages

**Question**: What's the best approach for auto-scrolling to newest messages while preserving user's manual scroll position when they're reviewing older messages?

#### Decision

Use `scrollIntoView()` with scroll position detection to auto-scroll only when user is at/near bottom. Pause auto-scroll if user scrolls up, resume when they scroll back to bottom.

#### Rationale

- **User Intent Detection**: If user is scrolled up, they're reviewing history - don't interrupt
- **Natural Behavior**: Auto-scroll only when user is already viewing newest messages
- **Threshold-Based**: Consider user "at bottom" if within 50px of bottom (accounts for scroll momentum)
- **Performance**: scrollIntoView() is native and highly optimized by browsers

#### Implementation Pattern

```typescript
const LiveInterviewCard = ({ messages, synthId }) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isUserScrolledUp, setIsUserScrolledUp] = useState(false);

  // Detect if user has scrolled up
  const handleScroll = () => {
    const container = scrollRef.current;
    if (!container) return;

    const { scrollTop, scrollHeight, clientHeight } = container;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;

    // User is considered "at bottom" if within 50px
    setIsUserScrolledUp(distanceFromBottom > 50);
  };

  // Auto-scroll when new messages arrive
  useEffect(() => {
    if (!isUserScrolledUp && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'end'
      });
    }
  }, [messages, isUserScrolledUp]);

  return (
    <ScrollArea ref={scrollRef} onScroll={handleScroll} className="h-[200px]">
      {messages.map((msg, i) => (
        <p key={i}>...</p>
      ))}
      <div ref={messagesEndRef} /> {/* Scroll anchor */}
    </ScrollArea>
  );
};
```

#### Threshold Tuning

- **50px threshold**: Recommended based on typical scroll wheel/touchpad sensitivity
- **Smooth behavior**: Provides visual continuity, less jarring than instant scroll
- **block: 'end'**: Ensures newest message is fully visible at bottom

#### Edge Cases Handled

- Empty messages list: No scroll attempted
- Very long messages (>500 words): Scroll shows newest message, user can scroll up to see full content
- Rapid message arrival: Smooth scroll queues naturally, no flashing

#### Alternatives Considered

- **Always Auto-Scroll**: Rejected - frustrating when user is reviewing history
- **Sticky Bottom (CSS)**: Rejected - doesn't work well with dynamic height content in fixed container
- **IntersectionObserver**: Rejected - overkill for this use case, more complex than needed

#### References

- Element.scrollIntoView(): https://developer.mozilla.org/en-US/docs/Web/API/Element/scrollIntoView
- Scroll Detection Patterns: https://developer.mozilla.org/en-US/docs/Web/API/Element/scroll_event

---

### 3. Performance Optimization for 10+ Cards

**Question**: How to efficiently render and update 10+ cards simultaneously? Are there virtualization techniques needed for the grid? What are React Query strategies for managing per-card data?

#### Decision

No virtualization needed. Use React.memo for cards, optimize re-renders with proper key props, leverage React Query's automatic batching and caching.

#### Rationale

- **Fixed Card Count**: 10-20 cards is well within React's rendering capabilities (not 1000s of items)
- **Fixed Height**: 200px cards with limited content (4-5 message pairs) = predictable memory footprint
- **Browser Optimization**: Modern browsers efficiently handle 10-20 scroll containers
- **React Query Caching**: Shared execution data cached once, per-card synth data cached separately

#### Implementation Strategy

**Component Optimization:**

```typescript
// Memoize card component - only re-render when messages change
const LiveInterviewCard = React.memo(({
  execId,
  synthId,
  messages,
  onClick
}: CardProps) => {
  // ... component implementation
}, (prevProps, nextProps) => {
  // Custom comparison: only re-render if messages actually changed
  return prevProps.messages === nextProps.messages &&
         prevProps.synthId === nextProps.synthId;
});

// Grid renders memoized cards with stable keys
const LiveInterviewGrid = ({ execId }) => {
  const { messagesBySynth } = useLiveInterviews(execId);

  return (
    <div className="grid grid-cols-2 gap-4">
      {Object.entries(messagesBySynth).map(([synthId, messages]) => (
        <LiveInterviewCard
          key={synthId}  // Stable key prevents unnecessary unmount/remount
          execId={execId}
          synthId={synthId}
          messages={messages}
          onClick={handleCardClick}
        />
      ))}
    </div>
  );
};
```

**React Query Strategy:**

```typescript
// Shared execution data - fetched once, cached
const { data: execution } = useQuery({
  queryKey: ['research', execId],
  queryFn: () => getExecution(execId),
  staleTime: 5000, // 5s cache
});

// Per-synth data - fetched in parallel, cached separately
const { data: synth } = useQuery({
  queryKey: ['synth', synthId],
  queryFn: () => getSynth(synthId),
  staleTime: Infinity, // Synth data doesn't change
});

// SSE messages - managed by custom hook, not React Query
// (SSE provides live updates, no need for polling)
```

#### Performance Benchmarks

Based on typical interview scenarios:
- **10 cards × 10 messages each = 100 DOM elements** (messages)
- **Each card**: ~300 bytes state (10 messages × ~30 chars average)
- **Total memory**: ~30KB for all card state (negligible)
- **Re-render time**: <16ms for all cards on message arrival (60fps target)

#### Virtualization Threshold

Virtualization (react-window or similar) would only be beneficial if:
- **>50 concurrent cards** (unlikely in normal usage)
- **>100 messages per card** (interviews typically 5-15 turns)
- **Performance issues observed** in profiling (none expected)

#### Alternatives Considered

- **React Virtualization (react-window)**: Rejected - adds complexity for minimal gain at this scale
- **Separate Pages per Interview**: Rejected - defeats purpose of simultaneous monitoring
- **Message Pagination**: Rejected - 10-15 messages per card is manageable

#### References

- React.memo(): https://react.dev/reference/react/memo
- React Query Caching: https://tanstack.com/query/latest/docs/react/guides/caching
- Performance Optimization: https://react.dev/learn/render-and-commit

---

### 4. SSE Event Message Parsing

**Question**: The SSE endpoint sends events with types (message, transcription_completed, execution_completed). How are these structured in the data payload?

#### Decision

Use TypeScript interfaces matching backend Pydantic models. Parse `data` field as JSON for structured events.

#### Rationale

From backend code analysis (`src/synth_lab/models/events.py` and `src/synth_lab/api/routers/research.py`):

**Event Format (SSE Protocol):**
```
event: <event_type>
data: <JSON payload>

```

**Event Types and Payloads:**

1. **message event** (Interview turn):
```typescript
{
  event_type: "message",
  exec_id: string,
  synth_id: string,
  turn_number: number,
  speaker: "Interviewer" | "Interviewee",
  text: string,  // May be JSON-formatted, requires extractMessageText()
  timestamp: string,  // ISO 8601
  is_replay: boolean  // true for historical messages, false for live
}
```

2. **transcription_completed event** (All interviews done):
```typescript
{
  successful_count: number,
  failed_count: number
}
```

3. **execution_completed event** (Summary generation done):
```typescript
{}  // Empty payload, event type is the signal
```

#### TypeScript Type Definitions

```typescript
// frontend/src/types/sse-events.ts

export interface InterviewMessageEvent {
  event_type: "message";
  exec_id: string;
  synth_id: string;
  turn_number: number;
  speaker: "Interviewer" | "Interviewee";
  text: string;
  timestamp: string;
  is_replay: boolean;
}

export interface TranscriptionCompletedEvent {
  successful_count: number;
  failed_count: number;
}

export type SSEEventType =
  | "message"
  | "transcription_completed"
  | "execution_completed";

export interface SSEMessageEventData extends InterviewMessageEvent {}

export type SSEEventData =
  | SSEMessageEventData
  | TranscriptionCompletedEvent
  | Record<string, never>;  // Empty object for execution_completed
```

#### Parsing Strategy

```typescript
// In use-sse.ts hook
eventSource.addEventListener('message', (e: MessageEvent) => {
  const event: InterviewMessageEvent = JSON.parse(e.data);

  // Group by synth_id for card display
  setMessages(prev => ({
    ...prev,
    [event.synth_id]: [...(prev[event.synth_id] || []), event]
  }));
});

eventSource.addEventListener('transcription_completed', (e: MessageEvent) => {
  const data: TranscriptionCompletedEvent = JSON.parse(e.data);
  console.log(`Completed: ${data.successful_count} successful, ${data.failed_count} failed`);
  setIsTranscribing(false);
});

eventSource.addEventListener('execution_completed', () => {
  // No data to parse, just close connection
  eventSource.close();
  setIsCompleted(true);
});
```

#### Historical Replay Handling

- Backend sends all existing messages with `is_replay: true` before live messages
- Frontend can use `is_replay` flag to:
  - Skip animations on initial load (instant render)
  - Only animate live messages (smooth scroll, highlight)
  - Track when historical replay completes

#### Alternatives Considered

- **Custom Binary Protocol**: Rejected - JSON is sufficient, SSE is text-based anyway
- **Message Batching**: Rejected - backend sends individual messages, batching would require buffering

#### References

- Backend Event Model: `src/synth_lab/models/events.py:16-40`
- Backend SSE Router: `src/synth_lab/api/routers/research.py:192-292`

---

### 5. Message Aggregation Strategy

**Question**: How to aggregate SSE messages by synth_id for display in individual cards? Should we use a reducer pattern, or is React Query's cache sufficient?

#### Decision

Use a custom hook (`use-live-interviews.ts`) with useState to aggregate messages by synth_id. React Query is not suitable for SSE data management.

#### Rationale

- **React Query Limitation**: Designed for request/response (HTTP), not streaming data
- **State Simplicity**: Dictionary keyed by synth_id is natural fit - `{ [synthId]: Message[] }`
- **Incremental Updates**: SSE delivers one message at a time, useState handles incremental state well
- **No Caching Needed**: SSE provides real-time source of truth, no need for cache invalidation

#### Implementation

```typescript
// frontend/src/hooks/use-live-interviews.ts

import { useState } from 'react';
import { useSSE } from './use-sse';
import type { InterviewMessageEvent } from '@/types/sse-events';

export interface LiveInterviewMessages {
  [synthId: string]: InterviewMessageEvent[];
}

export function useLiveInterviews(execId: string) {
  const [messagesBySynth, setMessagesBySynth] = useState<LiveInterviewMessages>({});
  const { isConnected, error } = useSSE(
    execId,
    true, // enabled
    (event: InterviewMessageEvent) => {
      // Callback when message event received
      setMessagesBySynth(prev => ({
        ...prev,
        [event.synth_id]: [
          ...(prev[event.synth_id] || []),
          event
        ]
      }));
    }
  );

  return {
    messagesBySynth,
    isConnected,
    error,
    synthIds: Object.keys(messagesBySynth)
  };
}
```

#### Data Flow

```
EventSource (SSE)
  → use-sse hook (manages connection, emits events)
  → use-live-interviews hook (aggregates by synth_id)
  → LiveInterviewGrid component
  → LiveInterviewCard components (one per synth)
```

#### State Structure

```typescript
// Example state after 2 synths, 3 messages each
{
  "synth-123": [
    { synth_id: "synth-123", speaker: "Interviewer", text: "Hello...", turn_number: 1, ... },
    { synth_id: "synth-123", speaker: "Interviewee", text: "Hi...", turn_number: 2, ... },
    { synth_id: "synth-123", speaker: "Interviewer", text: "How...", turn_number: 3, ... }
  ],
  "synth-456": [
    { synth_id: "synth-456", speaker: "Interviewer", text: "Hello...", turn_number: 1, ... },
    { synth_id: "synth-456", speaker: "Interviewee", text: "Good morning...", turn_number: 2, ... },
    { synth_id: "synth-456", speaker: "Interviewer", text: "Tell me...", turn_number: 3, ... }
  ]
}
```

#### Message Ordering

- Messages arrive in order from backend (turn_number increments)
- Array append (push) maintains order
- No need for explicit sorting

#### Memory Management

- State accumulates all messages for session duration
- Acceptable because:
  - Typical interview: 10-15 messages × 100 chars = 1.5KB per interview
  - 20 interviews = 30KB total (negligible)
  - State cleared on component unmount (user navigates away)

#### Alternatives Considered

- **useReducer Pattern**: Rejected - overkill for simple append operations, useState is clearer
- **React Query with setQueryData**: Rejected - awkward fit, SSE doesn't integrate with query cache
- **Zustand/Redux**: Rejected - adds dependency for simple local state

#### References

- React useState: https://react.dev/reference/react/useState
- Custom Hooks: https://react.dev/learn/reusing-logic-with-custom-hooks

---

## Summary

All research questions resolved. Key decisions:

1. **SSE Management**: Native EventSource with useEffect, auto-reconnect, readyState monitoring
2. **Auto-Scroll**: scrollIntoView() with user intent detection (50px threshold from bottom)
3. **Performance**: React.memo for cards, no virtualization needed for 10-20 cards
4. **Event Parsing**: TypeScript interfaces matching backend Pydantic models, JSON.parse for data payloads
5. **Message Aggregation**: Custom hook with useState, dictionary keyed by synth_id

**Next Phase**: Generate data-model.md, contracts/, and quickstart.md based on these research findings.
