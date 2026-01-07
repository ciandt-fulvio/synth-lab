# Feature Specification: Synth Material Integration

**Feature Branch**: `029-synth-material-integration`
**Created**: 2026-01-06
**Status**: Draft
**Input**: User description: "029-Synths \"Veem\" Materiais - Integration of experiment materials (images, PDFs, videos) into LLM contexts for interviews, summaries, PR-FAQs, and scenario exploration, enabling Synths to reference and interact with visual/document content"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Synths Reference Materials During Interviews (Priority: P1)

Synths participating in research interviews can view and reference experiment materials (wireframes, prototypes, videos) to provide contextual feedback based on their personality traits and demographics.

**Why this priority**: Core value proposition - enables realistic user feedback on visual materials, which is the primary use case for attaching materials to experiments.

**Independent Test**: Can be fully tested by conducting an interview with attached materials and verifying that the Synth references specific visual elements in responses, delivering realistic user feedback on designs.

**Acceptance Scenarios**:

1. **Given** an experiment has wireframe images attached, **When** a Synth with high Neuroticism is interviewed about the design, **Then** the Synth provides critical feedback referencing specific UI elements from the wireframe
2. **Given** an experiment has a prototype video attached, **When** a Synth with low Tech Literacy views the interaction flow, **Then** the Synth expresses confusion about complex UI patterns visible in the video
3. **Given** an experiment has multiple materials (wireframe, prototype, documentation), **When** the Synth is asked about the user experience, **Then** the Synth references elements across different materials in a coherent response

---

### User Story 2 - Materials Inform PR-FAQ Generation (Priority: P2)

Generated PR-FAQs automatically reference experiment materials to provide evidence-based insights, including specific visual elements, timestamps, and design patterns observed in user research.

**Why this priority**: Enhances research documentation quality by grounding insights in actual materials, making reports more actionable for product teams.

**Independent Test**: Can be tested by generating a PR-FAQ for an experiment with materials and verifying that the document includes material references with specific visual details and contextual insights.

**Acceptance Scenarios**:

1. **Given** an experiment with wireframe images has completed interviews, **When** a PR-FAQ is generated, **Then** the document includes a "Materiais de Referência" section listing all attached materials
2. **Given** a prototype video shows a specific interaction at timestamp 00:12, **When** a PR-FAQ is generated, **Then** insights reference the timestamp for specific observations (e.g., "calendário visual (ref: prototype-demo.mp4, 00:12)")
3. **Given** interview data reveals usability issues with a wireframe element, **When** a PR-FAQ is generated, **Then** the "Pontos de Atenção" section cites the specific material and visual element causing friction

---

### User Story 3 - Materials Enhance Scenario Exploration (Priority: P3)

During exploration scenario generation, Synths can reference experiment materials to create more realistic and contextually relevant scenario nodes, improving the depth of scenario-based research.

**Why this priority**: Extends material integration to exploration workflows, providing additional research depth beyond interviews and documentation.

**Independent Test**: Can be tested by running an exploration with attached materials and verifying that scenario nodes include material-based considerations and references.

**Acceptance Scenarios**:

1. **Given** an experiment has design materials attached, **When** scenario nodes are generated during exploration, **Then** nodes reference specific design elements that would impact the scenario outcome
2. **Given** a video demonstrates a multi-step process, **When** scenario exploration analyzes user paths, **Then** generated scenarios account for steps visible in the video material

---

### User Story 4 - Exploration Summaries Reference Materials (Priority: P3)

Generated exploration summaries and PR-FAQs include material references to support scenario-based insights, similar to interview-based documentation.

**Why this priority**: Completes the material integration across all documentation types, ensuring consistent evidence-based reporting.

**Independent Test**: Can be tested by completing an exploration with materials and verifying that the summary document includes material references supporting scenario insights.

**Acceptance Scenarios**:

1. **Given** an exploration with attached materials completes, **When** a summary is generated, **Then** the summary includes references to materials that informed scenario outcomes
2. **Given** exploration PR-FAQ generation, **When** the document is created, **Then** it follows the same material reference format as interview PR-FAQs

---

### Edge Cases

- What happens when a material file is corrupted or inaccessible during interview/generation?
- How does the system handle extremely large video files that may timeout during LLM processing?
- What happens when materials are in unsupported formats?
- How does the system behave when an experiment has no materials attached but material-aware prompts are used?
- What happens when a Synth requests a material that doesn't exist (wrong ID)?
- How does the system handle materials with non-English text or content?
- What happens when multiple materials have similar content and the LLM needs to disambiguate?
- How does the system handle rate limits when processing many materials in a single interview?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create structured metadata for all experiment materials, including description, MIME type, and unique identifier (format: mat_XXXXXX)
- **FR-002**: System MUST inject material metadata into LLM system prompts using structured XML tags (e.g., `<attachments>`)
- **FR-003**: System MUST provide a function/tool that LLMs can invoke to retrieve the full content of a specific material by ID
- **FR-004**: System MUST make materials available during interview sessions for both interviewer and interviewee LLM agents
- **FR-005**: System MUST make materials available during interview summary and PR-FAQ generation
- **FR-006**: System MUST make materials available during exploration scenario node generation
- **FR-007**: System MUST make materials available during exploration summary and PR-FAQ generation
- **FR-008**: Synths MUST be able to reference specific elements within materials (e.g., "the green button", "the video at 00:12")
- **FR-009**: Generated PR-FAQs MUST include a "Materiais de Referência" section listing all experiment materials
- **FR-010**: Generated PR-FAQs MUST include material references (filename, timestamps for videos) when citing specific insights
- **FR-011**: System MUST support image materials (PNG, JPEG, GIF, WebP) for visual reference
- **FR-012**: System MUST support PDF materials for document reference
- **FR-013**: System MUST support video materials (MP4, WebM) for interaction flow reference
- **FR-014**: System MUST handle gracefully when materials are unavailable or corrupted
- **FR-015**: Synth responses MUST reflect personality traits when evaluating materials (e.g., high Neuroticism → more critical of designs)
- **FR-016**: Synth responses MUST reflect demographic factors when evaluating materials (e.g., low Tech Literacy → confusion with complex UI)

### Key Entities

- **Material Metadata**: Represents information about an attached material, including unique ID (mat_XXXXXX), description, MIME type, original filename, and storage location reference
- **Material Reference**: Represents a citation of a material in generated content, including material ID, optional timestamp (for videos), and contextual description
- **LLM Tool/Function**: Represents the callable interface that allows LLMs to request full material content by ID, returning the material in a format suitable for the LLM's multimodal capabilities

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Synths reference experiment materials in at least 70% of interview responses when materials are attached
- **SC-002**: Generated PR-FAQs include specific material references (filename + context) for 100% of experiments with attached materials
- **SC-003**: Material retrieval requests complete within 5 seconds for images and PDFs, 10 seconds for videos under 50MB
- **SC-004**: Synth feedback quality increases by 40% (measured by specificity of visual element references) when materials are available vs. text-only interviews
- **SC-005**: 90% of material references in PR-FAQs include actionable context (specific element, timestamp, or design pattern)
- **SC-006**: System successfully handles 100% of supported material formats without errors
- **SC-007**: PR-FAQ generation time increases by no more than 30% when processing experiments with materials vs. without

## Assumptions

- The existing `experiment_documents` table is suitable for storing material metadata and references
- LLM providers (OpenAI, etc.) support multimodal inputs for images, PDFs, and videos in the required formats
- Video materials will typically be short demonstrations (under 5 minutes) rather than long recordings
- Materials will be referenced using the existing S3-compatible storage system already used for experiment documents
- The LLM function calling mechanism supports returning binary/base64-encoded content for materials
- Material descriptions will be provided by users when uploading materials (not auto-generated)
- Synths will have the cognitive capability to process and reference visual/video content contextually
- PR-FAQ templates can be extended to include material reference sections without breaking existing functionality
- Phoenix tracing is already configured to handle LLM calls with multimodal content

## Dependencies

- Existing `experiment_documents` table and S3 storage infrastructure (from feature 001-experiment-materials)
- LLM provider multimodal API support (OpenAI GPT-4V or equivalent)
- Phoenix tracing infrastructure for LLM observability
- Existing interview, PR-FAQ generation, and exploration workflows

## Constraints

- Material retrieval must not cause interview response delays exceeding 10 seconds
- Material metadata in system prompts must not exceed 2000 tokens to preserve context window for conversation
- Supported material formats limited to: images (PNG, JPEG, GIF, WebP), PDF, videos (MP4, WebM)
- Maximum individual material file size: 50MB (to stay within LLM provider limits)
- Material references in PR-FAQs must be human-readable and actionable (no bare IDs)

## Out of Scope

- Auto-generation of material descriptions from content analysis
- Real-time collaboration on materials during interviews
- Material editing or annotation within the synth-lab interface
- Automatic extraction of text from PDFs or OCR for images
- Material versioning or change tracking
- Support for audio-only materials
- Interactive material manipulation by Synths (e.g., zooming, rotating images)
- Material search or filtering within the interface (users must know which materials to attach)
- Material recommendations based on experiment type
- Multi-language material content translation
