# Implementation Plan: Live Interview Cards Display

**Branch**: `014-live-interview-cards` | **Date**: 2025-12-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-live-interview-cards/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a real-time monitoring view for parallel interviews using a two-column grid of live cards (200px height each). Each card displays ongoing interview conversations with auto-scrolling to newest messages, synth identification (avatar, name, age), and click-to-expand functionality to open full TranscriptDialog. The feature leverages the existing `/research/{exec_id}/stream` Server-Sent Events API for real-time message updates instead of polling.

## Technical Context

**Language/Version**: TypeScript 5.5.3
**Primary Dependencies**: React 18.3.1, shadcn/ui, TanStack React Query 5.56, React Router DOM 6.26
**Storage**: N/A (frontend-only feature, consumes existing backend API)
**Testing**: Vitest (existing frontend testing framework)
**Target Platform**: Web (desktop-first, responsive for mobile)
**Project Type**: Web (frontend component)
**Performance Goals**: Handle 10+ parallel interview cards with smooth scrolling, <2s message latency
**Constraints**: Cards must maintain 200px height, two-column layout required, auto-scroll to newest messages
**Scale/Scope**: Support 10+ concurrent interviews, reuse existing TranscriptDialog and API services

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Evaluation

| Principle | Evaluation | Status |
|-----------|------------|--------|
| **I. Test-First Development (TDD/BDD)** | Component tests will be written before implementation, focusing on: card rendering, message display, auto-scroll behavior, SSE integration, click-to-expand interaction. BDD scenarios already defined in spec.md user stories. | ✅ PASS |
| **II. Fast Test Battery on Every Commit** | Component unit tests (rendering, event handlers) will complete in <1s. SSE integration tests may use mocks for speed. | ✅ PASS |
| **III. Complete Test Battery Before PRs** | Will include: unit tests (components), integration tests (SSE + React Query), visual regression tests (card layout), E2E tests (user flow from detail page to live cards to transcript popup). | ✅ PASS |
| **IV. Frequent Version Control Commits** | Commits at: SSE hook implementation, LiveInterviewCard component, LiveInterviewGrid component, integration with InterviewDetail page, styling/layout adjustments. | ✅ PASS |
| **V. Simplicity and Code Quality** | Components will be <300 lines each. Reuses existing TranscriptDialog, extractMessageText logic, synth APIs. Minimal new dependencies (native EventSource API). | ✅ PASS |
| **VI. Language** | Code in English, documentation in Portuguese. UI strings will use existing i18n pattern (Portuguese strings, externalized for future i18n). | ✅ PASS |
| **VII. Architecture** | Follows existing frontend architecture: `/components/interviews/` for new components, `/hooks/` for SSE hook, `/services/research-api.ts` already has getStreamUrl. Aligns with existing patterns. | ✅ PASS |
| **VIII. Logging** | Browser console logging for SSE connection states, errors. Aligns with existing frontend logging patterns. | ✅ PASS |
| **IX. Other Principles** | DRY: reuses TranscriptDialog, extractMessageText, synth services. SOLID: components have single responsibilities. KISS: native EventSource, no complex state management. | ✅ PASS |

**Overall Gate Status**: ✅ **PASSED** - All principles satisfied. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/014-live-interview-cards/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0: SSE patterns, auto-scroll techniques, performance optimization
├── data-model.md        # Phase 1: SSE event types, card state model
├── quickstart.md        # Phase 1: Usage guide for live cards view
├── contracts/           # Phase 1: SSE event schemas
│   └── sse-events.yaml  # EventSource message, transcription_completed, execution_completed events
└── checklists/
    └── requirements.md  # Spec quality validation (already created)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/
│   │   ├── interviews/
│   │   │   ├── InterviewDetail.tsx         # [MODIFY] Add live cards view toggle/section
│   │   │   ├── LiveInterviewCard.tsx       # [NEW] Single card component (200px, scrollable)
│   │   │   ├── LiveInterviewGrid.tsx       # [NEW] Two-column grid container
│   │   │   └── ...existing components...
│   │   └── shared/
│   │       └── TranscriptDialog.tsx        # [REUSE] No changes needed
│   │
│   ├── hooks/
│   │   ├── use-sse.ts                      # [MODIFY] Implement EventSource connection
│   │   └── use-live-interviews.ts          # [NEW] Aggregate SSE messages by synth_id
│   │
│   ├── services/
│   │   └── research-api.ts                 # [EXISTING] Already has getStreamUrl
│   │
│   ├── types/
│   │   ├── index.ts                        # [MODIFY] Add SSE event types
│   │   └── ...existing types...
│   │
│   └── lib/
│       └── message-utils.ts                # [NEW] extractMessageText (extracted from TranscriptDialog)
│
└── tests/
    ├── components/
    │   └── interviews/
    │       ├── LiveInterviewCard.test.tsx      # [NEW] Component rendering, auto-scroll
    │       └── LiveInterviewGrid.test.tsx      # [NEW] Layout, SSE integration
    └── hooks/
        ├── use-sse.test.ts                     # [NEW] EventSource lifecycle, event handling
        └── use-live-interviews.test.tsx        # [NEW] Message aggregation by synth
```

**Structure Decision**: Web application (frontend only). New components added to existing `frontend/src/components/interviews/` directory following established patterns. SSE hook implementation completes the placeholder in `frontend/src/hooks/use-sse.ts`. No backend changes required - leverages existing `/research/{exec_id}/stream` endpoint.

## Complexity Tracking

No complexity violations identified. Feature leverages existing patterns and APIs, introduces minimal new code, and follows constitution principles.

## Research Questions (Phase 0)

The following questions will be answered in `research.md`:

1. **SSE Best Practices**: How to handle EventSource reconnection, error states, and cleanup in React? What are common pitfalls with SSE in modern browsers?

2. **Auto-Scroll Techniques**: What's the best approach for auto-scrolling to newest messages while preserving user's manual scroll position when they're reviewing older messages?

3. **Performance Optimization**: How to efficiently render and update 10+ cards simultaneously? Are there virtualization techniques needed for the grid? What are React Query strategies for managing per-card data?

4. **SSE Event Message Parsing**: The SSE endpoint sends events with types (message, transcription_completed, execution_completed). How are these typically structured in the `data` payload? Need to research event format from backend implementation.

5. **Message Aggregation Strategy**: How to aggregate SSE messages by synth_id for display in individual cards? Should we use a reducer pattern, or is React Query's cache sufficient?

## Design Artifacts (Phase 1)

### Data Model (data-model.md)

Will define:
- SSE Event types (message, transcription_completed, execution_completed)
- Message payload structure (synth_id, speaker, text, timestamp)
- Card state model (messages array, scroll position, loading/error states)
- Synth identification data (id, name, age, avatar URL)

### API Contracts (contracts/sse-events.yaml)

Will document:
- EventSource endpoint: `GET /api/research/{exec_id}/stream`
- Event types and data formats
- Error responses and reconnection behavior
- Historical message replay mechanism

### Quickstart Guide (quickstart.md)

Will cover:
- How to access live cards view from InterviewDetail page
- How to monitor multiple interviews simultaneously
- How to click a card to open full transcript
- How auto-scroll behaves
- How to interpret card states (active, completed, failed)

## Implementation Strategy

### Component Hierarchy

```
InterviewDetail (page)
└── LiveInterviewGrid (new)
    ├── LiveInterviewCard (new) [for each synth]
    │   ├── Card Header (synth avatar, name, age)
    │   ├── ScrollArea (200px fixed height)
    │   │   └── Message list (speaker + text)
    │   └── Click handler (opens TranscriptDialog)
    └── TranscriptDialog (existing, opened on card click)
```

### State Management

- **SSE Connection**: `use-sse.ts` hook manages EventSource lifecycle, emits raw events
- **Message Aggregation**: `use-live-interviews.ts` hook consumes SSE events, groups by synth_id, maintains message history
- **Per-Card State**: Each LiveInterviewCard manages its own scroll position via ref, receives messages as prop
- **Dialog State**: InterviewDetail page manages which card's transcript is shown in popup (existing pattern)

### Styling Approach

- Reuse existing card styles from shadcn/ui Card component
- Match TranscriptDialog message formatting (blue #2563eb for SynthLab, green #16a34a for synth)
- Use CSS Grid for two-column layout with responsive breakpoints (single column on mobile)
- Fixed 200px height with overflow-y-auto for internal scrolling
- Match existing spacing and typography from InterviewDetail page

## Testing Strategy

### Unit Tests

- **LiveInterviewCard.test.tsx**: Render with messages, verify header format, test click handler, verify message text extraction, test scroll behavior
- **LiveInterviewGrid.test.tsx**: Render with multiple cards, verify two-column layout, verify responsive behavior
- **use-sse.test.ts**: EventSource lifecycle, event parsing, error handling, cleanup on unmount
- **use-live-interviews.test.ts**: Message aggregation by synth_id, message ordering, state updates

### Integration Tests

- SSE hook + React Query: Verify messages appear in cards within expected latency
- Card click → TranscriptDialog opening: Verify dialog receives correct exec_id and synth_id
- Background updates: Verify cards continue updating when dialog is open

### E2E Tests

- Navigate to InterviewDetail → start 4 interviews → verify 4 cards appear
- Wait for messages → verify cards auto-scroll to newest
- Click card → verify TranscriptDialog opens with correct conversation
- Close dialog → verify return to live cards view without state loss

### Visual Regression Tests

- Two-column grid layout at various viewport widths
- Card height consistency at 200px
- Message formatting matches TranscriptDialog
- Synth avatar and header display

## Rollout Plan

1. **Phase 0 Complete**: Merge research.md with SSE patterns and auto-scroll techniques
2. **Phase 1 Complete**: Merge data-model.md, contracts, quickstart guide
3. **Implement SSE Hook**: Complete use-sse.ts implementation (TDD: write tests first)
4. **Implement Message Aggregation**: Create use-live-interviews.ts hook (TDD)
5. **Implement LiveInterviewCard**: Create component with tests (TDD)
6. **Implement LiveInterviewGrid**: Create grid layout with tests (TDD)
7. **Integrate with InterviewDetail**: Add live cards section to page (TDD for integration)
8. **Manual Testing**: Start multiple interviews, verify real-time behavior
9. **Performance Testing**: Test with 10+ concurrent interviews
10. **PR Review**: Complete test battery passes, documentation updated
11. **Merge to Main**: Deploy to staging, then production

## Risk Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| SSE connection instability (network issues, browser tabs) | High - users lose real-time updates | Medium | Implement auto-reconnect with exponential backoff, show connection status indicator, graceful degradation to polling if SSE fails |
| Performance degradation with 10+ cards | High - poor UX | Low | Virtualize card grid if needed, throttle message updates, profile with React DevTools, consider memoization |
| Auto-scroll conflicts with user review | Medium - annoying UX | Medium | Detect user scroll events, pause auto-scroll when user scrolls up, resume on manual scroll to bottom |
| Message parsing errors (malformed JSON) | Medium - messages not displayed | Low | Reuse existing extractMessageText logic from TranscriptDialog, add error boundaries, log parsing failures |
| Browser compatibility (EventSource support) | Low - most modern browsers support SSE | Low | Add feature detection, fallback to polling if EventSource unavailable, document browser requirements |

## Constitution Re-Check (Post-Design)

| Principle | Evaluation | Status |
|-----------|------------|--------|
| **I. Test-First Development** | Test files identified in structure: LiveInterviewCard.test.tsx, LiveInterviewGrid.test.tsx, use-sse.test.ts, use-live-interviews.test.ts. All will follow TDD (tests before implementation). | ✅ PASS |
| **II. Fast Test Battery** | Component tests use mocked SSE events (no real network), expected to run in <1s total. | ✅ PASS |
| **III. Complete Test Battery** | Includes unit, integration, E2E, visual regression tests as documented in Testing Strategy. | ✅ PASS |
| **IV. Frequent Commits** | 10-step rollout plan ensures atomic commits at each phase. | ✅ PASS |
| **V. Simplicity and Code Quality** | LiveInterviewCard estimated ~150 lines, LiveInterviewGrid ~100 lines, use-sse.ts ~120 lines, use-live-interviews.ts ~80 lines. All under limits. No new external dependencies (native EventSource). | ✅ PASS |
| **VI. Language** | Code in English (components, hooks), docs in Portuguese (quickstart.md), UI strings in Portuguese (matching existing pattern). | ✅ PASS |
| **VII. Architecture** | Follows existing frontend structure. No new directories introduced. Fits into established component hierarchy. | ✅ PASS |

**Overall Gate Status**: ✅ **PASSED** - Design maintains constitution compliance.

## Next Steps

1. Run `/speckit.plan` Phase 0: Generate `research.md`
2. Run `/speckit.plan` Phase 1: Generate `data-model.md`, `contracts/`, `quickstart.md`
3. Run `/speckit.tasks`: Generate `tasks.md` organized by user stories
4. Begin TDD implementation following rollout plan
