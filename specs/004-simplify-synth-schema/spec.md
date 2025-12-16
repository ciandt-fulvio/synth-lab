# Feature Specification: Simplify Synth Schema

**Feature Branch**: `004-simplify-synth-schema`
**Created**: 2025-12-16
**Status**: Draft
**Input**: User description: "vamos simplificar os dados (JSON schema, inclusive) que definem um synth. retire os dados: psicografia.hobbies, psicografia.valores, psicografia.estilo_vida, comportamento.uso_tecnologia, comportamento.comportamento_compra. E crie regras que deixe mais coerentes entre si alguns atributos: vieses deve ter relacao com personalidade_big_five"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Simplified Schema for Faster Generation (Priority: P1)

As a synth generator user, I need a simplified schema that removes redundant psychographic and behavioral fields so that synth generation is faster and the data model is easier to understand and maintain.

**Why this priority**: Core schema simplification directly impacts generation performance and maintainability. This is the foundation that enables all other use cases.

**Independent Test**: Can be fully tested by generating a synth using the simplified schema and verifying that removed fields are absent while core functionality remains intact.

**Acceptance Scenarios**:

1. **Given** the current synth schema with all psychographic and behavioral fields, **When** I apply the schema simplification, **Then** the following fields are completely removed from the schema:
   - `psicografia.hobbies`
   - `psicografia.valores`
   - `psicografia.estilo_vida`
   - `comportamento.uso_tecnologia`
   - `comportamento.comportamento_compra`

2. **Given** a simplified schema without the removed fields, **When** I generate a new synth, **Then** the generated synth JSON does not contain any of the removed fields

3. **Given** the simplified schema, **When** I validate existing synths against it, **Then** validation fails for synths containing the removed fields

---

### User Story 2 - Coherent Bias-Personality Relationships (Priority: P1)

As a behavioral researcher using synths, I need cognitive biases to be logically aligned with Big Five personality traits so that the synths exhibit psychologically realistic and consistent behavior patterns.

**Why this priority**: Data coherence is critical for the credibility and usefulness of synthetic personas. Without this, the synths will exhibit contradictory behaviors that undermine their value.

**Independent Test**: Can be tested by generating synths with varying Big Five profiles and validating that their bias values follow the defined coherence rules.

**Acceptance Scenarios**:

1. **Given** a synth with high conscienciosidade (conscientiousness), **When** bias values are generated, **Then** `vies_status_quo` is high (70-90) and `desconto_hiperbolico` is low (10-30)

2. **Given** a synth with high neuroticismo (neuroticism), **When** bias values are generated, **Then** `aversao_perda` is high (70-95) and `sobrecarga_informacao` is high (60-85)

3. **Given** a synth with high abertura (openness), **When** bias values are generated, **Then** `vies_confirmacao` is low (10-35) and `sobrecarga_informacao` is low (15-40)

4. **Given** a synth with low amabilidade (agreeableness), **When** bias values are generated, **Then** `vies_confirmacao` is high (65-90)

5. **Given** a synth with high extroversao (extraversion), **When** bias values are generated, **Then** `desconto_hiperbolico` is moderate to high (50-80)

---

### User Story 3 - Validation of Schema Coherence Rules (Priority: P2)

As a quality assurance tester, I need automated validation that enforces the personality-bias coherence rules so that all generated synths maintain psychological consistency without manual verification.

**Why this priority**: Automated validation ensures long-term quality but can be implemented after the core rules are established in P1 stories.

**Independent Test**: Can be tested by attempting to create synths that violate coherence rules and verifying that validation fails with appropriate error messages.

**Acceptance Scenarios**:

1. **Given** a synth with high conscientiousness (80+), **When** I manually set `desconto_hiperbolico` to high (70+), **Then** validation fails with message "Inconsistent personality-bias: high conscientiousness incompatible with high hyperbolic discounting"

2. **Given** a synth with high openness (75+), **When** I manually set `vies_confirmacao` to high (70+), **Then** validation fails with message "Inconsistent personality-bias: high openness incompatible with high confirmation bias"

3. **Given** a synth with low neuroticism (20), **When** I manually set `aversao_perda` to very high (90), **Then** validation fails with message "Inconsistent personality-bias: low neuroticism incompatible with extreme loss aversion"

---

### Edge Cases

- What happens when a synth has moderate values (40-60) across all Big Five traits? (Bias values should also be moderate and have wider acceptable ranges)
- How does the system handle biases when personality traits conflict in their implications? (Use weighted averaging or prioritization hierarchy)
- What happens to existing synth data that contains the removed fields when migrating to the new schema? (Migration script needed to strip removed fields)
- Can users still query for synths by interests even though hobbies are removed? (Interests field remains available for searching)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Schema MUST remove the following fields entirely:
  - `psicografia.hobbies`
  - `psicografia.valores`
  - `psicografia.estilo_vida`
  - `comportamento.uso_tecnologia`
  - `comportamento.comportamento_compra`

- **FR-002**: Schema MUST retain all other existing fields including:
  - `psicografia.personalidade_big_five` (all 5 traits)
  - `psicografia.interesses`
  - `vieses` (all 7 bias types)
  - All demographic and capability fields

- **FR-003**: Schema MUST define coherence rules between `personalidade_big_five` and `vieses` attributes:
  - **High Conscienciosidade (70-100)** → High `vies_status_quo` (70-90), Low `desconto_hiperbolico` (10-30)
  - **Low Conscienciosidade (0-30)** → Low `vies_status_quo` (10-35), High `desconto_hiperbolico` (60-85)
  - **High Neuroticismo (70-100)** → High `aversao_perda` (70-95), High `sobrecarga_informacao` (60-85)
  - **Low Neuroticismo (0-30)** → Low `aversao_perda` (10-35), Low `sobrecarga_informacao` (15-40)
  - **High Abertura (70-100)** → Low `vies_confirmacao` (10-35), Low `sobrecarga_informacao` (15-40)
  - **Low Abertura (0-30)** → High `vies_confirmacao` (60-85), High `vies_status_quo` (60-85)
  - **High Amabilidade (70-100)** → Low `vies_confirmacao` (15-40), Moderate `ancoragem` (40-60)
  - **Low Amabilidade (0-30)** → High `vies_confirmacao` (65-90), High `ancoragem` (60-85)
  - **High Extroversao (70-100)** → Moderate-High `desconto_hiperbolico` (50-80), Low `sobrecarga_informacao` (20-45)
  - **Low Extroversao (0-30)** → Low-Moderate `desconto_hiperbolico` (20-50), Moderate `sobrecarga_informacao` (45-70)

- **FR-004**: System MUST implement validation logic that enforces personality-bias coherence rules during synth generation

- **FR-005**: System MUST provide meaningful error messages when manually-set bias values conflict with personality traits (for testing/validation purposes)

- **FR-006**: Updated schema MUST use semantic versioning to indicate breaking change (increment major version from current version)

- **FR-007**: System MUST maintain backward compatibility by allowing reading of old schema synths while writing new synths with simplified schema

### Key Entities *(include if feature involves data)*

- **Synth Schema**: JSON Schema document defining the structure and validation rules for synthetic personas
  - Properties: All demographic, psychographic, behavioral, and cognitive attributes
  - Relationships: References to Big Five personality model and cognitive bias taxonomy
  - Version: Semantic versioning to track schema evolution

- **Personality-Bias Coherence Rules**: Mapping between Big Five personality traits and cognitive bias intensities
  - Properties: Trait name, trait value range, bias name, bias value range, correlation type (positive/negative)
  - Purpose: Ensure psychological realism in generated synths

- **Synth Instance**: Individual synthetic persona conforming to the schema
  - Properties: All attributes defined in schema
  - Validation: Must pass both schema validation and coherence rule validation

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Schema file size is reduced by at least 15% compared to original schema (due to removal of 5 field definitions and their documentation)

- **SC-002**: Synth generation time decreases by at least 10% due to fewer fields to populate

- **SC-003**: 100% of newly generated synths pass personality-bias coherence validation with zero conflicts

- **SC-004**: All synths with extreme personality trait values (0-20 or 80-100) exhibit corresponding bias patterns within defined ranges

- **SC-005**: Schema validation rejects any synth containing removed fields (`hobbies`, `valores`, `estilo_vida`, `uso_tecnologia`, `comportamento_compra`)

- **SC-006**: Developers can understand the complete personality-bias relationship by reading coherence rule documentation (measured by successful implementation without clarification questions)

## Assumptions

1. **Psychological Validity**: The personality-bias coherence rules are based on established psychological research (Big Five correlations with decision-making biases)

2. **Data Migration**: Existing synths in the database will need migration to strip removed fields, but this is a separate implementation concern

3. **No New Fields**: This feature only removes and creates coherence rules; it does not add new fields to the schema

4. **Interests Sufficiency**: The `psicografia.interesses` field provides sufficient behavioral insight to replace the removed `hobbies`, `valores`, and `estilo_vida` fields

5. **Rule Ranges**: The specified bias value ranges for each personality trait level allow for natural variation while maintaining coherence (not overly restrictive)

6. **English/Portuguese Mix**: Schema uses Portuguese field names (following existing convention) with English documentation where helpful

## Dependencies

- Current JSON Schema file located at `data/schemas/synth-schema-cleaned.json`
- Existing synth generation logic that populates schema fields
- Any validation logic currently checking the fields to be removed

## Out of Scope

- Migration scripts for existing synth data (separate implementation task)
- UI changes to reflect simplified schema (handled separately)
- Performance optimization beyond field reduction (separate effort)
- Addition of new fields or attributes
- Changes to demographic or capability-related fields
