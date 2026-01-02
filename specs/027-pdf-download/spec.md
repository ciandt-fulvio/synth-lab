# Feature Specification: PDF Download for Document Viewer

**Feature Branch**: `027-pdf-download`
**Created**: 2026-01-01
**Status**: Draft
**Input**: User description: "Download PDF no DocumentViewer - Usar html2canvas + jspdf para capturar o conteúdo markdown renderizado e gerar um PDF com download automático"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export Document to PDF (Priority: P1)

Users need to save generated documents (PR/FAQ, Executive Summary, Summary) for offline reading, sharing with stakeholders, or archiving purposes. Currently, they can only view documents in the browser dialog.

**Why this priority**: This is the core functionality - enabling users to download documents in a widely-compatible format. Without this, users cannot easily share or archive their generated content.

**Independent Test**: Can be fully tested by opening any completed document in the DocumentViewer and clicking the download button, which should produce a PDF file with the document content.

**Acceptance Scenarios**:

1. **Given** a user views a completed PR/FAQ document, **When** they click the "Download PDF" button in the dialog header, **Then** a PDF file downloads automatically with the filename format "prfaq_[title-suffix].pdf"

2. **Given** a user views an Executive Summary document, **When** they click the "Download PDF" button, **Then** a PDF file downloads with the filename format "executive_summary_[title-suffix].pdf"

3. **Given** a user views a Summary document, **When** they click the "Download PDF" button, **Then** a PDF file downloads with the filename format "summary_[title-suffix].pdf"

4. **Given** the PDF is being generated, **When** the user looks at the download button, **Then** they see a loading spinner indicating the generation is in progress

5. **Given** a PDF has been generated, **When** the user opens the downloaded file, **Then** the PDF contains all the markdown content rendered with proper formatting (headings, lists, paragraphs, tables if present)

---

### User Story 2 - Prevent Invalid Download Attempts (Priority: P2)

Users should not be able to attempt PDF downloads when the document is not ready or has failed to generate. This prevents confusion and unnecessary error messages.

**Why this priority**: This is important for user experience but depends on P1 being implemented first. It's an enhancement to prevent misuse.

**Independent Test**: Can be fully tested by checking the download button state in various document states (generating, failed, empty) without clicking it.

**Acceptance Scenarios**:

1. **Given** a document is still generating, **When** the user views the DocumentViewer, **Then** the "Download PDF" button is disabled and cannot be clicked

2. **Given** a document generation has failed, **When** the user views the DocumentViewer, **Then** the "Download PDF" button is disabled and cannot be clicked

3. **Given** the document content is empty or unavailable, **When** the user views the DocumentViewer, **Then** the "Download PDF" button is disabled and cannot be clicked

4. **Given** a document is successfully loaded with content, **When** the user views the DocumentViewer, **Then** the "Download PDF" button is enabled and clickable

---

### Edge Cases

- What happens when the markdown content contains very long tables or images that exceed page boundaries?
- How does the system handle special characters or non-ASCII characters in the title suffix when generating the filename?
- What happens if the user clicks the download button multiple times in rapid succession?
- How does the system handle markdown content with embedded HTML or complex formatting?
- What happens if the PDF generation fails (e.g., due to browser limitations or memory constraints)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST add a "Download PDF" button to the DocumentViewer dialog header with a download icon
- **FR-002**: System MUST disable the download button when document status is 'generating', 'failed', or when content is empty/unavailable
- **FR-003**: System MUST show a loading spinner on the download button while PDF is being generated
- **FR-004**: System MUST capture the rendered markdown content from the `<article class="markdown-content">` element using html2canvas
- **FR-005**: System MUST generate high-quality PDF output using a 2x scale factor for html2canvas rendering
- **FR-006**: System MUST convert the canvas image to PDF format using jsPDF library
- **FR-007**: System MUST automatically trigger download of the generated PDF file
- **FR-008**: System MUST generate filename in the format `{documentType}_{titleSuffix}.pdf` where documentType is one of: 'prfaq', 'executive_summary', 'summary'
- **FR-009**: System MUST sanitize the titleSuffix to create a valid filename (replace spaces with hyphens, remove special characters)
- **FR-010**: System MUST preserve markdown formatting in the PDF including headings, paragraphs, lists, and tables
- **FR-011**: System MUST handle PDF generation errors gracefully and display an error message to the user if generation fails
- **FR-012**: System MUST maintain the DocumentViewer dialog open after PDF download completes

### Key Entities

- **DocumentViewer Component**: React component that displays document content and manages the PDF download functionality
  - Properties: documentType (prfaq/executive_summary/summary), markdownContent, status, titleSuffix
  - References: markdown content container element for PDF capture

- **PDF Generation State**: Local component state managing the PDF generation process
  - Attributes: isGeneratingPdf (boolean), error message (optional)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can download a PDF of any completed document in under 5 seconds from clicking the download button
- **SC-002**: Generated PDF files preserve 100% of visible markdown content from the dialog viewer
- **SC-003**: PDF text is readable at standard zoom levels (no pixelation or quality degradation visible at 100% zoom)
- **SC-004**: Download button correctly reflects three distinct states (enabled, disabled, loading) based on document status
- **SC-005**: Filename generation produces valid filenames for all document types and title combinations
- **SC-006**: Users receive clear feedback if PDF generation fails (error message visible within 3 seconds)
- **SC-007**: PDF generation works across modern browsers (Chrome, Firefox, Safari, Edge) without browser-specific issues

## Assumptions

- The existing `html2canvas` (v1.4.1+) and `jspdf` (v3.0.4+) packages are sufficient for PDF generation
- Markdown content is already rendered and styled correctly in the browser before PDF capture
- File download is initiated automatically by the browser (no server-side storage required)
- The `.markdown-content` CSS class provides adequate styling for PDF capture
- Maximum document length is reasonable for client-side PDF generation (under 50 pages)
- Users have permission to download files in their browser (no download blocking)
- Title suffix, when provided, contains only printable characters suitable for filenames

## Out of Scope

- Server-side PDF generation or rendering
- Custom PDF styling different from the rendered markdown appearance
- PDF compression or optimization
- Multi-page document formatting controls (page breaks, headers/footers)
- Email sharing or cloud storage integration
- Batch download of multiple documents
- PDF editing or annotation features
- Print preview functionality
- Alternative export formats (Word, HTML, etc.)
- PDF metadata (author, creation date, keywords)
