# Research Findings: Simplified Hypothesis Wizard

**Date**: 2026-01-28
**Feature**: Simplified Hypothesis Selection Wizard
**Purpose**: Document research decisions for scenario profiles, clarification questions, and qualitative response mapping

## Decision 1: Scenario Profile Parameter Mapping

**Question**: How should Conservative/Realistic/Optimistic profiles map to distribution parameters for each variable type?

**Decision**: Use multiplicative and additive adjustments based on distribution type and profile:

| Distribution | Parameter | Conservative | Realistic (Baseline) | Optimistic |
|--------------|-----------|--------------|---------------------|------------|
| Normal       | mean (μ)  | μ - 0.5σ     | μ                   | μ + 0.5σ   |
| Normal       | std (σ)   | σ × 1.5      | σ                   | σ × 0.75   |
| Uniform      | min       | min - 0.2×range | min              | min + 0.1×range |
| Uniform      | max       | max - 0.1×range | max              | max + 0.2×range |
| Beta         | α (success) | α × 0.7    | α                   | α × 1.3    |
| Beta         | β (failure) | β × 1.3    | β                   | β × 0.7    |
| LogNormal    | μ (log-mean) | μ - 0.3   | μ                   | μ + 0.3    |
| LogNormal    | σ (log-std)  | σ × 1.4   | σ                   | σ × 0.8    |
| Bernoulli    | p (success) | p × 0.8    | p                   | p × 1.2 (capped at 1.0) |
| Triangular   | min         | min - 0.15×range | min            | min + 0.1×range |
| Triangular   | mode        | mode - 0.1×range | mode           | mode + 0.1×range |
| Triangular   | max         | max - 0.1×range  | max            | max + 0.15×range |

**Range Clamping**: After adjustments, enforce `range_min` and `range_max` if specified in variable metadata.

**Rationale**:
- Conservative profile assumes worse outcomes (lower means, higher variance = more uncertainty)
- Optimistic profile assumes better outcomes (higher means, lower variance = more confidence)
- Realistic profile uses LLM-suggested market-average parameters as baseline (from existing `HypothesisParametrizerService`)
- Adjustments are moderate (±0.5σ, ×0.75-1.5 variance) to avoid extreme scenarios while providing meaningful differentiation
- Distribution-specific rules preserve statistical validity (e.g., Beta parameters maintain α, β > 0)

**Alternatives Considered**:
- **Fixed percentage adjustments** (e.g., ±20% for all parameters) - Rejected because different parameters have different sensitivities (variance scaling needs different treatment than mean shifting)
- **LLM-generated profiles** - Rejected due to cost (3 LLM calls per wizard run) and latency (15-20s instead of <1s)
- **User-configurable profiles** - Out of scope, reserved for future "custom profile" feature

**Implementation Note**: Apply profile adjustments AFTER LLM generates realistic baseline hypotheses, not during LLM prompt. This preserves LLM's domain knowledge while allowing fast profile switching.

---

## Decision 2: Criticality Ranking Algorithm

**Question**: How to identify 3-5 "critical" variables with highest impact and uncertainty?

**Decision**: Use composite criticality score combining impact and uncertainty:

```
criticality_score = impact_score × uncertainty_score

impact_score = (
    is_outcome × 3.0 +
    is_intervention × 2.0 +
    out_degree × 1.0 +
    (controllability == MEDIUM) × 1.5 +
    (controllability == HIGH) × 2.5
)

uncertainty_score = (
    distribution_variance_coefficient +
    (is_critical_uncertainty × 2.0)
)

distribution_variance_coefficient:
  - Normal/LogNormal: σ / μ (coefficient of variation)
  - Beta: sqrt(αβ / ((α+β)²(α+β+1))) (standard deviation)
  - Uniform: (max - min) / (max + min) (relative range)
  - Bernoulli: sqrt(p(1-p)) (standard deviation)
  - Triangular: (max - min) / mode (relative spread)
```

**Ranking Process**:
1. Calculate criticality_score for all variables
2. Sort descending by criticality_score
3. Take top N variables where N = min(5, max(3, num_critical_uncertainties))
4. Filter out variables with uncertainty_score < 0.3 (low uncertainty doesn't need clarification)

**Rationale**:
- Impact matters more than uncertainty (no point clarifying uncertain variables with low impact)
- Outcomes and interventions are prioritized (user cares most about these)
- Out-degree (number of downstream effects) indicates leverage points
- Controllability suggests variables user can adjust based on clarification
- `is_critical_uncertainty` flag (from variable metadata) allows domain experts to mark must-clarify variables

**Alternatives Considered**:
- **LLM-based ranking** - Rejected due to cost ($0.02 per call) and latency (3-5s)
- **Pure uncertainty ranking** - Rejected because high-uncertainty, low-impact variables waste user's time
- **Fixed variable selection** (e.g., always ask about outcomes) - Rejected because DAGs vary widely in structure

**Implementation Note**: Run ranking AFTER scenario profile selection, using profile-adjusted distributions for variance calculation. This ensures clarifications target the most uncertain variables post-profile.

---

## Decision 3: Qualitative Response Mapping

**Question**: How to map "more"/"less"/"equal"/"don't know" to quantitative distribution adjustments?

**Decision**: Apply response-specific adjustments to distribution parameters:

| Response     | Adjustment Strategy                                      | Example (Normal μ=10, σ=2) |
|--------------|----------------------------------------------------------|----------------------------|
| **"more"**   | Shift mean up by +0.5σ, reduce variance by 20%          | μ=11, σ=1.6                |
| **"less"**   | Shift mean down by -0.5σ, reduce variance by 20%        | μ=9, σ=1.6                 |
| **"equal"**  | Keep profile defaults (no adjustment)                    | μ=10, σ=2                  |
| **"don't know"** | Keep mean, increase variance by 50%                  | μ=10, σ=3                  |

**Distribution-Specific Rules**:

**Normal/LogNormal**:
- "more": μ += 0.5σ, σ ×= 0.8
- "less": μ -= 0.5σ, σ ×= 0.8
- "don't know": σ ×= 1.5

**Uniform**:
- "more": min += 0.2×range, max += 0.3×range
- "less": min -= 0.3×range, max -= 0.2×range
- "don't know": min -= 0.2×range, max += 0.2×range

**Beta** (success rate):
- "more": α ×= 1.3, β ×= 0.8 (shift toward success)
- "less": α ×= 0.8, β ×= 1.3 (shift toward failure)
- "don't know": α ×= 0.7, β ×= 0.7 (increase variance)

**Bernoulli** (probability):
- "more": p ×= 1.2 (capped at 1.0)
- "less": p ×= 0.8
- "don't know": Convert to Beta(α=p×10, β=(1-p)×10) with α×0.7, β×0.7 (wider uncertainty)

**Triangular**:
- "more": min += 0.1×range, mode += 0.15×range, max += 0.1×range
- "less": min -= 0.1×range, mode -= 0.15×range, max -= 0.1×range
- "don't know": min -= 0.2×range, max += 0.2×range

**Rationale**:
- "more" and "less" shift central tendency (mean/mode) while reducing variance (user has more confidence)
- "equal" preserves profile defaults (user confirms LLM guess was correct)
- "don't know" increases variance without shifting mean (user has no directional information, only acknowledges high uncertainty)
- Adjustments are moderate (±0.5σ, ±20-50% variance) to avoid over-correcting based on subjective input
- Variance reduction for "more"/"less" reflects that user provided information (less uncertainty)

**Alternatives Considered**:
- **Fixed percentage adjustments** (e.g., "more" = +20%) - Rejected because percentages interact poorly with different distribution scales
- **LLM re-parametrization** - Rejected due to cost and latency (would require 3-5 LLM calls per clarification)
- **Prompt user for numerical adjustments** - Out of scope (defeats purpose of qualitative wizard)

**Implementation Note**: Apply clarification adjustments AFTER scenario profile adjustments, treating profile-adjusted parameters as the baseline for clarification shifts.

---

## Decision 4: Decision Context Classification

**Question**: How to classify DAG as "simple" (3 questions max) vs "complex" (5 questions max)?

**Decision**: Use decision tree based on DAG structure:

```python
def classify_decision_context(dag: CausalDAG) -> Literal["simple", "complex"]:
    num_nodes = len(dag.nodes)
    num_edges = len(dag.edges)
    num_outcomes = sum(1 for v in dag.nodes if v.is_outcome)
    num_controllable = sum(1 for v in dag.nodes if v.controllability in [Controllability.MEDIUM, Controllability.HIGH])

    # Simple: small DAG with clear focus
    if num_nodes <= 5:
        return "simple"

    # Complex: large DAG or many outcomes/controllables
    if num_nodes > 10 or num_outcomes > 3 or num_controllable > 4:
        return "complex"

    # Medium: default to complex for safety (allow more questions)
    if num_edges / num_nodes > 1.5:  # Highly connected
        return "complex"

    return "simple"
```

**Question Limit Application**:
- Simple → max 3 clarification questions
- Complex → max 5 clarification questions

**Rationale**:
- Small DAGs (≤5 nodes) are inherently simple, few questions needed
- Large DAGs (>10 nodes) need more questions to capture critical uncertainties
- Multiple outcomes/controllables indicate complex decision space requiring more clarification
- High connectivity (edges/nodes > 1.5) suggests interdependent variables needing more questions
- Default to "complex" (5 questions) when ambiguous - better to ask slightly more questions than miss critical uncertainties

**Alternatives Considered**:
- **Fixed 5 questions for all** - Rejected because small DAGs don't need that many questions (user fatigue)
- **LLM-based classification** - Rejected due to cost and latency (unnecessary for simple heuristic)
- **User-selectable limit** - Rejected to maintain simplicity of wizard (no meta-configuration)

**Implementation Note**: Run classification BEFORE criticality ranking to determine how many top variables to select for clarification.

---

## Decision 5: LLM Prompt Engineering

**Question**: What prompts generate best scenario profiles and clarification questions?

### 5a. Scenario Profile Generation

**Decision**: Extend existing `HypothesisParametrizerService._build_parametrization_prompt()` with scenario profile hints.

**Prompt Extension** (add to existing prompt):
```
SCENARIO PROFILE: {profile_name}

{profile_name} profile guidance:
- Conservative: Assume worse-than-average outcomes, higher uncertainty. Use lower means for positive variables, higher means for negative variables, wider ranges.
- Realistic: Use market-average parameters based on domain knowledge. This is the default.
- Optimistic: Assume better-than-average outcomes, lower uncertainty. Use higher means for positive variables, lower means for negative variables, tighter ranges.

Note: Apply profile guidance when uncertain. Domain-specific knowledge takes precedence.
```

**Rationale**:
- Reuses existing LLM parametrization logic (gpt-4o with structured outputs)
- Profile hints guide LLM toward appropriate baseline without requiring complex post-processing
- Preserves LLM's domain knowledge (e.g., conversion rates typically 2-5%) while adjusting within those bounds
- One LLM call generates all hypotheses with profile awareness (vs 3 separate calls for each profile)

### 5b. Clarification Question Generation

**Decision**: Use algorithmic question generation (no LLM) based on variable metadata.

**Question Templates** (parameterized by variable):
```python
templates = {
    "frequency": "{variable_label} is more common or more rare in your context?",
    "magnitude": "{variable_label} tends to be higher or lower than average?",
    "volatility": "{variable_label} varies a lot or stays consistent?",
    "timing": "{variable_label} happens sooner or later than expected?",
}

def generate_question(variable: Variable) -> str:
    if variable.type == VariableType.EVENT:
        return templates["frequency"].format(variable_label=variable.label)
    elif variable.type == VariableType.METRIC:
        return templates["magnitude"].format(variable_label=variable.label)
    elif variable.type == VariableType.RATE:
        return templates["magnitude"].format(variable_label=variable.label)
    elif variable.type == VariableType.DURATION:
        return templates["timing"].format(variable_label=variable.label)
    else:
        return templates["magnitude"].format(variable_label=variable.label)
```

**Rationale**:
- Algorithmic generation is instant (<1ms) vs LLM (3-5s)
- Cost-free vs $0.01-0.02 per LLM call
- Templates are clear, testable, and consistent
- Variable type determines question framing (frequency for events, magnitude for metrics)
- Variable labels (from enrichment service) provide human-readable context

**Alternatives Considered**:
- **LLM-generated questions** - Rejected due to cost and latency (5 questions = $0.05-0.10, 15-25s)
- **Fixed generic question** ("Is this variable more or less?") - Rejected because less clear to users
- **User-provided question text** - Out of scope (requires UI for question customization)

**Implementation Note**: Use variable.label (from VariableEnrichmentService) for question text. Fall back to variable.name if label is empty.

---

## Decision 6: Backward Compatibility

**Question**: How to ensure wizard-generated hypotheses work with existing simulation engine?

**Decision**: Wizard uses existing `Hypothesis` entity and `HypothesisRepository` with no schema changes.

**Compatibility Checklist**:

- ✅ **Entity Structure**: `Hypothesis` entity unchanged (distribution_type, distrib_params, range_min, range_max all reused)
- ✅ **Distribution Types**: All DistributionType enum values (Normal, Uniform, Beta, LogNormal, Bernoulli, Triangular) supported
- ✅ **Parameter Shapes**:
  - NormalParams: μ, σ ✅
  - UniformParams: min, max ✅
  - BetaParams: α, β ✅
  - LogNormalParams: μ, σ ✅
  - BernoulliParams: p ✅
  - TriangularParams: min, mode, max ✅
- ✅ **Scenario Options**: Wizard does NOT populate scenario_options (reserved for controllable variables in manual editor)
- ✅ **Selected Scenario**: Wizard does NOT use selected_scenario field (profile selection is transient, not persisted)
- ✅ **Simulation Engine**: Engine reads `hypotheses` table via `HypothesisRepository.find_by_simulation_id()` - no changes needed
- ✅ **Versioning**: Wizard can optionally save hypothesis snapshot to `hypothesis_versions` table using existing versioning flow

**Persistence Strategy**:
- Scenario profile selection: NOT persisted (in-memory state during wizard)
- Clarification responses: NOT persisted (in-memory state during wizard)
- Final hypotheses: Persisted to `hypotheses` table (same as manual editor)
- User can save hypothesis version snapshot after wizard completion for comparison

**Rationale**:
- Zero schema changes = zero migration risk
- Wizard-generated hypotheses indistinguishable from manually-edited hypotheses at storage layer
- Wizard is a "hypothesis generation strategy" not a new entity type
- Preserves ability to switch between wizard and manual editor for same simulation

**Alternatives Considered**:
- **New `wizard_hypotheses` table** - Rejected because creates schema duplication and compatibility issues
- **Store wizard state in `hypotheses` table** - Rejected because pollutes hypothesis data with transient wizard metadata
- **Persist clarification responses in JSONB** - Rejected because not needed for simulation (only generation-time state)

**Implementation Note**: If future features need wizard provenance (e.g., "regenerate with different profile"), add optional JSONB metadata field to `hypotheses` table to store `generation_method: "wizard"`, `wizard_profile: "Conservative"`, `wizard_clarifications: [...]`.

---

## Research Summary

**Key Findings**:
1. **Scenario profiles**: Algorithmic adjustments to LLM-generated baselines (fast, predictable, testable)
2. **Criticality ranking**: Composite score (impact × uncertainty) identifies most valuable clarification targets
3. **Qualitative mapping**: Distribution-specific rules map responses to parameter adjustments
4. **Context classification**: Heuristic decision tree determines 3 vs 5 question limit
5. **Prompt engineering**: Minimal LLM changes (scenario hints only), algorithmic question generation (no LLM)
6. **Compatibility**: Full backward compatibility with existing simulation engine (zero schema changes)

**Implementation Implications**:
- **Low LLM cost**: 1 LLM call per wizard run (same as current flow, just add scenario hint to prompt)
- **Fast execution**: Scenario adjustment <100ms, criticality ranking <50ms, question generation <1ms
- **High testability**: All algorithms deterministic (no LLM variability in ranking or mapping)
- **Safe deployment**: No schema changes, wizard-generated hypotheses identical to manual at storage layer

**Risks Mitigated**:
- **LLM cost explosion**: Avoided by using algorithmic methods where possible (ranking, question gen, adjustments)
- **Latency**: Total wizard time ~5-10s (1 LLM call + fast algorithms) vs 15-25s if using LLM for everything
- **Schema migration**: Zero migration risk by reusing existing entities
- **Compatibility**: Full backward compatibility ensures safe rollout (can A/B test wizard vs manual)

**Next Phase**: Proceed to Phase 1 (Design & Contracts) with these decisions finalized.
