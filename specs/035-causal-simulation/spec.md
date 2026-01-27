# Feature Specification: Causal Simulation System for Decision Making

**Feature Branch**: `035-causal-simulation`
**Created**: 2026-01-26
**Status**: Draft
**Input**: Sistema completo de simulação causal para tomada de decisão: pergunta → DAG → hipóteses → simulação → evidência → insights acionáveis

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask Business Question and Get Adoption Forecast (Priority: P1)

A product manager wants to understand the expected adoption rate for a new subscription feature. They type a natural language question: "What will be the adoption rate for a weekly meal subscription?" The system automatically identifies the intervention, outcome, time horizon, and generates a complete analysis with probability distributions, key drivers, and failure modes.

**Why this priority**: This is the core value proposition - transforming ambiguous business questions into actionable insights. Without this, the entire system provides no value.

**Independent Test**: Can be fully tested by submitting a business question and receiving a structured forecast with percentile ranges (p5, p50, p95), sensitivity analysis, and recommendations. Delivers immediate value as a decision support tool.

**Acceptance Scenarios**:

1. **Given** a product manager has a new feature idea, **When** they type "What adoption rate should I expect for feature X?", **Then** the system extracts intervention, primary outcome, secondary outcomes, decision type, time horizon, and unit of analysis
2. **Given** a parsed business question, **When** the system generates a causal model, **Then** the model includes observable variables, latent variables, friction variables, failure variables, temporal variables, declared assumptions, and risks
3. **Given** a causal DAG, **When** the system parametrizes hypotheses, **Then** each variable has a distribution type, range, scope (world/user), temporality, and suggested correlations
4. **Given** parametrized hypotheses, **When** simulation runs, **Then** 500 unique worlds are created with varied parameters while maintaining causal consistency
5. **Given** completed simulation, **When** results are aggregated, **Then** output includes percentile distribution (p5, p50, p95), variance explanation by variable, detected failure modes, and distinct behavioral clusters
6. **Given** simulation evidence, **When** insights are generated, **Then** each insight references specific variables, assumptions, statistical results, includes risk/counterfactual analysis, and suggests practical next steps
7. **Given** any generated insight, **When** user asks "why?", **Then** system traces insight back to specific correlations, variables, hypotheses, and affected simulation worlds

---

### User Story 2 - Edit and Refine Causal Model (Priority: P2)

After seeing the initial causal model, a domain expert realizes a critical variable is missing (e.g., "regulatory approval delay" for a healthcare product). They add this variable to the DAG, specify its relationships to existing variables, and re-run the simulation to see how it changes the forecast.

**Why this priority**: Auto-generated models will never be perfect. Human domain expertise must be able to correct and enhance the model. This enables trust and accuracy.

**Independent Test**: Can be tested by loading an existing DAG, adding/removing nodes or edges, modifying variable properties, and observing how the updated simulation produces different results. Delivers value by allowing experts to inject domain knowledge.

**Acceptance Scenarios**:

1. **Given** a generated causal DAG, **When** user views it, **Then** all nodes (variables) and edges (causal relationships) are visually displayed with labels and classifications (observable/latent/friction/etc.)
2. **Given** a displayed DAG, **When** user adds a new variable node, **Then** system prompts for variable name, type, scope, and relationships to existing nodes
3. **Given** an edited DAG, **When** user saves changes, **Then** system validates DAG for cycles, orphaned nodes, and logical inconsistencies
4. **Given** a modified DAG, **When** user clicks "Re-simulate", **Then** system re-parametrizes only affected variables and re-runs simulation with the new structure
5. **Given** two DAG versions (before/after edit), **When** user requests comparison, **Then** system shows diff of added/removed nodes, changed edges, and how results changed

---

### User Story 3 - Adjust Hypothesis Parameters (Priority: P2)

A finance analyst reviewing the simulation notices that the "customer churn rate" range seems too optimistic (2-5%) based on their industry data. They adjust the range to 8-15% and see how this changes the overall forecast and which other variables become more critical.

**Why this priority**: Default parametrization will be wrong for specific contexts. Users must be able to inject real-world data constraints to get accurate forecasts.

**Independent Test**: Can be tested by opening hypothesis parameters, changing ranges/distributions/correlations for specific variables, and observing updated simulation results. Delivers value by grounding generic models in specific business contexts.

**Acceptance Scenarios**:

1. **Given** generated hypotheses, **When** user views hypothesis list, **Then** each variable shows its distribution type, range, scope, temporality, controllability, and suggested correlations
2. **Given** a specific variable hypothesis, **When** user edits range bounds, **Then** system validates that new bounds are logically consistent with variable type
3. **Given** a correlation hypothesis, **When** user adjusts correlation strength, **Then** system warns if correlation conflicts with DAG structure
4. **Given** modified hypotheses, **When** user clicks "Apply & Re-simulate", **Then** system preserves DAG structure and updates only affected parameter distributions
5. **Given** multiple hypothesis versions, **When** user requests diff view, **Then** system shows which parameters changed, by how much, and impact on variance explanation

---

### User Story 4 - Explore Failure Modes and Clusters (Priority: P3)

A risk manager wants to understand not just the median outcome, but what specific failure scenarios exist. They drill into the simulation results to see that "if delivery failure ≥ 2 in first month, then 90% churn" and discover that high-routine users behave completely differently from ad-hoc users.

**Why this priority**: Median outcomes hide critical risks. Understanding failure modes and behavioral clusters enables targeted mitigation strategies and segmentation.

**Independent Test**: Can be tested by running simulation, accessing cluster analysis, viewing failure mode detection, and filtering worlds by specific conditions. Delivers value by revealing hidden risks and opportunities.

**Acceptance Scenarios**:

1. **Given** completed simulation, **When** user views failure modes, **Then** system lists detected patterns where outcomes cross critical thresholds (e.g., "adoption < 5% in 90% of worlds when X happens")
2. **Given** identified clusters, **When** user views cluster details, **Then** each cluster shows defining variable ranges, percentage of worlds, and outcome distributions specific to that cluster
3. **Given** a specific failure mode, **When** user clicks to investigate, **Then** system shows which variables most strongly predict this failure and which worlds experienced it
4. **Given** multiple behavioral clusters, **When** user compares them, **Then** system highlights key differentiating variables and outcome differences
5. **Given** a specific world simulation, **When** user drills into it, **Then** system shows all parameter values, temporal progression (if applicable), and final outcomes for that world

---

### User Story 5 - Version and Compare Hypotheses (Priority: P3)

A strategy team runs multiple simulation scenarios over 2 weeks: optimistic case (low friction, high adoption), pessimistic case (high friction, logistics failures), and realistic case (mixed parameters). They version each hypothesis set and compare results to understand decision sensitivity.

**Why this priority**: Business decisions require scenario planning. Versioning enables "what-if" analysis and documents decision rationale for future reference.

**Independent Test**: Can be tested by creating multiple named hypothesis versions, running simulations for each, and viewing side-by-side comparisons of results. Delivers value by enabling scenario planning and decision documentation.

**Acceptance Scenarios**:

1. **Given** current hypothesis set, **When** user clicks "Save as Version", **Then** system prompts for version name/description and stores complete snapshot of all parameters and DAG structure
2. **Given** multiple saved versions, **When** user views version history, **Then** each version shows creation date, description, and summary of key parameter differences
3. **Given** two selected versions, **When** user clicks "Compare", **Then** system shows parameter diffs and outcome differences (percentile distributions, variance explanations, failure modes)
4. **Given** a previous version, **When** user clicks "Load", **Then** system restores that complete hypothesis set and DAG structure as the current working state
5. **Given** any saved version, **When** user requests audit trail, **Then** system shows what inputs, assumptions, and simulation parameters produced those results

---

### User Story 6 - Replay and Audit Simulations (Priority: P3)

A compliance officer needs to understand why a specific recommendation was made 3 months ago. They load the historical simulation, replay it, and trace each insight back to the exact variables, correlations, and assumptions that produced it.

**Why this priority**: For regulated industries or high-stakes decisions, full auditability is required. This enables accountability and learning from past decisions.

**Independent Test**: Can be tested by loading a historical simulation record, replaying it, and verifying that all inputs, parameters, randomness, and outputs are exactly reproduced. Delivers value by enabling compliance and decision review.

**Acceptance Scenarios**:

1. **Given** any completed simulation, **When** user views audit log, **Then** system shows original question, timestamp, DAG version, hypothesis version, random seed, and all generated insights
2. **Given** a historical simulation record, **When** user clicks "Replay", **Then** system reproduces exact same results using stored parameters and random seed
3. **Given** a specific historical insight, **When** user asks "why was this generated?", **Then** system shows traced path: insight → statistical result → variables → hypotheses → DAG assumptions → original question
4. **Given** multiple simulation runs for same question, **When** user compares them, **Then** system shows what parameters changed between runs and how results differ
5. **Given** simulation audit trail, **When** exported, **Then** output includes complete reproducibility package: question, DAG, hypotheses, random seed, results, and insights

---

### Edge Cases

- What happens when user provides an ambiguous question that could map to multiple interventions?
- How does system handle circular causal relationships in user-edited DAG?
- What if user sets impossible parameter constraints (e.g., probability range 0.8-1.2)?
- How does system behave if simulation produces no meaningful variance (all worlds converge to same outcome)?
- What if temporal simulation never converges or takes too long?
- How does system handle missing data when user asks to use "real data" for parametrization?
- What happens when user requests comparison between hypothesis versions that have structurally different DAGs?
- How does system prevent non-traceable insights from being generated?
- What if LLM fails to extract structured problem from natural language question?
- How does system handle conflicting user edits (e.g., specifying both independence and strong correlation between variables)?

## Requirements *(mandatory)*

### Functional Requirements

#### Question Parsing & Problem Decomposition

- **FR-001**: System MUST accept free-form natural language business questions as input
- **FR-002**: System MUST automatically extract from question: intervention, primary outcome, secondary outcomes, unit of analysis, time horizon, and decision type
- **FR-003**: System MUST return structured problem representation in machine-readable format
- **FR-004**: System MUST identify when question is ambiguous and request clarification before proceeding

#### Causal Model Construction

- **FR-005**: System MUST generate directed acyclic graph (DAG) representing causal relationships between variables
- **FR-006**: System MUST classify variables as: observable, latent, friction, failure, process, temporal, world-scoped, or user-scoped
- **FR-007**: System MUST declare explicit assumptions made during DAG construction
- **FR-008**: System MUST identify and document uncertainties and risks in causal model
- **FR-009**: System MUST allow human users to view generated DAG in visual format
- **FR-010**: System MUST allow human users to add/remove/modify nodes and edges in DAG
- **FR-011**: System MUST validate DAG for logical consistency (no cycles, no orphaned nodes, etc.) before allowing simulation
- **FR-012**: System MUST support temporal/process variables where causality unfolds over time

#### Hypothesis Parametrization

- **FR-013**: System MUST transform each DAG variable into quantitative hypothesis with: distribution type, range, scope, temporality, and controllability
- **FR-014**: System MUST suggest plausible correlations between variables based on DAG structure
- **FR-015**: System MUST never return fixed point estimates - only ranges and distributions
- **FR-016**: System MUST allow human users to view all hypothesis parameters
- **FR-017**: System MUST allow human users to adjust any hypothesis parameter: distribution type, ranges, correlations
- **FR-018**: System MUST validate hypothesis parameter changes for logical consistency
- **FR-019**: System MUST version hypothesis sets with user-provided names/descriptions
- **FR-020**: System MUST allow comparison (diff) between hypothesis versions

#### Simulation Engine

- **FR-021**: System MUST generate multiple distinct simulated worlds (minimum 500) with varied hypothesis parameters
- **FR-022**: System MUST create coherent synthetic population within each world
- **FR-023**: System MUST apply declared causal relationships from DAG to simulate outcomes
- **FR-024**: System MUST execute temporal simulations when variables have time-dependent causality
- **FR-025**: System MUST record all assumptions and parameters used in each simulated world
- **FR-026**: System MUST separate world-level assumptions from individual population member attributes
- **FR-027**: System MUST use deterministic randomness (seeded) to enable simulation replay

#### Evidence Calculation & Analysis

- **FR-028**: System MUST aggregate simulation results into outcome distributions
- **FR-029**: System MUST calculate percentile intervals: p5, p50, p95 for all outcomes
- **FR-030**: System MUST perform sensitivity analysis to identify variables explaining highest outcome variance
- **FR-031**: System MUST detect failure modes: patterns where outcomes cross critical thresholds
- **FR-032**: System MUST identify behavioral clusters: groups of worlds with distinct outcome patterns
- **FR-033**: System MUST measure correlation strength between each variable and outcome

#### Insight Generation

- **FR-034**: System MUST generate insights exclusively from simulation evidence (no unsupported claims)
- **FR-035**: System MUST link each insight to: specific variables, assumptions, statistical results, and affected simulation worlds
- **FR-036**: System MUST declare risks and counterfactuals for each insight
- **FR-037**: System MUST suggest practical actions: experiments to run, rollout strategies, exclusion criteria
- **FR-038**: System MUST identify where real-world data would most reduce forecast uncertainty
- **FR-039**: System MUST block generation of any insight that cannot be traced back to evidence
- **FR-040**: System MUST explain in plain language what each insight means and why it matters

#### Auditability & Traceability

- **FR-041**: System MUST record complete audit trail for every simulation: question, timestamp, DAG, hypotheses, random seed, results, insights
- **FR-042**: System MUST enable exact replay of any historical simulation
- **FR-043**: System MUST allow users to ask "why did this insight appear?" and receive traced explanation
- **FR-044**: System MUST support comparison between multiple simulation runs
- **FR-045**: System MUST enable export of complete reproducibility package for any simulation
- **FR-046**: System MUST maintain version history for DAGs and hypothesis sets
- **FR-047**: System MUST link insights across time to show how forecasts evolved as assumptions changed

### Key Entities

- **Business Question**: Natural language input from user, contains implicit intervention, outcomes, constraints, and decision context
- **Problem Decomposition**: Structured representation extracting intervention, primary outcome, secondary outcomes, unit of analysis, time horizon, decision type
- **Causal DAG**: Directed acyclic graph where nodes are variables and edges are causal relationships; includes variable classifications and declared assumptions
- **Variable**: Individual node in DAG with properties: name, type (observable/latent/friction/failure/process/temporal), scope (world/user), distribution, range, controllability
- **Hypothesis**: Quantitative parametrization of a variable including distribution type, range bounds, correlations with other variables, version metadata
- **Hypothesis Version**: Named snapshot of complete hypothesis set with description, timestamp, and diff from previous version
- **Simulated World**: Single execution of simulation with specific parameter draws, contains world-level assumptions and individual population outcomes
- **Synthetic Individual**: Member of population within a simulated world, has user-scoped variable values and computed outcomes
- **Evidence**: Aggregated statistics from all simulated worlds including percentile distributions, variance explanations, failure modes, clusters
- **Failure Mode**: Detected pattern where specific variable conditions reliably predict poor outcomes across multiple worlds
- **Behavioral Cluster**: Group of simulated worlds sharing similar variable patterns and outcome distributions
- **Insight**: Actionable conclusion derived from evidence, linked to specific variables, assumptions, and statistical results, includes risk assessment and recommended actions
- **Audit Trail**: Complete record of simulation including inputs, assumptions, parameters, randomness seed, outputs, and generated insights - enables exact replay

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can transform a natural language business question into a complete forecast in under 5 minutes (including reviewing and accepting initial DAG and hypotheses)
- **SC-002**: System generates causal DAG with 8-20 relevant variables for typical product/business questions
- **SC-003**: Generated DAGs include at least 2 latent variables and at least 1 friction/failure variable for 90% of questions
- **SC-004**: 90% of auto-generated hypothesis parameters are accepted by domain experts without adjustment
- **SC-005**: Simulation completes 500 worlds in under 2 minutes for DAGs with up to 20 variables
- **SC-006**: Variance explanation totals to at least 80% when top 5 variables are combined
- **SC-007**: System detects at least 1 failure mode for 70% of simulations (where outcome variance is significant)
- **SC-008**: System identifies at least 2 behavioral clusters for 60% of simulations (where population is heterogeneous)
- **SC-009**: 100% of generated insights can be traced back to specific variables, assumptions, and statistical evidence
- **SC-010**: Users can replay any historical simulation and reproduce identical results
- **SC-011**: Users can compare hypothesis versions and understand parameter diffs in under 1 minute
- **SC-012**: 85% of insights include actionable recommendations (experiment to run, rollout strategy, etc.)
- **SC-013**: Users can answer "why did you recommend X?" by following audit trail without technical assistance
- **SC-014**: System prevents generation of non-traceable insights (0% false insights pass validation)
- **SC-015**: User satisfaction score ≥ 4.0/5.0 for "confidence in forecast reliability"

### Qualitative Outcomes

- **SC-016**: Product managers report using forecasts to justify feature prioritization decisions
- **SC-017**: Domain experts trust forecasts enough to adjust based on their knowledge rather than dismissing them
- **SC-018**: Compliance/audit teams can validate decision rationale using audit trails
- **SC-019**: Users prefer this system over creating spreadsheet models manually
- **SC-020**: Users understand causal assumptions being made rather than treating system as black box

## Assumptions

- Users have domain expertise to validate causal relationships but lack statistical modeling skills
- Business questions map to interventions with measurable outcomes (not purely exploratory/descriptive questions)
- Most business decisions involve 10-30 meaningful causal variables, not hundreds
- Synthetic simulation provides sufficient insight even without real data (directional accuracy matters more than precision)
- Users value transparency and traceability more than black-box accuracy
- Distribution ranges and correlations can be reasonably estimated from domain knowledge alone
- Failure modes and clusters exist in most business scenarios (outcomes aren't purely random)
- LLMs can decompose natural language questions with 90%+ accuracy given clear product contexts
- Users will iteratively refine models rather than expecting perfect first-pass results
- Temporal simulations will converge within reasonable compute time for typical business processes

## Out of Scope

- Real-time data integration from databases, APIs, or analytics platforms (Phase 1 uses synthetic data only)
- Automatic causal discovery from observational data (Phase 1 requires explicit DAG construction)
- Running real A/B experiments or interventions (system only simulates, does not execute)
- Statistical inference or hypothesis testing against real data (system is purely simulation-based)
- Multi-agent simulations where individuals interact (Phase 1 assumes independent population members)
- Optimization algorithms to find "best" intervention parameters (system explores, does not optimize)
- Integration with decision execution systems (system provides insights, does not take actions)
- Collaborative multi-user DAG editing with conflict resolution (Phase 1 is single-user)
- Machine learning model training or automated parameter estimation from data
- Natural language chatbot interface for conversational refinement (Phase 1 uses structured UI)

## Dependencies

- LLM service (e.g., OpenAI, Anthropic) for question parsing, causal modeling, parametrization, and insight generation
- Probabilistic simulation engine or library capable of sampling from various distributions
- Graph data structure library for DAG representation and validation
- Statistical analysis library for sensitivity analysis, percentile calculation, clustering
- Database or storage system for persisting simulations, hypotheses, audit trails
- Frontend visualization library for rendering DAG graphs interactively
- Random number generation with seeding support for deterministic replay
- JSON schema validation for ensuring structured outputs from LLM calls
