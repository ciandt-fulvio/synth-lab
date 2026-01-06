# Feature Specification: Experiment Materials Upload

**Feature Branch**: `001-experiment-materials`
**Created**: 2026-01-05
**Status**: Draft
**Input**: User description: "Permitir que usuarios anexem contexto visual e documentacao ao criar ou editar experimentos, fornecendo aos synths acesso aos mesmos materiais que usuarios reais teriam durante a interacao com a feature."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload Materials During Experiment Creation (Priority: P1)

As a researcher creating an experiment, I want to upload images, videos, and documents (wireframes, prototypes, specs) so that synths can evaluate real designs during simulated interviews.

**Why this priority**: This is the core functionality that enables the entire feature. Without file upload capability, no other functionality can work. It transforms abstract simulations into concrete design evaluations.

**Independent Test**: Can be fully tested by creating an experiment with attached materials and verifying files are stored and retrievable. Delivers immediate value by enabling visual context for experiments.

**Acceptance Scenarios**:

1. **Given** I am on the experiment creation form, **When** I drag and drop a PNG image into the materials section, **Then** an instant preview thumbnail appears and the file is staged for upload
2. **Given** I have staged files for upload, **When** I save the experiment, **Then** all files are uploaded to storage and metadata is persisted to the database
3. **Given** I am editing an existing experiment, **When** I add new materials, **Then** they are added to the existing collection without removing previous files
4. **Given** I have multiple files staged, **When** I reorder them by dragging, **Then** the new order is preserved when the experiment is saved

---

### User Story 2 - View Materials Preview on Experiment Page (Priority: P2)

As a researcher viewing an experiment, I want to see previews of all attached materials in a gallery format so that I can quickly review what context synths will have during interviews.

**Why this priority**: Essential for researchers to verify and manage attached materials. Without preview capability, users cannot confirm what synths will see.

**Independent Test**: Can be tested by navigating to an experiment with materials and verifying all previews render correctly with metadata displayed.

**Acceptance Scenarios**:

1. **Given** an experiment has attached images, **When** I view the experiment page, **Then** I see thumbnail previews of each image with filename, type, size, and upload date
2. **Given** an experiment has attached videos, **When** I view the experiment page, **Then** I see a thumbnail of the first frame for each video
3. **Given** an experiment has attached PDFs, **When** I view the experiment page, **Then** I see a preview of the first page for each PDF
4. **Given** I am viewing material previews, **When** I click on a preview, **Then** I can view the full-size material or play the video

---

### User Story 3 - Synths Process Materials During Interviews (Priority: P3)

As a researcher running interviews, I want synths to "see" and reference the attached materials so that their responses reflect genuine reactions to the actual designs being tested.

**Why this priority**: This is the key differentiator that makes materials valuable. Synths referencing specific visual elements provides actionable design feedback. Depends on P1 and P2 being complete.

**Independent Test**: Can be tested by running an interview with materials attached and verifying synth responses reference specific visual elements from the materials.

**Acceptance Scenarios**:

1. **Given** an experiment has attached images, **When** an interview is executed, **Then** the synth can reference specific visual elements (buttons, colors, layout)
2. **Given** an experiment has attached videos, **When** an interview is executed, **Then** the synth can reference events and sequences from the video content
3. **Given** a synth has high Neuroticism trait, **When** viewing materials during interview, **Then** responses reflect more critical evaluation of the design
4. **Given** a synth has low Tech Literacy trait, **When** viewing complex UI materials, **Then** responses reflect confusion or difficulty understanding the interface

---

### User Story 4 - Materials Referenced in PR-FAQ Generation (Priority: P4)

As a researcher generating reports, I want materials to be automatically referenced in PR-FAQs and summaries so that insights are grounded in specific visual evidence.

**Why this priority**: Adds significant value to generated reports by providing concrete references. Depends on interviews having been run with materials (P3).

**Independent Test**: Can be tested by generating a PR-FAQ for an experiment with materials and verifying material references appear in the output.

**Acceptance Scenarios**:

1. **Given** an experiment has materials and completed interviews, **When** I generate a PR-FAQ, **Then** the document includes a "Reference Materials" section listing all attached files
2. **Given** insights reference specific visual elements, **When** the PR-FAQ is generated, **Then** the insights include references to specific materials (e.g., "ref: wireframe-checkout.png")
3. **Given** synths referenced a specific timestamp in a video, **When** the PR-FAQ is generated, **Then** the reference includes the timestamp (e.g., "ref: prototype-demo.mp4, 00:12")

---

### Edge Cases

- What happens when a user uploads a file exceeding the size limit?
  - System displays an error message indicating the limit and prevents upload
- What happens when a user tries to upload more than 10 files?
  - System displays a warning and prevents additional uploads until some are removed
- How does the system handle corrupted or malformed files?
  - System validates file format on upload and rejects invalid files with clear error message
- What happens when a user deletes all materials from an experiment that has completed interviews?
  - Materials are removed but historical interview references are preserved (may show "[material removed]")
- How does the system handle very long videos?
  - Videos up to 100MB are accepted; larger files are rejected with size limit message
- What happens during interview if material storage is temporarily unavailable?
  - Interview continues without visual context; system logs the error and synth responses note materials were unavailable

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support file upload via drag-and-drop or file picker in the experiment creation/edit form
- **FR-002**: System MUST support batch upload of multiple files simultaneously
- **FR-003**: System MUST accept the following image formats: PNG, JPG, JPEG, WebP, GIF
- **FR-004**: System MUST accept the following video formats: MP4, MOV, WebM
- **FR-005**: System MUST accept the following document formats: PDF, TXT, MD
- **FR-006**: System MUST enforce file size limits: 25MB for images/documents, 100MB for videos
- **FR-007**: System MUST enforce a maximum of 10 files per experiment
- **FR-008**: System MUST enforce a maximum total size of 250MB per experiment
- **FR-009**: System MUST allow users to categorize each material with a type: Design, Prototype, Competitor, Spec, Other
- **FR-010**: System MUST allow users to reorder materials (order affects context presentation)
- **FR-011**: System MUST display instant preview when files are staged for upload
- **FR-012**: System MUST generate and display thumbnail previews for images
- **FR-013**: System MUST generate and display first-frame thumbnails for videos
- **FR-014**: System MUST generate and display first-page previews for PDFs
- **FR-015**: System MUST display file metadata: name, type, size, upload date
- **FR-016**: System MUST allow deletion of individual materials from an experiment
- **FR-017**: System MUST send image materials to vision-capable LLM during interview execution
- **FR-018**: System MUST process video materials and extract key frames for LLM context
- **FR-019**: System MUST extract text content from PDF/TXT/MD files for LLM context
- **FR-020**: System MUST include material references in generated PR-FAQ documents
- **FR-021**: System MUST persist material metadata in the experiment_materials database table
- **FR-022**: System MUST store files in cloud storage with path structure: experiments/{experiment_id}/materials/{file_id}.{ext}

### Key Entities

- **ExperimentMaterial**: Represents an uploaded file attached to an experiment
  - Attributes: id (uuid), experiment_id (fk), file_type (image/video/document), file_url, file_name, file_size, material_type (design/prototype/competitor/spec/other), description (optional), display_order, created_at
  - Relationships: belongs to one Experiment; Experiment has many ExperimentMaterials

- **Experiment** (existing): Extended to support material attachments
  - New relationship: has many ExperimentMaterials ordered by display_order

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can upload and attach materials to experiments in under 30 seconds for typical file sizes (under 10MB)
- **SC-002**: 95% of file uploads complete successfully without errors
- **SC-003**: Preview thumbnails render within 2 seconds of file selection
- **SC-004**: Synth responses reference at least one specific visual element from materials in 80% of interviews with attached materials
- **SC-005**: Generated PR-FAQs include material references when interviews discussed visual elements
- **SC-006**: System handles 50 concurrent file uploads without degradation
- **SC-007**: Users can identify attached materials and their types at a glance on the experiment page
- **SC-008**: Material context increases synth response specificity (qualitative improvement in design feedback)

## Assumptions

- railway storage (compatible) is available and configured for the application
- OpenAI GPT is available for processing image, video and PDF content
- The existing experiment creation/edit flow can be extended without major restructuring
- File upload will use presigned URLs for direct-to-storage uploads to avoid backend bottlenecks
