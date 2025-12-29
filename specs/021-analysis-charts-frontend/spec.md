# Feature Specification: Analysis Charts Frontend Integration

**Feature Branch**: `021-analysis-charts-frontend`
**Created**: 2025-12-28
**Status**: Draft
**Input**: User description: "Bring remaining quantitative analysis charts from backend to frontend. TryVsSuccess, Distribution) already implemented. Need to implement Phases 2-6 following the established pattern."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Problem Location Charts

UX Researcher accesses Problem Location identify where the user experience breaks using Heatmap, Box Plot, Scatter Correlation, and Tornado charts.

**Independent Test**: Can be tested by navigating to an experiment's results page, selecting the "Localização" tab, and verifying all four chart types render correctly with interactive controls.

**Acceptance Scenarios**:

1. **Given** an experiment with completed analysis, **When** user navigates to Problem Location phase, **Then** user sees Failure Heatmap, Box Plot, Scatter Correlation, and Tornado charts with loading states while data fetches.
2. **Given** Failure Heatmap is displayed, **When** user changes X or Y axis selectors, **Then** chart updates with new data from API based on selected dimensions.
3. **Given** Box Plot is displayed, **When** user selects a different attribute, **Then** chart updates showing distribution for that attribute across outcome groups.
4. **Given** Scatter Correlation is displayed, **When** user changes X and Y axis, **Then** chart updates with correlation coefficient and trendline.
5. **Given** any chart encounters an API error, **When** error occurs, **Then** user sees error state with "Retry" button that refetches data.

---

### User Story 2 - Persona Segmentation

UX Researcher groups synths into clusters using K-Means or Hierarchical Clustering to identify distinct persona segments.

**Independent Test**: Can be tested by navigating to Segmentation phase, configuring clustering parameters, generating clusters, and viewing Elbow/Dendrogram and Radar comparison charts.

**Acceptance Scenarios**:

1. **Given** experiment with completed analysis, **When** user navigates to Segmentation phase, **Then** user sees clustering configuration panel with K-Means and Hierarchical tabs.
2. **Given** K-Means tab selected, **When** user sets number of clusters and clicks "Generate Clusters", **Then** system creates clusters and displays Radar comparison chart.
3. **Given** K-Means tab selected, **When** Elbow chart is displayed, **Then** user can click on a point to auto-fill the K value input.
4. **Given** Hierarchical tab selected, **When** Dendrogram is displayed, **Then** user can click to set cut height and generate clusters.
5. **Given** clusters have been generated, **When** user views Radar Comparison chart, **Then** chart displays overlaid cluster profiles with distinct colors for each cluster.

---

### User Story 3 - Edge Cases Identification

UX Researcher identifies extreme synths and statistical outliers to select candidates for qualitative interviews.

**Independent Test**: Can be tested by navigating to Edge Cases  viewing tables of extreme cases (worst failures, best successes, unexpected) and outliers.

**Acceptance Scenarios**:

1. **Given** experiment with completed analysis, **When** user navigates to Edge Cases phase, **Then** user sees tables for Extreme Cases and Outliers.
2. **Given** Extreme Cases table is displayed, **When** data loads, **Then** table shows synths categorized as "worst failure", "best success", or "unexpected" with attributes and suggested interview questions.
3. **Given** Outliers table is displayed, **When** user adjusts contamination slider, **Then** outlier detection reruns with new sensitivity and table updates.
4. **Given** a synth is displayed in any table, **When** user views synth details, **Then** synth's attributes and outcome rates are visible.

---

### User Story 4 - Deep Explanation

UX Researcher understands why specific synths failed using SHAP explanations and PDP (Partial Dependence Plots) for feature impact analysis.

**Independent Test**: Can be tested by navigating to Explainability phase, viewing SHAP summary chart, selecting a synth for individual SHAP explanation, and viewing PDP charts.

**Acceptance Scenarios**:

1. **Given** experiment with completed analysis, **When** user navigates to Explainability phase, **Then** user sees SHAP Summary chart showing global feature importance.
2. **Given** SHAP Summary is displayed, **When** user clicks on a synth in any table/chart, **Then** individual SHAP Waterfall chart is displayed for that synth.
3. **Given** Explainability displayed, **When** user views PDP section, **Then** PDP charts show how each feature affects success probability.
4. **Given** multiple features available, **When** user views PDP comparison, **Then** charts display side-by-side PDPs ranked by impact.

---

### User Story 5 - LLM Insights

UX Researcher obtains AI-generated insights and executive summary to communicate findings to stakeholders.

**Independent Test**: Can be tested by navigating to Insights phase, viewing any existing insights, and generating new insights for specific charts or executive summary.

**Acceptance Scenarios**:

1. **Given** experiment with completed analysis, **When** user navigates to Insights phase, **Then** user sees list of generated insights (or empty state if none).
2. **Given** user is on a chart in any phase, **When** user clicks "Generate Insight" button on chart, **Then** LLM generates insight with caption, explanation, evidence, and recommendation.
3. **Given** multiple insights exist, **When** user clicks "Generate Executive Summary", **Then** LLM creates comprehensive summary across all insights.
4. **Given** insight is displayed, **When** user views insight, **Then** short caption, medium explanation, evidence bullets, and actionable recommendation are visible.

---

### Edge Cases

- **Empty data**: What happens when an analysis has no synth outcomes?
  - Charts show "No data available" empty state with descriptive message

- **Analysis not completed**: What happens when analysis is still running or failed?
  - Charts are disabled with message indicating analysis must complete first

- **Clustering not generated**: What happens when user tries to view Radar before generating clusters?
  - Show empty state with "Generate clusters first" message

- **API timeout**: What happens when chart data fetch times out?
  - Show error state with retry button; React Query handles automatic retries

- **Invalid thresholds**: What happens when user sets invalid threshold values?
  - UI validates input ranges; API returns validation errors for out-of-range values

## Requirements *(mandatory)*

### Functional Requirements

** Problem Location**:
- **FR-001**: System MUST display Failure Heatmap chart with configurable X and Y axis dimensions
- **FR-002**: System MUST display Box Plot chart comparing attribute distributions across outcome groups (success, failed, did_not_try)
- **FR-003**: System MUST display Scatter Correlation chart with trendline and correlation coefficient
- **FR-004**: System MUST display Tornado chart showing attribute impact on success probability
- **FR-005**: All harts MUST support axis/attribute selection via dropdown controls

** Segmentation**:
- **FR-006**: System MUST display Elbow chart for K-Means optimal cluster selection
- **FR-007**: System MUST allow user to input number of clusters and trigger clustering
- **FR-008**: System MUST display Dendrogram for hierarchical clustering with interactive cut height
- **FR-009**: System MUST display Radar Comparison chart showing cluster profiles
- **FR-010**: System MUST support both K-Means and Hierarchical clustering methods

** Edge Cases**:
- **FR-011**: System MUST display Extreme Cases table with categorized synths (worst_failure, best_success, unexpected)
- **FR-012**: System MUST display Outliers table with anomaly scores and explanations
- **FR-013**: System MUST allow user to configure outlier detection sensitivity (contamination parameter)

** Explainability**:
- **FR-014**: System MUST display SHAP Summary chart showing global feature importance
- **FR-015**: System MUST display SHAP Waterfall chart for individual synth explanation
- **FR-016**: System MUST display PDP charts for feature impact on success probability
- **FR-017**: System MUST display PDP Comparison showing multiple features ranked by impact

** LLM Insights**:
- **FR-018**: System MUST display list of generated insights for an analysis
- **FR-019**: System MUST allow user to generate insights for individual charts
- **FR-020**: System MUST allow user to generate executive summary across all insights
- **FR-021**: Each insight MUST include caption, explanation, evidence, and recommendation

**Cross-cutting**:
- **FR-022**: All charts MUST display loading skeleton while data is fetching
- **FR-023**: All charts MUST display error state with retry button on API failure
- **FR-024**: All charts MUST display empty state when no data is available
- **FR-025**: Chart data MUST be cached using React Query with 5-minute stale time

### Key Entities

**Chart Data Types** (already defined in `frontend/src/types/simulation.ts`):
- **FailureHeatmapChart**: Cells with x/y bins and metric values for heatmap visualization
- **BoxPlotChart**: Statistics (min, q1, median, q3, max, outliers) per outcome category
- **ScatterCorrelationChart**: Points with x/y values, outcome, correlation, and trendline
- **TornadoChart**: Bars with dimension impact (low_delta, high_delta, impact_score)
- **ClusterProfile/KMeansResult/HierarchicalResult**: Cluster assignments and profiles
- **RadarChart**: Cluster comparison with axis values
- **ExtremeCasesTable/OutlierResult**: Synth identification for interviews
- **ShapSummary/ShapExplanation**: Feature importance and individual explanations
- **PDPResult/PDPComparison**: Partial dependence data for feature effects
- **ChartInsight/SimulationInsights**: LLM-generated insights

**API Service Functions** (already defined in `frontend/src/services/simulation-api.ts`):
- `getFailureHeatmap`, `getBoxPlotChart`, `getScatterCorrelation`, `getTornadoChart`
- `createClustering`, `getClustering`, `getElbowData`, `getDendrogram`, `getRadarComparison`
- `getExtremeCases`, `getOutliers`
- `getShapSummary`, `getShapExplanation`, `getPDP`, `getPDPComparison`
- `getSimulationInsights`, `generateChartInsight`, `generateExecutiveSummary`

## Assumptions

1. Backend API endpoints for all phases are already implemented and functional
2. TypeScript types for all chart data structures are already defined in `frontend/src/types/simulation.ts`
3. API service functions are already defined in `frontend/src/services/simulation-api.ts`
4. Query keys for all chart types are already defined in `frontend/src/lib/query-keys.ts`
5. hart components exist but use `/simulation/simulations/{id}/...` endpoints; need to use `/experiments/{id}/analysis/...` endpoints
6. Frontend routing structure with s is already in place
7. ChartContainer shared component for loading/error/empty states already exists
8. Design system colors and styles from `frontend/CLAUDE.md` should be followed

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 6 phases accessible from experiment results page with functional tab navigation
- **SC-002**: Charts render within 2 seconds of tab selection (including API call and rendering)
- **SC-003**: Interactive controls (axis selectors, sliders, cluster configuration) update charts immediately upon change
- **SC-004**: 100% of charts display appropriate loading, error, and empty states
- **SC-005**: User can complete full analysis workflow (Overview → Location → Segmentation → Edge Cases → Explainability → Insights) without page refresh
- **SC-006**: Charts match visual style defined in design system (indigo/slate color palette, consistent typography)
- **SC-007**: All chart tooltips display relevant information on hover
- **SC-008**: Clustering generation completes and displays Radar comparison within 10 seconds for typical experiments (500 synths)
