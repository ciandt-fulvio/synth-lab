# Feature Specification: Sankey Diagram for Outcome Flow Visualization

**Feature Branch**: `025-sankey-diagram`
**Created**: 2025-12-31
**Status**: Draft
**Input**: User description: "Sankey diagram visualization showing 3-level flow: Population → Outcomes (did_not_try, failed, success) → Root Causes"

## Clarifications

### Session 2025-12-31

- Q: Where should the Sankey diagram be placed in the UI? → A: Inside `experiments/{id}`, quantitative analysis, "Geral" tab, above "Tentativa vs Sucesso" chart
- Q: How should the chart handle caching and data fetching? → A: Follow existing analysis chart patterns (React Query cache, parallel fetch, same error/loading states)
- Q: What should be the Portuguese title for the Sankey diagram section? → A: "Fluxo de Resultados"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Outcome Distribution Flow (Priority: P1)

As a product manager viewing simulation results, I want to see a Sankey diagram showing how the synth population flows through outcomes, so that I can immediately understand the distribution of success, failure, and non-adoption.

**Why this priority**: This is the core visualization that provides the primary value - understanding at a glance how users distribute across outcomes. Without this, there is no feature.

**Independent Test**: Can be fully tested by running a simulation and viewing the Sankey diagram. Delivers visual understanding of outcome distribution with clickable flows.

**Acceptance Scenarios**:

1. **Given** a completed simulation with synth outcomes, **When** I navigate to the Sankey diagram view, **Then** I see a 3-level flow diagram showing Population → Outcomes → Root Causes
2. **Given** a Sankey diagram is displayed, **When** I look at the first level, **Then** I see the total population count flowing to three outcome categories (did_not_try, failed, success)
3. **Given** a Sankey diagram with outcome flows, **When** I examine any flow link, **Then** I see the count of synths represented by that flow

---

### User Story 2 - Understand Root Causes for Non-Adoption (Priority: P2)

As a product manager, I want to see why synths in the "did_not_try" category didn't attempt to use the feature, so that I can identify which barriers (high effort, perceived risk, or complexity) are preventing adoption.

**Why this priority**: Understanding why users don't try is critical for improving adoption rates. This extends the basic visualization with diagnostic value.

**Independent Test**: Can be tested by examining the third level of the Sankey for "did_not_try" outcomes and verifying root causes are displayed with correct attribution.

**Acceptance Scenarios**:

1. **Given** synths with "did_not_try" as their dominant outcome, **When** the Sankey diagram is rendered, **Then** I see flows from "did_not_try" to specific root causes: "Esforço inicial alto", "Risco percebido", or "Complexidade aparente"
2. **Given** a synth didn't try due to motivation gap (effort > motivation), **When** their root cause is calculated, **Then** they are attributed to "Esforço inicial alto"
3. **Given** a synth didn't try due to trust gap (risk > trust), **When** their root cause is calculated, **Then** they are attributed to "Risco percebido"
4. **Given** a synth didn't try due to friction gap (complexity > friction tolerance), **When** their root cause is calculated, **Then** they are attributed to "Complexidade aparente"

---

### User Story 3 - Understand Root Causes for Failure (Priority: P3)

As a product manager, I want to see why synths in the "failed" category couldn't complete the feature successfully, so that I can identify whether the feature is too complex or takes too long to deliver value.

**Why this priority**: Understanding failure causes helps prioritize UX improvements. This completes the diagnostic picture for all non-success outcomes.

**Independent Test**: Can be tested by examining the third level of the Sankey for "failed" outcomes and verifying root causes are displayed with correct attribution.

**Acceptance Scenarios**:

1. **Given** synths with "failed" as their dominant outcome, **When** the Sankey diagram is rendered, **Then** I see flows from "failed" to specific root causes: "Capability insuficiente" or "Desistiu antes do valor"
2. **Given** a synth failed due to capability gap (complexity > capability), **When** their root cause is calculated, **Then** they are attributed to "Capability insuficiente"
3. **Given** a synth failed due to patience gap (time_to_value > friction_tolerance), **When** their root cause is calculated, **Then** they are attributed to "Desistiu antes do valor"

---

### User Story 4 - View Success Distribution (Priority: P4)

As a product manager, I want to see the success category in the Sankey diagram without further breakdown, so that I understand the proportion of synths who successfully adopted the feature.

**Why this priority**: Success is the positive outcome and doesn't require root cause diagnosis. Showing it completes the picture but adds less actionable insight than failure analysis.

**Independent Test**: Can be tested by verifying the "success" outcome appears in the Sankey with correct count and terminates at level 2 (no level 3 breakdown).

**Acceptance Scenarios**:

1. **Given** synths with "success" as their dominant outcome, **When** the Sankey diagram is rendered, **Then** I see a flow from "População" to "success" with the correct count
2. **Given** the success category, **When** I view the diagram, **Then** there is no further breakdown to a third level (success is a terminal node)

---

### Edge Cases

- What happens when a simulation has 0 synths in a particular outcome category?
  - The flow for that outcome should not be displayed (no empty flows)
- What happens when all synths have the same outcome?
  - Only the relevant flows are shown; other outcome categories are omitted
- How does the system handle synths with tied root cause gaps (e.g., motivation_gap = trust_gap)?
  - The system uses a deterministic priority order to break ties: motivation_gap > trust_gap > friction_gap for "did_not_try"; capability_gap > patience_gap for "failed"
- What happens when a simulation has no synth outcomes yet (simulation in progress)?
  - The Sankey diagram view shows a loading state or message indicating results are not yet available

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST calculate the dominant outcome for each synth based on their outcome rates (did_not_try_rate, failed_rate, success_rate)
- **FR-002**: System MUST aggregate synths by their dominant outcome to produce Level 1 → Level 2 flows
- **FR-003**: System MUST diagnose root causes for synths with "did_not_try" as dominant outcome by comparing user state against feature scorecard dimensions
- **FR-004**: System MUST diagnose root causes for synths with "failed" as dominant outcome by comparing synth capabilities against feature scorecard dimensions
- **FR-005**: System MUST generate flow data in a format suitable for Sankey diagram rendering (source, target, value)
- **FR-006**: System MUST expose an endpoint to retrieve Sankey flow data for a given simulation
- **FR-007**: System MUST display the Sankey diagram in the "Geral" (Overview) tab of quantitative analysis, positioned above the "Tentativa vs Sucesso" chart
- **FR-008**: System MUST show counts/values on each flow link in the diagram
- **FR-009**: System MUST use deterministic tie-breaking when multiple gaps are equal (priority order defined in edge cases)
- **FR-010**: System MUST fetch Sankey data in parallel with other Phase 1 charts using React Query with standard caching (staleTime: 5 minutes)

### Key Entities

- **SankeyFlow**: Represents a flow between two nodes in the diagram (source node label, target node label, value/count)
- **SankeyNode**: Represents a node in the diagram (label, optional color, level)
- **OutcomeDiagnosis**: Represents the root cause diagnosis for a synth (synth_id, dominant_outcome, root_cause, gap_values)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can identify the largest barrier to adoption (root cause with highest flow value) within 5 seconds of viewing the diagram
- **SC-002**: The Sankey diagram correctly displays all non-zero outcome flows from a simulation
- **SC-003**: Root cause attribution accuracy: 100% of synths are assigned exactly one root cause based on gap calculations
- **SC-004**: The diagram renders within 2 seconds for simulations with up to 10,000 synths
- **SC-005**: Users report the visualization helps them understand outcome distribution (qualitative validation during testing)

## UI Placement & Integration

- **Location**: Experiments page (`/experiments/{id}`), Quantitative Analysis section, "Geral" (Overview) tab
- **Position**: Above the "Tentativa vs Sucesso" scatter chart
- **Section Title**: "Fluxo de Resultados"
- **Behavior**: Must follow existing analysis chart patterns:
  - Use React Query with caching (staleTime: 5 minutes, matching Phase 1 charts)
  - Data fetched in parallel with other Phase 1 charts
  - Query key pattern: `['analysis', experimentId, 'sankey-flow']`
  - Standard loading/error/empty states consistent with other charts
  - Wrapped in `ChartErrorBoundary`

## Assumptions

- The Sankey diagram will be rendered using a charting library available in the frontend (e.g., Recharts, which is already in the project)
- Root cause labels will be displayed in Portuguese as specified in the user description ("Esforço inicial alto", "Risco percebido", etc.)
- The feature scorecard dimensions (complexity, initial_effort, perceived_risk, time_to_value) each have min/max ranges, and the midpoint is used for gap calculations
- Synth latent traits (capability_mean, trust_mean, friction_tolerance_mean) are available in SimulationAttributes
- The scenario modifiers affect motivation, trust, and friction tolerance when sampling user state
- Success outcomes do not require root cause breakdown (terminal node)
