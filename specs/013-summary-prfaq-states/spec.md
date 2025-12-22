# Feature Specification: Summary and PR-FAQ State Management

**Feature Branch**: `013-summary-prfaq-states`
**Created**: 2025-12-21
**Status**: Draft
**Input**: User description: "Backend state management for summary and PR-FAQ generation with prerequisites, states (generate, generating, view), and proper UI state handling"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Summary When Available (Priority: P1)

As a researcher, I want to see the research summary immediately when it becomes available, so that I can quickly understand the insights from the interviews.

**Why this priority**: The summary is the primary output of research execution. Users need immediate access to generated summaries with clear visual indication of availability.

**Independent Test**: Can be fully tested by completing a research execution with at least one successful interview and verifying the summary is accessible via a "Visualizar" button that appears automatically.

**Acceptance Scenarios**:

1. **Given** a research execution has completed with `summary_available = true`, **When** I view the execution details page, **Then** I see a "Visualizar" button for the summary that opens the summary content when clicked.

2. **Given** a research execution is still running, **When** I view the execution details page, **Then** the summary button is disabled with a message indicating the summary is not yet available.

3. **Given** a research execution has failed, **When** I view the execution details page, **Then** the summary button is disabled with appropriate messaging about the failure state.

---

### User Story 2 - Generate PR-FAQ When Prerequisites Met (Priority: P2)

As a researcher, I want to generate a PR-FAQ document from a completed summary, so that I can create a structured product artifact for stakeholders.

**Why this priority**: PR-FAQ generation depends on having a summary first. This is the second most important action after viewing the summary, enabling users to create actionable deliverables.

**Independent Test**: Can be fully tested by having a research execution with an available summary, clicking "Gerar PR/FAQ", observing the loading state, and then viewing the generated PR-FAQ document.

**Acceptance Scenarios**:

1. **Given** a research execution has `summary_available = true` and `prfaq_available = false`, **When** I view the execution details page, **Then** I see a "Gerar" button for PR-FAQ that is enabled.

2. **Given** I click the "Gerar" button for PR-FAQ, **When** the generation starts, **Then** the button shows a loading indicator with "Gerando..." text and becomes non-clickable.

3. **Given** PR-FAQ generation completes successfully, **When** the page updates, **Then** the button changes to "Visualizar" and I can view the generated PR-FAQ content.

4. **Given** a research execution has `summary_available = false`, **When** I view the execution details page, **Then** the PR-FAQ button is disabled with a tooltip explaining "Summary necessario" (summary required as prerequisite).

---

### User Story 3 - View PR-FAQ When Available (Priority: P3)

As a researcher, I want to view a previously generated PR-FAQ, so that I can review or share the document without regenerating it.

**Why this priority**: Once a PR-FAQ is generated, users should be able to access it easily. This is a natural follow-up to generation.

**Independent Test**: Can be fully tested by having a research execution with `prfaq_available = true` and clicking the "Visualizar" button to open the PR-FAQ content.

**Acceptance Scenarios**:

1. **Given** a research execution has `prfaq_available = true`, **When** I view the execution details page, **Then** I see a "Visualizar" button for PR-FAQ that opens the PR-FAQ content when clicked.

2. **Given** I click "Visualizar" for PR-FAQ, **When** the modal/drawer opens, **Then** I see the full PR-FAQ content in markdown format with proper formatting.

---

### User Story 4 - Clear State Indication Across All Artifacts (Priority: P4)

As a researcher, I want to see clear visual indicators for the state of each artifact (summary, PR-FAQ), so that I understand what actions are available to me at any moment.

**Why this priority**: Clear UI feedback prevents user confusion and reduces support requests. Users should never be uncertain about what they can or cannot do.

**Independent Test**: Can be fully tested by viewing execution details in various states and verifying that button labels, colors, and enabled/disabled states match the documented state machine.

**Acceptance Scenarios**:

1. **Given** any execution state, **When** I view the details page, **Then** each artifact (summary, PR-FAQ) displays its current state clearly via button label and visual styling.

2. **Given** an artifact is in "generating" state, **When** I view the page, **Then** I see a spinner or loading animation and cannot interact with the button until generation completes or fails.

3. **Given** an artifact has a failed generation, **When** I view the page, **Then** I see an error indicator and can retry the generation.

---

### Edge Cases

- What happens when PR-FAQ generation fails mid-process? The system should mark the state as failed and allow retry.
- How does the system handle concurrent generation requests for the same execution? The backend should prevent duplicate generation and return the existing pending/completed state.
- What happens if the user refreshes the page during generation? The UI should query the current state and show the appropriate loading indicator if generation is still in progress.
- What happens if the summary becomes unavailable after PR-FAQ generation starts? Generation should fail gracefully with a clear error message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST track generation state for each artifact (summary, PR-FAQ) with states: `unavailable`, `pending`, `generating`, `available`, `failed`
- **FR-002**: System MUST provide a unified endpoint to query the current state of all artifacts for a given execution
- **FR-003**: System MUST validate prerequisites before allowing generation (e.g., summary required before PR-FAQ)
- **FR-004**: System MUST prevent concurrent generation requests for the same artifact on the same execution
- **FR-005**: System MUST provide real-time or polling-based state updates during generation
- **FR-006**: Frontend MUST display different button states based on artifact state:
  - `unavailable`: Disabled button with tooltip explaining prerequisite
  - `pending`: Should not occur (internal state only)
  - `generating`: Loading indicator, non-clickable
  - `available`: "Visualizar" button to view content
  - `failed`: Error indicator with retry option
- **FR-007**: System MUST persist generation state across page refreshes and user sessions
- **FR-008**: System MUST support retry after failed generation

### Key Entities

- **Research Execution**: Represents a batch of interviews with a topic guide. Contains `exec_id`, `status`, `summary_available`, `prfaq_available`, and content fields. Links to transcripts and generated artifacts.

- **Artifact State**: Represents the generation state of a single artifact (summary or PR-FAQ). Contains `artifact_type`, `state`, `error_message`, `started_at`, `completed_at`. Associated with a research execution.

- **PR-FAQ Metadata**: Represents generated PR-FAQ document metadata. Contains `exec_id`, `headline`, `generated_at`, `model`, `markdown_content`, `validation_status`. Links back to research execution.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can understand the current state of any artifact within 2 seconds of page load
- **SC-002**: Button states update within 3 seconds of state changes (generation complete, failure, etc.)
- **SC-003**: 100% of prerequisite violations are blocked with clear user messaging before any generation attempt
- **SC-004**: 0 duplicate generation requests reach the backend for the same artifact and execution
- **SC-005**: Failed generations can be retried successfully without requiring page refresh
- **SC-006**: Users report 90%+ satisfaction rating for understanding artifact availability states

## Assumptions

- The current database schema (`research_executions`, `prfaq_metadata`) can be extended with additional state columns without breaking existing functionality
- The frontend already uses React Query for state management and will continue to leverage it for polling/invalidation
- Summary generation remains automatic (triggered as part of research execution completion), while PR-FAQ generation remains user-initiated
- Real-time updates via WebSocket are not required; polling-based updates are acceptable for MVP
- The existing `ExecutionStatus` enum can be extended or a new artifact-specific state field can be added
