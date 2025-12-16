# Feature Specification: UX Research Interviews with Synths

**Feature Branch**: `005-ux-research-interviews`
**Created**: 2025-12-16
**Status**: Draft
**Input**: User description: "Entrevista de Pesquisa UX com Synths - Execute simulated UX research interviews with synths using two LLMs in conversation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Basic UX Research Interview (Priority: P1)

A UX researcher wants to conduct a simulated interview with a synthetic persona to gather qualitative insights about user behavior, preferences, and pain points for a product or service being researched.

**Why this priority**: This is the core value proposition - enabling researchers to simulate UX interviews without recruiting real participants. It validates the entire feature concept and delivers immediate research value.

**Independent Test**: Can be fully tested by running a single interview session with any synth and observing the conversation flow, message exchange, and final transcript output.

**Acceptance Scenarios**:

1. **Given** a valid synth ID exists in the database, **When** the researcher starts an interview with a topic guide, **Then** the system initiates a conversation where the interviewer LLM asks questions and the synth LLM responds in character.

2. **Given** an interview is in progress, **When** the interviewer LLM determines the interview is complete (should_end=true), **Then** the conversation ends gracefully and the transcript is saved.

3. **Given** an interview is in progress, **When** the maximum number of conversation rounds is reached, **Then** the conversation ends and the transcript is saved.

4. **Given** the interview completes, **When** viewing the transcript, **Then** all messages from both participants are included with timestamps and speaker identification.

---

### User Story 2 - View Real-time Interview Progress (Priority: P2)

A researcher wants to observe the interview as it happens, seeing each message appear in real-time so they can understand the conversation flow and potentially learn from the interviewer LLM's technique.

**Why this priority**: Real-time visibility enhances the researcher's experience and allows them to learn from the simulated interview process. However, the core value (getting the transcript) can be delivered without this.

**Independent Test**: Can be tested by running an interview and verifying messages appear sequentially in the terminal with clear visual distinction between interviewer and interviewee.

**Acceptance Scenarios**:

1. **Given** an interview is running, **When** each participant sends a message, **Then** the message is displayed immediately in the terminal with the speaker clearly identified.

2. **Given** messages are being displayed, **When** viewing the conversation, **Then** interviewer messages and synth responses are visually distinguishable (different colors or formatting).

---

### User Story 3 - Use Custom Topic Guides (Priority: P2)

A researcher wants to provide a custom topic guide file that defines the interview structure, themes to explore, and specific questions to cover, allowing tailored research sessions for different projects.

**Why this priority**: Topic guides are essential for professional UX research but the system can work with a default general-purpose guide as fallback.

**Independent Test**: Can be tested by creating two different topic guide files and verifying that interviews using each guide produce conversations aligned with their respective topics.

**Acceptance Scenarios**:

1. **Given** a topic guide file path is provided, **When** the interview starts, **Then** the interviewer LLM follows the structure and themes defined in the guide.

2. **Given** a topic guide contains specific questions, **When** conducting the interview, **Then** those questions are naturally incorporated into the conversation flow.

3. **Given** an invalid topic guide path is provided, **When** attempting to start an interview, **Then** a clear error message indicates the file was not found.

---

### User Story 4 - Save and Review Interview Transcripts (Priority: P1)

A researcher wants the complete interview transcript saved to a file so they can analyze it later, share with team members, or use it as input for other analysis tools.

**Why this priority**: Without saved transcripts, the research output is lost. This is essential for the feature to deliver lasting value.

**Independent Test**: Can be tested by completing an interview and verifying the transcript file exists with the complete conversation in the expected format.

**Acceptance Scenarios**:

1. **Given** an interview completes, **When** the transcript is saved, **Then** a JSON file is created containing all messages, timestamps, and metadata.

2. **Given** the transcript file is created, **When** opening it, **Then** it contains the synth ID, interview timestamp, topic guide used, and complete message history.

3. **Given** multiple interviews are conducted, **When** viewing the transcripts directory, **Then** each interview has a unique file with an identifiable name (includes synth ID and timestamp).

---

### Edge Cases

- What happens when the synth ID does not exist in the database?
- How does the system handle LLM API failures or timeouts mid-interview?
- What happens if the topic guide file is empty or malformed?
- How are very long interviews handled (approaching context limits)?
- What if the synth has extreme personality traits that make conversation difficult (e.g., very low openness, very high neuroticism)?
- What happens if the interviewer LLM never sets should_end=true?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load a synth by ID from the existing synths.json data file
- **FR-002**: System MUST construct an interviewer system prompt that includes UX research best practices and the provided topic guide
- **FR-003**: System MUST construct a synth system prompt that includes the complete persona (Big Five personality, demographics, biases, behaviors, cognitive capabilities)
- **FR-004**: System MUST execute a conversation loop where interviewer and synth alternate messages
- **FR-005**: System MUST parse structured JSON responses from both LLMs containing message content and control flags
- **FR-006**: System MUST end the interview when the interviewer signals should_end=true OR max_rounds is reached
- **FR-007**: System MUST display each message in real-time to the terminal using Rich formatting
- **FR-008**: System MUST save the complete transcript to a JSON file upon interview completion
- **FR-009**: System MUST provide a CLI command (`synthlab research`) with parameters for synth_id, topic_guide, and max_rounds
- **FR-010**: System MUST validate that the specified synth ID exists before starting the interview
- **FR-011**: System MUST handle LLM API errors gracefully with informative error messages
- **FR-012**: System MUST include internal_notes field in the response format for optional interviewer annotations

### Response Format Requirements

Each LLM response MUST conform to this Pydantic-validated JSON structure:

```json
{
  "message": "The actual spoken message text",
  "should_end": false,
  "internal_notes": "Optional internal annotations (not shown to the other participant)"
}
```

- **FR-013**: The `message` field MUST contain the spoken text for the conversation
- **FR-014**: The `should_end` field MUST be a boolean, only set to true by the interviewer when the interview is complete
- **FR-015**: The `internal_notes` field MUST be optional and used for researcher insights or synth internal state

### Key Entities

- **Interview Session**: Represents a complete interview execution (synth_id, topic_guide_path, max_rounds, start_time, end_time, status)
- **Message**: A single conversation turn (speaker: "interviewer" | "synth", content, timestamp, internal_notes)
- **Topic Guide**: A text file containing interview themes, questions, and structure
- **Transcript**: The complete interview output (session metadata, list of messages, synth persona snapshot)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete a simulated UX interview in under 5 minutes for a 10-round conversation
- **SC-002**: Interview transcripts are successfully saved for 100% of completed interviews
- **SC-003**: Synth responses reflect their persona attributes (personality, demographics, biases) in at least 80% of conversations as judged by manual review
- **SC-004**: System handles invalid synth IDs with clear error messages within 2 seconds
- **SC-005**: Real-time message display has less than 1 second delay between LLM response and terminal output
- **SC-006**: Topic guides with 5+ questions result in interviews covering at least 80% of the specified topics

## Assumptions

- The synths.json file follows the v2.0.0 schema structure with complete persona data
- LLM API access is configured externally (API keys available as environment variables)
- Users have basic familiarity with running CLI commands
- Topic guide files are plain text or markdown format with interview questions/themes
- The existing synthlab CLI infrastructure (typer-based) will be extended with the new command
- Default max_rounds of 10 provides sufficient depth for most research interviews
- Transcripts will be saved to a `data/transcripts/` directory following existing data organization patterns
