# Feature Specification: Mechanism & Sensitivity Update

**Feature Branch**: `040-mechanism-sensitivity-update`
**Created**: 2026-02-06
**Status**: Draft
**Input**: User description: "Add 7 user sensitivities derived from synth data via YAML rules, add 3 new feature mechanisms, create emergent state calculator for mechanism x sensitivity interactions, and integrate into Monte Carlo simulation engine"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Synths Are Created With Derived Sensitivities (Priority: P1)

When a synth is generated, the system derives 7 personality-based sensitivities (risk_aversion, social_dependency, institutional_trust_level, habit_plasticity, friction_tolerance, pragmatism, digital_capability) from the synth's demographic data using configurable YAML rules. These sensitivities are persisted alongside the synth data.

**Why this priority**: Sensitivities are the foundation for all subsequent features. Without them, emergent states and improved Monte Carlo cannot function.

**Independent Test**: Generate a synth and verify it contains all 7 sensitivities with values between 0 and 1, derived from its demographics (age, education, family composition, disabilities).

**Acceptance Scenarios**:

1. **Given** a synth generation request with demographic data for a 25-year-old tech professional, **When** the synth is built, **Then** the synth data includes a `sensitivities` object with all 7 fields, each between 0.0 and 1.0, and the young person has lower risk_aversion and higher digital_capability than defaults.
2. **Given** a synth generation request for a 65-year-old with low education and physical disabilities, **When** the synth is built, **Then** risk_aversion is higher than default, habit_plasticity is lower, and digital_capability is lower.
3. **Given** a synth generation request with missing optional fields (e.g., no disability data), **When** the synth is built, **Then** sensitivities default gracefully without errors and all 7 values are present.
4. **Given** any generated synth, **When** inspecting the persisted data, **Then** sensitivities include metadata with derivation version, config name, and list of applied rules.

---

### User Story 2 - Three New Feature Mechanisms Are Available (Priority: P2)

The system supports 3 new feature mechanisms (valor_intrinseco, friccao_operacional, frequencia_de_uso) in addition to the existing 6, bringing the total to 9. These new mechanisms are available for selection when configuring an experiment's feature analysis.

**Why this priority**: The new mechanisms enrich the feature model and are needed for emergent state calculations, but the system already functions with the existing 6.

**Independent Test**: Seed the database with the 3 new mechanisms and verify they appear in the mechanism list with correct options.

**Acceptance Scenarios**:

1. **Given** the database has been seeded, **When** listing all mechanisms, **Then** 9 mechanisms are returned including valor_intrinseco, friccao_operacional, and frequencia_de_uso.
2. **Given** the new mechanisms exist, **When** viewing valor_intrinseco options, **Then** 5 options are available ranging from "cosmetico" (0.0) to "transformador" (1.0).
3. **Given** the new mechanisms exist, **When** viewing friccao_operacional options, **Then** 5 options range from "sem friccao" (0.0) to "friccao extrema" (1.0).
4. **Given** the new mechanisms exist, **When** viewing frequencia_de_uso options, **Then** 5 options range from "rarissimo" (0.0) to "diario ou mais" (1.0).
5. **Given** an experiment configured with old mechanisms only (6), **When** running the experiment, **Then** the 3 new mechanisms default to 0.0 and do not break existing behavior.

---

### User Story 3 - Emergent States Drive Monte Carlo Probability (Priority: P3)

When running a Monte Carlo simulation, the system calculates emergent states from the interaction of 9 feature mechanisms with 7 user sensitivities. These emergent states (7 barriers + 2 appeals) adjust the adoption probability for each synth, producing more nuanced and differentiated simulation outcomes.

**Why this priority**: This is the ultimate goal -- richer simulations. But it depends on sensitivities (P1) and mechanisms (P2) being in place first.

**Independent Test**: Run a simulation for the same feature with two different synth populations (young/tech-savvy vs elderly/risk-averse) and verify that outcomes differ meaningfully based on sensitivity-mechanism interactions.

**Acceptance Scenarios**:

1. **Given** a feature with high irreversibility (0.8) and a synth with high risk_aversion (0.9), **When** running a simulation, **Then** the perceived_risk emergent state is high (~0.72) and adoption probability is reduced compared to a synth with low risk_aversion.
2. **Given** a feature with high valor_intrinseco (0.9) and a synth with high pragmatism (0.8), **When** running a simulation, **Then** intrinsic_appeal is high (~0.72) and adoption probability is boosted.
3. **Given** a feature with high friccao_operacional (0.7) and a synth with low friction_tolerance (0.2), **When** running a simulation, **Then** friction_burden is high (~0.56) and acts as an adoption barrier.
4. **Given** the same feature scorecard, **When** running simulations for a young tech-savvy population vs an elderly population, **Then** aggregate adoption rates differ by at least 10 percentage points.
5. **Given** a synth with pre-persisted sensitivities, **When** running a simulation, **Then** the system uses the stored sensitivities rather than re-deriving them.
6. **Given** a synth without persisted sensitivities (legacy data), **When** running a simulation, **Then** sensitivities are derived on-demand and the simulation proceeds normally.

---

### Edge Cases

- What happens when a synth has no demographic data at all? Sensitivities should default to 0.5 (neutral) for all 7 dimensions.
- What happens when the YAML rules file is malformed or missing? The system should raise a clear error at startup, not silently fail during generation.
- What happens when all 9 mechanisms are set to 0.0? Emergent states should all be 0.0 and probability should equal the base probability (no adjustment).
- What happens when barrier adjustments reduce probability below 0.0? Probability should be clamped to 0.0.
- What happens when appeal boosts increase probability above 1.0? Probability should be clamped to 1.0.
- What happens when the YAML config version changes? Metadata should reflect which version was used for each synth's sensitivity derivation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST derive 7 user sensitivities (risk_aversion, social_dependency, institutional_trust_level, habit_plasticity, friction_tolerance, pragmatism, digital_capability) from raw synth demographic data.
- **FR-002**: Sensitivity derivation rules MUST be defined in a YAML configuration file, supporting numeric operators (>=, <=, >, <, ==) and string operators (contains, contains_any, in).
- **FR-003**: Each sensitivity MUST have a base value and adjustment rules that produce a final value clamped between 0.0 and 1.0.
- **FR-004**: Derived sensitivities MUST be persisted in the synth data alongside demographics.
- **FR-005**: Each sensitivity derivation MUST include metadata: derivation version, config name, and list of applied rules.
- **FR-006**: System MUST support 9 feature mechanisms total: the existing 6 (irreversibility, network_effect, institutional_trust, habit_displacement, learning_curve, social_visibility) plus 3 new (valor_intrinseco, friccao_operacional, frequencia_de_uso).
- **FR-007**: Each new mechanism MUST have 5 configurable options with values ranging from 0.0 to 1.0.
- **FR-008**: Existing experiments using only 6 mechanisms MUST continue to work without modification (new mechanisms default to 0.0).
- **FR-009**: System MUST calculate 9 emergent states from the interaction of mechanisms and sensitivities: 7 barriers (perceived_risk, trust_barrier, habit_resistance, learning_frustration, friction_burden, social_pressure, network_barrier) and 2 appeals (intrinsic_appeal, frequency_value).
- **FR-010**: Emergent state formulas MUST follow these specific mappings:
  - **Resistance barriers** (mechanism x (1 - sensitivity)): trust_barrier (institutional_trust x (1 - institutional_trust_level)), habit_resistance (habit_displacement x (1 - habit_plasticity)), learning_frustration (learning_curve x (1 - digital_capability)), friction_burden (friccao_operacional x (1 - friction_tolerance)), network_barrier (network_effect x (1 - social_dependency))
  - **Affinity barriers** (mechanism x sensitivity): perceived_risk (irreversibility x risk_aversion), social_pressure (social_visibility x social_dependency)
  - **Appeals** (mechanism x sensitivity): intrinsic_appeal (valor_intrinseco x pragmatism), frequency_value (frequencia_de_uso x pragmatism)
- **FR-011**: Monte Carlo simulation MUST use emergent states to adjust base adoption probability with the formula: `prob = 0.5 − sum(7 barriers) × 0.15 + sum(2 appeals) × 0.20`, clamped to [0.0, 1.0], then sampled via Bernoulli(prob) for binary outcome (adopted/not_adopted). Weights 0.15 and 0.20 are initial calibration values.
- **FR-012**: Adjusted probability MUST be clamped between 0.0 and 1.0.
- **FR-013**: Simulation MUST support synths with pre-persisted sensitivities (use stored) and synths without them (derive on-demand).

### Key Entities

- **UserSensitivities**: 7 float fields (0.0-1.0) representing a synth's personality-based sensitivity profile. Derived from demographics, persisted with synth data.
- **FeatureMechanisms** (updated): 9 float fields (0.0-1.0) representing feature characteristics. 6 existing + 3 new (valor_intrinseco, friccao_operacional, frequencia_de_uso).
- **EmergentState**: 9 calculated values (7 barriers + 2 appeals) from mechanism x sensitivity interaction, plus metadata about top contributors.
- **SensitivityRules** (YAML config): Versioned rule definitions with base values and conditional adjustments for each of the 7 sensitivities.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All newly generated synths include 7 sensitivities derived from their demographic data, with derivation metadata.
- **SC-002**: Sensitivity values vary meaningfully across synth demographics -- a young tech professional and an elderly person with disabilities produce sensitivity profiles that differ by at least 0.15 on average across the 7 dimensions.
- **SC-003**: 9 mechanisms are available for experiment configuration, with backward compatibility for experiments using only the original 6.
- **SC-004**: Monte Carlo simulations with the same feature but different synth populations (varying demographics) produce adoption rates that differ by at least 10 percentage points.
- **SC-005**: A feature with high barriers and low appeal produces at least 20% lower adoption than the same feature with low barriers and high appeal, for the same synth population.
- **SC-006**: All validation blocks and automated tests pass (unit tests for deriver, integration tests for synth generation and emergent state calculation).
- **SC-007**: Existing simulations using only 6 mechanisms produce equivalent results to before the change (new mechanisms at 0.0 have zero impact).

## Assumptions

- The Brazilian population demographic model is the primary context. YAML rules are calibrated for this population.
- Sensitivity derivation is deterministic -- same synth data always produces the same sensitivities.
- The barrier_penalty weight (0.15) and appeal_boost weight (0.20) are initial calibration values that may need tuning with real usage data. This calibration is out of scope.
- Minimal UI changes: `MechanismEditor.tsx` (hardcoded slider configs) and `FeatureMechanisms` TypeScript interface need 3 new mechanism entries. The narrative mechanism system (`NarrativeMechanismEditor`, hooks, services, API) is fully dynamic and requires NO changes — it loads mechanisms from the database. `UserSensitivities` TypeScript interface is NOT updated (sensitivities are only consumed by backend simulation).
- No database schema migration is needed -- sensitivities are stored in existing JSONB fields within synth data.
- Simulation outcomes change from 3 states (did_not_try, failed, success) to 2 states (adopted, not_adopted), aligned with the barrier/appeal probability model.

## Dependencies

- Existing mechanism seeding infrastructure (seed scripts)
- Existing synth generation pipeline (synth_builder)
- Existing Monte Carlo simulation engine (simulation_engine, probability_calculator)
- Existing JSONB storage for synth data
