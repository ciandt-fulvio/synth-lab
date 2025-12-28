# Feature Specification: Experiment Results Frontend

**Feature Branch**: `020-experiment-results-frontend`
**Created**: 2025-12-28
**Status**: Draft
**Input**: User description: "Frontend implementation of experiment analysis results display with 6 phases: Visão Geral, Localização, Segmentação, Casos Especiais, Aprofundamento, and Insights LLM. Integrates with existing backend API endpoints for simulation charts, clustering, outliers, explainability (SHAP/PDP), and LLM-generated insights."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Phase 1: Visão Geral (Overview) (Priority: P1)

UX Researcher views the overall simulation results to quickly understand what happened with the feature being tested. They see Try vs Success quadrant chart, outcome distribution pie chart, and Sankey flow diagram showing user journey paths.

**Why this priority**: This is the entry point for analysis. Without an overview, users cannot begin their research investigation. It answers the fundamental question "O que aconteceu?" (What happened?).

**Independent Test**: Can be fully tested by navigating to `/experiments/{id}`, clicking on "Visão Geral" tab, and verifying all three charts (Try vs Success, Distribution, Sankey) render correctly with data from the backend.

**Acceptance Scenarios**:

1. **Given** an experiment with completed simulation, **When** user navigates to experiment detail and selects "Visão Geral" tab, **Then** they see Try vs Success scatter chart showing synths positioned by their try and success rates
2. **Given** an experiment with completed simulation, **When** user views "Visão Geral", **Then** they see outcome distribution pie chart with success (green), failed (red), and did_not_try (gray) segments with percentages
3. **Given** an experiment with completed simulation, **When** user views "Visão Geral", **Then** they see Sankey diagram showing flow from total synths through try/not-try to success/fail outcomes
4. **Given** an experiment without simulation data, **When** user selects "Visão Geral" tab, **Then** they see an empty state prompting them to run the analysis

---

### User Story 2 - Phase 2: Localização (Problem Location) (Priority: P1)

UX Researcher identifies where in the user experience problems occur using failure heatmap, box plots, scatter plots, and tornado charts.

**Why this priority**: Critical for understanding WHERE problems exist before diving into WHO is affected. Directly supports the question "Onde exatamente a experiência tem mais potencial de problema?"

**Independent Test**: Can be fully tested by navigating to "Localização" tab and verifying all four visualization types (Heatmap, Box Plot, Scatter, Tornado) render with correct data.

**Acceptance Scenarios**:

1. **Given** completed simulation, **When** user views "Localização" tab, **Then** they see failure heatmap showing correlation between attributes and failure rates
2. **Given** completed simulation, **When** user views "Localização" tab, **Then** they see box plots comparing success/fail distributions across key dimensions
3. **Given** completed simulation, **When** user views "Localização" tab, **Then** they see scatter plot allowing exploration of two variables against outcomes
4. **Given** completed simulation, **When** user views "Localização" tab, **Then** they see tornado chart ranking factors by impact on success/failure

---

### User Story 3 - Phase 3: Segmentação (Persona Segmentation) (Priority: P2)

UX Researcher groups synths into behavioral clusters to understand distinct user types using K-Means clustering with elbow method visualization, radar charts for cluster comparison, and dendrograms for hierarchical relationships.

**Why this priority**: Segmentation builds on location data to reveal WHO behaves differently. Important but requires Phase 1-2 context first.

**Independent Test**: Can be fully tested by navigating to "Segmentação" tab, triggering cluster generation, and verifying elbow chart, radar comparison, and dendrogram visualizations.

**Acceptance Scenarios**:

1. **Given** completed simulation without clusters, **When** user views "Segmentação" tab, **Then** they see option to generate clusters with configurable number of clusters (k)
2. **Given** clusters have been generated, **When** user views "Segmentação" tab, **Then** they see elbow chart showing optimal k value and silhouette scores
3. **Given** clusters exist, **When** user views cluster details, **Then** they see radar chart comparing cluster profiles across behavioral dimensions
4. **Given** clusters exist, **When** user selects dendrogram view, **Then** they see hierarchical clustering visualization with suggested cut points

---

### User Story 4 - Phase 4: Casos Especiais (Edge Cases) (Priority: P2)

UX Researcher identifies extreme cases and outliers to prioritize synths for qualitative follow-up interviews.

**Why this priority**: Identifies interview candidates, which is valuable but depends on understanding segments first.

**Independent Test**: Can be fully tested by navigating to "Casos Especiais" tab and verifying extreme cases table and outlier detection results display correctly.

**Acceptance Scenarios**:

1. **Given** completed simulation, **When** user views "Casos Especiais" tab, **Then** they see table of worst failures (top 10) with synth profiles and suggested interview questions
2. **Given** completed simulation, **When** user views "Casos Especiais" tab, **Then** they see table of best successes (top 10) with synth profiles
3. **Given** completed simulation, **When** user views "Casos Especiais" tab, **Then** they see unexpected cases (synths that defied predictions based on attributes)
4. **Given** outlier detection enabled, **When** user views outliers section, **Then** they see outlier synths with anomaly scores and explanations

---

### User Story 5 - Phase 5: Aprofundamento (Deep Explanation) (Priority: P2)

UX Researcher understands WHY specific synths succeeded or failed using SHAP explanations for individual cases and PDP charts for understanding feature effects.

**Why this priority**: Provides causal understanding after identifying who to focus on in Phase 4.

**Independent Test**: Can be fully tested by selecting a synth from edge cases and viewing SHAP waterfall chart and PDP curves for key features.

**Acceptance Scenarios**:

1. **Given** a synth selected for analysis, **When** user views SHAP explanation, **Then** they see waterfall chart showing each feature's contribution to the prediction
2. **Given** completed simulation, **When** user views SHAP summary, **Then** they see global feature importance ranking across all synths
3. **Given** a feature selected, **When** user views PDP chart, **Then** they see how varying that feature affects predicted success rate
4. **Given** multiple features selected, **When** user views PDP comparison, **Then** they see overlaid PDP curves for comparing feature effects

---

### User Story 6 - Phase 6: Insights LLM (AI-Generated Insights) (Priority: P3)

UX Researcher obtains AI-generated insights and executive summary for communicating findings to stakeholders.

**Why this priority**: Final synthesis step that depends on all previous phases. Lower priority but high value for stakeholder communication.

**Independent Test**: Can be fully tested by navigating to "Insights" tab and generating insights for individual charts and executive summary.

**Acceptance Scenarios**:

1. **Given** chart data available, **When** user requests insight for a specific chart, **Then** they see caption, explanation, evidence list, and recommendation
2. **Given** multiple insights generated, **When** user views insights list, **Then** they see all generated insights organized by chart type
3. **Given** insights available, **When** user requests executive summary, **Then** they receive consolidated summary suitable for stakeholder presentation
4. **Given** insight generation in progress, **When** user views insight panel, **Then** they see loading state with progress indication

---

### Edge Cases

- What happens when backend API returns empty data for a chart? → Display informative empty state with guidance
- How does system handle API timeout during chart data fetch? → Show error state with retry option
- What happens when cluster generation fails? → Display error message and allow retry with different parameters
- How does system handle very large datasets (1000+ synths)? → Paginate data tables, use efficient chart rendering
- What happens when SHAP calculation fails for a synth? → Show message explaining why and suggest alternatives
- What happens when user navigates between tabs rapidly? → Cancel pending requests, show only latest data

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display AnalysisPhaseTabs component with 6 tabs navigable sequentially and directly
- **FR-002**: System MUST fetch chart data from backend API using React Query with appropriate caching and error handling
- **FR-003**: System MUST render Try vs Success scatter chart using Recharts library with synth points colored by outcome
- **FR-004**: System MUST render outcome distribution pie chart with legend showing success/failed/did_not_try percentages
- **FR-005**: System MUST render Sankey diagram showing user flow from population through try decision to outcome
- **FR-006**: System MUST render failure heatmap showing correlation matrix between attributes and failure rates
- **FR-007**: System MUST render box plots comparing value distributions across outcome categories
- **FR-008**: System MUST render scatter plot with configurable X/Y axis selection and outcome coloring
- **FR-009**: System MUST render tornado chart ranking factors by absolute impact magnitude
- **FR-010**: System MUST allow user to trigger cluster generation with configurable k parameter
- **FR-011**: System MUST render elbow chart showing inertia and silhouette scores for k values 2-10
- **FR-012**: System MUST render radar charts for individual clusters and comparison overlay
- **FR-013**: System MUST render dendrogram visualization with interactive cut point selection
- **FR-014**: System MUST display extreme cases tables (worst failures, best successes, unexpected)
- **FR-015**: System MUST display outlier detection results with anomaly scores and explanations
- **FR-016**: System MUST render SHAP waterfall chart for individual synth explanation
- **FR-017**: System MUST render SHAP summary (global feature importance) chart
- **FR-018**: System MUST render PDP line charts with optional confidence intervals
- **FR-019**: System MUST allow user to generate LLM insights for specific chart types
- **FR-020**: System MUST display generated insights with caption, explanation, evidence, and recommendation
- **FR-021**: System MUST allow user to generate executive summary consolidating all insights
- **FR-022**: System MUST show loading states for all async operations (skeleton or spinner)
- **FR-023**: System MUST show error states with retry capability for failed API calls
- **FR-024**: System MUST show empty states with guidance when no data is available

### Key Entities *(include if feature involves data)*

- **ChartData**: Response from chart endpoints containing visualization-ready data (varies by chart type)
- **ClusterResult**: K-Means or hierarchical clustering result with cluster profiles and assignments
- **ExtremeCasesTable**: Collection of worst failures, best successes, and unexpected cases
- **OutlierResult**: List of outlier synths with anomaly scores and explanations
- **ShapExplanation**: Feature contributions explaining individual synth outcome
- **PDPResult**: Partial dependence plot data for a feature
- **ChartInsight**: LLM-generated insight with caption, explanation, evidence, and recommendation
- **SimulationInsights**: Collection of all insights for a simulation with optional executive summary

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 6 analysis phases are navigable within 1 second tab switch time
- **SC-002**: Charts render within 2 seconds of data availability (excluding API latency)
- **SC-003**: Users can complete analysis journey (Phase 1 → Phase 6) without errors on valid data
- **SC-004**: Empty, loading, and error states display correctly for all data-dependent components
- **SC-005**: UI remains responsive (no blocking) during data fetching and chart rendering
- **SC-006**: Users can identify top 3 insights within 5 minutes of viewing completed analysis
- **SC-007**: Generated insights are displayed in under 1 second after API response
- **SC-008**: Design consistency maintained with existing PRFAQ/Summary display patterns (MarkdownPopup, ArtifactButton)

## Assumptions

- Backend API endpoints are already implemented and tested (per documentation provided)
- Recharts library (already installed) can handle all required chart types
- React Query (already installed) provides adequate caching and state management
- Existing AnalysisPhaseTabs component provides the tab navigation foundation
- shadcn/ui components provide consistent styling without customization
- Sankey diagram will use a specialized Recharts component or compatible library
- Dendrogram visualization may require custom SVG rendering if Recharts doesn't support it
- SHAP waterfall chart will use horizontal bar chart with positive/negative styling
