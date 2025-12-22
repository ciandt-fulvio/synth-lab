# Feature Specification: Live Interview Cards Display

**Feature Branch**: `014-live-interview-cards`
**Created**: 2025-12-21
**Status**: Draft
**Input**: User description: "exibicao de entrevista conforme elas ocorrem numa situacao dessas queremos mostrar cards com as entrevistas acontecendo. devemos ter duas colunas de cards, com todas as entrevistas que estao ocorrendo em paralelo (mesmo que já finalizadas). cada um dos cards deve ter a mesma aparencia de quando abrimos um popup de entrevista (imagem em anexo), a altura desses cards deve ser 200px, com um scrol interno que vai rolando conforme novas mensagens chegam, de forma a sempre mostrar as mensagens mais novas (na parte inferior da entrevista)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Monitor Active Interviews in Real-Time (Priority: P1)

A researcher initiates multiple parallel interviews and wants to monitor all ongoing conversations simultaneously to observe response patterns, identify interesting insights as they happen, and track overall progress without navigating between individual interview popups.

**Why this priority**: This is the core value proposition - enabling researchers to see all interviews at once. Without this, users must click individual cards repeatedly to check progress, missing the ability to spot patterns and insights in real-time across multiple conversations.

**Independent Test**: Can be fully tested by starting 4 interviews in parallel and verifying that all 4 appear as live cards in a two-column layout, with messages auto-scrolling as they arrive, without requiring any navigation or popup opening.

**Acceptance Scenarios**:

1. **Given** a research execution with 4 active interviews, **When** the user navigates to the interview detail page, **Then** the system displays 4 interview cards arranged in two columns
2. **Given** multiple interview cards are displayed, **When** a new message arrives in any interview, **Then** the corresponding card auto-scrolls to show the newest message at the bottom
3. **Given** an interview card with more messages than fit in 200px height, **When** the user views the card, **Then** the card shows an internal scroll with the view positioned at the most recent messages
4. **Given** multiple interviews in different states (active, completed, failed), **When** viewing the live cards, **Then** all interviews remain visible regardless of their status

---

### User Story 2 - View Interview Details Without Losing Context (Priority: P2)

While monitoring multiple interviews, a researcher spots an interesting response in one of the live cards and wants to read the full conversation history without losing visibility of the other ongoing interviews.

**Why this priority**: Enhances the monitoring experience by allowing deep-dives into specific conversations while maintaining awareness of parallel interviews. This is secondary to the core monitoring capability but important for practical research workflows.

**Independent Test**: Can be tested by displaying live cards, clicking on one to open the full transcript popup, verifying the popup matches the existing TranscriptDialog design, and confirming that live cards remain visible/accessible in the background.

**Acceptance Scenarios**:

1. **Given** live interview cards are displayed, **When** the user clicks on a card, **Then** the system opens the full TranscriptDialog popup matching the existing design (70vw width, 80vh height)
2. **Given** the TranscriptDialog is open from a live card, **When** the user closes the dialog, **Then** the system returns to the live cards view without losing scroll position or state
3. **Given** a TranscriptDialog is open, **When** new messages arrive in other interviews, **Then** the live cards in the background continue to update in real-time

---

### User Story 3 - Identify Interview Participants at a Glance (Priority: P3)

A researcher viewing multiple live interview cards wants to quickly identify which synth is being interviewed in each card without clicking into the full transcript.

**Why this priority**: Improves usability and reduces cognitive load when monitoring many interviews. While helpful, researchers can still effectively monitor conversations without this - the message content itself provides context.

**Independent Test**: Can be tested by displaying live cards and verifying that each card shows the synth avatar, name, and age in the header, matching the format from TranscriptDialog ("Entrevista com [FirstName], [Age] anos").

**Acceptance Scenarios**:

1. **Given** live interview cards are displayed, **When** the user views any card, **Then** each card header shows the synth avatar, first name, and age in the format "Entrevista com [FirstName], [Age] anos"
2. **Given** a synth without an age specified, **When** viewing their live card, **Then** the header shows "Entrevista com [FirstName]" without the age
3. **Given** multiple cards for different synths, **When** viewing the grid, **Then** each card displays a unique avatar helping visually distinguish between interviews

---

### Edge Cases

- What happens when a very long message arrives (e.g., 500+ word response) - does the card maintain the 200px height with internal scroll?
- How does the system handle interviews that complete very quickly (< 5 seconds) - do they still appear as live cards?
- What happens when more than 10 interviews run in parallel - does the two-column layout continue vertically or is there a limit?
- How does the system handle network interruptions during live updates - do cards freeze or show an error state?
- What happens when a synth has no avatar image - does the fallback icon (User) display correctly in the compact card header?
- How does the auto-scroll behave when the user is manually scrolling up to review previous messages - does new message arrival force scroll to bottom or preserve user's position?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display all interviews from a research execution as live cards in a two-column grid layout
- **FR-002**: Each interview card MUST have a fixed height of 200px with internal scrolling for message overflow
- **FR-003**: Each interview card MUST display messages in the same visual format as TranscriptDialog (speaker name in color: blue #2563eb for SynthLab, green #16a34a for synth; followed by message text in gray)
- **FR-004**: Each card header MUST display the synth avatar, first name, and age in the format "Entrevista com [FirstName], [Age] anos"
- **FR-005**: Cards MUST auto-scroll to show the newest messages at the bottom when new messages arrive
- **FR-006**: System MUST update cards in real-time as messages arrive during active interviews
- **FR-007**: Cards MUST remain visible for completed and failed interviews (not just active ones)
- **FR-008**: Users MUST be able to click a card to open the full TranscriptDialog popup without navigating away from the live cards view
- **FR-009**: System MUST continue updating other live cards even when a TranscriptDialog popup is open
- **FR-010**: Each message in a card MUST extract text from JSON-formatted responses using the same `extractMessageText()` logic as TranscriptDialog
- **FR-011**: The two-column layout MUST be responsive and adjust to viewport width
- **FR-012**: Cards MUST display in a consistent order (e.g., by synth_id or interview start time) to prevent layout shifts during updates

### Key Entities

- **Live Interview Card**: Represents a single ongoing or completed interview in the compact card view
  - Displays synth identification (avatar, name, age)
  - Shows conversation messages with speaker labels and colors
  - Maintains scroll position to show most recent messages
  - Links to full transcript via click interaction

- **Interview Message**: A single message in the conversation
  - Speaker identification (interviewer vs synth)
  - Message text (potentially JSON-formatted requiring extraction)
  - Display formatting (color, font weight based on speaker)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can monitor 4+ parallel interviews simultaneously without navigation, seeing all conversations in a single view
- **SC-002**: New messages appear in live cards within 2 seconds of being generated in the backend
- **SC-003**: Users can identify which synth is being interviewed in each card within 1 second (via avatar and name in header)
- **SC-004**: Users can transition from live card monitoring to full transcript view in 1 click, then return to monitoring without losing context
- **SC-005**: The live cards view handles 10+ parallel interviews without performance degradation (smooth scrolling, timely updates)
- **SC-006**: 90% of users successfully use live cards to identify interesting insights across multiple interviews without opening individual popups

## Assumptions

### Technical Assumptions

- The existing API endpoints (`getTranscript()`, `getSynth()`, `getSynthAvatarUrl()`) provide all necessary data for rendering live cards
- Real-time updates can be achieved through polling or the existing query mechanisms (React Query with short refetch intervals)
- The frontend can efficiently render and update 10+ cards simultaneously without significant performance issues
- The two-column grid layout will use standard CSS Grid or Flexbox for responsive behavior

### UX Assumptions

- Users will primarily view this on desktop/laptop screens where a two-column layout makes sense (responsive behavior for mobile can be single column)
- Automatically scrolling to newest messages is always the desired behavior (no user preference for "sticky scroll" when manually reviewing)
- The 200px card height provides enough space to show meaningful conversation context (approximately 4-5 message exchanges)
- Users understand that clicking a card opens the full transcript - no additional "View Full" button needed

### Data Assumptions

- All messages are stored and retrievable via the transcript API
- Message arrival order is consistent and preserved in the API response
- Synth demographic data (name, age) is always available when an interview exists
- Interview status transitions (active → completed/failed) are reliably tracked in the backend

## Dependencies

### Internal Dependencies

- **Existing Components**: Reuses TranscriptDialog component for full transcript view when cards are clicked
- **API Services**: Depends on `research-api.ts` (getTranscript) and `synths-api.ts` (getSynth, getSynthAvatarUrl)
- **Design System**: Uses shadcn/ui components (Card, Avatar, ScrollArea) for consistent styling
- **State Management**: Integrates with React Query for data fetching and real-time updates

### External Dependencies

- None - this is a pure frontend feature using existing backend APIs

## Out of Scope

The following are explicitly **not** included in this feature:

- **Real-time WebSocket updates**: Live cards will use polling or existing query refetch strategies, not dedicated WebSocket connections
- **Card filtering or search**: Users cannot filter cards by synth characteristics or search message content
- **Customizable card height**: The 200px height is fixed per requirements
- **Reordering or sorting controls**: Cards appear in a system-determined order (by synth_id or start time)
- **Interview controls in cards**: No stop/pause buttons - cards are read-only monitoring views
- **Export or sharing from cards**: Users must open full TranscriptDialog to access any export/share features (if they exist)
- **Multi-column layout options**: Always two columns, no user preference for 1, 3, or 4 columns
- **Notifications or alerts**: No highlighting or alerts when specific keywords appear in messages
- **Card minimization**: All cards are always visible at full 200px height, no expand/collapse
