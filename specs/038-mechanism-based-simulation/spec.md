# Feature Specification: Mechanism-Based Simulation

**Feature Branch**: `038-mechanism-based-simulation`
**Created**: 2026-02-04
**Status**: Draft
**Input**: User description: "Mechanism-based Monte Carlo simulation - replace scorecard-only approach with feature identity (types + mechanisms) interacting with user sensitivities to produce emergent states"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Define Feature Mechanisms (Priority: P1)

As a Product Manager, I want to define the structural mechanisms of my feature (irreversibility, network effects, institutional trust required, etc.) so that the simulation considers the true nature of the feature, not just abstract scores.

**Why this priority**: This is the foundational input that enables all other differentiation. Without mechanism definition, the system cannot distinguish between features of different natures.

**Independent Test**: Can be fully tested by creating a feature with mechanisms and verifying they are stored and retrievable. Delivers value by capturing feature identity that was previously lost.

**Acceptance Scenarios**:

1. **Given** I am creating a new experiment scorecard, **When** I define mechanism intensities (irreversibility=0.9, network_effect=0.7, institutional_trust=0.8), **Then** these mechanisms are persisted alongside the scorecard and available for simulation.

2. **Given** I have an existing experiment, **When** I view the feature definition, **Then** I see both the scorecard scores AND the mechanism intensities clearly separated.

3. **Given** I define mechanisms for a feature, **When** I leave some mechanisms undefined, **Then** they default to 0.0 (mechanism not present) without error.

---

### User Story 2 - Simulate with User Sensitivities (Priority: P1)

As a Product Manager, I want synths to have sensitivities that interact with feature mechanisms so that different user segments respond differently to the same feature based on their psychological profile.

**Why this priority**: The interaction between mechanisms and sensitivities is the core differentiator - it produces the emergent behavior that makes simulations meaningful.

**Independent Test**: Can be tested by running simulation with two synth groups having different sensitivities against the same feature, verifying different outcome distributions.

**Acceptance Scenarios**:

1. **Given** a feature with high irreversibility (0.9) and two synth groups - one with high risk aversion (0.8) and one with low risk aversion (0.2), **When** I run simulation, **Then** the high-aversion group shows significantly lower adoption rates than the low-aversion group.

2. **Given** a feature with high network effect (0.8) and synths with varying social dependency, **When** I run simulation, **Then** early adopters (low social dependency) attempt the feature more readily while followers wait.

3. **Given** the same scorecard scores but different mechanisms (financial vs visual feature), **When** I run simulation with the same synth population, **Then** the outcomes differ by at least 15% in adoption rates.

---

### User Story 3 - View Emergent States Explanation (Priority: P2)

As a Product Manager, I want to understand WHY different segments behave differently so that I can make informed product decisions and explain results to stakeholders.

**Why this priority**: Understanding causality is valuable but depends on the simulation producing meaningful differences first (P1 stories).

**Independent Test**: Can be tested by running a simulation and verifying that explanation of segment differences references specific mechanism x sensitivity interactions.

**Acceptance Scenarios**:

1. **Given** I have run a simulation, **When** I view results for a segment with low adoption, **Then** I see which mechanism x sensitivity interactions drove that outcome (e.g., "High perceived risk emerged from: irreversibility(0.9) x risk_aversion(0.73) = 0.66").

2. **Given** two segments with different outcomes, **When** I compare them, **Then** I see the top 3 differentiating factors expressed as mechanism x sensitivity products.

---

### User Story 4 - Compare Features in Same World (Priority: P2)

As a Product Manager, I want to compare two different features simulated against the same "world" (same synth population with resolved uncertainties) so that I can make fair A/B comparisons.

**Why this priority**: Fair comparison requires controlling for user variation. This enables strategic feature prioritization.

**Independent Test**: Can be tested by running two features in same-world mode and verifying identical user states were used for both simulations.

**Acceptance Scenarios**:

1. **Given** two features (Pix via WhatsApp and New Homepage) with same scorecard scores but different mechanisms, **When** I run comparison in same-world mode, **Then** both features are evaluated against identical sampled user states.

2. **Given** same-world comparison results, **When** I view the comparison, **Then** I see clearly that Feature A outperforms Feature B because of specific mechanism differences, not random variation.

---

### User Story 5 - Backward Compatibility (Priority: P1)

As a user with existing experiments, I want my current experiments to continue working without modification so that I don't lose historical data or need to re-configure existing work.

**Why this priority**: Breaking existing experiments would destroy trust and adoption of the system.

**Independent Test**: Can be tested by loading existing experiments (without mechanisms defined) and running simulation, verifying results are consistent with legacy behavior.

**Acceptance Scenarios**:

1. **Given** an existing experiment created before this feature, **When** I run simulation, **Then** it uses scorecard-only logic (mechanisms default to 0, sensitivities have no effect).

2. **Given** an existing experiment, **When** I view its configuration, **Then** I am NOT required to add mechanisms - the feature is opt-in for new or updated experiments.

---

### Edge Cases

- What happens when all mechanisms are set to 0.0? System falls back to scorecard-only behavior (backward compatible).
- What happens when a synth has no sensitivity values defined? Use neutral defaults (0.5) that minimize mechanism interaction effects.
- What happens when mechanisms sum to values that produce extreme probability states? Emergent states are clamped to valid ranges [0, 1] before probability calculations.
- How does the system handle mechanism values outside [0, 1] range? Validation rejects values outside valid range.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support definition of feature mechanisms with configurable intensity values in [0, 1] range.
- **FR-002**: System MUST support at least 6 core mechanisms: irreversibility, network_effect, institutional_trust, habit_displacement, learning_curve, social_visibility.
- **FR-003**: System MUST support user sensitivity traits that pair with mechanisms: risk_aversion, social_dependency, institutional_trust_level, habit_plasticity, learning_tolerance, social_influence.
- **FR-004**: System MUST calculate emergent states from mechanism x sensitivity interactions before probability calculation.
- **FR-005**: System MUST derive contextual scorecard values from emergent states (rather than using raw scorecard inputs directly when mechanisms are defined).
- **FR-006**: System MUST maintain backward compatibility - experiments without mechanisms defined must produce identical results to current system.
- **FR-007**: System MUST allow defining feature types (categories) as optional metadata (e.g., financial, social, utility).
- **FR-008**: System MUST support same-world comparison mode where multiple features are evaluated against identical sampled user states.
- **FR-009**: System MUST generate explanation data showing which mechanism x sensitivity products most influenced outcomes.
- **FR-010**: System MUST validate that mechanism and sensitivity values are within [0, 1] range.

### Key Entities

- **FeatureMechanisms**: Represents the structural mechanisms of a feature. Contains intensity values for each mechanism type. Associated with FeatureScorecard.
- **UserSensitivities**: Extension to synth simulation_attributes containing sensitivity values. Paired with latent_traits structure.
- **EmergentState**: Intermediate calculation result showing mechanism x sensitivity products. Used to derive contextual scorecard values.
- **World**: A specific instantiation where all uncertainties are resolved (all user sensitivity values sampled, all mechanism values fixed). Enables fair feature comparison.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Two features with identical scorecard scores but different mechanisms produce outcome variance of at least 15% when simulated against the same population.
- **SC-002**: Segment differences can be attributed to specific mechanism x sensitivity interactions in 100% of cases where mechanisms are defined.
- **SC-003**: Existing experiments without mechanisms produce results identical to pre-feature baseline (zero regression).
- **SC-004**: Same-world comparison mode produces reproducible, fair comparisons (identical seed produces identical results).
- **SC-005**: PMs can identify the top 3 factors driving adoption differences between segments in under 30 seconds of viewing results.
- **SC-006**: System supports all 6 core mechanisms and 6 paired sensitivities at launch.

## Assumptions

- Mechanism intensity values are manually input by the PM (not auto-derived from feature description).
- Sensitivity values for synths will be added as an extension to the existing simulation_attributes structure.
- The 6 mechanism-sensitivity pairs are sufficient for initial release; additional pairs may be added in future iterations.
- The interaction model (simple multiplication) is sufficient to produce meaningful differentiation; more complex interaction models are out of scope.
- Performance target remains 100 synths x 100 executions in < 1 second even with mechanism-based calculations.
