# Feature Specification: AI-Generated Insights for Quantitative Analysis

**Feature Branch**: `023-quantitative-ai-insights`
**Created**: 2025-12-29
**Status**: Draft
**Input**: User description: "vamos agora trabalhar no uso de IA no processo quantitativo - teremos 2 tipos de relatorios: insights individuais por gráfico e um resumo executivo agregado"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Individual Chart Insights (Priority: P1)

As a researcher analyzing quantitative results, I want to see AI-generated insights directly within each chart card, so I can quickly understand what the data reveals without manual interpretation.

**Why this priority**: This is the core value proposition - automatic interpretation of simulation data. Delivers immediate value even without the executive summary, as each chart becomes self-explanatory.

**Independent Test**: Can be fully tested by running a simulation, navigating to any supported chart (Try vs Success, SHAP, PDP, PCA, Profile Comparison, Extreme Cases, or Outliers), and verifying that an expandable insight section appears within the chart card with AI-generated analysis.

**Acceptance Scenarios**:

1. **Given** a simulation has completed and chart data is cached, **When** I view a supported chart (e.g., Try vs Success), **Then** I see a collapsible "Insights" section within the chart card
2. **Given** the insights section is collapsed, **When** I click to expand it, **Then** I see a concise summary (≤200 words) describing what the AI understood about the problem, trends observed, and key findings
3. **Given** I'm viewing an unsupported chart type, **When** the chart loads, **Then** no insight section appears (only supported charts: Try vs Success, SHAP, PDP, PCA, Profile Comparison, Extreme Cases, Outliers)
4. **Given** chart data is being recalculated, **When** new results are cached, **Then** insights are automatically regenerated in the background

---

### User Story 2 - Access Executive Summary (Priority: P2)

As a product manager reviewing simulation results, I want to access a consolidated executive summary that synthesizes all chart insights, so I can understand the overall findings without reviewing each chart individually.

**Why this priority**: Provides high-level overview for decision-makers who need the big picture. Depends on individual insights (P1) being available first.

**Independent Test**: Can be tested by running a simulation, waiting for all chart insights to generate, clicking "View Summary" button at the top of the results page, and verifying a modal/panel displays with aggregated findings.

**Acceptance Scenarios**:

1. **Given** all individual chart insights have been generated, **When** I click "View Summary" button at the top of the results page, **Then** a modal or side panel opens displaying the executive summary
2. **Given** the executive summary is displayed, **When** I read it, **Then** it contains a synthesis of all individual insights in ≤800 words, organized by analysis phase (Overview, Problem Location, Segmentation, Explainability)
3. **Given** not all insights have finished generating, **When** I try to view the summary, **Then** I see a loading indicator or message indicating "Generating insights... X of 7 complete"
4. **Given** insight generation failed for some charts, **When** I view the summary, **Then** it includes available insights and notes which charts had no insights generated

---

### User Story 3 - Automatic Insight Generation Workflow (Priority: P1)

As a system user, I expect insights to be generated automatically in the background after simulation completes, so I don't have to manually trigger analysis or wait for sequential processing.

**Why this priority**: Critical for UX - users should never have to think about triggering insight generation. This is infrastructure that enables P1 and P2.

**Independent Test**: Can be tested by running a simulation, monitoring background tasks, and verifying that insight generation starts automatically after chart caching completes, runs in parallel for all chart types, and completes within reasonable time.

**Acceptance Scenarios**:

1. **Given** a simulation completes, **When** each chart's data is written to the analysis_cache table, **Then** an async insight generation task is triggered for that chart type
2. **Given** multiple chart insights are being generated, **When** I check system status, **Then** all insight generation processes run in parallel (not sequentially)
3. **Given** all individual insights complete, **When** the last insight finishes, **Then** the executive summary generation automatically starts
4. **Given** insight generation for a chart fails, **When** viewing that chart, **Then** the insights section shows "Insights unavailable" without breaking the page

---

### Edge Cases

- What happens when a simulation has no data for certain chart types (e.g., no outliers detected)? → Insight generation should gracefully skip that chart type
- How does the system handle very large datasets (e.g., 10,000+ data points in SHAP summary)? → AI should sample or aggregate data to fit within token limits while maintaining representativeness
- What if the LLM API is unavailable or rate-limited? → System should queue insight generation with retry logic and show "Insights pending" in UI
- What happens to old insights when a simulation is re-run? → Old insights should be replaced with newly generated ones, with timestamp indicating freshness
- How are insights handled for experiments with missing context (no hypothesis, description)? → AI should work with available data only, noting in the insight that context is limited

## Requirements *(mandatory)*

### Functional Requirements

#### Chart Insight Generation

- **FR-001**: System MUST automatically trigger insight generation for each supported chart type (Try vs Success, SHAP Summary, PDP, PCA Scatter, Radar Comparison, Extreme Cases, Outliers) immediately after that chart's data is cached in analysis_cache table
- **FR-002**: System MUST generate insights using a reasoning-capable LLM model (04-mini or equivalent) with input including: experiment hypothesis/description, simulation metadata (synth count, scorecard), chart-specific data in tabular format
- **FR-003**: Each individual insight MUST include: (a) what the AI understood about the problem context, (b) what trends/patterns it observed in the chart data, (c) 2-4 key findings specific to that chart, (d) a concise summary in ≤200 words
- **FR-004**: System MUST run insight generation tasks in parallel for all chart types, not sequentially
- **FR-005**: System MUST store generated insights in analysis_cache table with foreign key to experiment_id, chart_type identifier, insight text content, generation timestamp, and status (pending/completed/failed)

#### Executive Summary Generation

- **FR-006**: System MUST automatically trigger executive summary generation after all individual chart insights have completed (either succeeded or failed)
- **FR-007**: Executive summary MUST synthesize all available individual insights into a cohesive narrative of ≤800 words
- **FR-008**: Executive summary MUST be organized by analysis phases: Overview (Try vs Success), Explainability (SHAP, PDP), Segmentation (PCA, Profiles), Edge Cases (Extremes, Outliers)
- **FR-009**: System MUST store executive summary in analysis_cache table linked to experiment_id with summary text, generation timestamp, and status

#### UI Presentation

- **FR-010**: Each supported chart card MUST display a collapsible "Insights" section (collapsed by default) showing the AI-generated insight for that chart type
- **FR-011**: Results page MUST display a "View Summary" button prominently at the top of the page (e.g., in the header or phase navigation area)
- **FR-012**: Clicking "View Summary" MUST open a modal or side panel displaying the executive summary with clear section headings
- **FR-013**: UI MUST remove the existing "Insights" tab from phase navigation and the "Gerar Insight" button from individual chart cards
- **FR-014**: Insights section MUST show loading state while insight is being generated, completed insight text when available, or "Insights unavailable" if generation failed

#### Error Handling & Resilience

- **FR-015**: System MUST gracefully handle LLM API failures with automatic retry (up to 3 attempts with exponential backoff)
- **FR-016**: If insight generation fails for a specific chart after retries, system MUST mark that insight as "failed" in database and continue processing other charts
- **FR-017**: If too few insights are available (< 3 out of 7 charts), executive summary generation SHOULD note the limited data and still provide synthesis of available insights

### Key Entities

- **ChartInsight**: Represents an AI-generated insight for a specific chart type
  - Linked to: Experiment ID (which simulation this analyzes)
  - Attributes: chart_type (enum: try_vs_success, shap_summary, pdp, pca_scatter, radar_comparison, extreme_cases, outliers), insight_text (≤200 words), generation_timestamp, status (pending/completed/failed), reasoning_trace (optional: LLM's reasoning steps for debugging)

- **ExecutiveSummary**: Represents aggregated analysis across all charts
  - Linked to: Experiment ID
  - Attributes: summary_text (≤800 words), generation_timestamp, status, included_chart_types (which charts contributed to this summary)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can access individual chart insights without any manual action - insights appear automatically within 2 minutes of chart data being cached
- **SC-002**: Executive summary becomes available within 30 seconds after the last individual insight completes
- **SC-003**: Insight generation succeeds for at least 90% of supported chart types under normal LLM API conditions
- **SC-004**: Users spend 40% less time interpreting quantitative results compared to manual analysis (measured by time from simulation completion to actionable insights)
- **SC-005**: Insight text quality is validated - at least 85% of insights correctly identify primary trends and findings when reviewed against ground truth in test scenarios

## Assumptions

1. **LLM Access**: System has reliable access to 04-mini or equivalent reasoning-capable model via existing LLM infrastructure
2. **Data Format**: Chart data in analysis_cache is already structured in a format suitable for LLM consumption (JSON with clear schemas)
3. **Concurrency**: Backend infrastructure supports running 7+ parallel async tasks for insight generation without resource contention
4. **Token Limits**: Chart data can be represented within LLM context window limits (~10K tokens for input per chart)
5. **Existing UI**: Current results page has a clear location for "View Summary" button and charts are already card-based components that can accommodate collapsible sections

## Dependencies

- **DEP-001**: Analysis cache system (analysis_cache table) must be operational and reliably storing chart data
- **DEP-002**: LLM client infrastructure with support for reasoning models (04-mini)
- **DEP-003**: Async task queue/worker system for running parallel insight generation
- **DEP-004**: Experiment metadata (hypothesis, description) available via experiment repository

## Out of Scope

- Manual insight editing or customization (v1 is fully automated)
- Insight generation for charts outside the specified 7 chart types
- Comparative insights across multiple experiments (only single-experiment analysis)
- Export of insights to PDF or other formats (can be added later)
- User feedback mechanism on insight quality (can be added for future iterations)
