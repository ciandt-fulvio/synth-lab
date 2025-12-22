# Data Model: Live Interview Cards Display

**Feature**: 014-live-interview-cards
**Date**: 2025-12-21
**Status**: Phase 1 Design

## Purpose

This document defines the data structures, state models, and type definitions required for the Live Interview Cards feature. All types align with backend models and SSE event schemas documented in research.md.

## SSE Event Types

### InterviewMessageEvent

Represents a single message in an interview (interviewer or interviewee turn).

**Source**: Backend `InterviewMessageEvent` model (`src/synth_lab/models/events.py:16-40`)

**TypeScript Definition**:

```typescript
export interface InterviewMessageEvent {
  // Event metadata
  event_type: "message";
  exec_id: string;

  // Interview identification
  synth_id: string;
  turn_number: number;

  // Message content
  speaker: "Interviewer" | "Interviewee";
  text: string;  // May contain JSON-formatted response, requires extractMessageText()

  // Timing
  timestamp: string;  // ISO 8601 datetime string
  is_replay: boolean; // true for historical messages, false for new live messages
}
```

**Field Descriptions**:

- `event_type`: Always "message" for interview turns
- `exec_id`: Research execution identifier (UUID format)
- `synth_id`: Synthetic person identifier (UUID format)
- `turn_number`: Sequential number of this turn in the interview (1-indexed)
- `speaker`: Role of the speaker - "Interviewer" (SynthLab) or "Interviewee" (synth)
- `text`: Message text content. May be JSON string like `{"message": "...", "should_end": false}` requiring extraction via `extractMessageText()`
- `timestamp`: ISO 8601 datetime when message was generated
- `is_replay`: Indicates if this is a historical message (replay on connection) or new live message

**Validation Rules**:

- `synth_id` must be valid UUID
- `turn_number` must be positive integer
- `speaker` must be exactly "Interviewer" or "Interviewee" (case-sensitive)
- `text` must not be empty string
- `timestamp` must be valid ISO 8601 datetime

**Example**:

```json
{
  "event_type": "message",
  "exec_id": "exec-abc-123",
  "synth_id": "synth-xyz-789",
  "turn_number": 3,
  "speaker": "Interviewee",
  "text": "{\"message\": \"Eu prefiro comprar na Amazon pela conveniência e rapidez na entrega.\", \"should_end\": false}",
  "timestamp": "2025-12-21T14:30:45.123Z",
  "is_replay": false
}
```

---

### TranscriptionCompletedEvent

Signals that all interviews in an execution have finished transcription.

**Source**: Backend SSE router (`src/synth_lab/api/routers/research.py:258-267`)

**TypeScript Definition**:

```typescript
export interface TranscriptionCompletedEvent {
  successful_count: number;  // Number of interviews completed successfully
  failed_count: number;      // Number of interviews that failed
}
```

**Field Descriptions**:

- `successful_count`: Count of interviews that completed without errors
- `failed_count`: Count of interviews that encountered errors and failed

**Example**:

```json
{
  "successful_count": 8,
  "failed_count": 2
}
```

---

### ExecutionCompletedEvent

Signals that all processing (interviews + summary generation) has finished.

**Source**: Backend SSE router (`src/synth_lab/api/routers/research.py:246,255-256`)

**TypeScript Definition**:

```typescript
export interface ExecutionCompletedEvent {
  // Empty payload - event type itself is the signal
}
```

**SSE Format**:

```
event: execution_completed
data: {}

```

---

## Component State Models

### LiveInterviewCardProps

Props for the individual card component.

```typescript
export interface LiveInterviewCardProps {
  // Identifiers
  execId: string;
  synthId: string;

  // Message data
  messages: InterviewMessageEvent[];

  // Interaction
  onClick: (synthId: string) => void;
}
```

**Field Descriptions**:

- `execId`: Research execution ID (for opening full transcript dialog)
- `synthId`: Synth ID for this specific interview
- `messages`: Array of interview messages for this synth (in chronological order)
- `onClick`: Callback when card is clicked (opens TranscriptDialog)

---

### LiveInterviewGridProps

Props for the grid container component.

```typescript
export interface LiveInterviewGridProps {
  execId: string;  // Research execution to display interviews for
}
```

---

### LiveInterviewMessages

State structure for aggregated messages by synth.

```typescript
export interface LiveInterviewMessages {
  [synthId: string]: InterviewMessageEvent[];
}
```

**Structure**:

- **Keys**: Synth IDs (UUIDs)
- **Values**: Arrays of InterviewMessageEvent in chronological order (by turn_number)

**Example**:

```typescript
{
  "synth-abc-123": [
    { synth_id: "synth-abc-123", turn_number: 1, speaker: "Interviewer", text: "Olá!...", ... },
    { synth_id: "synth-abc-123", turn_number: 2, speaker: "Interviewee", text: "Oi...", ... },
    { synth_id: "synth-abc-123", turn_number: 3, speaker: "Interviewer", text: "Como...", ... }
  ],
  "synth-def-456": [
    { synth_id: "synth-def-456", turn_number: 1, speaker: "Interviewer", text: "Olá!...", ... },
    { synth_id: "synth-def-456", turn_number: 2, speaker: "Interviewee", text: "Bom dia...", ... }
  ]
}
```

---

### SSEHookState

State returned by the `useSSE` hook.

```typescript
export interface SSEHookState {
  // Connection status
  isConnected: boolean;   // true when EventSource.readyState === OPEN
  error: Error | null;    // Error if connection fails

  // Event handlers (set by consumer)
  onMessage?: (event: InterviewMessageEvent) => void;
  onTranscriptionCompleted?: (data: TranscriptionCompletedEvent) => void;
  onExecutionCompleted?: () => void;
}
```

---

### LiveInterviewsHookState

State returned by the `useLiveInterviews` hook.

```typescript
export interface LiveInterviewsHookState {
  // Aggregated messages
  messagesBySynth: LiveInterviewMessages;

  // Connection status (from SSE hook)
  isConnected: boolean;
  error: Error | null;

  // Derived data
  synthIds: string[];  // Array of synth IDs (keys of messagesBySynth)
}
```

---

## Synth Identification Data

Uses existing types from `frontend/src/types/index.ts`.

### SynthSummary (Existing Type - No Changes)

```typescript
export interface SynthSummary {
  id: string;
  nome: string;  // Full name (e.g., "Maria Silva")
  demografia?: {
    idade?: number;
    // ... other fields
  };
  // ... other fields
}
```

**Usage in Live Cards**:

- Fetch via `getSynth(synthId)` for each card
- Extract first name: `nome.split(' ')[0]`
- Display age: `demografia?.idade` (optional, may be undefined)
- Avatar URL: `getSynthAvatarUrl(synthId)`

---

## Message Text Extraction

### extractMessageText Function

Utility function to extract human-readable text from potentially JSON-formatted message text.

**Location**: `frontend/src/lib/message-utils.ts` (new file, extracted from TranscriptDialog logic)

**Signature**:

```typescript
export function extractMessageText(text: string): string;
```

**Logic** (from `frontend/src/components/shared/TranscriptDialog.tsx:30-65`):

1. Check if text is JSON format (starts with `{` and ends with `}`)
2. Attempt JSON.parse()
   - If successful and has `message` field: return `parsed.message`
3. If parse fails (malformed JSON with newlines):
   - Use regex to extract `"message": "..."` value
   - Unescape `\n`, `\"`, `\\` characters
4. If no JSON detected: return original text

**Example Inputs/Outputs**:

```typescript
// JSON-formatted message
extractMessageText('{"message": "Eu prefiro Amazon.", "should_end": false}')
// → "Eu prefiro Amazon."

// Malformed JSON (newlines)
extractMessageText('{"message": "Linha 1\nLinha 2", "should_end": false}')
// → "Linha 1\nLinha 2"

// Plain text
extractMessageText('Hello, how are you?')
// → "Hello, how are you?"
```

---

## State Transitions

### SSE Connection Lifecycle

```
[Disconnected]
    ↓ (useSSE hook initialized with enabled=true)
[Connecting] (EventSource.CONNECTING)
    ↓ (onopen event)
[Connected] (EventSource.OPEN, isConnected=true)
    ↓ (messages received)
[Receiving Messages] (continuous)
    ↓ (execution_completed event OR user navigates away)
[Closed] (EventSource.CLOSED, isConnected=false)
```

**Error States**:

```
[Connected]
    ↓ (network error, server error)
[Reconnecting] (EventSource auto-reconnects)
    ↓ (successful reconnection)
[Connected] (back to receiving)

    OR

    ↓ (fatal error, readyState=CLOSED)
[Error] (error state, isConnected=false, error object set)
```

---

### Message Aggregation Flow

```
1. SSE Connection Opens
   → Historical messages replayed (is_replay=true)
   → Messages added to messagesBySynth state

2. Historical Replay Completes
   → All existing interviews have messages populated
   → Cards render with initial conversation state

3. Live Messages Arrive (is_replay=false)
   → New messages appended to respective synth arrays
   → Cards auto-scroll to show newest messages

4. Transcription Completed
   → No new messages arrive
   → Cards show final conversation state

5. Execution Completed
   → SSE connection closes
   → Final state persists until user navigates away
```

---

## Data Relationships

```
ResearchExecution (1)
    ↓ has many
InterviewMessageEvents (N)
    ↓ groups by
LiveInterviewMessages { [synthId]: Message[] }
    ↓ renders in
LiveInterviewCard (N cards, one per synth)
    ↓ each fetches
SynthSummary (for avatar, name, age)
```

---

## Validation & Constraints

### Message Ordering

- **Assumption**: Backend sends messages in chronological order by turn_number
- **Verification**: Turn numbers increment sequentially (1, 2, 3, ...)
- **Enforcement**: Frontend appends to array without sorting (maintains order)

### Synth ID Uniqueness

- **Constraint**: Each synth has exactly one interview in a research execution
- **Verification**: synth_id is unique within an execution
- **Enforcement**: Dictionary key (synthId) naturally prevents duplicates

### Card Display Order

- **Requirement**: FR-012 - Cards MUST display in consistent order
- **Implementation**: Sort synth IDs alphabetically OR preserve order of first message arrival
- **Rationale**: Prevents layout shifts when new cards appear

### Maximum Card Count

- **Soft Limit**: 10-20 interviews (typical usage)
- **Hard Limit**: None enforced, but performance tested up to 20 cards
- **Fallback**: If >20, consider pagination or virtualization (not in current scope)

---

## Type Export Structure

All types will be exported from `frontend/src/types/sse-events.ts` (new file):

```typescript
// frontend/src/types/sse-events.ts

// Event types
export interface InterviewMessageEvent { ... }
export interface TranscriptionCompletedEvent { ... }
export interface ExecutionCompletedEvent { ... }

// Component prop types
export interface LiveInterviewCardProps { ... }
export interface LiveInterviewGridProps { ... }

// State types
export interface LiveInterviewMessages { ... }
export interface SSEHookState { ... }
export interface LiveInterviewsHookState { ... }

// Utility types
export type SSEEventType = "message" | "transcription_completed" | "execution_completed";
```

Existing types (SynthSummary, ResearchExecutionDetail) remain in `frontend/src/types/index.ts`.

---

## Summary

This data model provides:

1. **Type Safety**: TypeScript interfaces for all SSE events and component state
2. **Backend Alignment**: Matches Pydantic models from backend
3. **Clear State Structure**: Dictionary-based message aggregation by synth_id
4. **Validation Rules**: Constraints for data integrity
5. **State Transitions**: Documented lifecycles for SSE and message aggregation

All types are ready for implementation in Phase 2 (tasks generation and coding).
