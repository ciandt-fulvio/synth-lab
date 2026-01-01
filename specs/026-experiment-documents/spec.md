# Feature Specification: Unified Experiment Documents

**Feature Branch**: `026-experiment-documents`
**Created**: 2025-12-31
**Status**: Draft
**Input**: User description: "Finalize unified experiment documents feature - the experiment_documents table is not being correctly populated"

## Overview

The synth-lab platform generates various documents for experiments: research summaries, PR-FAQs, and executive summaries. Currently, these documents are stored inconsistently across different tables and structures. A partial implementation exists but is incomplete:

1. **Entity, Repository, and Service** are implemented but the database table is missing from the schema
2. **API Router** is implemented but not registered in the main application
3. **Frontend components** are implemented but cannot function without the backend

This feature completes the unification by:
- Adding the `experiment_documents` table to the database schema
- Registering the documents router in the API
- Ensuring the document service integrates with existing document generators

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Experiment Documents (Priority: P1)

As a researcher, I want to view all documents associated with an experiment from a single unified interface, so I can quickly access summaries, PR-FAQs, and executive summaries without navigating to different sections.

**Why this priority**: This is the core user-facing value - a single place to access all experiment documents.

**Independent Test**: Can be fully tested by navigating to an experiment's documents section and seeing a list of available documents. Delivers immediate value by showing document status and allowing access to content.

**Acceptance Scenarios**:

1. **Given** an experiment with a completed research summary, **When** I navigate to the experiment's documents section, **Then** I see the summary listed with status "completed" and can view its content
2. **Given** an experiment with no documents, **When** I navigate to the documents section, **Then** I see an empty state indicating no documents are available
3. **Given** an experiment with a document in "generating" status, **When** I view the documents list, **Then** I see a progress indicator for that document

---

### User Story 2 - Generate Executive Summary (Priority: P2)

As a product manager, I want to generate an executive summary that synthesizes insights from the quantitative analysis, so I can share strategic recommendations with stakeholders.

**Why this priority**: Executive summary generation is the most complex document type and requires analysis results to exist.

**Independent Test**: Can be tested by triggering generation via the API and verifying the document is stored in experiment_documents table with markdown content.

**Acceptance Scenarios**:

1. **Given** an experiment with completed analysis and at least 2 chart insights, **When** I request executive summary generation, **Then** the system starts generation and returns a "generating" status
2. **Given** an experiment with completed analysis and insights, **When** generation completes, **Then** the document is stored with status "completed" and markdown content
3. **Given** an experiment without completed analysis, **When** I request executive summary generation, **Then** I receive an error indicating analysis must be run first

---

### User Story 3 - Access Document Markdown (Priority: P3)

As a user, I want to retrieve document content in markdown format, so I can render it in the frontend or export it for external use.

**Why this priority**: This enables the frontend to display documents and supports future export functionality.

**Independent Test**: Can be tested by requesting a document's markdown endpoint and receiving plain text markdown content.

**Acceptance Scenarios**:

1. **Given** a completed document, **When** I request the markdown endpoint, **Then** I receive the full markdown content with correct content-type header
2. **Given** a document that doesn't exist, **When** I request its markdown, **Then** I receive a 404 error with descriptive message

---

### Edge Cases

- What happens when generation fails mid-process? The document status is set to "failed" with an error message stored for debugging.
- How does the system handle concurrent generation requests for the same document type? The system rejects concurrent requests and returns the current status.
- What happens if the database table doesn't exist on an existing installation? The table is created during database initialization via an automatic migration.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST store experiment documents in a centralized `experiment_documents` table
- **FR-002**: System MUST support three document types: summary, prfaq, executive_summary
- **FR-003**: System MUST track document status: pending, generating, completed, failed, partial
- **FR-004**: System MUST prevent concurrent generation of the same document (via status check returning existing in-progress status)
- **FR-005**: System MUST expose REST API endpoints under `/experiments/{experiment_id}/documents`
- **FR-006**: System MUST register the documents router in the main FastAPI application
- **FR-007**: System MUST create the experiment_documents table during database initialization (with migration for existing databases)
- **FR-008**: System MUST return appropriate HTTP status codes (200, 404, 400) for document operations

### Key Entities

- **ExperimentDocument**: Central entity for all document types
  - id: Unique identifier (doc_XXXXXXXX format)
  - experiment_id: Foreign key to experiments table
  - document_type: One of summary, prfaq, executive_summary
  - markdown_content: Full document content in markdown format
  - metadata: Type-specific metadata (optional)
  - status: Current generation status
  - model: LLM model used for generation
  - generated_at: Timestamp of generation

## Dependencies & Assumptions

### Dependencies

- Existing experiment and analysis infrastructure must be functional
- LLM client must be available for executive summary generation
- Chart insights must exist in analysis_cache for executive summary generation

### Assumptions

- The existing entity, repository, service, router, and schema implementations are correct and complete
- The only missing pieces are: database table in schema, router registration, and database migration
- Frontend components will work once backend is properly configured

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three document types can be stored and retrieved via the unified API
- **SC-002**: Executive summary generation stores documents in experiment_documents table with full markdown content
- **SC-003**: Document listing returns all available documents for an experiment
- **SC-004**: Frontend can display document list and content using the new API endpoints
- **SC-005**: Existing databases are migrated to include experiment_documents table without data loss

## Out of Scope

- Migration of existing documents from legacy storage (prfaq_metadata, analysis_cache) to new table
- Summary and PR-FAQ generation integration with new table (these continue to use their existing storage)
- Document versioning (documents are replaced on regeneration)
- Document deletion confirmation in UI
