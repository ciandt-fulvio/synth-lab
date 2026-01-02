# Feature Specification: synth-lab REST API with Database Layer

**Feature Branch**: `010-rest-api`
**Created**: 2025-12-19
**Status**: Draft
**Input**: User description: "Implement a REST API for synth-lab based on the specification in `specs/api-pre-work.md`, migrating data from the current file-based structure to a database solution with PostgreSQL, exposed via standalone FastAPI service."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Access Synth Data Programmatically (Priority: P1)

External systems and developers need to query and retrieve synth persona data through a standardized API instead of directly accessing JSON files.

**Why this priority**: This is the foundational capability that enables all other API functionality. Synths are the core entities that participate in research executions.

**Independent Test**: Can be fully tested by making HTTP requests to synth endpoints and verifying correct JSON responses with pagination.

**Acceptance Scenarios**:

1. **Given** a running API server with synths in the database, **When** I request `GET /synths/list`, **Then** I receive a paginated JSON response with synth summaries (id, nome, arquetipo, descricao) and pagination metadata.
2. **Given** a valid synth ID "ynnasw", **When** I request `GET /synths/ynnasw`, **Then** I receive the complete synth profile including demografia, psicografia, deficiencias, and capacidades_tecnologicas.
3. **Given** a non-existent synth ID, **When** I request `GET /synths/invalid`, **Then** I receive a 404 response with error code `SYNTH_NOT_FOUND`.
4. **Given** search criteria for age > 30 and region = 'Sudeste', **When** I POST to `/synths/search` with a WHERE clause, **Then** I receive only synths matching those criteria.

---

### User Story 2 - Retrieve Research Execution Data (Priority: P1)

Users and systems need to access interview transcripts, research summaries, and execution metadata to analyze research results.

**Why this priority**: Research executions are the primary output of the system. Access to transcripts and summaries is essential for analysis and PR-FAQ generation.

**Independent Test**: Can be fully tested by querying research execution endpoints and verifying transcript/summary retrieval.

**Acceptance Scenarios**:

1. **Given** a completed research execution, **When** I request `GET /research/{exec_id}`, **Then** I receive execution metadata including synth count, status, timestamps, and model used.
2. **Given** a research execution with transcripts, **When** I request `GET /research/{exec_id}/transcripts`, **Then** I receive a list of all transcript summaries with synth info and status.
3. **Given** a specific synth in an execution, **When** I request `GET /research/{exec_id}/transcripts/{synth_id}`, **Then** I receive the complete interview transcript with all messages.
4. **Given** an execution with a summary, **When** I request `GET /research/{exec_id}/summary`, **Then** I receive the Markdown summary document.

---

### User Story 3 - Browse Topic Guides (Priority: P2)

Users need to discover and review available topic guides to understand what research topics are configured.

**Why this priority**: Topic guides are required inputs for research execution. Users must be able to see available topics and their structure.

**Independent Test**: Can be fully tested by listing topics and retrieving topic details.

**Acceptance Scenarios**:

1. **Given** topic guides exist, **When** I request `GET /topics/list`, **Then** I receive a list of all topic guides with name, description, question count, and file count.
2. **Given** a valid topic name "compra-amazon", **When** I request `GET /topics/compra-amazon`, **Then** I receive the full topic guide including script questions and associated files.
3. **Given** a topic with past executions, **When** I request `GET /topics/{name}/research`, **Then** I receive a list of all research executions for that topic.

---

### User Story 4 - Access PR-FAQ Documents (Priority: P2)

Users need to retrieve generated PR-FAQ documents and their metadata to review strategic outputs from research.

**Why this priority**: PR-FAQs are the strategic deliverable generated from research synthesis. Access is essential but depends on research being completed first.

**Independent Test**: Can be fully tested by listing PR-FAQs and retrieving Markdown content.

**Acceptance Scenarios**:

1. **Given** PR-FAQs have been generated, **When** I request `GET /prfaq/list`, **Then** I receive a list of all PR-FAQs with headlines, topics, and validation status.
2. **Given** a valid execution ID with a PR-FAQ, **When** I request `GET /prfaq/{exec_id}/markdown`, **Then** I receive the complete PR-FAQ document in Markdown format.
3. **Given** an execution without a PR-FAQ, **When** I request `GET /prfaq/{exec_id}/markdown`, **Then** I receive a 404 with error code `PRFAQ_NOT_FOUND`.

---

### User Story 5 - Execute New Research (Priority: P3)

Users need to trigger new research executions programmatically, specifying topic and synth selection criteria.

**Why this priority**: Write operations are lower priority since research can already be executed via CLI. API execution adds convenience for automation.

**Independent Test**: Can be tested by triggering a research execution and verifying the returned execution ID.

**Acceptance Scenarios**:

1. **Given** a valid topic name, **When** I POST to `/research/execute` with `topic_name` and `synth_count`, **Then** I receive a 201 response with `exec_id` and execution begins.
2. **Given** specific synth IDs, **When** I POST to `/research/execute` with `synth_ids` array, **Then** only those specific synths are interviewed.
3. **Given** an invalid topic name, **When** I POST to `/research/execute`, **Then** I receive a 404 with error code `TOPIC_NOT_FOUND`.
4. **Given** no synth selection criteria, **When** I POST without `synth_ids` or `synth_count`, **Then** I receive a 422 validation error.

---

### User Story 6 - Generate PR-FAQ from Research (Priority: P3)

Users need to trigger PR-FAQ generation from completed research executions.

**Why this priority**: Like research execution, this is a convenience feature for automation since it's already available via CLI.

**Independent Test**: Can be tested by triggering generation and verifying the PR-FAQ is created.

**Acceptance Scenarios**:

1. **Given** a completed research execution with summary, **When** I POST to `/prfaq/generate` with the `exec_id`, **Then** I receive a 201 response with generation metadata.
2. **Given** an execution without a summary, **When** I POST to `/prfaq/generate`, **Then** I receive a 422 with error code `GENERATION_FAILED` and reason `missing_summary`.

---

### User Story 7 - Retrieve Synth Avatars (Priority: P3)

Users and UI applications need to display synth avatar images.

**Why this priority**: Visual representation is useful but not essential for core API functionality.

**Independent Test**: Can be tested by requesting an avatar and verifying PNG image response.

**Acceptance Scenarios**:

1. **Given** a synth with an avatar, **When** I request `GET /synths/{id}/avatar`, **Then** I receive the PNG image with `Content-Type: image/png`.
2. **Given** a synth without an avatar, **When** I request the avatar, **Then** I receive a 404 with error code `SYNTH_NOT_FOUND`.

---

### Edge Cases

- What happens when database is unavailable? Return 503 with `DATABASE_ERROR`.
- What happens when a search query contains SQL injection attempts (INSERT, DELETE)? Return 422 with `INVALID_QUERY`.
- What happens when pagination exceeds total records? Return empty data array with pagination showing `has_next: false`.
- What happens when requesting markdown for a research with no summary? Return 404 with appropriate error code.
- What happens when concurrent requests modify the same resource? Database handles via transaction isolation.

## Requirements *(mandatory)*

### Functional Requirements

**Data Access:**
- **FR-001**: System MUST expose all synth data via REST endpoints with JSON responses
- **FR-002**: System MUST support pagination for list endpoints (limit, offset, total count)
- **FR-003**: System MUST support field selection on list endpoints to reduce payload size
- **FR-004**: System MUST support sorting by any field on list endpoints
- **FR-005**: System MUST provide advanced search with WHERE clause filtering for synths

**Research Operations:**
- **FR-006**: System MUST expose research execution metadata and transcripts via REST endpoints
- **FR-007**: System MUST return Markdown content with appropriate `Content-Type: text/markdown` header
- **FR-008**: System MUST support triggering new research executions via POST endpoint
- **FR-009**: System MUST block until research execution completes before returning response (synchronous)

**Topic Guides:**
- **FR-010**: System MUST list all available topic guides with metadata
- **FR-011**: System MUST return complete topic guide structure including script and files

**PR-FAQ:**
- **FR-012**: System MUST list all generated PR-FAQs with metadata
- **FR-013**: System MUST return PR-FAQ content in Markdown format
- **FR-014**: System MUST support triggering PR-FAQ generation via POST endpoint

**Error Handling:**
- **FR-015**: System MUST return consistent error response structure with code and message
- **FR-016**: System MUST use appropriate HTTP status codes (200, 201, 400, 404, 422, 500, 503)
- **FR-017**: System MUST validate SQL queries to prevent injection (block INSERT, DELETE, UPDATE, DROP)

**Database:**
- **FR-018**: System MUST migrate existing file-based data to a unified database
- **FR-019**: System MUST maintain backward compatibility with existing CLI commands during transition
- **FR-020**: System MUST support concurrent read operations without blocking

### Key Entities

- **Synth**: Synthetic persona with demographic, psychographic, disability, and technology capability profiles. Identified by 6-character alphanumeric ID.
- **Topic Guide**: Research interview script with context, questions, and associated files (screenshots). Identified by directory name.
- **Research Execution**: A batch of interviews with multiple synths on a single topic. Contains transcripts, summary, and optionally PR-FAQ. Identified by `exec_id` format: `batch_{topic}_{timestamp}`.
- **Transcript**: Complete interview conversation between interviewer and synth. Linked to execution and synth.
- **PR-FAQ**: Amazon Working Backwards document generated from research synthesis. Contains press release, FAQs, and validation metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 17 API endpoints return correct responses matching the specification in `specs/api-pre-work.md`
- **SC-002**: Metadata queries (synth details, execution info) complete in under 200ms
- **SC-003**: Large document retrieval (transcripts, summaries) complete in under 1 second
- **SC-004**: System supports 10 concurrent API clients without performance degradation
- **SC-005**: Data migration preserves 100% of existing records (9 synths, 14 transcripts, 37 traces, 6 reports)
- **SC-006**: Existing CLI commands continue to function correctly after migration
- **SC-007**: Search queries with WHERE clauses return results in under 500ms for current dataset size
- **SC-008**: API auto-generates interactive documentation (OpenAPI/Swagger)

## Assumptions

- The system operates in a development/internal environment without authentication requirements
- Write operations (research execution, PR-FAQ generation) are acceptable to be synchronous/blocking
- The current data volume (~79 files) is small enough that complex query optimization is not required
- Cross-origin requests (CORS) should be allowed for all origins during development
- The existing DuckDB module can remain operational during transition for backward compatibility
