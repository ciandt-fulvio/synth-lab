# Tasks: Live Interview Cards Display

**Input**: Design documents from `/specs/014-live-interview-cards/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/sse-events.yaml

**Tests**: This feature follows Test-Driven Development (TDD). All test tasks MUST be completed (and FAIL) before implementation tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story (P1: Monitor Active Interviews, P2: View Details Without Losing Context, P3: Identify Participants).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: All paths are `frontend/src/...` and `frontend/tests/...`
- **No backend changes**: This feature is frontend-only, leveraging existing SSE API

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: TypeScript type definitions and utility functions that all components will use

- [X] T001 Create SSE event type definitions in frontend/src/types/sse-events.ts (InterviewMessageEvent, TranscriptionCompletedEvent, ExecutionCompletedEvent)
- [X] T002 [P] Extract extractMessageText utility function from TranscriptDialog to frontend/src/lib/message-utils.ts
- [X] T003 [P] Export new SSE types from frontend/src/types/sse-events.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core SSE infrastructure that ALL user stories depend on for real-time updates

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Write unit tests for useSSE hook in frontend/tests/hooks/use-sse.test.ts (EventSource lifecycle, onopen, onerror, cleanup, event parsing)
- [ ] T005 [P] Write unit tests for useLiveInterviews hook in frontend/tests/hooks/use-live-interviews.test.ts (message aggregation by synth_id, state updates)
- [ ] T006 Implement useSSE hook in frontend/src/hooks/use-sse.ts (EventSource connection management, event listeners for message/transcription_completed/execution_completed, auto-reconnect on error, cleanup on unmount)
- [ ] T007 Implement useLiveInterviews hook in frontend/src/hooks/use-live-interviews.ts (consume useSSE, aggregate messages by synth_id in LiveInterviewMessages state, provide synthIds array)
- [ ] T008 Verify SSE hooks integration: Run tests T004 and T005, confirm they now pass with implementations T006 and T007

**Checkpoint**: SSE foundation ready - all user stories can now access real-time interview messages

---

## Phase 3: User Story 1 - Monitor Active Interviews in Real-Time (Priority: P1) 🎯 MVP

**Goal**: Display all interviews from an execution as live cards in a two-column grid, with auto-scrolling to newest messages and real-time updates via SSE

**Independent Test**: Start 4 interviews in parallel, navigate to InterviewDetail page, verify 4 cards appear in two-column layout, verify messages auto-scroll as they arrive, verify all cards remain visible regardless of status (active/completed/failed)

### Tests for User Story 1 (TDD - Write Tests First) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Write unit test for LiveInterviewCard in frontend/tests/components/interviews/LiveInterviewCard.test.tsx (render with messages, verify 200px height, verify scroll to bottom on new messages, verify auto-scroll pause when user scrolls up)
- [ ] T010 [P] [US1] Write unit test for LiveInterviewGrid in frontend/tests/components/interviews/LiveInterviewGrid.test.tsx (render with messagesBySynth, verify two-column grid layout, verify responsive single-column on mobile, verify card ordering consistency)

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement LiveInterviewCard component in frontend/src/components/interviews/LiveInterviewCard.tsx (200px fixed height ScrollArea, message list with speaker colors, scrollIntoView auto-scroll with 50px threshold detection, onClick handler)
- [ ] T012 [P] [US1] Implement LiveInterviewGrid component in frontend/src/components/interviews/LiveInterviewGrid.tsx (use useLiveInterviews hook, render cards in grid grid-cols-2 gap-4, pass messages and onClick to each card, responsive breakpoint for single column)
- [ ] T013 [US1] Integrate LiveInterviewGrid into InterviewDetail page in frontend/src/pages/InterviewDetail.tsx (add LiveInterviewGrid component below interview info section, pass execId prop, manage TranscriptDialog state for card clicks)
- [ ] T014 [US1] Verify User Story 1 tests: Run T009 and T010, confirm they now pass with implementations T011, T012, T013
- [ ] T015 [US1] Manual validation: Start 4 interviews, verify live cards display, verify auto-scroll, verify two-column layout, verify cards remain visible for all statuses

**Checkpoint**: At this point, User Story 1 is fully functional - researchers can monitor multiple interviews in real-time without navigation

---

## Phase 4: User Story 2 - View Interview Details Without Losing Context (Priority: P2)

**Goal**: Enable clicking a live card to open the full TranscriptDialog popup while keeping live cards updating in the background

**Independent Test**: Display live cards, click on one card, verify TranscriptDialog opens with 70vw×80vh dimensions, close dialog, verify return to live cards without losing scroll position or state, verify other cards continued updating during dialog display

### Tests for User Story 2 (TDD - Write Tests First) ⚠️

- [ ] T016 [P] [US2] Write integration test for card click → dialog flow in frontend/tests/components/interviews/LiveInterviewCard.test.tsx (simulate card click, verify onClick callback with synthId, verify TranscriptDialog receives correct props)
- [ ] T017 [P] [US2] Write integration test for background updates in frontend/tests/components/interviews/LiveInterviewGrid.test.tsx (open dialog, simulate new SSE messages, verify non-dialog cards update, close dialog, verify state preserved)

### Implementation for User Story 2

- [ ] T018 [US2] Update LiveInterviewCard onClick handler in frontend/src/components/interviews/LiveInterviewCard.tsx (ensure entire card is clickable, pass synthId to parent callback)
- [ ] T019 [US2] Update InterviewDetail page TranscriptDialog integration in frontend/src/pages/InterviewDetail.tsx (add selectedSynthId state, handle card onClick to set selectedSynthId, pass execId and synthId to TranscriptDialog, handle onOpenChange to clear selectedSynthId)
- [ ] T020 [US2] Verify User Story 2 tests: Run T016 and T017, confirm they now pass with implementations T018 and T019
- [ ] T021 [US2] Manual validation: Click card, verify dialog opens, verify background cards updating, close dialog, verify state preserved

**Checkpoint**: At this point, User Stories 1 AND 2 both work independently - researchers can both monitor and deep-dive without losing context

---

## Phase 5: User Story 3 - Identify Interview Participants at a Glance (Priority: P3)

**Goal**: Display synth avatar, name, and age in each card header to help researchers quickly identify which synth is being interviewed

**Independent Test**: Display live cards, verify each card header shows synth avatar (or fallback User icon), first name, and age in format "Entrevista com [FirstName], [Age] anos", verify cards without age show "Entrevista com [FirstName]"

### Tests for User Story 3 (TDD - Write Tests First) ⚠️

- [ ] T022 [P] [US3] Write unit test for card header in frontend/tests/components/interviews/LiveInterviewCard.test.tsx (render with synth data, verify avatar displays, verify name format with age, verify name format without age, verify fallback User icon when no avatar)

### Implementation for User Story 3

- [ ] T023 [US3] Add synth data fetching to LiveInterviewCard in frontend/src/components/interviews/LiveInterviewCard.tsx (use useQuery with getSynth(synthId), extract firstName from nome.split(' ')[0], format title with age if available, render Avatar with getSynthAvatarUrl(synthId), add User fallback icon)
- [ ] T024 [US3] Verify User Story 3 tests: Run T022, confirm it now passes with implementation T023
- [ ] T025 [US3] Manual validation: View cards, verify avatars display, verify name/age format matches spec, verify fallback icon for missing avatars

**Checkpoint**: All user stories are now independently functional - complete live monitoring experience

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Refinements that improve the complete feature across all user stories

- [ ] T026 [P] Add message text extraction to LiveInterviewCard in frontend/src/components/interviews/LiveInterviewCard.tsx (import extractMessageText from message-utils, apply to each message.text before display)
- [ ] T027 [P] Add speaker color styling to LiveInterviewCard messages in frontend/src/components/interviews/LiveInterviewCard.tsx (blue #2563eb for "Interviewer"/SynthLab, green #16a34a for "Interviewee"/synth name, match TranscriptDialog styling)
- [ ] T028 [P] Add React.memo optimization to LiveInterviewCard in frontend/src/components/interviews/LiveInterviewCard.tsx (memoize with custom comparison on messages and synthId props)
- [ ] T029 [P] Add connection status indicator to LiveInterviewGrid in frontend/src/components/interviews/LiveInterviewGrid.tsx (display isConnected and error states from useLiveInterviews, show reconnecting message if disconnected)
- [ ] T030 [P] Add loading states to LiveInterviewCard in frontend/src/components/interviews/LiveInterviewCard.tsx (show Loader2 spinner while synth data fetching, show empty state if no messages yet)
- [ ] T031 [P] Add error boundaries around LiveInterviewGrid in frontend/src/pages/InterviewDetail.tsx (catch rendering errors, display user-friendly error message, log to console)
- [ ] T032 Performance testing: Start 10+ interviews, verify smooth scrolling, verify message updates within 2s latency, profile with React DevTools
- [ ] T033 Browser compatibility testing: Test in Chrome, Firefox, Safari, Edge, verify EventSource support, verify fallback message if EventSource unavailable
- [ ] T034 Responsive testing: Test at mobile viewport (single column), tablet (two columns), desktop (two columns), verify layout adapts correctly
- [ ] T035 Visual regression testing: Verify card height 200px, verify message formatting matches TranscriptDialog, verify avatar and header display, verify grid spacing consistent
- [ ] T036 Run quickstart.md validation: Follow quickstart guide steps, verify all scenarios work as documented

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001-T003) - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational (T004-T008) completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (US1 → US2 → US3)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Foundational (T008) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1 (T015) - Needs LiveInterviewCard and LiveInterviewGrid to exist
- **User Story 3 (P3)**: Depends on User Story 1 (T015) - Enhances existing cards with synth identification

### Within Each User Story

**TDD Workflow (CRITICAL)**:
1. Tests FIRST (must FAIL with clear error)
2. Implementation to make tests PASS
3. Verification that tests now pass
4. Manual validation against acceptance scenarios

**Task Order Within Story**:
- Tests before implementation (TDD)
- Components before integration
- Verification before moving to next story

### Parallel Opportunities

- **Phase 1 Setup**: All tasks (T001-T003) can run in parallel [P]
- **Phase 2 Foundational Tests**: T004 and T005 can run in parallel [P]
- **Phase 2 Foundational Implementation**: T006 and T007 can run in parallel [P] (after tests written)
- **User Story Tests**: All test tasks within a story marked [P] can run in parallel
- **User Story Components**: T011 and T012 in US1 can run in parallel [P]
- **Polish Tasks**: Most Phase 6 tasks (T026-T031) can run in parallel [P]
- **Different User Stories**: After Foundational complete, US1, US2, US3 can be worked on by different team members in parallel (though US2 and US3 enhance US1)

---

## Parallel Example: User Story 1

```bash
# 1. Write all tests for US1 together (they should FAIL):
Task T009: "Write LiveInterviewCard unit test" (parallel)
Task T010: "Write LiveInterviewGrid unit test" (parallel)

# 2. Implement components in parallel (tests should now PASS):
Task T011: "Implement LiveInterviewCard component" (parallel)
Task T012: "Implement LiveInterviewGrid component" (parallel)

# 3. Integration (depends on T011 and T012):
Task T013: "Integrate LiveInterviewGrid into InterviewDetail page"

# 4. Verification (sequential):
Task T014: "Verify US1 tests pass"
Task T015: "Manual validation"
```

---

## Parallel Example: Multiple User Stories

```bash
# After Foundational (T008) completes, if you have 3 developers:

Developer A (works on US1 - Priority P1):
- T009, T010 (tests)
- T011, T012 (implementation)
- T013, T014, T015 (integration & verification)

Developer B (starts US2 after A finishes T013):
- T016, T017 (tests)
- T018, T019 (implementation)
- T020, T021 (verification)

Developer C (starts US3 after A finishes T013):
- T022 (tests)
- T023 (implementation)
- T024, T025 (verification)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only) - RECOMMENDED

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T008) - CRITICAL
3. Complete Phase 3: User Story 1 (T009-T015)
4. **STOP and VALIDATE**: Test US1 independently using quickstart.md
5. Deploy/demo if ready - researchers can now monitor interviews in real-time

**Why MVP First?**
- Delivers core value (real-time monitoring) quickly
- User Story 1 is independently testable and valuable
- Can gather feedback before investing in P2/P3
- Reduces risk by validating SSE infrastructure with simplest use case

### Incremental Delivery

1. Complete Setup + Foundational (T001-T008) → SSE foundation ready
2. Add User Story 1 (T009-T015) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (T016-T021) → Test independently → Deploy/Demo (click-to-expand)
4. Add User Story 3 (T022-T025) → Test independently → Deploy/Demo (synth identification)
5. Add Polish (T026-T036) → Final refinements → Production ready
6. Each story adds value without breaking previous stories

### Full Feature (All Stories)

If implementing all stories from the start:

1. Setup (T001-T003)
2. Foundational (T004-T008)
3. US1 (T009-T015)
4. US2 (T016-T021) - Can start in parallel with US3 if staffed
5. US3 (T022-T025) - Can start in parallel with US2 if staffed
6. Polish (T026-T036)

---

## Test-Driven Development (TDD) Checklist

Before marking any implementation task complete, verify:

- [ ] Test was written BEFORE implementation
- [ ] Test FAILED with clear, expected error message
- [ ] Implementation makes test PASS
- [ ] No test modifications needed to make it pass (test was correct)
- [ ] Manual validation confirms behavior matches acceptance scenarios
- [ ] Code follows constitution principles (functions <30 lines, files <300 lines, no unnecessary complexity)

---

## Notes

- **[P] marker**: Tasks with different file paths and no dependencies can run in parallel
- **[Story] label**: Maps task to specific user story (US1, US2, US3) for traceability
- **TDD CRITICAL**: Write tests first, ensure they fail, then implement to make them pass
- **SSE Foundation**: Phase 2 is critical - all stories depend on useSSE and useLiveInterviews hooks
- **Independent Stories**: Each story can be tested and deployed independently (though US2/US3 enhance US1)
- **File Limits**: LiveInterviewCard ~150 lines, LiveInterviewGrid ~100 lines, hooks ~80-120 lines each (all under 300 line limit)
- **Commit Frequency**: Commit after each task completion or logical group (T-shirt sizing: each task is 30-60 min)
- **Stop Points**: Any checkpoint can be a stop/validation/demo point
- **Avoid**: Vague tasks, same-file conflicts in parallel tasks, skipping tests, implementing before tests

---

## Task Summary

- **Total Tasks**: 36
- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational)**: 5 tasks (BLOCKS all stories)
- **Phase 3 (US1 - MVP)**: 7 tasks (P1 priority - core value)
- **Phase 4 (US2)**: 6 tasks (P2 priority - enhances US1)
- **Phase 5 (US3)**: 4 tasks (P3 priority - enhances US1)
- **Phase 6 (Polish)**: 11 tasks (cross-cutting improvements)

**Parallel Opportunities**: 17 tasks marked [P] can run in parallel (48% of tasks)

**Independent Test Criteria**:
- **US1**: 4 cards in two columns, auto-scroll, real-time updates
- **US2**: Click opens dialog, background updates continue, close preserves state
- **US3**: Avatar, name, age in header for all cards

**Suggested MVP Scope**: Complete through Phase 3 (T001-T015) for core real-time monitoring capability
