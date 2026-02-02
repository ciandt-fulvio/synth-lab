# Feature Specification: Unified DAG & Hypothesis Generation

**Feature Branch**: `037-unified-dag-hypotheses`
**Created**: 2026-02-02
**Status**: Draft
**Input**: User description: "Unify DAG and hypothesis generation into a single LLM step. Add relevance weights and range clamping to hypotheses. Redesign node interaction with drawer-based editing and relevance-driven visual saturation."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Unified DAG + Hypotheses Generation (Priority: P1)

A researcher creates a new simulation and describes their causal model. The system generates the causal DAG **and** all hypothesis distributions in a single step, rather than two separate LLM calls. This cuts the wait time roughly in half and reduces costs by using a faster model.

**Why this priority**: This is the core architectural change. All other stories depend on hypotheses being generated together with the DAG. It also directly addresses the speed concern — the primary motivation for this feature.

**Independent Test**: Create a simulation with a problem description → system generates DAG nodes, edges, AND distribution hypotheses (with relevance and range) in one response → all variables have distributions assigned → user sees the DAG immediately with hypothesis data attached.

**Acceptance Scenarios**:

1. **Given** a simulation with a described problem, **When** the user triggers DAG generation, **Then** the system produces nodes, edges, assumptions, risks, AND distribution hypotheses (type, parameters, relevance, range) in a single generation step.
2. **Given** a simulation, **When** DAG+hypotheses are generated, **Then** the total generation time is at most 60% of the previous two-step approach (DAG generation + hypothesis parametrization).
3. **Given** a generated DAG+hypotheses result, **When** the user views the DAG, **Then** every variable node already has a distribution type, parameters, relevance level, and value range assigned.
4. **Given** the generation step fails or returns incomplete data, **When** the system detects missing hypotheses for some variables, **Then** it falls back to reasonable defaults (uniform distribution, medium relevance, no range clamp) and logs a warning.

---

### User Story 2 - Relevance-Driven Node Visualization (Priority: P2)

After generation, the DAG displays nodes with visual weight reflecting their relevance. High-relevance variables appear at full color saturation (current behavior). Medium-relevance variables appear slightly desaturated. Low-relevance variables appear noticeably desaturated. This lets researchers quickly identify which variables matter most just by looking at the graph.

**Why this priority**: Visual differentiation is the most impactful UX improvement — it gives immediate at-a-glance understanding of variable importance without clicking anything.

**Independent Test**: Generate a DAG where some variables have high, medium, and low relevance → visually confirm that node colors differ in saturation based on relevance level.

**Acceptance Scenarios**:

1. **Given** a DAG with variables of different relevance levels, **When** the user views the graph, **Then** high-relevance nodes display at full color saturation (identical to current nodes), medium-relevance nodes at ~70% saturation, and low-relevance nodes at ~40% saturation.
2. **Given** a user changes a variable's relevance from low to high (via the node editor), **When** the change is saved, **Then** the node's visual saturation updates immediately without page reload.
3. **Given** a DAG with all high-relevance variables, **When** the user views the graph, **Then** all nodes appear at full saturation (backward compatible with current display).

---

### User Story 3 - Drawer-Based Node Editing (Priority: P3)

When a user clicks on a DAG node, a side drawer opens from the right showing the variable's details and editable properties. The drawer displays the variable description (read-only), allows changing the relevance level (low/medium/high), and allows editing the value range (min, max) used for clamping distribution samples. The distribution type and parameters are NOT shown to the user (they are internal implementation details). The drawer replaces the current tooltip-based information display.

**Why this priority**: The drawer provides a much better editing UX than tooltips (which are read-only and ephemeral). However, the system works without it — users could still view the DAG and run simulations. This enhances the edit experience.

**Independent Test**: Click on any DAG node → drawer opens showing variable name, description, relevance selector, and range inputs → edit relevance and range → save → drawer closes → node visual updates.

**Acceptance Scenarios**:

1. **Given** a DAG is displayed, **When** the user clicks on a node, **Then** a drawer slides in from the right side showing the variable's name, description, current relevance level, and current range (min/max).
2. **Given** the drawer is open for a variable, **When** the user changes the relevance from "medium" to "high", **Then** the change persists and the node's visual saturation updates immediately.
3. **Given** the drawer is open for a variable, **When** the user sets a range of min=10 and max=100, **Then** the range is saved and used for clamping distribution samples during simulation.
4. **Given** the drawer is open, **When** the user clicks outside the drawer or presses the close button, **Then** the drawer closes gracefully.
5. **Given** the drawer is open for one node, **When** the user clicks a different node, **Then** the drawer updates to show the newly clicked node's details (no need to close and reopen).
6. **Given** a variable has no range set (null min/max), **When** the drawer opens, **Then** the range fields are empty and clamping is disabled for that variable (distribution samples are used as-is).

---

### Edge Cases

- What happens when the unified LLM response is missing hypothesis data for some variables? → System assigns defaults (uniform distribution, medium relevance, no range clamp).
- What happens when the user sets min > max in the range fields? → System shows validation error and does not save.
- What happens when the user sets a range that excludes most distribution samples? → System warns that the range is very narrow relative to the distribution but allows it.
- How does the drawer behave on small screens? → Drawer takes full width on screens narrower than 768px.
- What happens when the DAG has no nodes (empty)? → No nodes to click, drawer cannot open. Standard empty state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate the causal DAG (nodes, edges, assumptions, risks) AND distribution hypotheses (distribution type, parameters, relevance, range) in a single generation step.
- **FR-002**: The unified generation MUST use a faster model to compensate for the larger prompt, resulting in total generation time no greater than the current DAG-only generation time.
- **FR-003**: Each hypothesis MUST include a relevance level with three possible values: low, medium, or high.
- **FR-004**: Each hypothesis MUST include an optional value range (min, max) used for clamping sampled values during simulation. Both min and max are optional — if omitted, no clamping is applied.
- **FR-005**: The DAG visualization MUST render nodes with color saturation proportional to their relevance level: high = 100% saturation (current), medium = ~70%, low = ~40%.
- **FR-006**: Clicking a DAG node MUST open a right-side drawer displaying: variable name (read-only), variable description (read-only), relevance selector (low/medium/high), and range editor (min/max numeric inputs).
- **FR-007**: The drawer MUST NOT display distribution type or distribution parameters to the user. These are internal.
- **FR-008**: Changes made in the drawer (relevance, range) MUST persist when the drawer is closed.
- **FR-009**: When the user changes a node's relevance in the drawer, the node's visual saturation MUST update immediately.
- **FR-010**: The range fields MUST validate that min ≤ max when both are provided. Invalid ranges MUST be rejected with an inline error message.
- **FR-011**: The system MUST apply range clamping during simulation: any sampled value below min is set to min, any value above max is set to max.
- **FR-012**: The current tooltip-based node info display MUST be replaced by the drawer interaction. Hover tooltips are removed.
- **FR-013**: Clicking a different node while the drawer is open MUST update the drawer contents to the newly selected node.
- **FR-014**: The drawer MUST be closable via a close button or by clicking outside.

### Key Entities

- **Hypothesis** (modified): Existing entity gains two new attributes:
  - **relevance**: Categorical value (low, medium, high) indicating the variable's importance to the simulation outcome. Default: medium.
  - **range**: Optional value bounds (min, max) for clamping distribution samples. Both are optional floats. Default: no clamp (null).
- **CausalDAG** (unchanged): Existing entity. Nodes and edges remain the same structure.
- **Variable** (unchanged): Existing DAG node entity. No structural changes — relevance and range live on the Hypothesis, not on the variable itself.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Combined DAG + hypothesis generation completes within 15 seconds for a typical simulation (8-15 variables), compared to 20-30 seconds for the current two-step approach.
- **SC-002**: 100% of generated variables have a distribution type, parameters, and relevance level assigned after generation (no variables left unparametrized).
- **SC-003**: Users can identify high-relevance variables within 3 seconds of viewing the DAG, by visual differentiation alone (no clicking required).
- **SC-004**: Users can edit a variable's relevance and range in under 10 seconds using the drawer interface.
- **SC-005**: The drawer opens within 200ms of clicking a node (perceived as instant).
- **SC-006**: Range clamping correctly constrains 100% of out-of-bounds samples during simulation execution.

## Assumptions

- The faster model is capable of producing valid DAG structures AND reasonable distribution parameters in a single structured output call. If quality degrades significantly, we may need to revisit this assumption.
- The existing hypothesis database schema can accommodate the new `relevance` and `range` fields with a simple migration (adding columns).
- The existing simulation engine already samples from distributions; clamping is applied as a post-sampling step.
- Users are comfortable with a drawer interaction pattern (standard in modern web apps).
- The current wizard flow (scenario profiles, clarification questions) from feature 036 will coexist with this change — the wizard applies profile adjustments AFTER the unified generation, and the drawer provides per-variable fine-tuning.

## Scope

### In Scope

- Unified single-step DAG + hypothesis generation
- Switch to faster model for both DAG and hypothesis generation
- Relevance attribute (low/medium/high) on hypotheses
- Range attribute (optional min/max) on hypotheses for clamping
- Relevance-driven node saturation in DAG visualization
- Right-side drawer for node detail viewing and editing (relevance + range)
- Removal of tooltip-based node info display
- Database migration for new hypothesis fields
- Backend range clamping during simulation sampling

### Out of Scope

- Changing the DAG structure itself (nodes, edges, types, scopes)
- Modifying the hypothesis wizard flow from feature 036 (scenario profiles, clarification questions)
- Changing the simulation engine's core sampling logic beyond clamping
- User-facing distribution editing (distributions remain internal)
- Batch editing of multiple nodes' relevance/range at once
- Undo/redo for drawer edits

## Dependencies

- Feature 035 (Causal Simulation) must be deployed — provides the DAG and hypothesis infrastructure
- Feature 036 (Hypothesis Wizard) should be merged first — provides wizard flow that this feature extends
