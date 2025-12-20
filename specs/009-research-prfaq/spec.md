# Feature Specification: Research Report to PR/FAQ Generator

**Feature Branch**: `009-research-prfaq`
**Created**: 2025-12-19
**Status**: Draft
**Input**: User description: "crie uma funcinalidade que, a partir de um report (gerado pelo agente sumarizador), seja possível criar uma PQ/FAQ (conforme este padrao: https://workingbackwards.com/concepts/working-backwards-pr-faq-process/)"

## Overview

Generate professional PR-FAQ documents directly from research batch reports using Amazon's Working Backwards framework. This feature transforms qualitative research insights (from batch research summaries) into structured customer-focused documents that clarify the problem statement, customer benefits, and differentiation.

## Clarifications

### Session 2025-12-19

- Q1: What is the batch_summary.json structure? → A: Markdown text with structured sections (executive_summary, recurrent_patterns, relevant_divergences, identified_tensions, notable_absences, key_quotes, **recommendations**). Required fields: batch_id, summary_content, sections.executive_summary, sections.recommendations.

- Q2: What LLM prompt strategy? → A: Hybrid Chain-of-Thought + Structured Output: Few-shot examples of quality Press Releases/FAQs, JSON Schema validation, and chain-of-thought instruction to identify pain points/benefits from "recommendations" and "recurrent_patterns" sections before generating PR-FAQ.

- Q3: What is the PR-FAQ template structure? → A: Minimal format (Headline, One-liner, Problem, Solution) + FAQ with 8-12 Q&A pairs. Each FAQ answer includes a **Customer Segment** field linking to synth persona archetypes for context and rastreability.

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Generate PR-FAQ from Research Report (Priority: P1)

Product managers want to transform research findings into a structured PR-FAQ document that clearly articulates the customer problem, solution benefits, and key differentiators discovered during user research interviews.

**Why this priority**: This is the core functionality. Without it, no PR-FAQ can be generated. It delivers immediate value by automating the synthesis of qualitative research into strategic documents.

**Independent Test**: User can select a research batch report and generate a complete, valid PR-FAQ document with all required sections (Press Release and FAQ). The document should be immediately usable for stakeholder alignment.

**Acceptance Scenarios**:

1. **Given** a completed research batch report exists in `data/transcripts/{batch_id}/batch_summary.json`, **When** user runs `synthlab research-prfaq generate --batch-id {batch_id}`, **Then** a PR-FAQ document is created at `data/outputs/prfaq/{batch_id}_prfaq.json` with all required sections populated

2. **Given** a research batch summary with identified insights and pain points, **When** the PR-FAQ is generated, **Then** the Press Release section includes: headline, one-liner value proposition, and customer problem statement (all derived from research data)

3. **Given** a research batch summary with noted benefits and use cases, **When** the PR-FAQ is generated, **Then** the FAQ section includes 8-12 questions covering: product benefits, customer segments, key differentiators, and usage scenarios

---

### User Story 2 - Refine and Edit Generated PR-FAQ (Priority: P2)

Product managers need to customize and refine the AI-generated PR-FAQ to match brand voice, organizational strategy, and address any gaps in the auto-generated content.

**Why this priority**: Generated content needs human review and refinement. This feature enables iterative improvement while preserving AI-generated insights.

**Independent Test**: User can load a generated PR-FAQ, edit Press Release and FAQ sections, and save changes. The edited PR-FAQ can be re-exported in multiple formats.

**Acceptance Scenarios**:

1. **Given** a generated PR-FAQ document, **When** user runs `synthlab research-prfaq edit --prfaq-id {id}`, **Then** an interactive editor loads the PR-FAQ sections for modification

2. **Given** edited PR-FAQ content, **When** user saves changes, **Then** modifications are persisted and the document version is updated with change timestamp

3. **Given** edited PR-FAQ, **When** user regenerates from the same research report, **Then** user is prompted to confirm overwrite or preserve manual edits

---

### User Story 3 - Export PR-FAQ to Multiple Formats (Priority: P2)

Product managers need to share PR-FAQ documents with stakeholders in various formats (Markdown for Git, PDF for presentations, HTML for internal wikis).

**Why this priority**: Enables distribution and consumption across different stakeholder groups and documentation systems without manual format conversion.

**Independent Test**: User can export a PR-FAQ document to PDF, Markdown, and HTML formats. Each export preserves content structure and is ready for consumption.

**Acceptance Scenarios**:

1. **Given** a completed PR-FAQ document, **When** user runs `synthlab research-prfaq export --prfaq-id {id} --format pdf`, **Then** a professional PDF is generated with proper formatting, headings, and styling

2. **Given** a PR-FAQ document, **When** user runs `synthlab research-prfaq export --prfaq-id {id} --format markdown`, **Then** a Markdown file is generated with proper heading hierarchy and is Git-friendly

3. **Given** a PR-FAQ document, **When** user exports to multiple formats, **Then** all formats are generated in a timestamped directory under `data/outputs/prfaq/{batch_id}_exports/`

---

### User Story 4 - View PR-FAQ Generation History (Priority: P3)

Users need to track which research reports have been converted to PR-FAQs and compare different versions over time.

**Why this priority**: Enables audit trail and comparison of how PR-FAQ evolved as research findings were refined. Useful for understanding decision-making process.

**Independent Test**: User can list all generated PR-FAQs linked to research reports and view metadata (creation date, linked report, number of edits).

**Acceptance Scenarios**:

1. **Given** multiple PR-FAQs exist, **When** user runs `synthlab research-prfaq list`, **Then** a table displays: batch_id, creation date, last modified, linked research report, and status

2. **Given** a specific batch ID, **When** user runs `synthlab research-prfaq history --batch-id {id}`, **Then** version timeline shows all generated and manually edited versions with timestamps

### Edge Cases

- What happens when research report has insufficient insights (< 3 identified pain points)? System should warn user and allow manual input for missing sections.
- How does system handle research reports with conflicting findings? System should highlight multiple perspectives in FAQ responses.
- What if batch research summary is incomplete or malformed? System should validate report structure and request correction before processing.
- How does system handle very short reports (< 500 words)? System should expand with clarifying questions in FAQ based on research participant persona data.
- What if user wants to generate PR-FAQ from multiple research batches on same topic? System should support report fusion/merging before PR-FAQ generation.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST accept batch research report JSON from `data/transcripts/{batch_id}/batch_summary.json` as input. Required fields: batch_id, summary_content (Markdown text), sections.executive_summary, sections.recommendations. Optional fields: sections.recurrent_patterns, sections.relevant_divergences, sections.identified_tensions, sections.notable_absences, sections.key_quotes

- **FR-002**: System MUST parse research report structure to extract from batch_summary.json sections: pain points (from recurrent_patterns and identified_tensions), customer quotes (from key_quotes and divergences), and proposed benefits (from recommendations). Also extract executive summary and identified tensions

- **FR-003**: System MUST use LLM with hybrid chain-of-thought + structured output strategy to generate PR-FAQ document: Press Release section (headline, one-liner, problem statement, solution overview) and FAQ section (8-12 Q&A pairs, each with question, answer, and customer_segment field linking to synth persona archetypes). LLM shall use few-shot examples and JSON Schema validation. Chain-of-thought instruction: identify pain points/benefits from batch_summary.json "recommendations" and "recurrent_patterns" sections before generating PR-FAQ

- **FR-004**: System MUST validate generated PR-FAQ against PR-FAQ structure requirements (all mandatory sections present, proper formatting, internal consistency)

- **FR-005**: System MUST persist generated PR-FAQ to disk in JSON format with metadata (batch_id, generated_at, version, edit_history)

- **FR-006**: System MUST provide interactive editor (CLI or API) allowing users to modify Press Release and FAQ content with change tracking

- **FR-007**: System MUST support exporting PR-FAQ to PDF, Markdown, and HTML formats with proper styling and readability

- **FR-008**: System MUST track PR-FAQ versions and edits with timestamps and allow comparison between versions

- **FR-009**: System MUST validate research report completeness and suggest user clarification if critical insights are missing

- **FR-010**: System MUST handle research reports that lack sufficient data and offer prompts to user for manual input of missing key insights

- **FR-011**: System MUST integrate with existing SynthLab research infrastructure (use existing synth persona data for FAQ customer segment identification)

- **FR-012**: System MUST provide summary statistics about generated PR-FAQ (word count, number of FAQs, customer segments covered, pain points addressed)

### Key Entities *(include if feature involves data)*

- **Research Report**: Batch summary (Markdown text) with required sections: batch_id, summary_content, executive_summary, recommendations. Optional sections: recurrent_patterns, relevant_divergences, identified_tensions, notable_absences, key_quotes

- **PR-FAQ Document**: Structured output with:
  - **Press Release**: headline (string), one_liner (string), problem_statement (string), solution_overview (string)
  - **FAQ**: Array of 8-12 question objects, each with: question (string), answer (string), customer_segment (string referencing synth persona archetype)
  - **Metadata**: batch_id, generated_at, version, edit_history, validation_status

- **PR-FAQ Version**: Historical record of PR-FAQ with generation timestamp, generation method (auto-generated vs. manual edit), source batch ID, and diff with previous version

- **Generation Metadata**: Tracking information including batch_id, generation_timestamp, model_used, prompt_strategy, token_usage, and validation_status

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: Users can generate a complete, valid PR-FAQ document from a research batch report in under 2 minutes (including LLM processing time)

- **SC-002**: Generated PR-FAQ documents contain all required sections with proper formatting and internal consistency (100% validation pass rate)

- **SC-003**: Generated Press Release headline and value proposition accurately reflect research findings as validated by users (≥85% acceptance in user testing)

- **SC-004**: Generated FAQ questions and answers are relevant and specific to research findings (≥80% of FAQs directly address pain points or benefits identified in research)

- **SC-005**: Users can export PR-FAQ to all supported formats (PDF, Markdown, HTML) without errors (100% export success rate)

- **SC-006**: System processes batch research summaries of 5,000+ words without performance degradation (generation completes in <3 minutes)

- **SC-007**: Users report that PR-FAQ documents can be used directly in stakeholder communication with minimal manual edits (≥75% direct usability score)

- **SC-008**: System correctly identifies and handles incomplete research reports, prompting users for critical missing information before generation (100% of incomplete reports detected and handled)

## Implementation Boundaries

### In Scope

- PR-FAQ generation from research batch reports
- Interactive CLI/API for PR-FAQ creation and editing
- Export to PDF, Markdown, HTML formats
- Version tracking and history
- Integration with existing research infrastructure

### Out of Scope

- Automated research report generation (already handled by batch research feature)
- Multi-language PR-FAQ generation
- Real-time collaborative editing
- Automatic PR-FAQ publishing to external platforms
- Competitor analysis integration

## Assumptions

1. Batch research summary follows JSON structure from summarizer agent: Markdown text with required sections (batch_id, summary_content, executive_summary, recommendations) and optional sections (recurrent_patterns, relevant_divergences, identified_tensions, notable_absences, key_quotes)

2. LLM has sufficient context from research data + few-shot examples to generate relevant, specific PR-FAQ content. Chain-of-thought prompting will extract pain points/benefits from "recommendations" and "recurrent_patterns" sections

3. Synth persona archetypes are available and can be matched to FAQ customer_segment fields during generation (FR-011)

4. Users have domain knowledge to validate and refine generated PR-FAQ content

5. PDF, Markdown, and HTML export libraries are available and compatible with project dependencies

6. PR-FAQ generation is sequential (one report at a time), not requiring batch processing of multiple reports simultaneously

7. Generated PR-FAQ documents are stored locally in project data directory, not synced to external systems

## Dependencies & References

- **Amazon Working Backwards**: PR-FAQ framework based on https://workingbackwards.com/concepts/working-backwards-pr-faq-process/
- **Existing Research Infrastructure**: Leverages batch research reports from `research-batch` feature (008) with summarizer agent output
- **LLM Integration**: Uses existing OpenAI API integration from project with:
  - Few-shot prompting (1-2 high-quality PR-FAQ examples)
  - JSON Schema validation for structured output
  - Chain-of-thought instruction focusing on "recommendations" and "recurrent_patterns" extraction
- **Synth Personas**: Links FAQ customer_segment fields to existing synth persona archetypes for rastreability (FR-011)
- **Document Export**: Requires PDF generation library (e.g., reportlab or similar) and HTML/Markdown templating

## Related Features

- **005-ux-research-interviews**: Source of individual interview data
- **009-research-batch** (planned): Batch research execution and summarization
- **006-topic-guides**: Context and research materials organization
