# Research: Sankey Diagram for Outcome Flow Visualization

**Feature**: 025-sankey-diagram
**Date**: 2025-12-31

## Research Questions

### 1. Gap Calculation Algorithm for Root Cause Diagnosis

**Question**: How should we calculate gaps to determine root causes for "did_not_try" and "failed" outcomes?

**Decision**: Use the existing probability calculation formulas from `probability.py` but invert them to identify which gap is largest.

**Rationale**: The existing simulation engine already calculates `p_attempt` using:
- `w_motivation * motivation + w_trust * trust - w_risk * perceived_risk - w_effort * initial_effort`

For root cause diagnosis, we calculate gaps:
- `motivation_gap = initial_effort - motivation` (effort exceeds motivation)
- `trust_gap = perceived_risk - trust` (risk exceeds trust)
- `friction_gap = complexity - friction_tolerance` (complexity exceeds tolerance)

The largest positive gap indicates the primary barrier.

**Alternatives considered**:
1. Use raw score differences without weighting - rejected because weights reflect actual impact on behavior
2. Use probability derivatives - rejected as overly complex for visualization purposes
3. Simple threshold comparison - rejected as less accurate than gap-based approach

### 2. Scorecard Dimension Sampling

**Question**: Should we use the scorecard's point estimate (score) or sample from uncertainty range (min/max)?

**Decision**: Use the point estimate (`score` field) from each ScorecardDimension.

**Rationale**:
- The simulation already uses point estimates for probability calculations
- Using uncertainty ranges would require re-running the Monte Carlo simulation
- For aggregated visualization, the point estimate provides consistent interpretation

**Alternatives considered**:
1. Sample from [min_uncertainty, max_uncertainty] range - rejected as inconsistent with how simulation was run
2. Use midpoint of uncertainty range - rejected as essentially equivalent to using score

### 3. Dominant Outcome Calculation

**Question**: How should we determine a synth's dominant outcome from their rate distributions?

**Decision**: The dominant outcome is the outcome with the highest rate (did_not_try_rate, failed_rate, success_rate). For ties, use priority order: success > failed > did_not_try.

**Rationale**:
- Each synth has rates that sum to 1.0 (within tolerance)
- The highest rate represents the most likely outcome across Monte Carlo executions
- Tie-breaking favors more positive outcomes (success over failure)

**Alternatives considered**:
1. Use threshold-based classification (e.g., success_rate > 0.5) - rejected as arbitrary
2. Weighted scoring - rejected as unnecessarily complex

### 4. Synth Traits for Gap Calculation

**Question**: Should we use latent traits or sample a user state for gap calculation?

**Decision**: Use the stored `synth_attributes.latent_traits` (capability_mean, trust_mean, friction_tolerance_mean) directly, without scenario modifiers.

**Rationale**:
- The synth's simulation attributes are stored with each outcome in `synth_outcome.synth_attributes`
- These represent the synth's baseline characteristics
- The gap calculation identifies inherent mismatches, not scenario-specific ones
- Using stored traits ensures consistency with simulation results

**Alternatives considered**:
1. Re-sample user state with scenario modifiers - rejected as would introduce randomness
2. Use observable traits instead of latent traits - rejected as latent traits are directly comparable to scorecard dimensions

### 5. Frontend Charting Library

**Question**: Which library should render the Sankey diagram?

**Decision**: Use D3-Sankey (`d3-sankey` + `d3-shape`) with custom React component.

**Rationale**:
- Lightweight (~50 KB) compared to Plotly (~3.5 MB)
- Full control over styling and visual appearance
- Professional look with smooth curves and proper link rendering
- D3 is the industry standard for data visualization
- Recharts Sankey has limited customization and basic appearance

**Alternatives considered**:
1. Recharts Sankey - rejected as visually basic and limited customization
2. Plotly.js - rejected as too heavy (~3.5 MB bundle increase)
3. @nivo/sankey - good option but adds another chart library to maintain

### 6. Root Cause Labels

**Question**: Should labels be hardcoded in Portuguese or use i18n?

**Decision**: Hardcode in Portuguese initially with labels defined as constants for easy future i18n.

**Rationale**:
- Spec explicitly requires Portuguese labels
- Current UI does not have i18n infrastructure for charts
- Using constants makes future i18n migration straightforward

**Labels defined**:
```typescript
// did_not_try causes
"Esforço inicial alto"    // motivation_gap (initial_effort > motivation)
"Risco percebido"         // trust_gap (perceived_risk > trust)
"Complexidade aparente"   // friction_gap (complexity > friction_tolerance)

// failed causes
"Capability insuficiente" // capability_gap (complexity > capability)
"Desistiu antes do valor" // patience_gap (time_to_value > friction_tolerance)
```

### 7. Scorecard Access for Gap Calculation

**Question**: How should the service access the feature scorecard dimensions?

**Decision**: Retrieve the experiment's embedded scorecard from the analysis run's linked experiment.

**Rationale**:
- Each experiment has a `scorecard` field with the full FeatureScorecard
- The analysis run is linked to an experiment via `experiment_id`
- This is consistent with how AnalysisExecutionService accesses the scorecard

**Data flow**:
```
analysis_id → AnalysisRun → experiment_id → Experiment → scorecard → dimensions
```

### 8. Caching Strategy

**Question**: Should we cache the Sankey flow data?

**Decision**: Follow existing Phase 1 chart caching pattern (staleTime: 5 minutes, cache by analysis_id).

**Rationale**:
- Sankey data is computed from static synth outcomes (no parameters change it)
- 5-minute stale time matches TryVsSuccess and Distribution charts
- Cache key: `['analysis', experimentId, 'sankey-flow']`

### 9. Tie-Breaking for Equal Gaps

**Question**: How should we handle cases where multiple gaps are exactly equal?

**Decision**: Use deterministic priority order as defined in spec edge cases.

**Priority order for did_not_try**:
1. motivation_gap (initial_effort barriers)
2. trust_gap (perceived risk barriers)
3. friction_gap (complexity barriers)

**Priority order for failed**:
1. capability_gap (skill barriers)
2. patience_gap (time-to-value barriers)

**Rationale**: Prioritizes actionable causes (effort/capability are more directly addressable than trust/patience).

### 10. Motivation Calculation for Gap Analysis

**Question**: How should we derive motivation for gap calculation since it's scenario-dependent?

**Decision**: Use `task_criticality` from the baseline scenario (0.5) as the motivation proxy.

**Rationale**:
- The analysis runs with the baseline scenario (scenario_id = "baseline")
- In baseline: motivation_modifier = 0.0, task_criticality = 0.5
- Therefore, motivation ≈ task_criticality = 0.5 for all synths
- This creates a fair comparison across synths

**Alternatives considered**:
1. Sample motivation per synth - rejected as introduces randomness
2. Use 0.0 (no motivation data) - rejected as unfair to compare against effort
3. Use trust_mean as motivation proxy - rejected as conceptually different

## Summary of Decisions

| Question | Decision |
|----------|----------|
| Gap calculation | Use difference between scorecard dimension and synth trait |
| Scorecard values | Use point estimate (score field) |
| Dominant outcome | Highest rate, ties favor success > failed > did_not_try |
| Synth traits | Use stored latent_traits from synth_attributes |
| Charting library | Recharts Sankey component |
| Labels | Portuguese hardcoded with constants |
| Scorecard access | Via experiment.scorecard |
| Caching | 5-minute staleTime, cache by analysis_id |
| Tie-breaking | Priority order: motivation > trust > friction (did_not_try), capability > patience (failed) |
| Motivation value | Use 0.5 (baseline scenario's task_criticality) |
